# Implementation Plan — Interactive System Design Learning Platform

**Document:** `PLAN.md`
**Version:** 0.1
**Date:** 2026-08-23
**Status:** Approved implementation plan
**Companion document:** `SYSTEM.md` v0.1 (product/architecture specification)
**Codebase root (future):** `D:\Project\system_design\system-design-platform\`
**Development context:** Solo developer + AI coding assistance; every phase must end with something runnable.

---

## Current Stage (updated 2026-08-25)

**Repo:** https://github.com/shashi3070/ArchAtlas · branch `master`

| Phase | Status |
| --- | --- |
| 0–3 Foundation, engine, lab | ✅ Complete |
| 4 Challenge packs + run UI | ✅ Complete |
| 5 AI Tutor & Coach | ✅ Complete + hardening pass |
| 5.5 Node Library Expansion | ✅ Complete |
| Node Guides encyclopedia (5.6) | 🔄 In progress — content ~55%, UI pending |
| 6 Interview Agent | ⏳ Next |

**Delivered since Phase 5 core commit (`6975f78`):**
- Mentor chat hardening: strict JSON mode (`json_object` + gpt-oss low reasoning), live per-provider model listing (`GET /api/agent/models`), Groq default → `openai/gpt-oss-120b`, raised token budgets, clickable follow-up suggestion chips, "+ New chat", resumable scoped chat history (localStorage), LLMProviderError → HTTP 502 mapping, graceful non-JSON degradation.
- Canvas correctness: collision-proof node/edge id counters, shared fuzzy proposal applier (`applyProposal.ts`) with applied/skipped reporting, rewritten vertical barycenter auto-layout, always-on animated arrows (26px markers), right-click context menus.
- Challenge UX: spoiler-gated solution reveal (server-enforced 403), challenge-scoped Ask AI with explain-result/solution actions, Configure opens as centered modal above panels, duplicate-no-longer-drags-source fix, Ask-AI/brief overlap fix.
- Phase 5.5: catalog grown **11 → 85 nodes** across 19 palette groups; new `kind` taxonomy (`concept`/`implementation`/`pattern`) in schema + generated models; engine role frozensets expanded additively (golden fixtures unchanged); pattern nodes excluded from SPOF/capacity/reach math and styled dashed-slate; lucide icon + category color per node (`nodeVisuals.ts`, 83 icons); palette search box; glossary +12 terms; project renamed **ArchAtlas** everywhere incl. `app_name`.
- Verification at last push: backend pytest **196 passed**, ruff + mypy clean; frontend lint/typecheck/12 vitest/production build all green.

**Next steps:** finish node-guide corpus (parts C/D) + guide viewer UI → Phase 6 Interview Agent (session state machine over the twelve-step method, interviewer prompts consuming board state, deterministic-first final report with communication scoring separate).

---

## Table of Contents

1. [How to Use This Document](#1-how-to-use-this-document)
2. [Executive Summary](#2-executive-summary)
3. [Guiding Principles](#3-guiding-principles)
4. [Competitive Research & Differentiation](#4-competitive-research--differentiation)
5. [Product Scope](#5-product-scope)
6. [System Architecture Overview](#6-system-architecture-overview)
7. [Canonical Data Model](#7-canonical-data-model)
8. [Component Taxonomy & Knowledge Model](#8-component-taxonomy--knowledge-model)
9. [Deterministic Evaluation Engine](#9-deterministic-evaluation-engine)
10. [Recommendation Engine](#10-recommendation-engine)
11. [AI / Agent Architecture](#11-ai--agent-architecture)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Backend Architecture](#13-backend-architecture)
14. [Persistence & Data Model](#14-persistence--data-model)
15. [Content Architecture](#15-content-architecture)
16. [Testing Strategy](#16-testing-strategy)
17. [Observability, Security & Cost](#17-observability-security--cost)
18. [Delivery Roadmap (Phases 0–11)](#18-delivery-roadmap-phases-011)
19. [MVP Boundary](#19-mvp-boundary)
20. [Repository Layout](#20-repository-layout)
21. [Definition of Done — First Production Milestone](#21-definition-of-done--first-production-milestone)
22. [Risks & Mitigations](#22-risks--mitigations)
23. [Success Metrics](#23-success-metrics)
24. [Open Decisions Log](#24-open-decisions-log)

---

# 1. How to Use This Document

`SYSTEM.md` is the **what and why** (product vision, principles, schemas, phases).
`PLAN.md` is the **how and when** (concrete technical decisions, work breakdown, sequencing, verification).

Rules of engagement for any developer or coding agent:

1. Read `SYSTEM.md` before making architectural changes (its Agent Rule #1).
2. Follow `PLAN.md` phase order. Do not skip ahead or reorder without updating both documents.
3. Each phase ends with a runnable, demonstrable increment and passing tests before the next begins.
4. Never violate the architectural invariants in `SYSTEM.md` §64 or the development rules in §61.

**Decisions locked during planning** (2026-08-23):

| Decision | Choice |
|---|---|
| Plan scope | Full roadmap — equal depth across all 12 phases |
| Repository location | `system-design-platform/` subfolder under workspace root |
| Team context | Solo developer + AI assistance |
| LLM providers | All four adapters (OpenAI, Anthropic, Gemini, Ollama) built day one behind one gateway |

---

# 2. Executive Summary

Build a web platform where learners **learn system design by building, breaking, fixing, and understanding systems**.

Core learning loop:

```text
Learn → Build → Evaluate → Diagnose → Modify → Re-evaluate → Understand
```

Three technical pillars (in investment-priority order per `SYSTEM.md` §81):

1. **Canonical ArchitectureGraph + requirement model + deterministic evaluation engine** — the platform's brain. Every component, connection, property, requirement, constraint, and scenario is structured data that rules, simulations, and agents reason over identically.
2. **The feedback loop between an architectural change and its consequences** — the product's soul. Adding Redis must visibly change read pressure, latency risk, and introduce new trade-offs.
3. **Contextual teaching grounded in the learner's actual architecture** — not generic chatbot responses. AI explains, hints, critiques; deterministic logic decides correctness.

Delivery: 12 phases (0–11), MVP after Phase 5 ≈ 12–16 weeks solo+AI, full roadmap beyond that. Stack: React + TypeScript + React Flow on the front; Python + FastAPI + PostgreSQL + Redis on the back; pluggable LLM gateway across OpenAI / Anthropic / Gemini / Ollama.

---

# 3. Guiding Principles

Restated from `SYSTEM.md` §4 because every implementation decision defers to them:

| # | Principle | Practical consequence |
|---|---|---|
| P1 | Architecture is data, not pixels | Canvas is a view. `ArchitectureGraph` is source of truth. No business logic in React components. |
| P2 | Deterministic first, AI second | If rules can answer, rules answer. LLM never sole authority for correctness. |
| P3 | Every recommendation explainable | No bare "Add Kafka." Always problem + evidence + trade-offs + what it does NOT solve. |
| P4 | No premature canonical architecture | Evaluator distinguishes Required / Strongly recommended / Optional / Context-dependent / Invalid. |
| P5 | Requirements drive evaluation | Components are good/bad *relative to workload*. Redis useless at 100 RPS, vital at 500K RPS. |
| P6 | Explain trade-offs | Every fix introduces new problems. Show them explicitly. |

Additional engineering invariants (`SYSTEM.md` §64): reproducible evaluations, immutable architecture versions, user-approved changes create new versions, agent modifications are preview/diffs requiring approval, versioned content/rules/prompts.

---

# 4. Competitive Research & Differentiation

## 4.1 Research Findings (verified Aug 2026)

### ScaleDojo (scaledojo.dev) — primary benchmark

- Six labs, 368+ challenges: HLD Architecture (100 levels), LLD Schema (80), API Design (50), GenAI Systems Lab (58), Forge Algorithm Lab (76), SQL Lab (50).
- Hybrid scoring: deterministic engine scores instantly across 5 dimensions (correctness, scalability, reliability, cost efficiency, latency) + Gemini-powered "AI Architect Review."
- **Murphy's Lab**: chaos simulator inside every HLD challenge — inject crashes/partitions/spikes, live metrics (latency ms, error %, throughput rps).
- Deep free content (Fundamentals courses, Origin Files, wiki, roadmap skill tree); freemium annual pricing with credit-metered LLM usage; XP, leaderboards, sequential unlocks, boss challenges; fictional-company scenario framing; certificates with public verification.

### MockArch (mockarch.in) — depth-in-narrowness

- Interview-simulator only; drag/drop palette; **connections carry semantic parameters** (throughput, read/write ratios on edges); explicit workload assumptions before simulating.
- Real-time traffic simulation + live latency metrics + monthly infra cost estimator ($ figures incl. multi-region transfer) — simulation is free-tier.
- Two-layer evaluation cleanly split by paywall: free deterministic rule checks (SPOF, bottleneck scanning); Pro LLM deep analysis capped at 20 runs/month.
- Composite score + sub-scores update live while fixing; "Apply Recommendations" button; over-engineering critiques ("K8s for a simple worker tier").

### sysd.ai — Design Drills

- Micro-format drills: pre-built working architecture with exactly one thing wrong; find and fix in ~60 seconds.
- Live telemetry panel narrates failure: "9k of 50k req/sec sustained, p99 1.9s, 18% errors, PostgreSQL CPU pinned" — metrics recover visibly when fixed correctly; wrong answers show *how* they fail.
- Full questions use Excalidraw embeds + AI evaluation + community peer review; 3 free drills, no signup.

### System Design Simulator (systemdesignsimulator.in)

- Client-side SPA; drag/drop infra palette (12+ types); wire topology then run:
  - **Trace mode** — watch one request traverse hop-by-hop.
  - **Monte Carlo mode** — simulate 1,000+ requests → p50/p95/p99 + error rates.
- Failure injection mid-request shows retries/fallbacks propagating. Deterministic simulation only; no AI layer; no curriculum.

### 10xarch (GitHub: AhmadMHawwash/10xarch)

- T3 stack: Next.js 14, tRPC, Zod, **React Flow v11**, Zustand, Drizzle ORM/Postgres, Clerk auth, Upstash Redis ratelimit, Stripe credits/subscriptions.
- AI-only feedback (chat assistant + structured feedback feature). Validates React Flow + Zustand stack choice. Org accounts, token top-ups.

### Sidebar (GitHub: JoshuaHirakawa/Sidebar)

- "Educational board game": React Flow board with 30+ categorized components; **phase-gated AI interviewer** (Requirements → High-Level Design → Deep Dive → Scale & Reliability → Feedback) fed by board state; scratch notes as first-class entity; PostgreSQL JSONB component props.

### LeetSys (leetsys.dev)

- Two-stage loop: guided walkthrough (chapters, architecture builds live, multiple-choice decision checkpoints with instant verdicts) → mock interview on the same system. Seniority-adaptive interviewer tone.

### systemdesign42/system-design-academy (27.9k★)

- Content-only index into systemdesign.one: Case Studies (Uber ETA @500k RPS, Netflix chaos eng., WhatsApp 50B msgs), Fundamentals A–Z, Interview frameworks, strong AI Engineering pillar (agents, MCP, RAG, vector DBs, agent memory, LLM evals), white papers (Dynamo, Spanner, XFaaS). Borrow taxonomy ideas, respect CC BY-NC-ND license — do not copy content.

## 4.2 Consolidated Feature Matrix

| Product | Interactive canvas | Drag/drop | AI feedback | Deterministic evaluation | Simulation | Learning/tutorials | Agent/AI-systems domain |
|---|---|---|---|---|---|---|---|
| ScaleDojo | ✅ | ✅ | ✅ | ✅ | Partial | ✅ | ✅ |
| MockArch | ✅ | ✅ | ✅ | ✅ | ✅ | Some | Some |
| sysd.ai | ✅ | ✅ | ✅ | Drills only | ✅ | Some | — |
| System Design Lab | ✅ | ✅ | ✅ | — | — | Some | — |
| Scalcraft | ✅ | ✅ | ✅ | — | — | Some | — |
| TheInfraLab | ✅ | ✅ | Gemini | Some | — | ✅ | — |
| 10xarch | ✅ | ✅ | ✅ | — | — | ✅ | — |
| System Design Simulator | ✅ | ✅ | — | ✅ | ✅ | Some | — |
| LeetSys | ✅ | ✅ | AI tutor | MCQs only | — | Strong | — |
| DevWhiteboard | ✅ | ✅ | AI agents | — | — | — | Strong |
| **This platform (target)** | ✅ | ✅ | ✅ (grounded) | ✅ first-class | ✅ analytical | ✅ linked to practice | ✅ first-class |

## 4.3 Patterns Worth Borrowing → Mapped to Our Roadmap

| Source pattern | Our implementation | Phase |
|---|---|---|
| sysd.ai Design Drills (broken arch, ~60s fix, failure telemetry) | **Repair Mode** short-form challenges generated from corrupted golden architectures | P4 |
| MockArch semantic edges (ratios on connections) | Edge properties: protocol, traffic_type, pattern, delivery, ordering | P2 |
| MockArch free-rules / paid-LLM split | Cost tiering: deterministic evaluation always free; AI actions metered | P5, §17 |
| ScaleDojo Murphy's Lab chaos injection | **Chaos Mode** event library with before/after deltas | P8 |
| Simulator trace vs Monte Carlo | Two simulation views over one analytical model | P7 |
| LeetSys learn→practice pairing | Every lesson ends with linked lab/challenge ("Interactive Lab", "Challenge" tabs) | P1/P4 |
| Sidebar phase-gated interviewer fed by board state | Interviewer Agent consumes ArchitectureGraph + RuleResults as context | P6 |
| ScaleDojo fictional-company scenarios | Scenario narrative field required in challenge schema | P4 |
| 10xarch/Sidebar React Flow + Zustand validation | Confirms frontend stack choice | P2 |

## 4.4 Positioning Statement

Do not compete on "we have AI feedback" — that is table stakes. Compete on:

> **We teach you system design by letting you change the system and observe the consequences.**

The verified open lane: **no competitor combines (a) deterministic evaluation as a first-class engine, (b) drill-style micro-fixes, (c) AI coaching grounded in that deterministic output, and (d) GenAI/agent systems as a first-class design domain.** That combination is the product.

Candidate taglines (from `SYSTEM.md` §79): "Build. Break. Fix. Learn System Design."

---

# 5. Product Scope

## 5.1 Target Users

- **Primary:** engineers preparing for system/senior/staff interviews.
- **Secondary:** engineers learning distributed systems and production architecture.
- **Future:** students, bootcamps, EMs, architects, corporate training.

## 5.2 Learning Modes (all planned, phased)

| Mode | Description | Phase |
|---|---|---|
| Learn | Concept → explanation → diagram → example → trade-offs → mini-exercise | P1 |
| Explore | Blank canvas, free experimentation, no scoring | P2 |
| Challenge | Requirements + constraints → build solution → scored evaluation | P4 |
| Repair | Broken architecture provided; identify and fix the flaw (drill-style) | P4 |
| Interview | AI interviewer: clarify → challenge → capacity → trade-offs → scored feedback | P6 |
| Chaos | Inject failures (cache/DB/region/spike/hot key/retry storm); respond | P8 |
| Compare | Evaluate two architectures side-by-side across 7 dimensions | P10 |

## 5.3 Core UX Surface (Lab screen)

```text
┌──────────────────────────────────────────────────────────┐
│ Challenge / Requirements                                  │
├────────────┬───────────────────────────┬─────────────────┤
│ Components │                           │ Evaluation      │
│ (palette)  │     ARCHITECTURE CANVAS   │ Requirements    │
│            │                           │ Bottlenecks     │
│ searchable,│   React Flow view of      │ Warnings        │
│ categorized│   ArchitectureGraph       │ Suggestions     │
│            │                           │ Metrics         │
└────────────┴───────────────────────────┴─────────────────┘
```

Evaluation panel shows dimension scores (Functionality, Scalability, Availability, Latency, Consistency, Security, Cost, Observability) — but every score expands into evidence-backed issues (⚠/✓ lines citing nodes, requirements, numbers).

---

# 6. System Architecture Overview

Target MVP topology (`SYSTEM.md` §32) — modular monolith, no Kafka/Kubernetes for the platform itself:

```text
React (Vite) ── HTTPS ──► FastAPI
                            ├── PostgreSQL   (authoritative state)
                            ├── Redis        (cache, rate limiting, sessions)
                            ├── Evaluation Engine  (pure domain, no I/O)
                            └── AI Gateway
                                  ├── OpenAI adapter
                                  ├── Anthropic adapter
                                  ├── Gemini adapter
                                  └── Ollama adapter (local/free path)
```

Long-term target (`SYSTEM.md` §80) adds Simulation and Challenge engines alongside Content/Evaluation, feeding a shared State/Results/Evidence store consumed by the AI layer. The modular monolith grows into that shape by extracting modules along module boundaries — not by premature microservices.

Key structural decision: **the Evaluation Engine and the canonical schemas have zero dependencies on FastAPI, SQLAlchemy, or any LLM SDK.** They are pure Python packages (and mirrored TS types) so they can be tested, versioned, and eventually extracted/reused independently.

---

# 7. Canonical Data Model

Single source of truth: **JSON Schema files in `schemas/`**, from which Pydantic models (backend) and TypeScript types (frontend) are generated. This enforces Invariant 1 (frontend and backend share one canonical schema).

## 7.1 Schemas to Author (Phase 0)

| File | Purpose |
|---|---|
| `architecture.schema.json` | ArchitectureGraph envelope: id, version, nodes[], edges[], groups[], requirements[], constraints[], traffic_model, deployment_model, metadata |
| `node.schema.json` | ArchitectureNode: id, type, name, technology, position{x,y}, properties{}, capacity{}, availability{}, deployment{}, metadata{} |
| `edge.schema.json` | ArchitectureEdge: id, source, target, direction, protocol, traffic_type, properties{} |
| `requirement.schema.json` | Requirement: id, category, description, target, unit, priority, validation_rules[] |
| `constraint.schema.json` | Constraint (budget, residency, consistency class, durability…) |
| `component.schema.json` | Component catalog entry incl. knowledge block (§8 below) |
| `challenge.schema.json` | Challenge YAML shape per `SYSTEM.md` §25 |
| `evaluation.schema.json` | EvaluationState, RuleResult, MetricScore, Recommendation, evidence structures |
| `scenario.schema.json` | Chaos/scenario events and expected behaviors (Phase 8) |

## 7.2 Key Modeling Rules

- Node `type` references the component catalog (§8); unknown types fail validation.
- Edge semantics are mandatory for evaluation-relevant edges: at minimum `traffic_type` (sync_request / async_event / replication / batch) and `direction`.
- Requirements carry machine-checkable `validation_rules[]` (e.g., `rps >= 100000`, `p95 <= 200ms`, `availability >= 99.99`) — the evaluator maps RuleResults onto requirement ids.
- Positions (`x,y`) are presentation-only; evaluators must be position-insensitive (P1).
- Graph serialization for agents is compact (summarized node/edge lists, not raw JSON dump) per `SYSTEM.md` §22.

## 7.3 Codegen Pipeline (Phase 0 deliverable)

```text
schemas/*.json
   ├── datamodel-code-generator ──► backend/app/domain/schemas/*.py  (Pydantic v2)
   └── json-schema-to-typescript ──► frontend/src/types/generated/*.ts
```

CI check: generated artifacts must be up-to-date with schemas (fail build on drift). Hand-written extensions go in separate wrapper types, never by editing generated files.

---

# 8. Component Taxonomy & Knowledge Model

## 8.1 Catalog (from `SYSTEM.md` §9)

Categories: Client, Edge, Traffic, Compute, Cache, Databases, Messaging, Storage, Observability, Reliability, AI/GenAI.

Phase 2 initial set (11): client, api, load_balancer, cdn, redis, postgresql, mongodb, kafka, rabbitmq, worker, object_storage.
Phase 3 additions: rate_limiter, api_gateway, dns, waf, memcached, mysql, dynamodb, cassandra, elasticsearch, sqs, sns, pubsub, nats, scheduler, serverless_function, vm/container/k8s, metrics, logs, tracing, alert_manager, circuit_breaker, retry_policy, replication, multi_az, multi_region.
Phase 9 additions: llm, embedding_model, vector_db, rag_retriever, reranker, prompt_gateway, model_router, guardrail, agent, tool, mcp_server, agent_memory, evaluation_service, ai_gateway.

Each component ships as a versioned catalog entry in `content/components/<id>.json`.

## 8.2 Knowledge Block (machine-readable, per `SYSTEM.md` §10)

Every component entry carries:

```json
{
  "type": "redis",
  "category": "cache",
  "capabilities": ["low_latency_reads", "temporary_storage", "distributed_cache"],
  "helps_with": ["database_read_load", "latency"],
  "does_not_solve": ["durable_primary_storage", "global_consistency"],
  "risks": ["cache_failure", "stale_data", "eviction", "invalidation"],
  "common_patterns": ["cache_aside", "write_through"],
  "failure_modes": ["node_failure", "network_partition", "hot_key"],
  "tradeoffs": ["cost", "consistency"]
}
```

Plus capacity defaults used by rules/simulation (e.g., default safe reads/sec, writes/sec, memory ceiling) — clearly labeled as assumptions with configurable values per node instance.

Authoring workflow per component (per `SYSTEM.md` §63): definition → knowledge → frontend representation (icon, palette group, property panel schema) → serialization → evaluation rules touching it → tests → docs.

---

# 9. Deterministic Evaluation Engine

The platform's foundation. Pure Python package `evaluation/`, independent of web frameworks and LLMs (Invariants 2, 3).

## 9.1 Pipeline

```text
ArchitectureGraph
   ↓ Normalize          (fill defaults, resolve aliases, validate against catalog)
   ↓ Validate Graph     (structural integrity rules)
   ↓ Build Dependency Graph (data-flow paths, ingress→egress, critical paths)
   ↓ Apply Rules        (registered, prioritized, category-tagged)
   ↓ Calculate Metrics  (per-dimension scores with contributing evidence)
   ↓ Detect Bottlenecks (capacity vs demand comparisons)
   ↓ Detect SPOFs       (single-instance critical-path analysis)
   ↓ Map to Requirements (rule results ↔ requirement_ids)
   ↓ Generate EvaluationState
```

Determinism guarantee: same graph + same requirements + same rule_version ⇒ identical result bytes.

## 9.2 Core Structures (per `SYSTEM.md` §12)

```python
class EvaluationRule:
    id: str                 # e.g. "availability.single_database"
    name: str
    category: str           # graph|scale|availability|performance|consistency|reliability|security|observability|cost
    priority: str           # critical|high|medium|low
    applies(ctx: EvalContext) -> bool
    evaluate(ctx: EvalContext) -> RuleResult

class RuleResult:
    rule_id: str
    status: PASS | WARNING | FAIL | INFO | UNKNOWN
    severity: str
    message: str
    evidence: list[str]           # concrete numbers/node facts, never vibes
    affected_nodes: list[str]
    affected_edges: list[str]
    requirement_ids: list[str]
    suggested_actions: list[SuggestedAction]   # action + rationale + tradeoffs + alternatives
    confidence: HIGH|MEDIUM|LOW
```

Confidence modeling (`SYSTEM.md` §15): results near thresholds or relying on incomplete capacity assumptions get `confidence: LOW/MEDIUM` with a stated reason. Prevents false precision.

## 9.3 Initial Rule Catalog (55 rule ids)

**Graph integrity (7)** — `graph.disconnected_required_component`, `graph.invalid_edge`, `graph.missing_source`, `graph.missing_destination`, `graph.inappropriate_cycle`, `graph.no_ingress`, `graph.no_data_store_required`

**Scalability (8)** — `scale.single_compute_high_traffic`, `scale.db_write_bottleneck`, `scale.db_read_bottleneck`, `scale.insufficient_worker_capacity`, `scale.queue_consumer_shortage`, `scale.partition_hot_spot`, `scale.missing_load_balancing`, `scale.missing_horizontal_scaling`

**Availability (6)** — `ha.single_database`, `ha.single_cache`, `ha.single_compute_node`, `ha.single_region`, `ha.single_load_balancer`, `ha.missing_failover`

**Performance (4)** — `perf.sync_expensive_dependency`, `perf.excessive_network_hops`, `perf.no_cache_high_read`, `perf.slow_storage_on_critical_path`

**Consistency (3)** — `cons.replica_for_strong_consistency`, `cons.cache_stale_strict_requirement`, `cons.async_where_sync_required`

**Reliability (5)** — `rel.retries_without_timeout`, `rel.retries_without_backoff`, `rel.retry_amplification`, `rel.missing_idempotency`, `rel.queue_without_dlq`

**Security (5)** — `sec.public_database`, `sec.missing_authentication`, `sec.missing_authorization`, `sec.unencrypted_sensitive_flow`, `sec.missing_secrets_management`

**Observability (4)** — `obs.no_metrics`, `obs.no_logs`, `obs.no_tracing`, `obs.no_alerts_critical`

**Edge semantics & patterns (7)** — `edge.missing_traffic_type`, `edge.cache_not_inline`, `edge.queue_unconsumed`, `edge.cdn_unused_static`, `edge.rate_limiter_absent_public_api`, `edge.waf_absent_public_edge`, `edge.write_path_through_cache_direct`

**Cost (3)** — `cost.budget_exceeded`, `cost.overprovisioned_low_traffic`, `cost.multi_region_justification`

**Workload-fit (3)** — `fit.nosql_for_transactional`, `fit.rdbms_for_massive_write_scale`, `fit.search_store_missing_search_req`

Total: **55**. Phase 3 exit requires ≥30 fully implemented + tested; remaining follow in P4–P9 as their domains arrive (e.g., `ai.*` rules ship with P9).

Rules live as **versioned content/config** (`content/rules/` metadata + Python implementations registered in a registry) — never inline in React (Agent Rule #3).

## 9.4 Evidence Standard (per `SYSTEM.md` §14)

Every FAIL/WARNING must render like:

```text
FAIL: Database write capacity
Evidence:
- Required writes: 20,000/sec
- Estimated primary capacity: 8,000/sec
- No sharding detected
Affected requirement: R-SCALE-WRITE
Suggested options:
1. Add database sharding
2. Introduce write queue if async acceptable
3. Select horizontally scalable datastore
```

Test fixture standard: every rule gets ≥2 fixtures (trigger case + pass case). Golden architecture suite (§16.4) guards regressions.

---

# 10. Recommendation Engine

Turns RuleResults into the teaching loop (`SYSTEM.md` §29, §66):

```text
Current bottleneck → Possible interventions → Expected benefit
                   → New trade-offs         → Next likely bottleneck
```

Every recommendation object contains: Problem, Evidence, Recommendation, Expected benefit, Trade-offs, Alternatives, Confidence, Related learning topics (linking into content taxonomy). This structure is shared with agents so Tutor/Coach outputs stay grounded.

Example output shape:

```text
Problem: Database read load is 80K/sec
Evidence: DB estimated safe read capacity: 20K/sec
Recommendation: Add distributed cache
Expected benefit: Reduce repeated DB reads
Trade-offs: stale data, invalidation, cache availability
Alternative: Read replicas
Confidence: HIGH
Learn: Caching → Cache Aside
```

---

# 11. AI / Agent Architecture

## 11.1 Gateway & Provider Abstraction (all four providers day one)

```python
class LLMProvider(Protocol):
    async def generate(request) -> LLMResponse
    async def stream(request) -> AsyncIterator[Chunk]
    async def structured_output(request, schema) -> StructuredResult
```

Adapters: `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `OllamaProvider`. Selection via config-driven routing table; application code never imports provider SDKs directly (Agent Rule #2). OpenAI-compatible endpoints ride the OpenAI adapter config.

Routing tiers (`SYSTEM.md` §21):

| Task | Tier | Default routing |
|---|---|---|
| classification, tagging, simple explanation | cheap | small hosted model or local Ollama |
| architecture critique | strong | flagship model |
| interview simulation | strong | flagship model |
| complex trade-offs | reasoning | strongest available |
| scenario/content generation | strong | flagship model |

Selection modes: automatic (task-based), user-selected, admin-configured.

## 11.2 Agent Roles (per `SYSTEM.md` §19)

| Agent | Ships | Purpose | Hard boundaries |
|---|---|---|---|
| Tutor | P5 | Explain concepts at learner level | Cite deterministic results when discussing current architecture |
| Coach | P5 | Hints, questions, trade-off surfacing | No full solutions unless requested |
| Evaluator | P5 | Qualitative reasoning atop RuleResults/Simulation | Must not contradict deterministic facts |
| Interviewer | P6 | Phase-gated interview simulation | Scores explanation quality separately from architecture quality |
| Scenario Generator | P8/P9 | New challenges from concepts/weaknesses | Must pass deterministic validation before publication |
| Content Agent | P9+ | Draft educational material | Draft-only until reviewed |

## 11.3 Safety Rules (non-negotiable, enforced in gateway middleware + prompt contracts)

Per `SYSTEM.md` §20: never claim deterministic results without evaluator evidence; never invent benchmark numbers as facts; label assumptions; distinguish convention vs hard requirement; offer alternatives; ask when uncertain; **never silently modify learner architecture**; modifications are preview/diffs requiring explicit user approval (Invariants 6–7); learner-approved changes create a new immutable version.

Implementation mechanism: agent responses requesting architecture changes return a typed `GraphDiffProposal`; frontend renders diff; only user click creates a new version server-side.

## 11.4 Cost Control (per `SYSTEM.md` §22)

- Every call logged to `LLMRequest`: provider, model, request_id, agent, task, input/output tokens, latency, cost, cache_hit, success/failure.
- Prompt caching where supported; response caching keyed by (architecture_hash + task + prompt_version); compact graph summaries instead of raw dumps; cheap models for cheap tasks; deterministic preprocessing before any LLM call.
- Free tier: AI actions metered (credits/quota), deterministic features unlimited (borrowed from MockArch's clean split).

---

# 12. Frontend Architecture

## 12.1 Stack

React 18 + TypeScript + Vite; **React Flow** for canvas (validated by 10xarch + Sidebar); Zustand for client state; TanStack Query for server state; Tailwind CSS + shadcn/ui primitives; Vitest + Testing Library; Playwright for E2E later phases.

## 12.2 Strict State Separation (`SYSTEM.md` §34)

| Store | Owner | Contents |
|---|---|---|
| Canvas Store | Zustand | React Flow node/edge positions, selection, viewport — **derived from graph, never authoritative** |
| Server State | TanStack Query | topics, challenges, saved architectures, evaluations fetch/cache |
| Evaluation State | dedicated slice | last EvaluationState, per-node issue overlays |
| UI State | Zustand | panels, modals, theme, tour state |

Sync contract: canvas edits produce graph mutations → debounced autosave/version draft → explicit evaluate trigger posts graph to `/evaluate`. Undo/redo operates on graph commands (command pattern), not React Flow internals.

## 12.3 Canvas Interactions (P2 acceptance list, from `SYSTEM.md` §35)

Drag from palette · move · connect (with edge-property inspector) · delete · duplicate · group · configure (property panel per component schema) · zoom/pan · auto-layout (dagre/elk) · undo/redo · save/load · version snapshot · export JSON · inspect node (knowledge card + "Why did I add this?" panel) · evaluate button.

Edge inspector fields: direction, protocol, traffic_type, pattern (sync/async), delivery (at_most/at_least/exactly_once), ordering. Defaults inferred from endpoint component types; user-overridable.

## 12.4 Feature Folders (mirrors `SYSTEM.md` §60)

`features/{learning,canvas,challenges,evaluation,interview,simulation,chaos,progress}` + `graph/` (graph<->React Flow adapters) + `api/` (typed clients) + `stores/` + `types/`.

---

# 13. Backend Architecture

## 13.1 Stack

Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, httpx, pytest. Docker Compose for local orchestration (web, api, postgres, redis, ollama optional profile).

## 13.2 Module Map (`SYSTEM.md` §33)

```text
backend/app/
  api/               routers: topics, components, challenges, architectures,
                     evaluate, simulate, scenarios, ai, progress, auth
  domain/
    architecture/    graph model ops, validation, diff, versioning
    challenges/      challenge lifecycle, submissions, scoring
    components/      catalog loading, knowledge access
    learning/        topics, lessons, progress
  evaluation/        rules/, engine/, metrics/, recommendations/   ← pure
  simulation/        traffic_model, capacity, latency, queues      ← pure (P7)
  chaos/             event definitions, injection, delta-eval      ← pure (P8)
  agents/            tutor/ coach/ interviewer/ evaluator/ generator/
  llm/               providers/{openai,anthropic,gemini,ollama}.py,
                     routing.py, prompts/ (versioned), usage_ledger.py
  content/           loaders for content/ tree (topics, challenges, components, rules)
  persistence/       SQLAlchemy models, repositories, migrations glue
  auth/              email/password + OAuth-ready, session/JWT
  observability/     OTel setup, structured logging, metrics
```

Purity rule: `domain/`, `evaluation/`, `simulation/`, `chaos/` import nothing from `api/`, `llm/`, `persistence/`.

## 13.3 API Surface (`SYSTEM.md` §36, extended)

```text
GET/POST   /api/topics, /api/topics/{id}
GET        /api/components, /api/components/{id}
GET/POST   /api/challenges, /api/challenges/{id}
POST       /api/challenges/{id}/submit
POST/GET/PUT /api/architectures, /api/architectures/{id}
POST       /api/architectures/{id}/versions        (immutable snapshots)
GET        /api/architectures/{id}/diff?v1=&v2=
POST       /api/architectures/{id}/evaluate
GET        /api/architectures/{id}/evaluations
POST       /api/architectures/{id}/simulate        (P7)
POST       /api/architectures/{id}/inject-event    (P8)
POST       /api/ai/tutor | /coach | /critique | /interview
POST       /api/ai/propose-changes                 → returns GraphDiffProposal only
POST       /api/graph-diffs/{id}/apply             (user approval gate)
GET        /api/progress
GET        /api/health, /metrics
```

All mutating agent-related endpoints enforce approval gates. Rate limiting via Redis on `/api/ai/*`.

---

# 14. Persistence & Data Model

Entities (`SYSTEM.md` §37): User, Topic, Lesson, Component(+ComponentCapability), Challenge, Requirement, Constraint, Architecture, ArchitectureVersion, ArchitectureNode, ArchitectureEdge, Evaluation, EvaluationRuleResult, SimulationRun, Scenario, ScenarioRun, AgentSession, LLMRequest, LearningProgress.

Strategy (`SYSTEM.md` §38): PostgreSQL authoritative; JSONB for evolving flexible parts (node/edge properties, evaluation details, challenge config). Do **not** over-normalize the graph in first release — nodes/edges stored as rows on `ArchitectureVersion` with properties JSONB, upgradeable later. ArchitectureVersions immutable (Invariant 5). Redis: session/cache/rate-limit only — never authoritative.

Auth MVP: email/password (+ anonymous playground with local-only storage until save), OAuth (GitHub/Google) scaffolded, enterprise SSO deferred to P11.

---

# 15. Content Architecture

## 15.1 Structure

```text
content/
  topics/<topic-id>/
    topic.yaml            (taxonomy, prerequisites, related)
    sections/*.mdx        (concept, how-it-works, patterns, trade-offs, examples)
    labs/*.yaml           (linked interactive exercises)
    quiz/*.yaml
  challenges/<challenge-id>/challenge.yaml + assets
  components/<component-id>.json
  rules/<category>.yaml   (rule metadata; implementations in backend)
  scenarios/<event>.yaml  (P8)
  golden_architectures/<name>.json
```

MDX for prose; YAML/JSON for anything machines consume. Topic template per lesson: Concept → Explanation → Diagram → Example → Trade-offs → Common mistakes → Interactive lab link → Challenge link (`SYSTEM.md` §6.1, §23).

## 15.2 Topic Taxonomy Launch Set (P1: 10 pillars, 30–50 lessons)

Foundations (client/server, HTTP, DNS, TLS, REST, WebSockets) · Traffic management (LB, reverse proxy, API gateway, rate limiting, CDN, WAF) · Caching (patterns, TTL, eviction, invalidation, hot keys, Redis vs Memcached vs CDN vs local) · Databases (relational/NoSQL, indexing, replication, read replicas, sharding, partitioning, transactions, isolation) · Messaging (queues, Kafka/RabbitMQ/SQS/PubSub/NATS, consumer groups, ordering, DLQ) · Distributed systems (CAP, consensus, locks, idempotency, leader election) · Reliability (retries/timeouts, circuit breaker, bulkhead, failover, DR, multi-AZ/region) · Observability (logs/metrics/traces, SLI/SLO/SLA, alerting) · AI/GenAI systems (gateway, routing, RAG, embeddings, vector DB, reranking, agents, tools, MCP, memory, guardrails, evals) · Interview method (structured process per `SYSTEM.md` §70).

Content quality bar (`SYSTEM.md` §68–69): distinguish Concept / Pattern / Rule-of-thumb / Convention / Hard requirement / Trade-off / Tech-specific behavior; concepts before products; case-study-flavored narratives inspired by systemdesign42 academy taxonomy (original writing only — that repo is CC BY-NC-ND).

## 15.3 Challenge Program (initial 15 families → 50 challenges)

From `SYSTEM.md` §50: static website, 3-tier app, URL shortener, rate limiter, notification system, chat system, file storage, image processing, video streaming, search system, news feed, payment system, job queue, metrics system, distributed cache.

Each family becomes a **progressive chain** (URL-shortener L1–L6 pattern from §27: 100 RPS monolith → LB+horizontal → cache for read-heavy → CDN/multi-region → HA/failover → spike/queues/backpressure). Chains yield ~45–60 natural levels.

Plus **Repair Drills** (Repair Mode, P4): programmatically corrupted golden architectures — one flaw each (remove failover, point reads at primary, drop DLQ…), 60-second format, telemetry-style expected symptoms in the brief. Generated from the same fixtures used in testing, guaranteeing solvability and determinism.

Every challenge YAML carries: requirements, constraints, difficulty (Beginner/Intermediate/Advanced/Expert per §26), allowed_components, evaluation_rules subset, scenarios hooks, learning_objectives, narrative (fictional company), hints ladder, AI context notes.

---

# 16. Testing Strategy

## 16.1 Backend Unit (pytest)

Rule engine (each rule: apply/pass/trigger/confidence cases) · graph validation · normalization · diff/versioning · recommendation builder · requirement mapping · simulation math (P7) · chaos delta math (P8). Target: ≥100 evaluator tests at P3 exit (`SYSTEM.md` §49), growing with rules.

## 16.2 Integration

API ↔ PostgreSQL ↔ Redis · evaluation pipeline end-to-end through FastAPI · LLM gateway with recorded/canned provider responses (VCR-style) + contract tests per adapter; Ollama adapter integration-tested locally in CI optional job.

## 16.3 Frontend

Canvas interactions (drag/drop, connect, property edit) · state separation (no graph truth in canvas store) · undo/redo command integrity · evaluation panel rendering from fixture EvaluationState · API mocking via MSW.

## 16.4 Golden Architecture Tests (regression bedrock, `SYSTEM.md` §42)

Canonical fixtures with expected evaluation digests, e.g.:

```text
url_shortener_good:        PASS functional, PASS read-scale, WARNING single-db-primary, PASS latency
url_shortener_spof:        FAIL ha.single_database
notification_async_bad:    FAIL cons.async_where_sync_required, WARNING rel.retries_without_backoff
overloaded_db:             FAIL scale.db_write_bottleneck with exact evidence numbers
missing_cache_reads:       WARNING perf.no_cache_high_read
```

Any rule-engine change runs the entire golden suite; digest diffs require explicit review (this is how evaluator regressions get caught).

## 16.5 Agent Evaluation Suite (from P5, `SYSTEM.md` §43)

Fixture-driven: given (graph, requirements, RuleResults), assert agent outputs — factual correctness, zero contradiction with deterministic results, hallucination rate sampling, structured-output validity, hint-ladder appropriateness, refusal-to-over-prescribe. Runs on every prompt change against canned model responses; periodic live-model spot checks manual/nightly.

---

# 17. Observability, Security & Cost

## 17.1 Observability (`SYSTEM.md` §40)

OpenTelemetry SDK from day one (traces around API + evaluation + LLM calls), structured JSON logs, Prometheus `/metrics`. Grafana/Loki/Tempo dashboards deferred to post-MVP hardening week. Track: latency, errors, token usage, model, cost, evaluation/simulation duration, challenge completions, rule-failure rates, agent failures. Philosophy: instrument the platform the way the platform teaches.

## 17.2 Security (`SYSTEM.md` §44)

Server-side provider keys only; secrets via env/secret manager; request limits + Redis rate limits on AI routes; no unnecessary PII to LLMs (context builders whitelist graph/requirements/results only); audit log for agent proposals/applies; agent outputs treated as untrusted input (schema-validate GraphDiffProposal before rendering).

## 17.3 Cost Architecture (`SYSTEM.md` §45)

Free forever: lessons, playground, deterministic evaluation, limited challenges, local-Ollama AI path. Pro: advanced scenarios, tutor/coach quotas, interview mode, simulation, history. Metering via LLMRequest ledger + per-user counters in Redis. Core learning must never require paid AI.

Deployment: Docker Compose now → AWS (ECS/Fargate, RDS, ElastiCache, S3+CloudFront, ALB) when needed; no Kubernetes unless justified (`SYSTEM.md` §59, Agent Rule #10).

---

# 18. Delivery Roadmap (Phases 0–11)

Sequencing follows `SYSTEM.md` §46–57 / §81 order exactly. Estimates assume one senior developer working with AI coding assistance, part-time-to-full-time mix; ranges deliberately conservative. **Every phase ends runnable and demoable.**

## Phase 0 — Foundations & Contracts (≈1 week)

**Goal:** Repo, schemas, codegen, CI skeleton — the contracts everything else builds on.

Work:
1. Create `system-design-platform/` monorepo per §20 layout; git init; README.
2. Author 9 JSON Schemas (§7.1); wire datamodel-code-generator + json-schema-to-typescript; drift check in CI.
3. Scaffold backend (FastAPI + health endpoint + pytest) and frontend (Vite + React Flow smoke test page rendering a toy graph).
4. Docker Compose: web, api, postgres, redis.
5. Seed `content/components/` with the 11 P2 components (catalog JSON only).
6. Define 55 rule ids as YAML registry stubs; define challenge schema; sketch 20+ challenge concepts doc (P0 exit criterion).
7. CI: lint (ruff, eslint), typecheck (mypy strict on domain, tsc), tests, schema-drift check.

Deliverables: green pipeline; `GET /api/components` serving seeded catalog; browser page drawing two connected boxes serialized to canonical graph JSON.
**Exit:** schemas stable enough to code against; ≥20 challenge concepts listed; 55 rule ids documented; both hello-world apps run via one `docker compose up`.

## Phase 1 — Learning Platform MVP (≈2–3 weeks)

**Goal:** Educational foundation — content engine + reading experience.

Work: content loader service; Topic/Lesson models + migrations; MDX pipeline (frontend renders structured content); topic browser, lesson pages (sections, diagrams, trade-offs, common mistakes); glossary; full-text search (Postgres tsvector); progress tracking (lesson completion) + basic quizzes; landing page; responsive/mobile layout; seed 30–50 lessons across the 10-pillar launch taxonomy (AI-assisted drafting, human-reviewed, following §68 quality bar).

Deliverables: browsable, searchable curriculum with progress + quizzes; every lesson links forward to (future) lab slots.
**Exit (`SYSTEM.md` §47):** 30–50 high-quality lessons; progress tracking works; mobile-friendly; searchable.

## Phase 2 — Interactive Architecture Canvas (≈2–3 weeks)

**Goal:** The playground — graphs users build are real data.

Work: component palette (searchable, categorized from catalog API); React Flow canvas wired to canonical graph via adapter layer (§12.2); connect/disconnect with edge-property inspector (semantic defaults per §35); node property panels (capacity/replicas/deployment fields from component schema); undo/redo (command stack); save/load architectures (auth-gated); immutable version snapshots on save; export/import JSON; auto-layout; anonymous Explore Mode (local-storage persistence); node inspect drawer showing knowledge card + first cut of "Why did I add this?" (static from component knowledge block).

Deliverables: users construct/save/version the §48 reference chain (Client→CDN→LB→API→Redis→PostgreSQL) as machine-readable architecture.
**Exit:** round-trip fidelity proven — exported JSON validates against `architecture.schema.json` and reloads identically.

## Phase 3 — Deterministic Evaluation Engine (≈3–4 weeks) ⭐ core investment

**Goal:** Make the canvas intelligent.

Work: implement pipeline (§9.1) in pure package; implement ≥30 rules across graph/scale/availability/performance/consistency/reliability/security/observability (prioritized: graph integrity → SPOF family → read/write bottleneck family → caching opportunity → reliability basics); metrics scorer producing the 8 dimension bars with evidence lists; requirement-mapping layer; bottleneck + SPOF detectors; recommendation builder (§10); evaluation panel UI (PASS/WARNING/FAIL/INFO groups, expandable evidence, requirement badges, per-node issue markers on canvas); live re-evaluate on demand (debounced); evaluation history per architecture version; golden architecture test harness + first 10 goldens; rule tests to ≥100 total.

Deliverables: the §71 notification-system walkthrough plays out in-product (sync-provider FAILs → add Kafka → decoupling PASSes + new DLQ/idempotency WARNINGs).
**Exit (`SYSTEM.md` §49):** ≥30 useful rules, ≥100 automated tests, every result evidence-backed, deterministic (golden digests stable).

## Phase 4 — Challenge Engine + Repair Drills (≈2–3 weeks)

**Goal:** Real learning challenges.

Work: challenge runtime (load YAML, present requirements/constraints/narrative, restrict palette to allowed_components, scoped evaluation using challenge.evaluation_rules + requirement targets); submission flow (snapshot graph → evaluate → score breakdown → requirement checklist ✓/✗); scoring model aggregating rule statuses weighted by priority (transparent weights shown to learner); progressive unlock within chains (L1→L6 URL shortener et al.); hint ladder per challenge (nudge → concept → partial structure → full rationale; consumption tracked); first 15 families authored as chains (~45–60 levels); **Repair Drills**: corrupt-a-golden generator + 20 drills + drill player (brief with symptom telemetry text → fix → instant re-eval); difficulty tags; challenge browser with filters.

Deliverables: 20–30 polished playable challenges including drills.
**Exit:** 50 validated challenges defined and importable (playable subset ≥30); submission scoring matches golden expectations; MVP challenge bar met (`SYSTEM.md` §58).

## Phase 5 — AI Tutor & Coach (≈2 weeks)

**Goal:** Contextual AI without ceding authority.

Work: LLM gateway + 4 provider adapters + routing table + usage ledger + response caching; prompt library v1 (versioned files); Tutor endpoints (explain-component / explain-failure / explain-recommendation — context = challenge + requirements + compact graph + RuleResults + learner history snippet); Coach endpoints (hint, compare-alternatives, critique); chat panel UX in lab; **GraphDiffProposal flow** (agent proposes → typed diff → user approves → new version); metering/quotas for free tier; agent eval harness (§16.5) + prompt-contract tests asserting no contradiction with injected deterministic results; Ollama docker-compose profile proving the free/local path end-to-end.

Deliverables: "Ask AI why" works on every evaluation item; proposals require approval.
**Exit (`SYSTEM.md` §51):** AI never contradicts deterministic facts without flagging uncertainty; provider swap is config-only (integration test proves same conversation across all 4 adapters).

## Phase 5.5 — Node Library Expansion (≈1–2 weeks)

**Goal:** Grow the component catalog from 11 to ~150–200 nodes over time (launch with ~60–80 high-value), so challenges and the AI tutor can discuss real systems vocabulary. Node ≠ Technology: conceptual components, technology implementations, and architectural patterns are distinct kinds.

**Node kinds:** `concept` (abstract role, e.g. Cache, Message Queue), `implementation` (concrete tech, e.g. Redis, Kafka), `pattern` (behavioral/architectural motif placed as annotation nodes, e.g. Circuit Breaker, Saga). Patterns are visually distinct in canvas/palette and are EXCLUDED from engine capacity/connectivity/SPOF math.

**Metadata schema per node** (extends current catalog JSON): `kind`, `category`, `display_name`, `capabilities`, `helps_with`, `does_not_solve`, `risks`, `common_patterns`, `failure_modes`, `tradeoffs`, `properties` defaults, `capacity_defaults` (implementations only), `cost_defaults`, `palette {group, icon, color}`. The AI tutor consumes `helps_with`/`does_not_solve`/`risks` verbatim; engine consumes `capacity_defaults` + role mapping.

**Engine integration (additive-only rule):** new types join role frozensets (`DatastoreTypes`, `QueueTypes`, `CacheTypes`, `ComputeTypes`, `LBTypes`) so existing rules recognize them; behavior for the original 11 types is frozen (golden fixtures must stay green). Capacity math for alternate computes (serverless/k8s) is a follow-up — the api-tier RPS rule still keys on type `api`.

**Launch categories (~70 new):** Traffic (api_gateway, reverse_proxy, global_load_balancer, waf, dns, service_mesh); Compute (serverless_function, kubernetes, autoscaling_group); Cache (memcached); SQL (mysql, cockroachdb, spanner, timescaledb); NoSQL (cassandra, dynamodb, neo4j); Analytics/Search (clickhouse, elasticsearch, influxdb, data_warehouse); Storage (block_storage, file_storage); Messaging (sqs, pubsub, nats, kinesis, event_bus); Data processing (spark, flink, airflow, cdc_pipeline); Auth (identity_provider, secrets_manager); Observability (metrics_collector, log_aggregator, tracing_collector, alert_manager); Service comm (grpc, graphql_gateway); Coordination (distributed_lock, leader_election, id_generator); Workflow (workflow_engine, cron_scheduler); Payments (payment_gateway, ledger_service); Notifications (email_service, push_service, sms_service); Media (media_transcoder); Realtime (websocket_gateway, mqtt_broker); Feed (fanout_service); AI (llm_api, embeddings_model, vector_database, reranker, llm_router); RAG/Agents (rag_pipeline, tool_orchestrator, mcp_server, moderation_service); ML infra (recommendation_engine, feature_store, model_registry); Patterns (circuit_breaker, saga, cqrs, transactional_outbox, sidecar, backpressure, bulkhead, event_sourcing).

**Palette UX:** grouped by category (new groups ordered after existing), search box filters across name/capabilities/category; pattern group rendered last with distinct styling.

**Follow-on within this phase:** expand glossary terms for new concepts; extend challenge packs + learning modules to exercise the new nodes; regenerate golden solutions via scripts; capacity model for serverless/managed computes.

Deliverables: ~75-node launch library live in palette + tutor-aware metadata.
**Exit:** all golden fixtures pass unchanged; every new node renders with correct group/badge; palette search finds nodes by capability keyword.

## Phase 6 — Interview Agent (≈2 weeks)

**Goal:** Simulated system-design interviews.

Work: interview session state machine over the §70 twelve-step method (requirements → scale → APIs → data model → architecture → bottlenecks → scaling → consistency → availability → failures → observability → trade-offs); Interviewer prompts consuming board state (Sidebar-style phase gating) + elapsed time + question pack per scenario; candidate canvas embedded in interview view; adaptive follow-ups driven by detected gaps (weak capacity discussion, missing SPOF mitigation…); final report: 10 score dimensions (`SYSTEM.md` §52) each with evidence quotes from transcript + architecture RuleResults; communication-quality scoring separate from architecture quality; session replay transcript; post-interview study plan linking weak areas to lessons/challenges.

Deliverables: end-to-end 45-minute mock interview with credible report.
**Exit:** interview scores correlate sensibly with golden-architecture ground truth on scripted candidate runs; deterministic evaluator remains the architecture-score authority (AI scores process/communication only).

## Phase 7 — Simulation Layer (≈3 weeks)

**Goal:** From static judgment to quantitative behavior — analytical, not cloud-emulation.

Work: pure `simulation/` package implementing §16 I/O: traffic model (RPS, ratios, sizes), per-component capacity defaults (from catalog, overridable per node), hop latency composition, cache hit-ratio effects, queue throughput/backlog dynamics, utilization, p50/p95/p99 estimation (analytical queueing approximations e.g. M/M/c-informed), error-rate saturation, monthly cost estimation (catalog price tables); two frontend views over one model — **Trace view** (single animated request hop-by-hop, borrowed from systemdesignsimulator) and **Aggregate view** (Monte-Carlo-ish distribution charts); visual traffic overlays on canvas edges (thickness = load, color = saturation); "DB close to threshold" style callouts; simulation results feed recommendations AND evaluator-agent context; SimulationRun persistence + comparison across versions; challenge scenarios gain numeric assertions (e.g., estimated p95 ≤ 200ms).

Deliverables: §16 example reproduces in-product (100K RPS → 10×API → Redis 90% hit → 10K DB reads/sec with visible headroom warnings).
**Exit:** same-input determinism; capacity assumptions surfaced as editable, confidence-labeled; cost estimates render per-node breakdown.

## Phase 8 — Chaos Engineering Learning (≈2 weeks)

**Goal:** Teach failure behavior (ScaleDojo Murphy's-Lab energy, our own mechanics).

Work: event library per §54 (db_failure, cache_failure, queue_failure, region_outage, network_latency, traffic_spike ×N, hot_key, consumer_lag, dependency_outage, hit_ratio_drop); injection engine applying event transforms to a graph copy → re-run evaluator + simulation → **before/after delta report** (availability 99.95% → 71%, cause: no automatic failover — §17 style); Chaos Mode UI (event picker, run, timeline of metric deltas, guided repair loop); Compare-before-after view; challenge hooks (`scenarios:` in YAML become playable events); mitigation verification (adding failover flips the delta); Scenario Generator agent v1 (drafts new events/challenges from learner weakness profile — passes deterministic validation gate before publication).

Deliverables: inject → observe → repair → verify loop on ≥10 scenarios.
**Exit:** every event has deterministic expected-effect fixtures; repairs measurably change deltas.

## Phase 9 — AI/GenAI Systems Lab (≈2–3 weeks)

**Goal:** First-class agentic-systems design domain (the open-lane differentiator).

Work: 14 GenAI catalog components (§8.1 P9 list) with knowledge blocks + capacity/cost defaults (token throughput, embedding dims, vector-DB QPS, guardrail latency); GenAI-specific rules (`ai.*`: missing-guardrail-on-user-facing-LLM, missing-eval-harness, unbounded-agent-tool-loop, missing-memory-isolation, prompt-injection-surface, no-model-router-fallback, vector-db-not-refreshed, missing-observability-for-traces-of-LLM-calls); 10 GenAI challenges (`SYSTEM.md` §55: RAG system, enterprise chatbot, AI gateway, multi-model routing, agent platform, MCP platform, AI evaluation system, multi-agent workflow, inference platform, LLM observability) with narrative scenarios (budget-blowup style storytelling à la ScaleDojo GenAI lab); cost modeling for tokens; content pillar expansion (RAG deep-dive, agent patterns, MCP, evals — original material informed by the taxonomy breadth systemdesign42 demonstrates).

Deliverables: full GenAI track playable end-to-end.
**Exit:** GenAI architectures evaluate deterministically like classic ones; ≥10 validated GenAI challenges; `ai.*` rules tested.

## Phase 10 — Collaborative Platform (≈2–3 weeks, post-MVP)

**Goal:** Social/compare layer.

Work: share links + public/private architectures; **Compare Mode** (side-by-side graphs + evaluation diff across latency/throughput/consistency/availability/cost/complexity/failure-behavior — §6.7); version-diff viewer promoted to full feature (what changed/improved/regressed/new risks — §30–31); comments on shared designs; leaderboards (challenge scores, drill streaks); team exercises + instructor mode basics (assign challenge set, view cohort progress); peer review workflow for optional community feedback (sysd.ai-inspired); live collaboration explicitly deferred further (needs CRDT/WebSocket infrastructure — schedule only if demand justifies).

**Exit:** two architectures comparable with multidimensional delta; sharing privacy-safe.

## Phase 11 — Enterprise (future, unsized)

SSO (SAML/OIDC), private challenge libraries, org-specific architecture templates, custom scoring weights, team analytics dashboards, internal-knowledge ingestion (RAG over company docs), private-LLM support (already architecturally ready via gateway), audit logs. Gate: real enterprise demand signal.

---

# 19. MVP Boundary

MVP = **Phases 0–5 complete** (`SYSTEM.md` §58):

```text
Learning Content + Interactive Canvas + Architecture Graph
  + Deterministic Evaluation + 20–30 Challenges
AI limited to: Explain / Hint / Critique
```

Explicitly NOT in MVP: simulation (P7), chaos (P8), interview mode (P6 comes right after MVP but is not the MVP gate), GenAI lab (P9), collaboration (P10), billing, enterprise. Anti-goals (`SYSTEM.md` §77) remain in force: no generic diagramming, no real cloud provisioning, no LLM-only scoring.

---

# 20. Repository Layout

Created in Phase 0 under `system-design-platform/` (extends `SYSTEM.md` §60):

```text
system-design-platform/
├── frontend/
│   ├── src/
│   │   ├── components/          shared UI
│   │   ├── features/
│   │   │   ├── learning/  canvas/  challenges/  evaluation/
│   │   │   ├── interview/ simulation/ chaos/  progress/
│   │   ├── graph/               graph <-> React Flow adapters (pure)
│   │   ├── api/                 typed clients (from schemas)
│   │   ├── stores/              zustand slices (canvas/ui only)
│   │   └── types/               generated + hand-written
│   └── tests/                   vitest + playwright
├── backend/
│   ├── app/
│   │   ├── api/  domain/  evaluation/  simulation/  chaos/
│   │   ├── agents/  llm/  content/  persistence/  auth/  observability/
│   └── tests/
│       ├── unit/  integration/
│       └── golden/              golden architecture runner
├── content/
│   ├── topics/  challenges/  components/  rules/  scenarios/
│   └── golden_architectures/
├── schemas/                     JSON Schemas (source of truth)
│   ├── architecture.schema.json   challenge.schema.json
│   ├── component.schema.json      evaluation.schema.json
│   ├── node.schema.json  edge.schema.json
│   ├── requirement.schema.json  constraint.schema.json
│   └── scenario.schema.json
├── docs/
│   ├── architecture/  product/  agents/
│   └── adr/                     architecture decision records
├── infra/docker/                compose files, profiles (dev, ollama)
├── tests/golden_architectures/  cross-cutting fixture runner
├── .github/workflows/           ci.yml (lint, typecheck, test, schema-drift)
├── SYSTEM.md -> ../../SYSTEM.md (copied at scaffold time; canonical copy stays at workspace root)
├── PLAN.md                      (this document, copied into repo)
├── README.md
└── docker-compose.yml
```

---

# 21. Definition of Done — First Production Milestone

Direct checklist from `SYSTEM.md` §82; owner phase noted:

- [ ] Read system-design lessons — P1
- [ ] Browse component knowledge — P2
- [ ] Start a challenge with explicit requirements/constraints — P4
- [ ] Drag components, connect them — P2
- [ ] Architecture stored as canonical graph, versioned — P0/P2
- [ ] Deterministic evaluator analyzes graph; results map to requirements — P3
- [ ] Every important issue has evidence — P3
- [ ] User sees what a component solved + new trade-offs introduced — P2/P3
- [ ] Hints available; AI explanations use deterministic context — P5
- [ ] AI cannot silently change architecture — P5 (GraphDiffProposal gate)
- [ ] ≥20 challenges; ≥100 evaluator tests; golden architecture tests — P3/P4
- [ ] Observability for backend + AI calls — P0/P5
- [ ] Multi-provider LLM abstraction incl. free/local path — P5
- [ ] Core learning requires no paid AI — P1–P4 by construction
- [ ] Architecture data exportable — P2
- [ ] Docs versioned with codebase — continuous

---

# 22. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Evaluator feels wrong/oversimplified → trust collapse | Medium | Fatal | Evidence-first results; confidence labels; golden fixtures reviewed against real-world judgment; avoid false precision (§15) |
| 2 | Rule explosion / maintenance burden | High | High | Registry + YAML metadata; per-rule test fixtures mandatory; retire rules via versioning not deletion |
| 3 | Capacity numbers challenged as made-up | High | Medium | All defaults editable + labeled assumptions; cite ranges not points; UNKNOWN status when data insufficient |
| 4 | AI contradicts deterministic results | Medium | High | Prompt contracts + injected RuleResults; agent eval suite gates merges; proposal-only modification flow |
| 5 | LLM cost blowout | Medium | Medium | Routing tiers, caching, ledger alerts, free-tier metering, Ollama fallback |
| 6 | Scope creep toward diagram-editor/me-too clone | Medium | Fatal | Guiding question (§83) on every feature; anti-goals list; phase gates |
| 7 | Solo-dev burnout / motivation dip mid-roadmap | Medium | High | Every phase ships runnable demo; MVP gate at P5; content batching with AI drafting + human review |
| 8 | React Flow limits (grouping, edge semantics, large graphs) | Low | Medium | Adapter layer isolates React Flow; escape hatch documented; elk/dagre for layout |
| 9 | Content volume stalls P1 | High | Medium | AI-assisted drafting with editorial review; 10-lesson weekly cadence; quality bar checklist |
| 10 | Schema churn breaks downstream | Medium | High | Schemas are versioned artifacts; codegen drift CI; migration discipline from day one |
| 11 | Licensed-content contamination from reference repos | Low | Legal | Original writing only; reference taxonomies/ideas, never text (academy repo is CC BY-NC-ND) |
| 12 | Determinism broken by hidden state | Low | High | Pure engine packages; property-based tests; byte-stable golden digests in CI |

---

# 23. Success Metrics

From `SYSTEM.md` §75–76, instrumented from P1 onward:

**Learning:** lesson completion, challenge completion, improvement-between-attempts.
**Architecture:** designs created, components used, iterations per challenge, average fixes-to-pass.
**Reasoning:** bottlenecks self-identified before reveal, hint-request trends, failed-requirement corrections.
**Interview (P6+):** score trajectory, completion time, requirements coverage, communication score.
**AI (P5+):** helpfulness rating, correction rate, hallucination rate (eval suite), cost/user, p95 latency.

**MVP success test (§76):** a new learner can read about caching → open the caching challenge → receive workload → build → drag Redis → connect → instantly see which requirement changed, what it solved, what new trade-off appeared → ask AI why → modify again → compare versions → complete. **If that loop feels excellent, the foundation is right.**

---

# 24. Open Decisions Log

| # | Decision | Status | Notes |
|---|---|---|---|
| 1 | Tagline selection (§79 options A–D) | Open | Decide before P1 landing page |
| 2 | Auto-layout library (elkjs vs dagre) | Open | Benchmark in P2 |
| 3 | Quiz engine depth for P1 | Open | Minimal MCQ now; richer formats deferred |
| 4 | Anonymous-playground persistence (local-only vs anon server records) | Open | Default local-only; revisit at P4 |
| 5 | Pricing model specifics (credits vs subscription vs hybrid) | Deferred | Post-MVP; ledger already captures usage data to decide empirically |
| 6 | Live collaboration tech (CRDT choice) | Deferred | Only if P10 demand justifies |
| 7 | Brand name / domain | Open | Blocking only for launch, not development |
| 8 | Whether Compare Mode moves earlier than P10 | Open | Cheap if version-diff lands well in P3/P4; reassess after P4 |

---

*End of PLAN.md v0.1 — companion to SYSTEM.md v0.1. Update both documents together when scope or sequencing changes.*
