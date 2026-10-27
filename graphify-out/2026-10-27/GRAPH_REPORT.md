# Graph Report - HAPA  (2026-10-27)

## Corpus Check
- 92 files · ~16,981 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .lock 1)

## Summary
- 826 nodes · 1857 edges · 57 communities (22 shown, 35 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 206 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e66943e2`
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
- TaskLifecycle
- evaluator.py
- Browser Automation
- subgraphs.py
- unittest
- create_initial_state
- _base.py
- _base.py
- Container Deployment
- settings.py
- Task Routing
- Workspace Manager
- AppSettings
- app.py
- Architecture Principles
- Entrypoint Tests
- TelemetryBus
- health.py
- RouteTests
- LLMSettings
- Quality Assurance
- Entrypoint Script
- HAPA Document

## God Nodes (most connected - your core abstractions)
1. `create_initial_state()` - 43 edges
2. `SchemaModel` - 35 edges
3. `GitWorkspaceHandler` - 31 edges
4. `GlobalSupervisorState` - 31 edges
5. `Tier` - 27 edges
6. `ApiStore` - 27 edges
7. `TaskLifecycle` - 22 edges
8. `build_supervisor_graph()` - 22 edges
9. `ClaudeCodeRunner` - 18 edges
10. `TestReport` - 17 edges

## Surprising Connections (you probably didn't know these)
- `make_handoff()` --uses--> `Tier`  [INFERRED]
  tests/test_core/test_schemas.py → src/core/schemas.py
- `RouterTests` --uses--> `Tier`  [INFERRED]
  tests/test_tiers/test_router.py → src/core/schemas.py
- `Tier2SubgraphTests` --uses--> `Tier`  [INFERRED]
  tests/test_tiers/test_tier2_subgraphs.py → src/core/schemas.py
- `SchemaTests` --uses--> `TaskLifecycle`  [INFERRED]
  tests/test_core/test_schemas.py → src/core/schemas.py
- `Tier2EvaluatorTests` --uses--> `TaskLifecycle`  [INFERRED]
  tests/test_tiers/test_tier2_evaluator.py → src/core/schemas.py

## Import Cycles
- None detected.

## Communities (57 total, 35 thin omitted)

### Community 0 - "Core API Dependencies"
Cohesion: 0.07
Nodes (27): decode_jwt(), _decode_part(), require_scopes(), dependency(), ApprovalDecision, ChatAcknowledgement, ChatMessageRequest, TaskRequest (+19 more)

### Community 1 - "LLM Provider Integrations"
Cohesion: 0.09
Nodes (16): AnthropicProvider, _build_provider(), create_configured_provider(), create_provider(), _default_transport(), GeminiProvider, LLMMessage, LLMProvider (+8 more)

### Community 2 - "Git Workspace Diffs"
Cohesion: 0.08
Nodes (9): validate_code_diff(), validate_test_report(), CodeDiffPayload, WorkspaceFileDelta, GitHandlerError, GitWorkspaceHandler, InvalidWorkspaceError, QualityGateTests (+1 more)

### Community 4 - "Application Settings"
Cohesion: 0.06
Nodes (35): api, host, log_level, port, public_base_url, auth, audience, issuer_url (+27 more)

### Community 5 - "Schedule Validation"
Cohesion: 0.11
Nodes (10): ScheduleRequest, ScheduleResponse, cancel_schedule(), create_schedule(), list_schedules(), pause_schedule(), resume_schedule(), _set_state() (+2 more)

### Community 6 - "Docker Execution"
Cohesion: 0.10
Nodes (5): ContainerExecutionError, ContainerManager, ContainerResult, DockerContainer, ContainerManagerTests

### Community 8 - "schemas.py"
Cohesion: 0.11
Nodes (11): TelemetryEvent, ExecutionLineage, ProvenanceMetadata, ReviewFinding, SchemaModel, TaskMetadata, TaskStatus, TestCaseResult (+3 more)

### Community 9 - "TaskLifecycle"
Cohesion: 0.21
Nodes (6): DiffKind, TaskLifecycle, begin_iteration(), begin_retry(), TransitionLimitError, SafeguardTests

### Community 10 - "evaluator.py"
Cohesion: 0.24
Nodes (7): TestOutcome, apply_evaluation(), evaluate_report(), EvaluationDecision, EvaluationResult, report(), Tier2EvaluatorTests

### Community 11 - "Browser Automation"
Cohesion: 0.07
Nodes (7): BrowserAutomation, BrowserAutomationError, ImageDetection, VisionParser, VisionParserError, BrowserAutomationTests, VisionParserTests

### Community 12 - "subgraphs.py"
Cohesion: 0.10
Nodes (12): apply_tier3_model(), select_tier3_model(), Tier3ModelDecision, Tier3ModelSelectionError, build_tier2_graph(), _coordinate(), Tier2Action, Tier2BoundaryError (+4 more)

### Community 13 - "unittest"
Cohesion: 0.08
Nodes (8): NoWorkspaceChangesError, capture_snapshot(), _checkpoint_path(), SnapshotRecord, SnapshotStatus, SnapshotWorkflow, _write_checkpoint(), SnapshotWorkflowActivityTests

### Community 14 - "create_initial_state"
Cohesion: 0.10
Nodes (17): ExecutionSummary, TaskHandOff, Tier, _approval(), build_supervisor_graph(), plan(), _route(), _route_key() (+9 more)

### Community 15 - "_base.py"
Cohesion: 0.29
Nodes (5): ReviewPersona, PersonaReviewer, EdgeCaseTester, PerformanceOptimizer, SecurityAuditor

### Community 16 - "_base.py"
Cohesion: 0.07
Nodes (8): PersonaReviewError, Runner, ClaudeCodeRunner, CodeRunnerError, CodeRunResult, FakeRunner, PersonaTests, ClaudeCodeRunnerTests

### Community 17 - "Container Deployment"
Cohesion: 0.12
Nodes (16): HAPA_API_HOST, HAPA_API_PORT, HAPA_WORKSPACE_ROOT, build, environment, healthcheck, ports, volumes (+8 more)

### Community 18 - "settings.py"
Cohesion: 0.13
Nodes (6): ApiSettings, BrowserSettings, DockerSettings, StorageSettings, TelemetrySettings, TemporalSettings

### Community 20 - "Task Routing"
Cohesion: 0.22
Nodes (4): route_task(), RouteDecision, RouteTarget, RouterTests

### Community 21 - "Workspace Manager"
Cohesion: 0.11
Nodes (5): IsolatedWorkspace, WorkspaceIsolationError, WorkspaceManager, Phase2IntegrationTests, WorkspaceManagerTests

### Community 23 - "AppSettings"
Cohesion: 0.21
Nodes (4): AppSettings, _default_settings_path(), load_settings(), SettingsTests

### Community 27 - "Architecture Principles"
Cohesion: 0.15
Nodes (11): Snapshot Workflow, Authentication and Authorization, SSE and WebSocket Telemetry, Task Lifecycle, Fast-path Routing, Workspace Isolation, FastAPI Gateway, HAPA (+3 more)

### Community 32 - "health.py"
Cohesion: 0.53
Nodes (3): live(), ready(), telemetry()

## Knowledge Gaps
- **8 isolated node(s):** `hapa`, `Snapshot Workflow`, `Authentication and Authorization`, `SSE and WebSocket Telemetry`, `Task Lifecycle` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 312 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SchemaModel` connect `schemas.py` to `Core API Dependencies`, `Git Workspace Diffs`, `LLMSettings`, `Schedule Validation`, `unittest`, `create_initial_state`, `settings.py`, `AppSettings`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `GitWorkspaceHandler` (e.g. with `CodeDiffPayload` and `DiffKind`) actually correct?**
  _`GitWorkspaceHandler` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `hapa`, `Snapshot Workflow`, `Authentication and Authorization` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core API Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.07322068612391193 - nodes in this community are weakly interconnected._
- **Why does `create_initial_state()` connect `create_initial_state` to `Core API Dependencies`, `LLM Provider Integrations`, `SQLite API Store`, `schemas.py`, `TaskLifecycle`, `evaluator.py`, `subgraphs.py`, `Task Routing`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `GlobalSupervisorState` (e.g. with `_approval()` and `build_supervisor_graph()`) actually correct?**
  _`GlobalSupervisorState` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `LLM Provider Integrations` be split into smaller, more focused modules?**
  _Cohesion score 0.08831168831168831 - nodes in this community are weakly interconnected._