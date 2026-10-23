# HAPA Architecture

## Overview

HAPA (Hierarchical Autonomous Personal Assistant) is a multi-tier agent framework designed to execute complex software, automation, and coordination work with minimal manual intervention. Its core design separates planning, oversight, execution, persistence, and ingress into distinct layers so that higher tiers can delegate without doing raw execution work themselves.

The repository currently contains the foundational schema layer in [`src/core/schemas.py`](../src/core/schemas.py) and schema validation tests in [`tests/test_core/test_schemas.py`](../tests/test_core/test_schemas.py). The rest of this document describes the intended target architecture defined by the project design artifacts and the current package layout.

## Architectural goals

HAPA is built around five central principles:

1. **Pure delegation**  
   Tier 1 and Tier 2 coordinate and validate work. They do not directly perform heavy execution, browser automation, or terminal-heavy tasks.

2. **Dynamic specialization**  
   Tier 3 workers are created on demand with the narrowest toolset needed for the task.

3. **Workspace isolation and copy-on-write**  
   Execution happens inside isolated workspaces or container volumes. Only verified diffs are propagated upward.

4. **Multi-perspective quality assurance**  
   Generated code and automation output are reviewed by distinct reviewers such as security, performance, and edge-case specialists.

5. **Fast-path routing**  
   Low-risk tasks can bypass deeper tiers to reduce latency and cost.

## Repository layout

The target layout described by the design artifacts is:

- [`src/main.py`](../src/main.py) — application entrypoint and Uvicorn runner
- [`src/api/app.py`](../src/api/app.py) — FastAPI application factory
- [`src/api/routes/chat.py`](../src/api/routes/chat.py) — `POST /api/v1/chat`
- [`src/api/routes/tasks.py`](../src/api/routes/tasks.py) — task scheduling and active-task APIs
- [`src/api/routes/approvals.py`](../src/api/routes/approvals.py) — human approval queues
- [`src/api/routes/observability.py`](../src/api/routes/observability.py) — WebSocket/SSE telemetry stream
- [`src/api/routes/health.py`](../src/api/routes/health.py) — health and telemetry endpoints
- [`src/api/websocket.py`](../src/api/websocket.py) — real-time telemetry bus
- [`src/core/schemas.py`](../src/core/schemas.py) — strict Pydantic v2 wire schemas
- [`src/tiers/tier1_supervisor/`](../src/tiers/tier1_supervisor/) — root supervisor, router, and global state
- [`src/tiers/tier2_subparent/`](../src/tiers/tier2_subparent/) — QA overseer sub-graphs and evaluator
- [`src/tiers/tier3_execution/`](../src/tiers/tier3_execution/) — code execution and automation workers
- [`src/persistence/`](../src/persistence/) — Temporal workflows and Git-based delta tracking
- [`src/integrations/`](../src/integrations/) — Discord and Telegram ingestion adapters
- [`tests/`](../tests/) — API, tier, and persistence test suites
- [`scripts/entrypoint.sh`](../scripts/entrypoint.sh) — container startup script

The container entrypoint creates the configured workspace, checkpoint, and
screenshot directories before starting the API. With no arguments it executes
`uvicorn src.main:app` using `HAPA_API_HOST`, `HAPA_API_PORT`, and
`HAPA_API_LOG_LEVEL`; an explicit command and its arguments are passed through
unchanged.

Phase 2 execution adapters are now implemented. Git worktrees provide
copy-on-write workspace isolation; Docker execution uses scoped mounts,
non-root containers, dropped capabilities, a read-only root filesystem, and
disabled networking by default. Mode A wraps non-interactive Claude Code CLI
execution and exposes structured results, while its security, performance, and
edge-case personas validate structured `ReviewFinding` payloads. Mode B
provides Playwright browser actions/screenshots and deterministic OpenCV
region detection. Focused tests use injected clients for deterministic
coverage; real Docker, Claude Code, and browser smoke tests remain deployment
environment checks.

## Layered system architecture

### 1. API gateway and ingress layer

This layer accepts user traffic from web, chat, and automation channels and normalizes it into a common internal request format.

Expected responsibilities:

- Accept user input through HTTP endpoints and bot adapters
- Validate incoming payloads at the boundary
- Create or schedule tasks
- Expose approval queues for dangerous or irreversible actions
- Stream live execution telemetry back to clients

Key interfaces:

- `POST /api/v1/chat`
- `POST /api/v1/tasks/schedule`
- `GET /api/v1/tasks/active`
- `GET /api/v1/approvals/pending`
- `POST /api/v1/approvals/{task_id}/resolve`
- `GET /api/v1/agents/health`
- `GET /api/v1/observability/stream`

### 2. Tier 1 supervisor

Tier 1 is the main coordinator and chief of staff. It owns global planning and orchestration.

Responsibilities:

- Interpret macro-goals
- Decide whether a request can use a fast path
- Decompose work into tier-appropriate tasks
- Maintain global task state and lineage
- Escalate or pause work when human approval is required
- Route completed work to Tier 2 for validation or directly to the caller when safe

Expected implementation modules:

- [`src/tiers/tier1_supervisor/graph.py`](../src/tiers/tier1_supervisor/graph.py)
- [`src/tiers/tier1_supervisor/router.py`](../src/tiers/tier1_supervisor/router.py)
- [`src/tiers/tier1_supervisor/state.py`](../src/tiers/tier1_supervisor/state.py)

### 3. Tier 2 sub-parent / QA overseer

Tier 2 acts as a middle manager that validates delegated work and coordinates specialist review.

Responsibilities:

- Receive hand-offs from Tier 1
- Provision the correct Tier 3 execution mode
- Watch execution streams and collect artifacts
- Evaluate outputs against success criteria
- Trigger self-correction when the result is not yet acceptable
- Merge or accept verified work only after it passes quality gates

Expected implementation modules:

- [`src/tiers/tier2_subparent/subgraphs.py`](../src/tiers/tier2_subparent/subgraphs.py)
- [`src/tiers/tier2_subparent/evaluator.py`](../src/tiers/tier2_subparent/evaluator.py)

### 4. Tier 3 execution

Tier 3 performs the actual work. It is split into two execution modes.

#### Mode A: software engineering execution

This mode handles code generation, bug fixing, refactoring, and script creation.

Expected modules:

- [`src/tiers/tier3_execution/mode_a_code/runner.py`](../src/tiers/tier3_execution/mode_a_code/runner.py)
- [`src/tiers/tier3_execution/mode_a_code/multi_persona/security_auditor.py`](../src/tiers/tier3_execution/mode_a_code/multi_persona/security_auditor.py)
- [`src/tiers/tier3_execution/mode_a_code/multi_persona/performance_optimizer.py`](../src/tiers/tier3_execution/mode_a_code/multi_persona/performance_optimizer.py)
- [`src/tiers/tier3_execution/mode_a_code/multi_persona/edge_case_tester.py`](../src/tiers/tier3_execution/mode_a_code/multi_persona/edge_case_tester.py)

#### Mode B: general and visual automation

This mode handles non-code automation, containerized workflows, and browser-based or GUI-driven interaction.

Expected modules:

- [`src/tiers/tier3_execution/mode_b_docker/container_mgr.py`](../src/tiers/tier3_execution/mode_b_docker/container_mgr.py)
- [`src/tiers/tier3_execution/mode_b_docker/workspace.py`](../src/tiers/tier3_execution/mode_b_docker/workspace.py)
- [`src/tiers/tier3_execution/mode_b_docker/visual/browser.py`](../src/tiers/tier3_execution/mode_b_docker/visual/browser.py)
- [`src/tiers/tier3_execution/mode_b_docker/visual/vision.py`](../src/tiers/tier3_execution/mode_b_docker/visual/vision.py)

## Persistence and recovery

Persistence is designed to make long-running agent work resilient to process crashes or restarts.

Primary responsibilities:

- Snapshot workspace changes on a short cadence
- Record Git deltas and diffs
- Support replay and recovery after interruption
- Preserve lineage between task hand-offs and generated artifacts

Expected implementation modules:

- [`src/persistence/temporal_workflows/snapshot_wf.py`](../src/persistence/temporal_workflows/snapshot_wf.py)
- [`src/persistence/git_handler.py`](../src/persistence/git_handler.py)

## Data and schema model

The current source-of-truth wire model lives in [`src/core/schemas.py`](../src/core/schemas.py).

### Core schema concepts

- **Tier** — identifies which operational layer owns or consumes a payload
- **TaskLifecycle** — life-cycle states such as pending, running, blocked, success, failed, and cancelled
- **TaskMetadata** — descriptive task identity, labels, deadlines, and creation timestamps
- **ExecutionLineage** — correlation, parent/root task IDs, hop count, and delegation provenance
- **TaskStatus** — current state plus retry and failure metadata
- **WorkspaceFileDelta** — a validated file-level change with diff metadata
- **CodeDiffPayload** — a grouped set of file deltas and unified diff metadata
- **ExecutionSummary** — concise human-readable execution outcome
- **TestCaseResult** and **TestReport** — structured validation results including multi-persona review findings
- **TaskHandOff** — the top-level cross-tier message envelope

### Schema enforcement rules

The schema layer is intentionally strict:

- extra fields are forbidden
- assignments are validated
- enumerations are explicit
- lineage and tier transitions are constrained
- diffs must include the expected fields for their diff type
- failed tasks must include a failure reason
- test reports cannot claim a passed outcome while also containing failed tests

These constraints are already covered by [`tests/test_core/test_schemas.py`](../tests/test_core/test_schemas.py).

## Data flow

### Task intake flow

1. A user sends a request through chat, web, or a bot integration.
2. The API layer normalizes the request into a task record.
3. Tier 1 evaluates the request and decides whether to:
   - execute it directly through a fast path,
   - delegate it to Tier 2 for orchestration, or
   - request human approval first.
4. Tier 2 selects the appropriate Tier 3 worker and defines success criteria.
5. Tier 3 performs the work inside an isolated workspace or container.
6. Tier 2 validates the generated artifact set.
7. Tier 1 publishes the final outcome, summary, or follow-up action.

### Validation and feedback flow

1. Tier 3 produces a `CodeDiffPayload`, `TestReport`, or `ExecutionSummary`.
2. Multi-perspective reviewers emit `ReviewFinding` objects.
3. Tier 2 checks whether the findings are blocking or whether a retry is needed.
4. If the result is acceptable, the merged output is surfaced upward.
5. If not, the task is corrected or escalated.

### Persistence flow

1. Tier 3 workspace changes are observed continuously.
2. Git-based diffs are captured and stored.
3. Temporal workflows manage the checkpoint cadence and long-running orchestration.
4. On recovery, the latest safe snapshot is restored before execution continues.

## Security guardrails

HAPA’s security posture relies on both architectural boundaries and runtime controls.

### Execution isolation

- Tier 3 workers operate only inside isolated workspaces or containers.
- Copy-on-write prevents speculative edits from affecting the parent workspace before approval.
- Containerized workers should run with the minimum privileges necessary.

### Approval gates

- Irreversible or externally visible operations must pause at human approval gates.
- Approval state should be explicit and queryable through the API.

### Tooling boundaries

- Tier 1 and Tier 2 must not directly perform raw execution work.
- Specialized execution modes should expose only the tools required for the task.
- Visual interaction tooling must remain scoped to the current task and workspace.

### Schema safety

- Strict Pydantic models prevent malformed hand-offs from crossing tiers.
- Lineage fields preserve traceability.
- Validation rules stop invalid state transitions before they propagate.

### Observability without privilege leakage

- Telemetry streams should expose enough detail for debugging without revealing secrets.
- Logs, stdout, and frame streams should respect the active task boundary and approval state.
