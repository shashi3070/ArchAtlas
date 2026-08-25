"""Component catalog API contract tests (Phase 0 deliverable)."""

EXPECTED_PHASE2_TYPES = {
    "client",
    "api",
    "load_balancer",
    "cdn",
    "redis",
    "postgresql",
    "mongodb",
    "kafka",
    "rabbitmq",
    "worker",
    "object_storage",
}


def test_list_components_returns_seeded_catalog(client) -> None:
    resp = client.get("/api/components")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 11
    types = {item["type"] for item in items}
    assert EXPECTED_PHASE2_TYPES <= types


def test_every_entry_has_required_fields(client) -> None:
    for item in client.get("/api/components").json():
        assert item["type"]
        assert item["category"]
        assert item["name"]
        assert item["version"].count(".") == 2


def test_get_single_component(client) -> None:
    resp = client.get("/api/components/redis")
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["category"] == "cache"
    # Knowledge block sanity per SYSTEM.md section 10.
    assert "durable_primary_storage" in entry["does_not_solve"]
    assert "cache_aside" in entry["common_patterns"]
    assert "hot_key" in entry["failure_modes"]
    assert entry["capacity_defaults"]["reads_per_sec_per_node"] > 0


def test_unknown_component_returns_404(client) -> None:
    resp = client.get("/api/components/definitely_not_real")
    assert resp.status_code == 404


# ── Guide endpoint tests ──────────────────────────────────────────────

def test_get_component_guide(client) -> None:
    resp = client.get("/api/components/redis/guide")
    assert resp.status_code == 200
    guide = resp.json()
    assert "s" in guide  # summary
    assert "w" in guide  # how it works
    assert "use" in guide
    assert "avoid" in guide
    assert "tips" in guide
    assert len(guide["use"]) >= 2
    assert len(guide["tips"]) >= 1


def test_guide_returns_404_for_missing(client) -> None:
    resp = client.get("/api/components/definitely_not_real/guide")
    assert resp.status_code == 404


def test_guide_covers_all_catalog_types(client) -> None:
    """Every catalog component should have a corresponding guide."""
    catalog = client.get("/api/components").json()
    missing = []
    for item in catalog:
        ctype = item["type"]
        resp = client.get(f"/api/components/{ctype}/guide")
        if resp.status_code != 200:
            missing.append(ctype)
    assert missing == [], f"Guides missing for: {missing}"
