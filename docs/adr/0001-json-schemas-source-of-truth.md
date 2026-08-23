# ADR 0001: JSON Schemas as the single source of truth for canonical models

- **Status:** Accepted
- **Date:** 2026-08-23
- **Deciders:** Platform owner, per PLAN.md section 7

## Context

The platform's core invariant (SYSTEM.md section 64, Invariant 1) requires the
frontend and backend to share one canonical schema for `ArchitectureGraph` and
related models. Duplicated hand-written models in TypeScript and Python would
inevitably drift, breaking the "architecture is data" principle and the
reproducibility of deterministic evaluation.

## Decision

1. All canonical data shapes live as JSON Schema draft 2020-12 files in
   `schemas/`.
2. Backend Pydantic v2 models are generated via `datamodel-code-generator`
   (`backend/scripts/gen_models.py`) into
   `backend/app/domain/schemas_generated/`.
3. Frontend TS types are generated via `json-schema-to-typescript`
   (`frontend/scripts/generate-types.mjs`) into `frontend/src/types/generated/`.
4. Generated artifacts are committed; CI regenerates them and fails on any
   drift between schemas and generated code.
5. Content files (`content/components/*.json`, later challenges/scenarios) are
   validated against these schemas at load time; violations crash startup.

## Consequences

- Positive: one contract; drift is impossible to merge silently; content is
  machine-checkable from day one.
- Negative: contributors must regenerate after schema edits (CI enforces);
  the composite architecture schema generates a small package rather than a
  single module due to modular-reference mode of the generator.
- The composite `architecture/` package duplicates the standalone node/edge/
  requirement/constraint modules; acceptable duplication for P0 clarity,
  revisit if it causes confusion.

## Compliance check performed at Phase 0

- Generated models parse a sample canonical graph and the seeded redis catalog
  entry (verified locally during Phase 0).
