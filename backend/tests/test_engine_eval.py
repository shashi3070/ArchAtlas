"""Engine-level tests: schema conformance, determinism, metrics composition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from app.content.loader import load_catalog
from app.core.config import default_schemas_dir
from app.domain.validate import normalize_graph
from app.evaluation.engine import RULE_VERSION, canonical_json, run_evaluation
from tests.eval_helpers import CLIENT_LB_API_DB, e, g, n


def _eval(graph: dict[str, Any]) -> dict[str, Any]:
    return run_evaluation(normalize_graph(graph), load_catalog())


def _schema_validator() -> Draft202012Validator:
    schema_path = Path(default_schemas_dir()) / "evaluation.schema.json"
    with schema_path.open("r", encoding="utf-8") as fh:
        return Draft202012Validator(json.load(fh))


def test_output_conforms_to_evaluation_schema():
    evaluation = _eval(CLIENT_LB_API_DB)
    errors = list(_schema_validator().iter_errors(evaluation))
    assert not errors, [err.message for err in errors[:5]]


def test_engine_pure_until_stamped():
    evaluation = _eval(CLIENT_LB_API_DB)
    assert "evaluated_at" not in evaluation
    assert evaluation["rule_version"] == RULE_VERSION


def test_determinism_byte_identical_reruns():
    first = canonical_json(_eval(CLIENT_LB_API_DB))
    second = canonical_json(_eval(CLIENT_LB_API_DB))
    assert first == second


def test_summary_shape_and_dimension_count():
    evaluation = _eval(CLIENT_LB_API_DB)
    dims = evaluation["summary"]["dimension_scores"]
    assert len(dims) == 8
    for dim in dims:
        assert 0.0 <= dim["score"] <= 100.0
        assert dim["status"] in ("info", "pass", "unknown", "warning", "fail")


def test_overall_fail_on_critical_rule(catalog=None):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2), n("db", "postgresql")],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    evaluation = _eval(graph)
    assert evaluation["summary"]["overall_status"] == "fail"


def test_metrics_block_reflects_traffic_model():
    graph = g(
        CLIENT_LB_API_DB["nodes"],
        CLIENT_LB_API_DB["edges"],
        traffic_model={"rps": 12000, "read_ratio": 0.75},
    )
    metrics = _eval(graph)["metrics"]
    assert metrics["demand_rps_estimated"] == 12000.0
    assert metrics["read_rps_estimated"] == 9000.0
    assert metrics["write_rps_estimated"] == 3000.0
    assert metrics["node_count"] == 4
    assert metrics["edge_count"] == 3


def test_unknown_demand_never_guessed_in_metrics():
    metrics = _eval(g([n("c", "client"), n("api", "api")], [e("e1", "c", "api")]))["metrics"]
    assert metrics["demand_rps_estimated"] is None
    assert metrics["read_rps_estimated"] is None
    assert metrics["write_rps_estimated"] is None


def test_low_confidence_findings_do_not_punish_scores():
    from app.evaluation.metrics import dimension_scores

    scores = dimension_scores(
        [
            {
                "rule_id": "scale.single_compute_high_traffic",
                "status": "UNKNOWN",
                "message": "?",
                "severity": "critical",
                "confidence": "low",
            }
        ]
    )
    scalability = next(d for d in scores if d["dimension"] == "scalability")
    assert scalability["score"] == 100.0
    assert scalability["status"] == "info"


def test_fail_deducts_by_severity_weight():
    from app.evaluation.metrics import SEVERITY_WEIGHT, dimension_scores

    scores = dimension_scores(
        [
            {
                "rule_id": "scale.db_write_bottleneck",
                "status": "FAIL",
                "message": "x",
                "severity": "critical",
                "confidence": "high",
            }
        ]
    )
    scalability = next(d for d in scores if d["dimension"] == "scalability")
    assert scalability["score"] == round(100 - SEVERITY_WEIGHT["critical"], 1)
    assert scalability["status"] == "fail"


def test_spof_entries_have_required_shape():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=1), n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    spofs = _eval(graph)["spofs"]
    assert spofs, "lone api in front of the datastore must surface a SPOF"
    for entry in spofs:
        assert set(entry) >= {"node_id", "blast_radius", "reason"}
        assert entry["blast_radius"] in ("total", "major", "partial")


def test_recommendations_capped_and_shaped():
    graph = g(
        [n("c", "client"), n("a1", "api", replicas=2), n("a2", "api", replicas=2),
         n("db", "mongodb")],
        [e("e1", "c", "a1"), e("e2", "a1", "db"), e("e3", "a2", "db")],
        traffic_model={"rps": 90000, "read_ratio": 0.9},
    )
    evaluation = _eval(graph)
    recs = evaluation["recommendations"]
    assert len(recs) <= 8
    for rec in recs:
        assert set(rec) >= {"problem", "recommendation", "expected_benefit", "confidence"}


def test_requirement_outcomes_cover_every_requirement():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=60), n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        requirements=[
            {"id": "tput", "validation_rules": ["rps >= 50000"]},
            {"id": "vague", "description": "be fast"},
        ],
    )
    outcomes = {o["requirement_id"]: o for o in _eval(graph)["requirement_outcomes"]}
    assert set(outcomes) == {"tput", "vague"}
    assert outcomes["tput"]["status"] in ("satisfied", "at_risk", "violated")
    assert outcomes["vague"]["status"] == "not_evaluable"
