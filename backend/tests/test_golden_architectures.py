"""Golden architecture fixtures: calibration contract for the rule engine.

Good fixtures must produce zero FAILs (warnings allowed); broken fixtures
must trip their targeted rules. These files double as Phase-4 drill starts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.content.loader import load_catalog
from app.core.config import default_content_dir
from app.domain.validate import normalize_graph
from app.evaluation.engine import run_evaluation

GOLDEN_DIR = Path(default_content_dir()) / "golden_architectures"

GOOD_FIXTURES = ("url_shortener_good", "secure_baseline_good")

EXPECTED_FAILS: dict[str, set[str]] = {
    "url_shortener_broken": {
        "ha.single_database",
        "perf.no_cache_high_read",
        "scale.db_read_bottleneck",
        "scale.single_compute_high_traffic",
        "sec.missing_authentication",
    },
    "notification_async_bad": {
        "cons.async_where_sync_required",
        "rel.missing_idempotency",
    },
    "queue_no_workers": {
        "edge.queue_unconsumed",
        "scale.queue_consumer_shortage",
    },
    "overloaded_db": {
        "scale.db_write_bottleneck",
        "scale.db_read_bottleneck",
    },
    "disconnected": {"graph.no_ingress"},
}


def _fixture(name: str) -> dict[str, Any]:
    with (GOLDEN_DIR / f"{name}.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _evaluate(name: str) -> dict[str, Any]:
    return run_evaluation(normalize_graph(_fixture(name)), load_catalog())


@pytest.mark.parametrize("name", GOOD_FIXTURES)
def test_good_fixture_has_zero_fails(name: str):
    evaluation = _evaluate(name)
    fails = [r["rule_id"] for r in evaluation["rule_results"] if r["status"] == "FAIL"]
    assert not fails, f"{name} regressed: {fails}"
    assert evaluation["summary"]["overall_status"] == "warning"


@pytest.mark.parametrize("fixture_name", sorted(EXPECTED_FAILS))
def test_broken_fixture_fails_list(fixture_name: str):
    evaluation = _evaluate(fixture_name)
    actual = {r["rule_id"] for r in evaluation["rule_results"] if r["status"] == "FAIL"}
    missing = EXPECTED_FAILS[fixture_name] - actual
    assert not missing, f"{fixture_name} no longer trips: {sorted(missing)}"


def test_all_fixtures_exist_and_are_valid_documents():
    names = {p.stem for p in GOLDEN_DIR.glob("*.json")}
    assert GOOD_FIXTURES and set(EXPECTED_FAILS) <= names
    for fixture_name in names:
        doc = _fixture(fixture_name)
        assert {"id", "version", "nodes", "edges"} <= set(doc)


def test_every_fixture_evaluation_is_deterministic():
    for path in sorted(GOLDEN_DIR.glob("*.json")):
        graph = normalize_graph(_fixture(path.stem))
        first = run_evaluation(graph, load_catalog())
        second = run_evaluation(graph, load_catalog())
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
