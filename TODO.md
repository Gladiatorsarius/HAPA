# HAPA Implementation TODO

This checklist is ordered by implementation phase and prioritized so the foundation is in place before orchestration and ingress layers are built.

## Phase 1: Core runtime, data validation, and persistence foundation

**Goal:** establish the shared data model, runtime baseline, and recovery primitives.

- [x] Define strict cross-tier schemas in [`src/core/schemas.py`](src/core/schemas.py)
- [x] Add schema validation tests in [`tests/test_core/test_schemas.py`](tests/test_core/test_schemas.py)
- [x] Normalize the project runtime to Python 3.14+ in [`pyproject.toml`](pyproject.toml)
- [x] Add package metadata and dependency pins for:
  - [x] Pydantic v2
  - [x] FastAPI
  - [x] Uvicorn
  - [x] LangGraph
  - [x] Temporal Python SDK
  - [x] GitPython
  - [x] Docker SDK for Python
  - [x] Playwright
  - [x] OpenCV
- [x] Create a shared application settings layer in [`config/settings.yaml`](config/settings.yaml) and a matching loader in `src/core/`
- [x] Implement [`src/persistence/git_handler.py`](src/persistence/git_handler.py) for workspace diff capture
- [x] Implement [`src/persistence/temporal_workflows/snapshot_wf.py`](src/persistence/temporal_workflows/snapshot_wf.py) for periodic checkpointing
- [x] Add persistence tests under [`tests/test_persistence/`](tests/test_persistence/)
- [x] Define the startup contract in [`scripts/entrypoint.sh`](scripts/entrypoint.sh)

## Phase 2: Sandboxing and execution subsystem

**Goal:** isolate task execution and create specialized worker backends.

- [x] Implement workspace isolation in [`src/tiers/tier3_execution/mode_b_docker/workspace.py`](src/tiers/tier3_execution/mode_b_docker/workspace.py)
- [x] Add copy-on-write support using Git worktrees or container volume overlays
- [x] Implement container lifecycle management in [`src/tiers/tier3_execution/mode_b_docker/container_mgr.py`](src/tiers/tier3_execution/mode_b_docker/container_mgr.py)
- [x] Enforce least-privilege container settings and scoped write volumes
- [x] Implement Claude Code CLI execution wrappers in [`src/tiers/tier3_execution/mode_a_code/runner.py`](src/tiers/tier3_execution/mode_a_code/runner.py)
- [x] Add multi-persona review agents:
  - [x] [`src/tiers/tier3_execution/mode_a_code/multi_persona/security_auditor.py`](src/tiers/tier3_execution/mode_a_code/multi_persona/security_auditor.py)
  - [x] [`src/tiers/tier3_execution/mode_a_code/multi_persona/performance_optimizer.py`](src/tiers/tier3_execution/mode_a_code/multi_persona/performance_optimizer.py)
  - [x] [`src/tiers/tier3_execution/mode_a_code/multi_persona/edge_case_tester.py`](src/tiers/tier3_execution/mode_a_code/multi_persona/edge_case_tester.py)
- [x] Implement Playwright automation bindings in [`src/tiers/tier3_execution/mode_b_docker/visual/browser.py`](src/tiers/tier3_execution/mode_b_docker/visual/browser.py)
- [x] Implement OpenCV-based visual parsing in [`src/tiers/tier3_execution/mode_b_docker/visual/vision.py`](src/tiers/tier3_execution/mode_b_docker/visual/vision.py)
- [x] Add execution-mode tests under [`tests/test_tiers/`](tests/test_tiers/)

## Phase 3: Orchestration, quality oversight, and routing

**Goal:** build the hierarchical agent flow and quality gates.

- [x] Implement the Tier 1 supervisor graph in [`src/tiers/tier1_supervisor/graph.py`](src/tiers/tier1_supervisor/graph.py)
- [x] Define global supervisor state in [`src/tiers/tier1_supervisor/state.py`](src/tiers/tier1_supervisor/state.py)
- [x] Implement fast-path routing logic in [`src/tiers/tier1_supervisor/router.py`](src/tiers/tier1_supervisor/router.py)
- [x] Implement Tier 2 sub-graphs in [`src/tiers/tier2_subparent/subgraphs.py`](src/tiers/tier2_subparent/subgraphs.py)
- [x] Implement Tier 2 success criteria and self-correction in [`src/tiers/tier2_subparent/evaluator.py`](src/tiers/tier2_subparent/evaluator.py)
- [x] Add retry and iteration safeguards to all tier transitions
- [x] Ensure Tier 2 never performs raw execution, terminal work, or browser interaction directly
- [x] Add orchestration tests for:
  - [x] hand-off validation
  - [x] tier routing
  - [x] fast-path bypasses
  - [x] approval escalation

## Phase 4: API gateway, ingestion, and observability

**Goal:** expose the external interface and real-time telemetry surface.

- [x] Create the FastAPI app factory in [`src/api/app.py`](src/api/app.py)
- [x] Add the main Uvicorn entrypoint in [`src/main.py`](src/main.py)
- [x] Implement chat ingress in [`src/api/routes/chat.py`](src/api/routes/chat.py)
- [x] Implement task scheduling and active-task endpoints in [`src/api/routes/tasks.py`](src/api/routes/tasks.py)
- [x] Implement human approval endpoints in [`src/api/routes/approvals.py`](src/api/routes/approvals.py)
- [x] Implement observability streaming in [`src/api/routes/observability.py`](src/api/routes/observability.py)
- [x] Implement health and telemetry endpoints in [`src/api/routes/health.py`](src/api/routes/health.py)
- [x] Implement the websocket telemetry bus in [`src/api/websocket.py`](src/api/websocket.py)
- [x] Add Discord ingress in [`src/integrations/discord_bot.py`](src/integrations/discord_bot.py)
- [x] Add Telegram ingress in [`src/integrations/telegram_bot.py`](src/integrations/telegram_bot.py)
- [x] Add API contract tests under [`tests/test_api/`](tests/test_api/)
- [x] Verify the container startup path in [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml)

## Cross-phase quality gates

- [ ] Keep all cross-tier payloads validated by Pydantic models
- [ ] Ensure every task carries lineage and provenance metadata
- [ ] Protect irreversible actions with explicit human approval
- [ ] Keep generated diffs and test reports structured and machine-readable
- [ ] Expand the test suite whenever a new tier, route, or persistence behavior is added
- [ ] Update [`README.md`](README.md) once the public runtime surface stabilizes
