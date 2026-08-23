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
