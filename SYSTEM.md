# Interactive System Design Learning Platform

## Product, Architecture, Agent, Evaluation, and Phased Delivery Specification

**Document:** `SYSTEM.md`\
**Version:** 0.1\
**Status:** Product/engineering blueprint\
**Primary stack:** React + TypeScript, Python + FastAPI, PostgreSQL,
Redis, pluggable LLM providers\
**Primary objective:** Build an interactive system-design learning
platform where users learn concepts, construct architectures, change
architectural decisions, observe consequences, and receive
deterministic + AI-assisted feedback.

------------------------------------------------------------------------

# 1. Executive Summary

Build a web platform for learning and practicing software/system design
through a combination of:

1.  Traditional educational content.
2.  Interactive architecture construction.
3.  Scenario-based challenges.
4.  Deterministic architecture analysis.
5.  AI/agent-based explanations and coaching.
6.  Progressive failure and scale scenarios.
7.  Eventually, lightweight traffic/capacity/failure simulation.
8.  Support for multiple LLM providers, including free/local and paid
    models.

The core learning loop is:

> **Learn → Build → Evaluate → Diagnose → Modify → Re-evaluate →
> Understand**

The platform must not behave like a generic diagram editor.

The architecture canvas is a **machine-readable system model**. Every
component, connection, property, requirement, constraint, and scenario
is represented as structured data so that deterministic rules,
simulations, and agents can reason over the same architecture.

The product should teach the learner not merely:

> "Add Redis."

but:

> "Your current read workload is likely to overload the database. A
> cache can reduce database reads. However, adding a single cache node
> introduces a cache availability risk. A replicated/clustered cache can
> address that risk, but introduces cost and invalidation/consistency
> trade-offs."

This distinction is the primary product principle.

------------------------------------------------------------------------

# 2. Product Vision

## 2.1 Vision

Create a system-design learning environment in which learners can safely
experiment with architecture decisions and immediately understand their
consequences.

Instead of passively reading:

> "Use caching for high-read workloads."

the learner should be able to experience:

``` text
Client
  ↓
Load Balancer
  ↓
API
  ↓
PostgreSQL
```

Then introduce a workload:

``` text
100,000 requests/sec
80% reads
20% writes
```

The platform identifies:

``` text
Database read pressure: HIGH
Latency risk: HIGH
Availability: MEDIUM
```

The learner drags Redis onto the canvas:

``` text
Client
  ↓
Load Balancer
  ↓
API
  ↓
Redis
  ↓
PostgreSQL
```

The platform updates:

``` text
Read pressure: LOW
API latency: IMPROVED
Database load: REDUCED

New concern:
Redis is a single point of failure.
```

The learner adds replication/cluster configuration.

The platform evaluates again.

This makes architecture a dynamic learning system rather than a static
diagram.

------------------------------------------------------------------------

# 3. Product Differentiation

There are already products covering portions of this space:

-   ScaleDojo provides interactive system-design labs, deterministic
    scoring, AI review, and GenAI architecture labs.
-   MockArch provides architecture canvas, traffic simulation, cost
    estimates, rule-based analysis, and AI feedback.
-   sysd.ai provides interactive diagrams, AI evaluation, and "Design
    Drills" where users fix a deliberately broken architecture.
-   System Design Simulator focuses on simulation and observing
    latency/capacity/failure behavior.
-   10xarch and other projects explore interactive system-design
    playgrounds and AI feedback.
-   systemdesign42/system-design-academy is a strong
    educational/reference repository for system design and distributed
    systems.

These projects validate the market and feature direction.

The product should therefore NOT be positioned merely as:

> "AI system design interview practice."

Instead, differentiate around:

> **Learning system design by building, breaking, fixing, and
> understanding systems.**

Core differentiators:

1.  Architecture state is continuously evaluable.
2.  Deterministic rules are first-class.
3.  AI explains reasoning rather than inventing the score.
4.  Components have meaningful properties.
5.  Scenarios can change while the learner's architecture remains.
6.  The learner can observe which requirements are satisfied and which
    are not.
7.  Failure scenarios can deliberately break the architecture.
8.  Educational content and interactive experimentation are linked.
9.  AI/agent architecture is treated as a first-class system-design
    domain.
10. The platform can eventually simulate traffic, capacity, latency,
    cost, and failures.

------------------------------------------------------------------------

# 4. Product Principles

## P1. The architecture is data, not pixels

Never make the React canvas the source of truth.

The source of truth is a canonical `ArchitectureGraph`.

The canvas is a visual representation of that graph.

## P2. Deterministic first, AI second

Use deterministic logic whenever the question can be answered reliably
with rules.

Use LLMs for:

-   explanations
-   trade-off reasoning
-   hints
-   teaching
-   question generation
-   interview simulation
-   natural-language interpretation
-   architecture critique
-   alternative designs

Do not allow an LLM to be the sole authority for basic architecture
correctness.

## P3. Every recommendation must be explainable

Never output:

> "Add Kafka."

without explaining:

-   what problem Kafka addresses,
-   which requirement it affects,
-   what assumptions justify it,
-   what new trade-offs it introduces,
-   what it does NOT solve.

## P4. Do not prescribe one canonical architecture too early

Many architecture questions have multiple valid solutions.

The evaluator should distinguish:

-   Required
-   Strongly recommended
-   Optional
-   Context-dependent
-   Invalid under current assumptions

## P5. Requirements drive evaluation

A component is not "good" or "bad" in isolation.

Example:

Redis may be unnecessary for:

``` text
100 requests/sec
```

but valuable for:

``` text
500,000 requests/sec
90% reads
low-latency requirement
```

## P6. Explain trade-offs

Every architectural improvement can create another problem.

Examples:

``` text
Cache
→ lower DB load
→ possible stale data
→ invalidation complexity
```

``` text
Read replicas
→ improve read scalability
→ replication lag
→ eventual consistency
```

``` text
Kafka
→ decoupling
→ buffering
→ asynchronous processing
→ operational complexity
```

``` text
Multi-region
→ availability
→ lower geographic latency
→ higher cost
→ consistency complexity
```

------------------------------------------------------------------------

# 5. Target Users

## Primary

Software engineers preparing for:

-   system design interviews
-   senior engineer interviews
-   staff engineer interviews
-   architecture discussions

## Secondary

Engineers learning distributed systems and production architecture.

## Future

-   engineering students
-   bootcamp learners
-   engineering managers
-   architects
-   internal corporate training

------------------------------------------------------------------------

# 6. Learning Modes

The platform should support several modes.

## 6.1 Learn Mode

Traditional educational content:

``` text
Concept
  ↓
Explanation
  ↓
Architecture diagram
  ↓
Example
  ↓
Trade-offs
  ↓
Interactive mini-exercise
```

Example:

`Caching`

Sections:

-   What is caching?
-   Why caching exists
-   Cache-aside
-   Write-through
-   Write-back
-   TTL
-   Eviction
-   Cache invalidation
-   Distributed cache
-   Redis
-   Memcached
-   CDN caching
-   Local caching
-   Failure modes
-   Interview considerations

## 6.2 Explore Mode

Learner starts with a blank canvas and experiments freely.

No score required.

## 6.3 Challenge Mode

A problem defines:

-   functional requirements
-   traffic
-   data size
-   latency
-   availability
-   consistency
-   durability
-   security
-   geographic scope
-   budget/cost constraints

Learner builds a solution.

## 6.4 Repair Mode

System provides a partially broken architecture.

Example:

``` text
API
 ↓
PostgreSQL
```

Requirement:

``` text
100K RPS
```

The learner must identify and fix the bottleneck.

## 6.5 Interview Mode

AI acts as interviewer.

It should:

-   ask clarifying questions
-   challenge assumptions
-   ask capacity questions
-   ask trade-off questions
-   introduce changing requirements
-   score explanation quality
-   assess architecture
-   provide post-interview feedback

## 6.6 Chaos Mode

The architecture is exposed to events:

-   cache failure
-   database failure
-   region outage
-   network partition
-   traffic spike
-   hot key
-   queue backlog
-   consumer failure
-   dependency timeout
-   retry storm

The learner must respond.

## 6.7 Compare Mode

Compare two architectures.

Example:

``` text
Architecture A
Redis + PostgreSQL

Architecture B
Kafka + Cassandra
```

Evaluate:

-   latency
-   throughput
-   consistency
-   availability
-   cost
-   operational complexity
-   failure behavior

------------------------------------------------------------------------

# 7. Core User Experience

## 7.1 Home

``` text
Learn
Practice
Challenges
Simulator
Interview
Progress
Components
```

## 7.2 Learning page

Example:

``` text
Caching

[Concept]
[How it works]
[Patterns]
[Trade-offs]
[Examples]
[Interactive Lab]
[Challenge]
```

## 7.3 Interactive Lab

Three major areas:

``` text
┌──────────────────────────────────────────────────────┐
│ Challenge / Requirements                              │
├────────────┬───────────────────────────┬──────────────┤
│ Components │                           │ Evaluation   │
│            │                           │              │
│ LB         │       ARCHITECTURE        │ Requirements │
│ Redis      │          CANVAS           │ Bottlenecks  │
│ Kafka      │                           │ Warnings     │
│ DB         │                           │ Suggestions  │
│ CDN        │                           │ Metrics      │
└────────────┴───────────────────────────┴──────────────┘
```

## 7.4 Evaluation panel

Show live state:

``` text
FUNCTIONALITY          100%
SCALABILITY             72%
AVAILABILITY             55%
LATENCY                  84%
CONSISTENCY              80%
SECURITY                 70%
COST                     91%
OBSERVABILITY            30%
```

But avoid presenting these scores as absolute truth.

Every score must be backed by evidence.

Example:

``` text
Availability: 55%

Issues:
⚠ PostgreSQL has a single primary.
⚠ Redis has no failover.
✓ API instances are redundant.
```

------------------------------------------------------------------------

# 8. Canonical Architecture Model

This is the most important technical design.

## 8.1 ArchitectureGraph

``` python
class ArchitectureGraph:
    id: str
    version: int
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]
    groups: list[ArchitectureGroup]
    requirements: list[Requirement]
    constraints: list[Constraint]
    traffic_model: TrafficModel
    deployment_model: DeploymentModel
    metadata: dict
```

## 8.2 ArchitectureNode

``` python
class ArchitectureNode:
    id: str
    type: str
    name: str
    technology: str | None
    position:
        x: float
        y: float
    properties: dict
    capacity: dict
    availability: dict
    deployment: dict
    metadata: dict
```

## 8.3 ArchitectureEdge

``` python
class ArchitectureEdge:
    id: str
    source: str
    target: str
    direction: str
    protocol: str | None
    traffic_type: str | None
    properties: dict
```

## 8.4 Requirements

``` python
class Requirement:
    id: str
    category: str
    description: str
    target: float | str | None
    unit: str | None
    priority: str
    validation_rules: list[str]
```

Examples:

``` text
RPS >= 100000
availability >= 99.99%
p95_latency <= 200ms
data_durability >= 99.999999999%
```

## 8.5 Constraints

Examples:

``` text
Budget <= $10,000/month
Must support global users
Strong consistency for payments
No data loss
EU data residency
```

------------------------------------------------------------------------

# 9. Component Taxonomy

The component catalog must be extensible.

## Client

-   Web client
-   Mobile client
-   IoT client
-   Internal service

## Edge

-   DNS
-   CDN
-   WAF
-   DDoS protection
-   Reverse proxy

## Traffic

-   Load balancer
-   API gateway
-   Rate limiter
-   Service mesh

## Compute

-   VM
-   Container
-   Kubernetes
-   Serverless function
-   Worker
-   Scheduler

## Cache

-   Local cache
-   Redis
-   Memcached
-   CDN cache
-   Distributed cache

## Databases

-   PostgreSQL
-   MySQL
-   SQL Server
-   MongoDB
-   DynamoDB
-   Cassandra
-   CockroachDB
-   Redis data store
-   Elasticsearch/OpenSearch

## Messaging

-   Kafka
-   RabbitMQ
-   SQS
-   SNS
-   Pub/Sub
-   NATS
-   Redis Streams

## Storage

-   Object storage
-   Block storage
-   File storage
-   Data warehouse

## Observability

-   Metrics
-   Logs
-   Tracing
-   Alert manager

## Reliability

-   Circuit breaker
-   Retry
-   Bulkhead
-   Failover
-   Replication
-   Multi-AZ
-   Multi-region

## AI/GenAI

-   LLM
-   Embedding model
-   Vector database
-   RAG retriever
-   Prompt gateway
-   Model router
-   Guardrail
-   Agent
-   Tool
-   MCP server
-   Agent memory
-   Evaluation service
-   AI gateway

------------------------------------------------------------------------

# 10. Component Knowledge Model

Every component should have machine-readable knowledge.

Example:

``` json
{
  "type": "redis",
  "category": "cache",
  "capabilities": [
    "low_latency_reads",
    "temporary_storage",
    "distributed_cache"
  ],
  "helps_with": [
    "database_read_load",
    "latency"
  ],
  "does_not_solve": [
    "durable_primary_storage",
    "global_consistency"
  ],
  "risks": [
    "cache_failure",
    "stale_data",
    "eviction",
    "invalidation"
  ],
  "common_patterns": [
    "cache_aside",
    "write_through"
  ],
  "failure_modes": [
    "node_failure",
    "network_partition",
    "hot_key"
  ],
  "tradeoffs": [
    "cost",
    "consistency"
  ]
}
```

This knowledge should live in versioned content/configuration, not
inside frontend code.

------------------------------------------------------------------------

# 11. Requirement Model

Requirements should be categorized.

## Functional

Examples:

-   users can upload files
-   users can send messages
-   users can search
-   users can create orders

## Scalability

Examples:

-   100K requests/sec
-   10M DAU
-   1TB/day

## Performance

Examples:

-   p95 \< 200ms
-   p99 \< 1s

## Availability

Examples:

-   99.9%
-   99.99%

## Consistency

Examples:

-   eventual consistency acceptable
-   strong consistency required

## Durability

Examples:

-   zero data loss
-   RPO \< 5 minutes

## Security

Examples:

-   encryption
-   authentication
-   authorization
-   tenant isolation

## Cost

Examples:

-   \<\$10K/month

------------------------------------------------------------------------

# 12. Deterministic Evaluation Engine

The rule engine is the foundation of the platform.

It must be independent of LLM providers.

## 12.1 Evaluation pipeline

``` text
ArchitectureGraph
       ↓
Normalize
       ↓
Validate Graph
       ↓
Build Dependency Graph
       ↓
Apply Rules
       ↓
Calculate Metrics
       ↓
Detect Bottlenecks
       ↓
Detect SPOFs
       ↓
Map Results to Requirements
       ↓
Generate EvaluationState
```

## 12.2 Rule structure

``` python
class EvaluationRule:
    id: str
    name: str
    category: str
    priority: str

    def applies(context) -> bool:
        ...

    def evaluate(context) -> RuleResult:
        ...
```

## 12.3 Rule result

``` python
class RuleResult:
    rule_id: str
    status: str
    severity: str
    message: str
    evidence: list[str]
    affected_nodes: list[str]
    affected_edges: list[str]
    requirement_ids: list[str]
    suggested_actions: list[str]
```

Statuses:

``` text
PASS
WARNING
FAIL
INFO
UNKNOWN
```

------------------------------------------------------------------------

# 13. Initial Deterministic Rules

## Graph integrity

-   disconnected required component
-   invalid edge
-   missing source
-   missing destination
-   cycles where inappropriate
-   no ingress
-   no data store where required

## Scalability

-   single compute instance under high traffic
-   database write bottleneck
-   database read bottleneck
-   insufficient worker capacity
-   queue consumer shortage
-   single partition hot spot
-   missing load balancing
-   missing horizontal scaling

## Availability

-   single database
-   single cache
-   single compute node
-   single region
-   single load balancer
-   missing failover

## Performance

-   synchronous expensive dependency
-   excessive network hops
-   no caching for high read workload
-   slow storage on latency-critical path

## Consistency

-   replica used for strongly consistent workflow
-   cache serving stale data for strict requirement
-   asynchronous pipeline used where synchronous confirmation is
    required

## Reliability

-   retries without timeout
-   retries without backoff
-   retry amplification
-   missing idempotency
-   queue without dead-letter handling

## Security

-   public database
-   missing authentication
-   missing authorization
-   unencrypted sensitive flow
-   missing secrets management

## Observability

-   no metrics
-   no logs
-   no tracing
-   no alerts for critical system

------------------------------------------------------------------------

# 14. Evidence-Based Evaluation

Every evaluator result must include evidence.

Bad:

``` text
Database is bad.
```

Good:

``` text
FAIL: Database write capacity

Evidence:
- Required writes: 20,000/sec
- Estimated primary capacity: 8,000/sec
- No sharding detected
- No write partitioning detected

Affected requirement:
R-SCALE-WRITE

Suggested options:
1. Add database sharding.
2. Introduce a write queue if asynchronous writes are acceptable.
3. Select a horizontally scalable datastore.
```

The learner must be able to inspect why the platform reached a
conclusion.

------------------------------------------------------------------------

# 15. Evaluation Is Not Binary

The engine should model architectural confidence.

Example:

``` text
Requirement:
p95 latency < 200ms

Current:
Estimated p95 = 170ms

Status:
PASS

Confidence:
MEDIUM

Reason:
Capacity model is approximate because
component-specific latency assumptions are incomplete.
```

This prevents false precision.

------------------------------------------------------------------------

# 16. Simulation Layer

Simulation should be Phase 3/4, not MVP.

## Inputs

-   RPS
-   read/write ratio
-   request size
-   data size
-   concurrency
-   latency
-   node capacity
-   cache hit ratio
-   replication factor
-   queue throughput
-   network latency

## Outputs

-   throughput
-   queue depth
-   utilization
-   p50
-   p95
-   p99
-   error rate
-   cache hit ratio
-   database load
-   estimated cost

## Example

``` text
Traffic:
100K RPS

API:
10 instances
10K RPS capacity each

Redis:
90% hit ratio

Database:
10K RPS

Result:
✓ API capacity
✓ Cache capacity
⚠ DB close to threshold
```

Simulation should initially be analytical/capacity-based rather than
attempting to model a complete cloud infrastructure.

------------------------------------------------------------------------

# 17. Failure / Chaos Engine

Later phases should support scenario events.

Examples:

``` text
EVENT: Redis node failure
EVENT: PostgreSQL primary failure
EVENT: traffic spike 10x
EVENT: Kafka consumer slowdown
EVENT: network partition
EVENT: region outage
EVENT: dependency latency +500ms
EVENT: cache hit ratio drops from 90% to 20%
EVENT: hot key detected
```

The engine evaluates the resulting architecture state.

Example:

``` text
Before:
Availability = 99.95%

Event:
Primary DB failure

After:
Availability = 71%

Cause:
No automatic failover.
```

------------------------------------------------------------------------

# 18. AI/Agent Architecture

AI must be modular.

``` text
                    AI Gateway
                        |
        +---------------+---------------+
        |               |               |
      OpenAI         Anthropic        Gemini
        |               |               |
        +---------------+---------------+
                        |
                Local/Ollama
```

Provider abstraction:

``` python
class LLMProvider:
    def generate(...)
    def stream(...)
    def structured_output(...)
```

Do not make application code provider-specific.

------------------------------------------------------------------------

# 19. Agent Roles

## 19.1 Tutor Agent

Purpose:

Explain concepts at the learner's level.

Inputs:

-   topic
-   learner level
-   current architecture
-   evaluation results

Outputs:

-   explanation
-   example
-   analogy
-   mini-exercise
-   next concept

## 19.2 Architecture Coach Agent

Purpose:

Help the learner without directly solving everything.

Behavior:

-   ask questions
-   provide hints
-   identify trade-offs
-   explain consequences

Do not immediately reveal the complete architecture unless requested.

## 19.3 Evaluator Agent

Purpose:

Provide qualitative reasoning after deterministic evaluation.

It receives:

``` text
ArchitectureGraph
Requirements
RuleResults
SimulationResults
```

It should NOT invent facts that conflict with deterministic results.

## 19.4 Interviewer Agent

Purpose:

Simulate system-design interviews.

It should progressively ask:

1.  requirements
2.  scale
3.  APIs
4.  data model
5.  high-level architecture
6.  bottlenecks
7.  reliability
8.  consistency
9.  trade-offs

## 19.5 Scenario Generator Agent

Generate new scenarios based on:

-   concepts
-   learner weaknesses
-   architecture patterns
-   difficulty
-   industry examples

Generated scenarios must pass deterministic validation before
publication.

## 19.6 Content Agent

Generate educational material drafts.

All generated content must be reviewed/validated before becoming
authoritative content.

------------------------------------------------------------------------

# 20. Agent Safety and Correctness

Agents must follow these rules:

1.  Never claim a deterministic result without evaluator evidence.
2.  Never invent benchmark numbers as facts.
3.  Clearly label assumptions.
4.  Distinguish industry convention from hard requirement.
5.  Explain alternative architectures.
6.  Avoid saying there is only one correct architecture when multiple
    designs satisfy requirements.
7.  If information is insufficient, ask for clarification or state
    uncertainty.
8.  Never silently modify learner architecture.
9.  Agent-proposed modifications must be previews/diffs.
10. The learner must approve architecture changes.

------------------------------------------------------------------------

# 21. AI Model Routing

Support task-based model selection.

Example:

``` text
Task                     Model Tier

classification           cheap
metadata extraction      cheap
content tagging          cheap
simple explanation       cheap
architecture critique    strong
interview simulation     strong
complex tradeoffs        reasoning
scenario generation      strong
content generation       strong
```

Allow:

``` text
Automatic
User selected
Admin configured
```

Providers should be pluggable.

Potential providers:

-   OpenAI
-   Anthropic
-   Google Gemini
-   Groq
-   local Ollama
-   other OpenAI-compatible endpoints

------------------------------------------------------------------------

# 22. AI Cost Control

AI calls must be observable.

Track:

``` text
provider
model
request_id
agent
task
input_tokens
output_tokens
latency
cost
cache_hit
success
failure
```

Use:

-   prompt caching where available
-   response caching
-   deterministic preprocessing
-   structured outputs
-   smaller models for simple tasks
-   batched generation
-   architecture summaries instead of full graph repetition
-   context pruning

The architecture graph should be serialized compactly for agent
consumption.

------------------------------------------------------------------------

# 23. Content Architecture

Content should be structured, not hardcoded into React.

Suggested model:

``` text
Topic
  ├── concept
  ├── explanation
  ├── diagrams
  ├── examples
  ├── tradeoffs
  ├── common_mistakes
  ├── interactive_labs
  ├── challenges
  └── related_topics
```

Content should support Markdown/MDX or structured JSON/YAML.

------------------------------------------------------------------------

# 24. Topic Taxonomy

Initial taxonomy:

## Foundations

-   client/server
-   HTTP
-   DNS
-   TLS
-   REST
-   WebSockets
-   networking basics

## Traffic management

-   load balancing
-   reverse proxy
-   API gateway
-   rate limiting
-   CDN
-   WAF

## Caching

-   local cache
-   Redis
-   Memcached
-   cache-aside
-   write-through
-   write-back
-   invalidation
-   TTL
-   eviction
-   hot keys

## Databases

-   relational
-   NoSQL
-   indexing
-   replication
-   read replicas
-   sharding
-   partitioning
-   transactions
-   isolation
-   consistency

## Messaging

-   queues
-   Kafka
-   RabbitMQ
-   SQS
-   Pub/Sub
-   NATS
-   consumer groups
-   ordering
-   retries
-   DLQ

## Distributed systems

-   CAP
-   consistency
-   availability
-   partition tolerance
-   consensus
-   distributed locks
-   idempotency
-   leader election

## Reliability

-   retries
-   timeout
-   circuit breaker
-   bulkhead
-   failover
-   disaster recovery
-   multi-AZ
-   multi-region

## Observability

-   logs
-   metrics
-   traces
-   SLI
-   SLO
-   SLA
-   alerting

## AI/GenAI systems

-   LLM gateway
-   model routing
-   RAG
-   embeddings
-   vector DB
-   reranking
-   agents
-   tool calling
-   MCP
-   agent memory
-   guardrails
-   AI observability
-   evaluation
-   inference scaling

------------------------------------------------------------------------

# 25. Challenge Schema

Example:

``` yaml
id: url-shortener-001
title: Design a URL Shortener
difficulty: easy

requirements:
  - id: r1
    type: functional
    description: Create short URLs

  - id: r2
    type: scale
    metric: requests_per_second
    value: 10000

  - id: r3
    type: latency
    metric: p95
    value: 200
    unit: ms

constraints:
  - eventual_consistency_allowed: true

learning_objectives:
  - caching
  - database_scaling
  - hashing
  - read_heavy_workloads

allowed_components:
  - client
  - load_balancer
  - api
  - redis
  - postgres
  - object_storage

evaluation_rules:
  - scale.read_capacity
  - database.primary_bottleneck
  - cache.opportunity

scenarios:
  - traffic_spike
  - cache_failure
  - database_failure
```

------------------------------------------------------------------------

# 26. Difficulty Model

## Beginner

Focus:

-   recognizing components
-   basic data flow
-   simple bottlenecks

## Intermediate

Focus:

-   scaling
-   caching
-   queues
-   replication
-   trade-offs

## Advanced

Focus:

-   distributed consistency
-   partitioning
-   multi-region
-   failure handling
-   cost
-   observability

## Expert

Focus:

-   ambiguous requirements
-   competing constraints
-   complex failure modes
-   architectural trade-offs
-   evolving requirements

------------------------------------------------------------------------

# 27. Progressive Challenge Design

A single system should evolve.

Example: URL shortener.

### Level 1

``` text
1K users
100 RPS
```

Learn:

-   API
-   DB

### Level 2

``` text
10K RPS
```

Introduce:

-   load balancer
-   horizontal scaling

### Level 3

``` text
80% reads
```

Introduce:

-   caching

### Level 4

``` text
global users
```

Introduce:

-   CDN
-   multi-region

### Level 5

``` text
99.99% availability
```

Introduce:

-   replication
-   failover

### Level 6

``` text
10x traffic spike
```

Introduce:

-   queues
-   autoscaling
-   backpressure

This should become a major content-generation pattern.

------------------------------------------------------------------------

# 28. The "Why Did I Add This?" Experience

Every component should have an educational explanation.

When the learner adds Redis:

``` text
Why Redis?

You added Redis between API and PostgreSQL.

Current effect:
✓ Reduces repeated DB reads
✓ Can lower latency
✓ Reduces DB load

New trade-offs:
⚠ Cache invalidation
⚠ Stale data
⚠ Cache availability

Relevant concepts:
→ Cache-aside
→ TTL
→ Cache eviction
→ Distributed cache
```

Buttons:

``` text
[Explain]
[Show Example]
[Try Mini Exercise]
[Show Alternative]
```

------------------------------------------------------------------------

# 29. Recommendation Engine

Recommendations must be generated from evidence.

Example:

``` text
Requirement:
100K RPS

Current:
API capacity = 20K RPS

Recommendation:
Add horizontal API scaling.

Why:
Current compute layer is below required capacity.

Expected effect:
Capacity increases.

New concern:
Database becomes the next likely bottleneck.
```

The recommendation engine should identify:

``` text
Current bottleneck
↓
Possible interventions
↓
Expected benefit
↓
New trade-offs
↓
Next likely bottleneck
```

This creates the interactive learning loop.

------------------------------------------------------------------------

# 30. Architecture State Timeline

Store architecture versions.

``` text
v1
API → PostgreSQL

v2
API → Redis → PostgreSQL

v3
LB → API replicas → Redis → PostgreSQL

v4
LB → API replicas → Redis Cluster → DB replicas
```

Allow users to compare:

``` text
v1 vs v2
v2 vs v3
```

Show:

``` text
What changed?
What improved?
What regressed?
What new risks appeared?
```

------------------------------------------------------------------------

# 31. Architecture Diff

Example:

``` diff
+ Load Balancer
+ Redis
+ API replica x4

- API single instance
```

Evaluation diff:

``` text
Scalability:
+24

Latency:
+18

Availability:
+15

Cost:
-8

Complexity:
-12
```

The learner should understand that improvements are multidimensional.

------------------------------------------------------------------------

# 32. Backend Architecture

Recommended MVP:

``` text
React
  |
  | HTTPS
  ↓
FastAPI
  |
  +--------------------+
  |                    |
  ↓                    ↓
PostgreSQL            Redis
  |
  +--------------------+
  |
  ↓
Evaluation Engine
  |
  ↓
AI Gateway
  |
  +--- OpenAI
  +--- Anthropic
  +--- Gemini
  +--- Ollama
```

Do not introduce Kafka/Kubernetes/microservices for the platform itself
in MVP unless a real requirement emerges.

Start as a modular monolith.

------------------------------------------------------------------------

# 33. Backend Modules

``` text
backend/
  app/
    api/
    domain/
      architecture/
      challenges/
      components/
      learning/
      evaluation/
      simulation/
    evaluation/
      rules/
      engine/
    agents/
      tutor/
      coach/
      interviewer/
      evaluator/
      generator/
    llm/
      providers/
      routing/
      prompts/
    content/
    persistence/
    auth/
    observability/
```

------------------------------------------------------------------------

# 34. Frontend Architecture

Recommended:

``` text
React
TypeScript
React Flow
TanStack Query
Zustand or equivalent state store
Tailwind or component library
```

Separate:

``` text
Canvas state
Server state
Evaluation state
UI state
```

Do not mix them.

------------------------------------------------------------------------

# 35. Canvas Design

Use React Flow or equivalent graph editor.

Required interactions:

-   drag component
-   move component
-   connect nodes
-   delete
-   duplicate
-   group
-   configure
-   zoom
-   pan
-   auto-layout
-   undo/redo
-   save
-   load
-   version
-   inspect
-   evaluate

Connections should have semantic properties.

Example:

``` text
API → Kafka

protocol: TCP
pattern: asynchronous
delivery: at_least_once
ordering: partition
```

------------------------------------------------------------------------

# 36. API Design

Example endpoints:

``` text
GET    /api/topics
GET    /api/topics/{id}

GET    /api/components
GET    /api/components/{id}

GET    /api/challenges
GET    /api/challenges/{id}

POST   /api/architectures
GET    /api/architectures/{id}
PUT    /api/architectures/{id}

POST   /api/architectures/{id}/evaluate
GET    /api/architectures/{id}/evaluations

POST   /api/architectures/{id}/simulate

POST   /api/ai/tutor
POST   /api/ai/coach
POST   /api/ai/interview

GET    /api/progress
```

------------------------------------------------------------------------

# 37. Database Model

Initial entities:

``` text
User
Topic
Lesson
Component
ComponentCapability
Challenge
Requirement
Constraint
Architecture
ArchitectureVersion
ArchitectureNode
ArchitectureEdge
Evaluation
EvaluationRuleResult
SimulationRun
Scenario
ScenarioRun
AgentSession
LLMRequest
LearningProgress
```

------------------------------------------------------------------------

# 38. Persistence Strategy

PostgreSQL stores authoritative state.

JSONB can be used for flexible component properties.

Example:

``` text
architecture_nodes.properties JSONB
architecture_edges.properties JSONB
evaluation.details JSONB
challenge.config JSONB
```

Do not over-normalize the evolving architecture graph in the first
release.

------------------------------------------------------------------------

# 39. Authentication

MVP:

-   email/password or OAuth
-   anonymous playground optional
-   saved designs require account

Future:

-   GitHub login
-   Google login
-   enterprise SSO

------------------------------------------------------------------------

# 40. Observability

Instrument:

``` text
Frontend
Backend
Evaluation engine
LLM gateway
Agents
Simulation
Database
```

Track:

-   latency
-   errors
-   token usage
-   model
-   cost
-   evaluation duration
-   simulation duration
-   challenge completion
-   rule failures
-   agent failures

Recommended technology:

``` text
OpenTelemetry
Prometheus
Grafana
Loki
Tempo/Jaeger
```

Use the same observability philosophy as the systems being taught.

------------------------------------------------------------------------

# 41. Testing Strategy

## Unit tests

-   rule engine
-   graph validation
-   component model
-   requirement evaluation
-   recommendation logic

## Integration tests

-   API
-   PostgreSQL
-   Redis
-   evaluation pipeline
-   LLM gateway

## Frontend tests

-   canvas interactions
-   drag/drop
-   edge creation
-   state persistence
-   evaluation display

## Scenario tests

Every challenge should have known architecture fixtures.

Example:

``` text
fixture_good_architecture
fixture_missing_cache
fixture_single_point_of_failure
fixture_overloaded_database
```

The evaluator must produce expected results.

------------------------------------------------------------------------

# 42. Golden Architecture Tests

Maintain canonical architecture examples.

Example:

``` text
URL Shortener

Expected:
PASS functional
PASS read scale
WARNING single DB primary
PASS latency
```

When the rule engine changes, run all golden architectures.

This prevents regressions.

------------------------------------------------------------------------

# 43. Agent Evaluation

Agents require their own evaluation suite.

Test:

-   factual correctness
-   consistency with deterministic evaluator
-   hallucination rate
-   helpfulness
-   difficulty appropriateness
-   explanation quality
-   refusal to over-prescribe
-   structured output validity

Use deterministic fixtures wherever possible.

------------------------------------------------------------------------

# 44. Security

Never send unnecessary user information to LLMs.

Protect:

-   API keys
-   model credentials
-   user designs
-   private architectures

Use:

-   server-side provider keys
-   secret management
-   request limits
-   authentication
-   authorization
-   audit logs

Agent-generated architecture modifications must be treated as untrusted
suggestions.

------------------------------------------------------------------------

# 45. Cost Architecture

MVP should work with free/local options.

Recommended tiers:

## Free

-   educational content
-   basic playground
-   deterministic evaluation
-   limited challenges
-   local/basic AI where feasible

## Pro

-   advanced scenarios
-   AI tutor
-   interview mode
-   deeper analysis
-   simulation
-   architecture history

## Future

-   enterprise
-   team challenges
-   private content
-   company-specific interview training

Do not make core learning dependent on expensive LLM calls.

------------------------------------------------------------------------

# 46. Phase Plan

## Phase 0 --- Research and Product Definition

Goal:

Validate product direction and finalize architecture model.

Tasks:

-   analyze competing products
-   catalog component types
-   define initial challenge taxonomy
-   define architecture graph
-   define requirement schema
-   define evaluator schema
-   define UI wireframes
-   define MVP boundaries

Deliverables:

``` text
SYSTEM.md
ArchitectureGraph schema
Component schema
Challenge schema
Evaluation schema
Initial UI wireframes
```

Exit criteria:

-   architecture can be represented without UI-specific assumptions
-   at least 20 initial challenge concepts defined
-   at least 50 deterministic rules identified

------------------------------------------------------------------------

# 47. Phase 1 --- Learning Platform MVP

Goal:

Build the educational foundation.

Features:

-   landing page
-   topics
-   articles
-   diagrams
-   examples
-   glossary
-   search
-   learning progress
-   basic quizzes

Content:

``` text
Networking
HTTP
Load Balancer
Caching
Databases
Queues
Replication
Sharding
CAP
Consistency
Availability
```

No complex AI required.

Exit criteria:

-   30--50 high-quality lessons
-   progress tracking
-   mobile-friendly learning experience
-   searchable content

------------------------------------------------------------------------

# 48. Phase 2 --- Interactive Architecture Canvas

Goal:

Build the architecture playground.

Features:

-   drag/drop
-   component palette
-   connections
-   properties
-   save/load
-   undo/redo
-   export
-   architecture JSON
-   versioning

Initial components:

``` text
Client
API
Load Balancer
CDN
Redis
PostgreSQL
MongoDB
Kafka
RabbitMQ
Worker
Object Storage
```

Exit criteria:

A user can construct and save:

``` text
Client
 → CDN
 → Load Balancer
 → API
 → Redis
 → PostgreSQL
```

as a machine-readable architecture.

------------------------------------------------------------------------

# 49. Phase 3 --- Deterministic Evaluation Engine

Goal:

Make the canvas intelligent.

Features:

-   graph validation
-   requirement evaluation
-   bottleneck detection
-   SPOF detection
-   scalability rules
-   availability rules
-   latency rules
-   consistency rules
-   basic recommendations

Evaluation panel:

``` text
PASS
WARNING
FAIL
INFO
```

Every result includes evidence.

Exit criteria:

At least 100 automated tests and 30+ useful rules.

------------------------------------------------------------------------

# 50. Phase 4 --- Scenario Engine

Goal:

Introduce real learning challenges.

Features:

-   challenge catalog
-   requirements
-   constraints
-   difficulty
-   allowed components
-   evaluation rules
-   progressive levels
-   scoring
-   architecture submission

Initial challenges:

1.  Static website
2.  3-tier web application
3.  URL shortener
4.  Rate limiter
5.  Notification system
6.  Chat system
7.  File storage
8.  Image processing
9.  Video streaming
10. Search system
11. News feed
12. Payment system
13. Job queue
14. Metrics system
15. Distributed cache

Exit criteria:

50 validated challenges.

------------------------------------------------------------------------

# 51. Phase 5 --- AI Tutor and Coach

Goal:

Add contextual AI without making AI the evaluator.

Features:

-   explain this component
-   explain this failure
-   explain this recommendation
-   ask for hint
-   compare alternatives
-   architecture critique
-   adaptive teaching

Agent input should include:

``` text
Challenge
Requirements
Architecture
Deterministic results
Learner history
```

Exit criteria:

AI never contradicts deterministic facts without explicitly identifying
uncertainty.

------------------------------------------------------------------------

# 52. Phase 6 --- Interview Agent

Goal:

Simulate real system-design interviews.

Features:

-   interviewer persona
-   adaptive questioning
-   time tracking
-   requirement clarification
-   architecture review
-   trade-off questioning
-   final score
-   detailed feedback

Score dimensions:

``` text
Requirements
Capacity estimation
Architecture
Scalability
Reliability
Consistency
Security
Observability
Trade-offs
Communication
```

------------------------------------------------------------------------

# 53. Phase 7 --- Simulation

Goal:

Move from static evaluation to quantitative behavior.

Implement:

-   traffic model
-   component capacity
-   latency model
-   cache hit model
-   queue throughput
-   database capacity
-   utilization
-   p50/p95/p99 estimation
-   cost estimation

Example:

``` text
100K RPS
↓
10 API nodes
↓
Redis 90% hit
↓
10K DB reads/sec
```

Show traffic visually.

------------------------------------------------------------------------

# 54. Phase 8 --- Chaos Engineering Learning

Goal:

Teach failure behavior.

Features:

-   inject failure
-   observe consequences
-   repair architecture
-   compare before/after

Scenarios:

``` text
DB failure
Cache failure
Queue failure
Region failure
Network latency
Traffic spike
Hot key
Consumer lag
Dependency outage
```

------------------------------------------------------------------------

# 55. Phase 9 --- AI/Agent System Design Lab

Goal:

Make modern AI architecture a first-class learning area.

Components:

``` text
User
API
AI Gateway
Model Router
LLM
Embedding Model
Vector DB
Retriever
Reranker
Prompt Store
Guardrail
Agent
Tool
MCP Server
Memory
Evaluation
Observability
```

Challenges:

-   RAG system
-   enterprise chatbot
-   AI gateway
-   multi-model routing
-   agent platform
-   MCP platform
-   AI evaluation system
-   multi-agent workflow
-   inference platform
-   LLM observability

------------------------------------------------------------------------

# 56. Phase 10 --- Collaborative Platform

Future:

-   share architecture
-   team exercises
-   instructor mode
-   peer review
-   leaderboard
-   architecture comments
-   live collaboration
-   classroom mode

------------------------------------------------------------------------

# 57. Phase 11 --- Enterprise

Future:

-   private challenge libraries
-   organization-specific architectures
-   SSO
-   analytics
-   team progress
-   custom scoring
-   internal knowledge integration
-   private LLMs
-   audit logs

------------------------------------------------------------------------

# 58. MVP Definition

Do NOT attempt all phases initially.

The recommended MVP is:

``` text
Learning Content
        +
Interactive Canvas
        +
Architecture Graph
        +
Deterministic Evaluation
        +
20–30 Challenges
```

AI should initially be limited to:

``` text
Explain
Hint
Critique
```

Do not build full simulation, chaos engineering, multi-agent
orchestration, billing, or enterprise collaboration in MVP.

------------------------------------------------------------------------

# 59. Suggested MVP Stack

## Frontend

``` text
React
TypeScript
Vite
React Flow
TanStack Query
Zustand
Tailwind CSS
```

## Backend

``` text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

## Database

``` text
PostgreSQL
```

## Cache

``` text
Redis
```

## AI

``` text
Provider abstraction
OpenAI
Anthropic
Gemini
Ollama
```

## Observability

``` text
OpenTelemetry
Prometheus
Grafana
Loki
```

## Deployment

Start simple:

``` text
Docker Compose
```

Later:

``` text
AWS
ECS/Fargate
RDS
ElastiCache
S3
CloudFront
ALB
```

Do not introduce Kubernetes unless operational requirements justify it.

------------------------------------------------------------------------

# 60. Recommended Repository

``` text
system-design-platform/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── learning/
│   │   │   ├── canvas/
│   │   │   ├── challenges/
│   │   │   ├── evaluation/
│   │   │   ├── interview/
│   │   │   └── progress/
│   │   ├── graph/
│   │   ├── api/
│   │   ├── stores/
│   │   └── types/
│   └── tests/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── domain/
│   │   ├── evaluation/
│   │   ├── simulation/
│   │   ├── agents/
│   │   ├── llm/
│   │   ├── content/
│   │   ├── persistence/
│   │   └── observability/
│   └── tests/
│
├── content/
│   ├── topics/
│   ├── challenges/
│   ├── components/
│   ├── rules/
│   └── scenarios/
│
├── schemas/
│   ├── architecture.schema.json
│   ├── challenge.schema.json
│   ├── component.schema.json
│   └── evaluation.schema.json
│
├── docs/
│   ├── architecture/
│   ├── product/
│   └── agents/
│
├── infra/
│   ├── docker/
│   └── deployment/
│
├── tests/
│   ├── golden_architectures/
│   ├── challenges/
│   └── evaluation/
│
├── SYSTEM.md
├── README.md
└── docker-compose.yml
```

------------------------------------------------------------------------

# 61. Agent Development Rules

All coding agents working on the repository must follow these rules.

## Rule 1

Read `SYSTEM.md` before making architectural changes.

## Rule 2

Never create provider-specific LLM logic in business modules.

## Rule 3

Never put evaluation rules in React components.

## Rule 4

Never make the canvas the source of truth.

## Rule 5

Never use an LLM where deterministic logic is sufficient.

## Rule 6

Never silently change public schemas.

## Rule 7

Add tests for every new evaluation rule.

## Rule 8

Add golden architecture fixtures for major evaluator changes.

## Rule 9

Prefer modular monolith architecture until scaling requirements justify
separation.

## Rule 10

Do not over-engineer the infrastructure.

------------------------------------------------------------------------

# 62. Agent Workflow

Every development task should follow:

``` text
Understand
   ↓
Inspect existing code
   ↓
Read relevant schemas
   ↓
Identify affected domain
   ↓
Plan
   ↓
Implement
   ↓
Test
   ↓
Run existing tests
   ↓
Check architecture invariants
   ↓
Document
```

Agents must not immediately start coding without understanding the
architecture.

------------------------------------------------------------------------

# 63. Feature Development Workflow

For a new component:

``` text
Component definition
      ↓
Component knowledge
      ↓
Frontend representation
      ↓
Graph serialization
      ↓
Evaluation rules
      ↓
Tests
      ↓
Documentation
```

For a new challenge:

``` text
Challenge definition
      ↓
Requirements
      ↓
Constraints
      ↓
Expected concepts
      ↓
Evaluation rules
      ↓
Golden architectures
      ↓
Hints
      ↓
AI context
      ↓
Challenge validation
```

------------------------------------------------------------------------

# 64. Important Architectural Invariants

These must always remain true.

### Invariant 1

Frontend graph and backend graph use the same canonical schema.

### Invariant 2

Evaluation must be reproducible.

Same architecture + same requirements + same rule version should produce
the same deterministic result.

### Invariant 3

AI does not determine core correctness.

### Invariant 4

Every recommendation has evidence.

### Invariant 5

Architecture versions are immutable after creation.

### Invariant 6

User-approved changes create a new architecture version.

### Invariant 7

Agent modifications require explicit user approval.

### Invariant 8

Content and evaluation rules are versioned.

------------------------------------------------------------------------

# 65. Versioning

Version:

``` text
Architecture
Challenge
Component knowledge
Evaluation rules
Agent prompts
Content
Simulation models
```

Evaluation should record:

``` text
rule_version
component_catalog_version
challenge_version
simulation_version
agent_prompt_version
model
```

This allows historical results to remain understandable.

------------------------------------------------------------------------

# 66. Recommendation Quality Model

A recommendation should contain:

``` text
Problem
Evidence
Recommendation
Expected benefit
Trade-offs
Alternatives
Confidence
Related learning topics
```

Example:

``` text
Problem:
Database read load is 80K/sec.

Evidence:
Current DB estimated safe read capacity: 20K/sec.

Recommendation:
Add a distributed cache.

Expected benefit:
Reduce repeated database reads.

Trade-offs:
- stale data
- cache invalidation
- cache failure

Alternative:
Read replicas.

Confidence:
HIGH

Learn:
Caching → Cache Aside
```

------------------------------------------------------------------------

# 67. Learning Personalization

Track:

``` text
weak topics
completed topics
failed rules
frequent mistakes
challenge difficulty
time spent
hint usage
architecture improvements
interview scores
```

Then recommend:

``` text
You frequently create single points of failure.

Recommended next lesson:
High Availability and Failover

Recommended challenge:
Design a highly available notification system.
```

------------------------------------------------------------------------

# 68. Content Quality

Educational content should distinguish:

``` text
Concept
Pattern
Rule of thumb
Common practice
Hard requirement
Trade-off
Technology-specific behavior
```

Avoid oversimplifications such as:

> "Always use Redis."

Instead:

> "Caching is useful when repeated reads justify the additional
> complexity and the workload can tolerate the cache's consistency
> characteristics."

------------------------------------------------------------------------

# 69. Technology Neutrality

Teach concepts before vendor products.

Example:

``` text
Concept:
Distributed cache

Examples:
Redis
Memcached
Hazelcast
Cloud-managed caches
```

Similarly:

``` text
Message broker
→ Kafka
→ RabbitMQ
→ SQS
→ Pub/Sub
→ NATS
```

The learner should understand why a category exists before memorizing
products.

------------------------------------------------------------------------

# 70. Interview-Oriented Learning

For interview challenges, the system should teach a structured process:

``` text
1. Clarify requirements
2. Estimate scale
3. Define APIs
4. Define data model
5. Draw high-level architecture
6. Identify bottlenecks
7. Scale critical components
8. Discuss consistency
9. Discuss availability
10. Discuss failures
11. Discuss observability
12. Discuss trade-offs
```

The platform should grade the process, not merely the final diagram.

------------------------------------------------------------------------

# 71. Example End-to-End Scenario

## Prompt

Design a notification system.

Requirements:

``` text
10M users
1M notifications/hour
Email + SMS + push
99.9% availability
Users should not wait for provider delivery
```

Initial learner architecture:

``` text
Client
 ↓
API
 ↓
PostgreSQL
 ↓
Email provider
```

Evaluator:

``` text
FAIL:
Synchronous provider calls violate asynchronous delivery requirement.

FAIL:
Provider latency directly affects API latency.

WARNING:
No retry strategy.

WARNING:
No delivery tracking.
```

Learner adds Kafka:

``` text
Client
 ↓
API
 ↓
Kafka
 ↓
Worker
 ↓
Email provider
```

Evaluator:

``` text
PASS:
API/provider decoupling

PASS:
Asynchronous processing

WARNING:
No retry/DLQ

WARNING:
No idempotency
```

Learner adds:

``` text
Retry
DLQ
Idempotency store
```

Evaluator updates.

This is the central learning experience the product should optimize for.

------------------------------------------------------------------------

# 72. Future "Architecture Autopilot"

Do not implement in MVP, but design the interfaces so it becomes
possible.

The learner could ask:

> "Show me three ways to solve the current bottleneck."

Agent produces:

``` text
Option A
Redis

Option B
Read replicas

Option C
Database sharding
```

Each option is represented as a graph diff.

The learner can apply one and evaluate it.

Never overwrite the original design.

------------------------------------------------------------------------

# 73. Future Agent-as-Learner

A future mode could allow:

``` text
Human architecture
vs
AI architecture
```

The AI must explain its decisions.

The learner can challenge it:

> Why Kafka instead of RabbitMQ?

The AI must defend the choice.

This turns architecture into a debate/learning environment.

------------------------------------------------------------------------

# 74. Future Multi-Agent Architecture

Possible later architecture:

``` text
                    Orchestrator
                         |
       +-----------------+----------------+
       |                 |                |
       ↓                 ↓                ↓
 Architecture       Reliability       Performance
 Agent              Agent             Agent
       |                 |                |
       +-----------------+----------------+
                         ↓
                    Critic Agent
                         ↓
                  Teacher Agent
```

Do not implement this complexity until single-agent workflows prove
useful.

------------------------------------------------------------------------

# 75. Metrics for Product Success

Track more than page views.

## Learning

-   lesson completion
-   concept retention
-   challenge completion
-   improvement between attempts

## Architecture

-   number of designs
-   components used
-   architecture iterations
-   average fixes per challenge

## Reasoning

-   bottlenecks identified
-   hints requested
-   trade-off explanations
-   failed requirements corrected

## Interview

-   score improvement
-   completion time
-   requirements coverage
-   communication score

## AI

-   helpfulness
-   correction rate
-   hallucination rate
-   cost/user
-   latency

------------------------------------------------------------------------

# 76. MVP Success Criteria

The MVP is successful if a new learner can:

1.  Read about caching.
2.  Open a caching challenge.
3.  Receive a workload.
4.  Build a basic architecture.
5.  Drag Redis onto the canvas.
6.  Connect it correctly.
7.  Immediately see which requirement changed.
8.  See what problem Redis solved.
9.  See what new trade-off appeared.
10. Ask the AI why.
11. Modify the architecture again.
12. Compare versions.
13. Complete the challenge.

If this loop feels excellent, the product has a strong foundation.

------------------------------------------------------------------------

# 77. Anti-Goals

Do NOT initially build:

-   generic diagramming like Miro
-   arbitrary cloud infrastructure provisioning
-   real AWS resource deployment
-   production traffic generation
-   complex Kubernetes orchestration
-   dozens of LLM agents
-   a massive social network
-   a marketplace
-   excessive gamification
-   vendor-specific lock-in
-   LLM-only scoring

The platform should first prove:

> **Interactive architecture reasoning improves learning.**

------------------------------------------------------------------------

# 78. Reference Projects and Research

These references should be treated as inspiration and competitive
analysis, not as implementation specifications.

## systemdesign42/system-design-academy

GitHub repository:

`https://github.com/systemdesign42/system-design-academy`

Useful for:

-   system-design topics
-   distributed systems
-   scalability
-   interview questions
-   educational content structure

The repository is public and currently has a large community following.
Its topics include computer science, distributed systems, high-level
design, scalability, software engineering, and system-design interviews.

Reference:

`https://github.com/systemdesign42/system-design-academy`

## ScaleDojo

`https://scaledojo.dev/`

Important references:

-   interactive HLD architecture lab
-   drag/drop architecture
-   deterministic scoring
-   AI architect review
-   progressive challenges
-   GenAI systems lab
-   chaos/failure learning concepts

ScaleDojo is particularly important as a competitive benchmark because
it combines interactive architecture construction with deterministic
scoring and AI review.

References:

`https://scaledojo.dev/`

`https://scaledojo.dev/about`

`https://scaledojo.dev/genai`

`https://scaledojo.dev/forge`

## MockArch

`https://mockarch.in/`

Important references:

-   drag/drop architecture
-   traffic simulation
-   cost estimation
-   rule-based analysis
-   AI feedback
-   interview scenarios

References:

`https://mockarch.in/`

`https://mockarch.in/system-design-simulator`

`https://mockarch.in/system-design-ai-feedback`

## sysd.ai

`https://sysd.ai/`

Important reference:

**Design Drills**

The user receives a broken architecture, identifies the flaw, fixes it,
and observes the traffic behavior.

This is highly relevant to the proposed Repair Mode and should influence
challenge design without copying implementation or content.

## System Design Simulator

`https://www.systemdesignsimulator.in/`

Useful for:

-   traffic visualization
-   capacity analysis
-   latency
-   failure behavior
-   simulation-oriented learning

## 10xarch

GitHub:

`https://github.com/AhmadMHawwash/10xarch`

Useful for:

-   interactive playground concepts
-   AI feedback
-   architecture practice
-   learning experience

## Sidebar

GitHub:

`https://github.com/JoshuaHirakawa/Sidebar`

Useful for:

-   interactive architecture board
-   AI interviewer
-   architecture interview learning

## React Flow

`https://reactflow.dev/`

Recommended reference for the architecture canvas implementation.

Use it as a graph UI layer, not as the canonical architecture model.

## OpenTelemetry

`https://opentelemetry.io/`

Reference for observability architecture.

## PostgreSQL

`https://www.postgresql.org/`

Reference for relational persistence.

## FastAPI

`https://fastapi.tiangolo.com/`

Reference for Python API implementation.

------------------------------------------------------------------------

# 79. Competitive Positioning

Do not compete on:

> "We have AI feedback."

That is becoming standard.

Compete on:

> **We teach you system design by letting you change the system and
> observe the consequences.**

Potential positioning:

### Option A

**Build. Break. Fix. Learn System Design.**

### Option B

**Learn System Design by Building Real Systems.**

### Option C

**A Simulator for System Design Thinking.**

### Option D

**Design the System. Discover the Trade-offs.**

The strongest product principle is:

> **Every architectural decision should teach something.**

------------------------------------------------------------------------

# 80. Final Architecture

Target long-term architecture:

``` text
                         ┌─────────────────────┐
                         │       React         │
                         │  Learning + Canvas  │
                         └──────────┬──────────┘
                                    │
                              Architecture
                                    │
                              Graph Schema
                                    │
                         ┌──────────▼──────────┐
                         │       FastAPI       │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       Content Engine        Evaluation Engine      Challenge Engine
              │                     │                     │
              │              ┌──────┴──────┐              │
              │              ▼             ▼              │
              │          Rule Engine   Simulation         │
              │              │             │              │
              └──────────────┼─────────────┼──────────────┘
                             │             │
                             ▼             ▼
                         State / Results / Evidence
                                   │
                              ┌────▼─────┐
                              │ AI Layer │
                              └────┬─────┘
                                   │
               ┌───────────────────┼───────────────────┐
               │                   │                   │
               ▼                   ▼                   ▼
            Tutor               Coach             Interviewer
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   │
                              AI Gateway
                                   │
                    ┌──────────────┼───────────────┐
                    ▼              ▼               ▼
                  OpenAI        Anthropic        Gemini
                    │
                  Ollama
```

------------------------------------------------------------------------

# 81. Final Development Principle

The platform should evolve in this order:

``` text
Content
  ↓
Architecture Graph
  ↓
Interactive Canvas
  ↓
Deterministic Evaluation
  ↓
Challenges
  ↓
AI Tutor
  ↓
Interview Agent
  ↓
Simulation
  ↓
Chaos
  ↓
AI Architecture Lab
  ↓
Multi-agent learning
```

Do not reverse this order.

The most important technical investment is the **canonical architecture
graph + requirement model + deterministic evaluation engine**.

The most important product investment is the **feedback loop between an
architectural change and its consequences**.

The most important AI investment is **contextual teaching based on the
learner's actual architecture**, not generic chatbot responses.

------------------------------------------------------------------------

# 82. Definition of Done for the First Production-Quality Milestone

The first major milestone is complete when:

-   [ ] User can read system-design lessons.
-   [ ] User can browse component knowledge.
-   [ ] User can start a challenge.
-   [ ] User receives explicit requirements and constraints.
-   [ ] User can drag components onto a canvas.
-   [ ] User can connect components.
-   [ ] Architecture is stored as a canonical graph.
-   [ ] Architecture can be versioned.
-   [ ] Deterministic evaluator analyzes the graph.
-   [ ] Evaluation maps results to requirements.
-   [ ] Every important issue has evidence.
-   [ ] User can see what a component solved.
-   [ ] User can see newly introduced trade-offs.
-   [ ] User can request a hint.
-   [ ] AI explanations use deterministic evaluation context.
-   [ ] AI cannot silently change the architecture.
-   [ ] At least 20 challenges exist.
-   [ ] At least 100 evaluator tests exist.
-   [ ] Golden architecture tests exist.
-   [ ] Observability exists for backend and AI calls.
-   [ ] LLM provider abstraction supports multiple providers.
-   [ ] Free/local LLM path is possible.
-   [ ] Core learning does not require paid AI.
-   [ ] Architecture data is exportable.
-   [ ] Documentation is versioned with the codebase.

------------------------------------------------------------------------

# 83. Guiding Question for Every Feature

Before implementing a feature, ask:

> **Does this help the learner understand a system-design decision, its
> consequence, or its trade-off?**

If the answer is no, defer the feature unless there is a clear platform
requirement.
