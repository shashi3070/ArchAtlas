#!/usr/bin/env python
"""Generate Pydantic models from the canonical JSON Schemas.

Usage (from repo root or backend/):
    python backend/scripts/gen_models.py

Outputs one module per schema into backend/app/domain/schemas_generated/.
Generated code is committed; CI regenerates and fails on drift.
Requires the ``dev`` extras (datamodel-code-generator).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
OUTPUT_DIR = REPO_ROOT / "backend" / "app" / "domain" / "schemas_generated"

# schema filename -> generated module name
# The composite architecture schema references node/edge/requirement/constraint
# schemas; datamodel-code-generator switches to "modular references" mode and
# requires a *directory* output (one module per referenced schema + __init__).
TARGETS = {
    "node.schema.json": "node_models.py",
    "edge.schema.json": "edge_models.py",
    "requirement.schema.json": "requirement_models.py",
    "constraint.schema.json": "constraint_models.py",
    "component.schema.json": "component_models.py",
    "challenge.schema.json": "challenge_models.py",
    "evaluation.schema.json": "evaluation_models.py",
    "scenario.schema.json": "scenario_models.py",
}
MODULAR_TARGETS = {
    "architecture.schema.json": "architecture",
}

COMMON_FLAGS = [
    "--input-file-type=jsonschema",
    "--output-model-type=pydantic_v2.BaseModel",
    "--target-python-version=3.11",
    "--disable-timestamp",
]


def _find_codegen() -> str:
    exe = Path(sys.executable).parent / (
        "datamodel-codegen.exe" if sys.platform == "win32" else "datamodel-codegen"
    )
    if exe.exists():
        return str(exe)
    return "datamodel-codegen"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codegen = _find_codegen()
    failures: list[str] = []
    generated = 0
    for schema_name, module_name in TARGETS.items():
        out_path = OUTPUT_DIR / module_name
        cmd = [
            codegen,
            "--input",
            str(SCHEMAS_DIR / schema_name),
            "--output",
            str(out_path),
            *COMMON_FLAGS,
        ]
        print(f"[gen] {schema_name} -> {module_name}")
        result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
        if result.returncode != 0:
            failures.append(schema_name)
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        else:
            generated += 1
    for schema_name, pkg_name in MODULAR_TARGETS.items():
        out_dir = OUTPUT_DIR / pkg_name
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            codegen,
            "--input",
            str(SCHEMAS_DIR / schema_name),
            "--output",
            str(out_dir),
            *COMMON_FLAGS,
        ]
        print(f"[gen] {schema_name} -> {pkg_name}/ (modular)")
        result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
        if result.returncode != 0:
            failures.append(schema_name)
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        else:
            generated += 1
    if failures:
        print(f"\nFAILED for: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"\nDone. Generated {generated} targets in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
