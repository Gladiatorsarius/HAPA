# Graph Report - HAPA  (2026-10-27)

## Corpus Check
- Corpus is ~17,018 words - fits in a single context window. You may not need a graph.

## Summary
- 874 nodes · 1922 edges · 51 communities (28 shown, 23 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 207 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Commit Datetime Difflib
- Cv2 Dataclasses Testclient
- Dotenv Functools Operator
- Schemas 1 168
- Fastapi Queue App
- Settings Api Host
- Isolatedworkspace Cleanup Enter
- Base64 Abc Responses
- Croniter Validator
- Api Browser Browserautomation
- Docker Errors Mgr
- Sqlite3 Store Apistore
- 22 Tasklifecycle Graph
- Authorization Urls Integrations
- Layer Supervisor Overseer
- Basemodel Pydantic 61
- Graph Plan 81
- Graph Init 1
- Executionlineage Provenancemetadata 115
- Patch Claudecoderunner Command
- Asyncio Taskrequest Taskresponse
- Enum Intenum 14
- Compose Host Port
- Policy Valueerror 1
- Models Chatacknowledgement Chatmessagerequest
- Completedprocess Entrypointcontracttests Passthrough
- Approvaldecision Approvals Approve
- Wf Task Defn
- Usage Configuration Hapa
- 11
- Executionsummary 103 State
- Standards Out Guidelines
- Entrypoint Entry
- Hapa

## God Nodes (most connected - your core abstractions)
1. `create_initial_state()` - 43 edges
2. `SchemaModel` - 35 edges
3. `GlobalSupervisorState` - 32 edges
4. `GitWorkspaceHandler` - 31 edges
5. `ApiStore` - 27 edges
6. `Tier` - 27 edges
7. `TaskLifecycle` - 26 edges
8. `build_supervisor_graph()` - 22 edges
9. `ClaudeCodeRunner` - 18 edges
10. `TestReport` - 17 edges

## Surprising Connections (you probably didn't know these)
- `FoundationTests` --uses--> `ApiStore`  [INFERRED]
  tests/test_api/test_foundation.py → src/api/store.py
- `SchedulingTests` --uses--> `ApiStore`  [INFERRED]
  tests/test_api/test_scheduling.py → src/api/store.py
- `make_handoff()` --uses--> `Tier`  [INFERRED]
  tests/test_core/test_schemas.py → src/core/schemas.py
- `Phase3IntegrationTests` --uses--> `Tier`  [INFERRED]
  tests/test_tiers/test_phase3_integration.py → src/core/schemas.py
- `SupervisorGraphTests` --uses--> `Tier`  [INFERRED]
  tests/test_tiers/test_supervisor_graph.py → src/core/schemas.py

## Import Cycles
- None detected.

## Communities (51 total, 23 thin omitted)

### Community 0 - "Commit Datetime Difflib"
Cohesion: 0.05
Nodes (19): validate_code_diff(), validate_test_report(), CodeDiffPayload, DiffKind, TestOutcome, TestReport, WorkspaceFileDelta, GitHandlerError (+11 more)

### Community 1 - "Cv2 Dataclasses Testclient"
Cohesion: 0.05
Nodes (11): capture_snapshot(), _checkpoint_path(), SnapshotRecord, SnapshotStatus, SnapshotWorkflow, _write_checkpoint(), ImageDetection, VisionParser (+3 more)

### Community 2 - "Dotenv Functools Operator"
Cohesion: 0.09
Nodes (17): AnthropicProvider, _build_provider(), _complete_response(), create_configured_provider(), create_provider(), _default_transport(), GeminiProvider, LLMMessage (+9 more)

### Community 3 - "Schemas 1 168"
Cohesion: 0.09
Nodes (12): ReviewFinding, ReviewPersona, TestCaseResult, PersonaReviewer, PersonaReviewError, Runner, EdgeCaseTester, PerformanceOptimizer (+4 more)

### Community 4 - "Fastapi Queue App"
Cohesion: 0.07
Nodes (10): create_app(), live(), ready(), telemetry(), TelemetryBus, AppSettings, _default_settings_path(), load_settings() (+2 more)

### Community 5 - "Settings Api Host"
Cohesion: 0.06
Nodes (35): api, host, log_level, port, public_base_url, auth, audience, issuer_url (+27 more)

### Community 6 - "Isolatedworkspace Cleanup Enter"
Cohesion: 0.11
Nodes (5): IsolatedWorkspace, WorkspaceIsolationError, WorkspaceManager, Phase2IntegrationTests, WorkspaceManagerTests

### Community 7 - "Base64 Abc Responses"
Cohesion: 0.13
Nodes (8): decode_jwt(), _decode_part(), require_scopes(), dependency(), events(), stream(), AuthSettings, FoundationTests

### Community 8 - "Croniter Validator"
Cohesion: 0.15
Nodes (10): ScheduleRequest, ScheduleResponse, cancel_schedule(), create_schedule(), list_schedules(), pause_schedule(), resume_schedule(), _set_state() (+2 more)

### Community 9 - "Api Browser Browserautomation"
Cohesion: 0.13
Nodes (3): BrowserAutomation, BrowserAutomationError, BrowserAutomationTests

### Community 10 - "Docker Errors Mgr"
Cohesion: 0.10
Nodes (5): ContainerExecutionError, ContainerManager, ContainerResult, DockerContainer, ContainerManagerTests

### Community 12 - "22 Tasklifecycle Graph"
Cohesion: 0.17
Nodes (12): TaskLifecycle, _approval(), _route(), _tier2(), _tier3(), begin_iteration(), begin_retry(), TransitionLimitError (+4 more)

### Community 13 - "Authorization Urls Integrations"
Cohesion: 0.08
Nodes (26): Authentication and authorization, Base URLs, Client integrations, Common conventions, GET /api/v1/approvals, GET /api/v1/tasks, GET /api/v1/tasks/{taskid}, GET /api/v1/tasks/{taskid}/events (+18 more)

### Community 14 - "Layer Supervisor Overseer"
Cohesion: 0.08
Nodes (25): 1. API gateway and ingress layer, 2. Tier 1 supervisor, 3. Tier 2 sub-parent / QA overseer, 4. Tier 3 execution, Approval gates, Architectural goals, Core schema concepts, Data and schema model (+17 more)

### Community 15 - "Basemodel Pydantic 61"
Cohesion: 0.11
Nodes (8): SchemaModel, ApiSettings, BrowserSettings, DockerSettings, LLMSettings, StorageSettings, TelemetrySettings, TemporalSettings

### Community 16 - "Graph Plan 81"
Cohesion: 0.15
Nodes (6): build_supervisor_graph(), plan(), create_initial_state(), Phase3IntegrationTests, SupervisorGraphTests, SupervisorStateTests

### Community 17 - "Graph Init 1"
Cohesion: 0.17
Nodes (7): build_tier2_graph(), _coordinate(), Tier2Action, Tier2BoundaryError, Tier2GraphState, validate_tier2_action(), Tier2SubgraphTests

### Community 18 - "Executionlineage Provenancemetadata 115"
Cohesion: 0.16
Nodes (7): ExecutionLineage, ProvenanceMetadata, TaskHandOff, TaskMetadata, TaskStatus, make_handoff(), SchemaTests

### Community 19 - "Patch Claudecoderunner Command"
Cohesion: 0.17
Nodes (3): ClaudeCodeRunner, CodeRunnerError, ClaudeCodeRunnerTests

### Community 20 - "Asyncio Taskrequest Taskresponse"
Cohesion: 0.30
Nodes (11): TaskRequest, TaskResponse, cancel_task(), _create(), create_task(), _deliver_callback(), _execute_state(), get_task() (+3 more)

### Community 21 - "Enum Intenum 14"
Cohesion: 0.19
Nodes (6): Tier, _route_key(), route_task(), RouteDecision, RouteTarget, RouterTests

### Community 22 - "Compose Host Port"
Cohesion: 0.12
Nodes (16): HAPA_API_HOST, HAPA_API_PORT, HAPA_WORKSPACE_ROOT, build, environment, healthcheck, ports, volumes (+8 more)

### Community 23 - "Policy Valueerror 1"
Cohesion: 0.23
Nodes (4): select_tier3_model(), Tier3ModelDecision, Tier3ModelSelectionError, ModelPolicyTests

### Community 24 - "Models Chatacknowledgement Chatmessagerequest"
Cohesion: 0.27
Nodes (4): ChatAcknowledgement, ChatMessageRequest, TelemetryEvent, message()

### Community 26 - "Approvaldecision Approvals Approve"
Cohesion: 0.47
Nodes (5): ApprovalDecision, approve(), _decide(), list_approvals(), reject()

### Community 28 - "Usage Configuration Hapa"
Cohesion: 0.22
Nodes (9): API usage, Configuration, HAPA, Cross-phase quality gates, HAPA Implementation TODO, Phase 1: Core runtime, data validation, and persistence foundation, Phase 2: Sandboxing and execution subsystem, Phase 3: Orchestration, quality oversight, and routing (+1 more)

### Community 29 - "11"
Cohesion: 0.25
Nodes (8): 0.1.1 (2026-10-11), 0.2.0 (2026-10-11), 0.3.0 (2026-10-11), 0.4.0 (2026-10-11), 0.5.0 (2026-10-11), 0.6.0 (2026-10-11), Feat, Refactor

### Community 32 - "Standards Out Guidelines"
Cohesion: 0.67
Nodes (3): 1. Test-Driven Development & Testing Standards, 2. Output & File Management (graphify-out), Agent Instructions & Guidelines

## Knowledge Gaps
- **15 isolated node(s):** `hapa`, `Agent Instructions & Guidelines`, `2. Output & File Management (graphify-out)`, `0.6.0 (2026-10-11)`, `0.5.0 (2026-10-11)` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 312 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SchemaModel` connect `Basemodel Pydantic 61` to `Commit Datetime Difflib`, `Cv2 Dataclasses Testclient`, `Schemas 1 168`, `Fastapi Queue App`, `Base64 Abc Responses`, `Croniter Validator`, `Executionlineage Provenancemetadata 115`, `Asyncio Taskrequest Taskresponse`, `Models Chatacknowledgement Chatmessagerequest`, `Approvaldecision Approvals Approve`, `Executionsummary 103 State`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `GlobalSupervisorState` (e.g. with `_approval()` and `build_supervisor_graph()`) actually correct?**
  _`GlobalSupervisorState` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `hapa`, `Agent Instructions & Guidelines`, `2. Output & File Management (graphify-out)` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Commit Datetime Difflib` be split into smaller, more focused modules?**
  _Cohesion score 0.05253077975376197 - nodes in this community are weakly interconnected._
- **Why does `create_initial_state()` connect `Graph Plan 81` to `Commit Datetime Difflib`, `Dotenv Functools Operator`, `Base64 Abc Responses`, `Sqlite3 Store Apistore`, `22 Tasklifecycle Graph`, `Graph Init 1`, `Executionlineage Provenancemetadata 115`, `Asyncio Taskrequest Taskresponse`, `Enum Intenum 14`, `Policy Valueerror 1`, `Executionsummary 103 State`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `GitWorkspaceHandler` (e.g. with `CodeDiffPayload` and `DiffKind`) actually correct?**
  _`GitWorkspaceHandler` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Cv2 Dataclasses Testclient` be split into smaller, more focused modules?**
  _Cohesion score 0.054244306418219465 - nodes in this community are weakly interconnected._