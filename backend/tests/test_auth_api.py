"""Tests for auth API routes and Groq model listing."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


# ── Auth endpoint tests ───────────────────────────────────────


class TestGoogleLogin:
    @patch("app.api.routes.auth.get_settings")
    def test_login_returns_503_without_google_client_id(
        self, mock_settings: MagicMock
    ) -> None:
        """Google login returns 503 when SDP_GOOGLE_CLIENT_ID not set."""
        mock_settings.return_value = MagicMock(
            google_client_id="",
            jwt_secret="test-secret",
        )
        resp = client.post("/api/auth/google", json={"credential": "fake-token"})
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"]

    @patch("app.api.routes.auth.get_settings")
    def test_login_rejects_invalid_token(self, mock_settings: MagicMock) -> None:
        """Google login returns 401 for invalid Google token."""
        mock_settings.return_value = MagicMock(
            google_client_id="test-client-id.apps.googleusercontent.com",
            jwt_secret="test-secret",
        )
        with patch("app.api.routes.auth.verify_google_token") as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            resp = client.post(
                "/api/auth/google",
                json={"credential": "invalid-token"},
            )
            assert resp.status_code == 401
            assert "Invalid Google token" in resp.json()["detail"]

    @patch("app.api.routes.auth.get_settings")
    def test_login_succeeds_with_valid_token(self, mock_settings: MagicMock) -> None:
        """Google login returns JWT on valid token."""
        mock_settings.return_value = MagicMock(
            google_client_id="test-client-id.apps.googleusercontent.com",
            jwt_secret="test-secret",
        )
        with patch("app.api.routes.auth.verify_google_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "google-user-123",
                "email": "test@gmail.com",
                "name": "Test User",
                "picture": "https://example.com/photo.jpg",
            }
            resp = client.post(
                "/api/auth/google",
                json={"credential": "valid-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert data["user"]["email"] == "test@gmail.com"
            assert data["user"]["tier"] == "free"
            assert data["token_type"] == "bearer"


class TestGetMe:
    def test_me_returns_401_without_token(self) -> None:
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_returns_user_with_valid_token(self) -> None:
        from app.auth.jwt import create_access_token

        token = create_access_token(
            {
                "sub": "u1",
                "email": "a@b.com",
                "name": "A",
                "picture": "",
                "tier": "free",
            },
            secret="test-secret",
        )
        # Patch settings for this test
        with patch("app.api.routes.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(jwt_secret="test-secret")
            with patch("app.auth.dependencies.get_settings") as dep_settings:
                dep_settings.return_value = MagicMock(jwt_secret="test-secret")
                resp = client.get(
                    "/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 200
                data = resp.json()
                assert data["email"] == "a@b.com"
                assert data["tier"] == "free"
                assert "rate_limit" in data


class TestRateLimit:
    def test_rate_limit_status_for_anonymous(self) -> None:
        resp = client.get("/api/auth/rate-limit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "anonymous"
        assert data["daily_limit"] == 50


# ── Groq model listing tests ──────────────────────────────────


class TestGroqModels:
    def test_list_groq_models(self) -> None:
        resp = client.get("/api/models/groq")
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "groq"
        assert len(data["models"]) == 9
        assert "free_tier_limits" in data
        assert data["free_tier_limits"]["requests_per_day_per_user"] == 1000
        assert data["free_tier_limits"]["cooldown_seconds"] == 10

    def test_get_specific_model(self) -> None:
        resp = client.get("/api/models/groq/detail?model_id=openai/gpt-oss-120b")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "openai/gpt-oss-120b"
        assert data["requests_per_day"] == 1000
        assert data["tokens_per_day"] == 200000

    def test_get_unknown_model(self) -> None:
        resp = client.get("/api/models/groq/detail?model_id=nonexistent/model")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_models_all_have_rate_limits(self) -> None:
        resp = client.get("/api/models/groq")
        data = resp.json()
        for model in data["models"]:
            assert "requests_per_minute" in model
            assert "requests_per_day" in model
            assert "tokens_per_minute" in model
            assert "tokens_per_day" in model
            assert "free" in model
