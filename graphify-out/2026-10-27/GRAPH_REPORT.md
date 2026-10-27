# Graph Report - HAPA  (2026-10-27)

## Corpus Check
- 92 files · ~16,981 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .lock 1)

## Summary
- 827 nodes · 1864 edges · 50 communities (21 shown, 29 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 209 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f91fdba2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Core API Dependencies
- LLM Provider Integrations
- Git Workspace Diffs
- task_schedule_wf.py
- Application Settings
- Schedule Validation
- Docker Execution
- SQLite API Store
- schemas.py
- state.py
- Visual Detection
- Browser Automation
- Tier Two Coordination
- Orchestration Tests
- Code Runner
- _base.py
- Container Deployment
- build_supervisor_graph
- Task Routing
- Workspace Manager
- app.py
- Model Policy
- Architecture Principles
- Entrypoint Tests
- Quality Assurance
- Entrypoint Script
- HAPA Document

## God Nodes (most connected - your core abstractions)
1. `create_initial_state()` - 43 edges
2. `SchemaModel` - 35 edges
3. `GlobalSupervisorState` - 32 edges
4. `GitWorkspaceHandler` - 31 edges
5. `ApiStore` - 27 edges
6. `Tier` - 27 edges
7. `TaskLifecycle` - 22 edges
8. `build_supervisor_graph()` - 22 edges
9. `ClaudeCodeRunner` - 18 edges
10. `LLMMessage` - 17 edges

## Surprising Connections (you probably didn't know these)
- `SchedulingTests` --uses--> `ApiStore`  [INFERRED]
  tests/test_api/test_scheduling.py → src/api/store.py
- `FoundationTests` --uses--> `AuthSettings`  [INFERRED]
  tests/test_api/test_foundation.py → src/core/settings.py
- `RouteTests` --uses--> `AppSettings`  [INFERRED]
  tests/test_api/test_routes.py → src/core/settings.py
- `SettingsTests` --uses--> `AppSettings`  [INFERRED]
  tests/test_core/test_settings.py → src/core/settings.py
- `SchemaTests` --uses--> `ProvenanceMetadata`  [INFERRED]
  tests/test_core/test_schemas.py → src/core/schemas.py

## Import Cycles
- None detected.

## Communities (50 total, 29 thin omitted)

### Community 0 - "Core API Dependencies"
Cohesion: 0.05
Nodes (36): decode_jwt(), _decode_part(), require_scopes(), dependency(), ApprovalDecision, ChatAcknowledgement, ChatMessageRequest, TaskRequest (+28 more)

### Community 1 - "LLM Provider Integrations"
Cohesion: 0.09
Nodes (14): AppSettings, AnthropicProvider, create_configured_provider(), create_provider(), _default_transport(), GeminiProvider, LLMMessage, LLMProvider (+6 more)

### Community 2 - "Git Workspace Diffs"
Cohesion: 0.06
Nodes (11): GitHandlerError, GitWorkspaceHandler, NoWorkspaceChangesError, capture_snapshot(), _checkpoint_path(), SnapshotRecord, SnapshotStatus, SnapshotWorkflow (+3 more)

### Community 4 - "Application Settings"
Cohesion: 0.06
Nodes (35): api, host, log_level, port, public_base_url, auth, audience, issuer_url (+27 more)

### Community 5 - "Schedule Validation"
Cohesion: 0.13
Nodes (10): ScheduleRequest, ScheduleResponse, cancel_schedule(), create_schedule(), list_schedules(), pause_schedule(), resume_schedule(), _set_state() (+2 more)

### Community 6 - "Docker Execution"
Cohesion: 0.09
Nodes (6): ContainerExecutionError, ContainerManager, ContainerResult, DockerClient, DockerContainer, ContainerManagerTests

### Community 8 - "schemas.py"
Cohesion: 0.05
Nodes (25): validate_code_diff(), validate_test_report(), CodeDiffPayload, DiffKind, ReviewFinding, TaskLifecycle, TaskMetadata, TaskStatus (+17 more)

### Community 9 - "state.py"
Cohesion: 0.18
Nodes (3): ExecutionSummary, TaskHandOff, state_task_id()

### Community 10 - "Visual Detection"
Cohesion: 0.13
Nodes (4): ImageDetection, VisionParser, VisionParserError, VisionParserTests

### Community 11 - "Browser Automation"
Cohesion: 0.13
Nodes (3): BrowserAutomation, BrowserAutomationError, BrowserAutomationTests

### Community 12 - "Tier Two Coordination"
Cohesion: 0.17
Nodes (8): build_tier2_graph(), _coordinate(), _finish(), Tier2Action, Tier2BoundaryError, Tier2GraphState, validate_tier2_action(), Tier2SubgraphTests

### Community 14 - "Orchestration Tests"
Cohesion: 0.18
Nodes (7): Tier, _tier2(), _tier3(), create_initial_state(), record_handoff(), Phase3IntegrationTests, SupervisorStateTests

### Community 15 - "Code Runner"
Cohesion: 0.17
Nodes (3): ClaudeCodeRunner, CodeRunnerError, ClaudeCodeRunnerTests

### Community 16 - "_base.py"
Cohesion: 0.10
Nodes (10): ReviewPersona, PersonaReviewer, PersonaReviewError, Runner, EdgeCaseTester, PerformanceOptimizer, SecurityAuditor, CodeRunResult (+2 more)

### Community 17 - "Container Deployment"
Cohesion: 0.12
Nodes (16): HAPA_API_HOST, HAPA_API_PORT, HAPA_WORKSPACE_ROOT, build, environment, healthcheck, ports, volumes (+8 more)

### Community 18 - "build_supervisor_graph"
Cohesion: 0.24
Nodes (4): build_supervisor_graph(), plan(), FakeProvider, SupervisorGraphTests

### Community 20 - "Task Routing"
Cohesion: 0.18
Nodes (9): _approval(), _plan_with_provider(), _route(), _route_key(), route_task(), RouteDecision, RouteTarget, GlobalSupervisorState (+1 more)

### Community 21 - "Workspace Manager"
Cohesion: 0.11
Nodes (5): IsolatedWorkspace, WorkspaceIsolationError, WorkspaceManager, Phase2IntegrationTests, WorkspaceManagerTests

### Community 23 - "app.py"
Cohesion: 0.05
Nodes (11): create_app(), live(), ready(), telemetry(), events(), stream(), TelemetryBus, _default_settings_path() (+3 more)

### Community 24 - "Model Policy"
Cohesion: 0.22
Nodes (5): apply_tier3_model(), select_tier3_model(), Tier3ModelDecision, Tier3ModelSelectionError, ModelPolicyTests

### Community 27 - "Architecture Principles"
Cohesion: 0.15
Nodes (11): Snapshot Workflow, Authentication and Authorization, SSE and WebSocket Telemetry, Task Lifecycle, Fast-path Routing, Workspace Isolation, FastAPI Gateway, HAPA (+3 more)

## Knowledge Gaps
- **8 isolated node(s):** `hapa`, `Snapshot Workflow`, `Authentication and Authorization`, `SSE and WebSocket Telemetry`, `Task Lifecycle` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 310 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SchemaModel` connect `Core API Dependencies` to `LLM Provider Integrations`, `Git Workspace Diffs`, `Schedule Validation`, `schemas.py`, `state.py`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `GlobalSupervisorState` (e.g. with `_approval()` and `build_supervisor_graph()`) actually correct?**
  _`GlobalSupervisorState` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `hapa`, `Snapshot Workflow`, `Authentication and Authorization` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core API Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.0531883632089333 - nodes in this community are weakly interconnected._
- **Why does `create_initial_state()` connect `Orchestration Tests` to `Core API Dependencies`, `SQLite API Store`, `schemas.py`, `state.py`, `Tier Two Coordination`, `build_supervisor_graph`, `Task Routing`, `Model Policy`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `GitWorkspaceHandler` (e.g. with `CodeDiffPayload` and `DiffKind`) actually correct?**
  _`GitWorkspaceHandler` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `LLM Provider Integrations` be split into smaller, more focused modules?**
  _Cohesion score 0.09216255442670537 - nodes in this community are weakly interconnected._