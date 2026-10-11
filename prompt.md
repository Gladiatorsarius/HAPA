You are an expert software architect and technical writer. Your task is to review the complete system design, directory layout, implementation phases, and technology stack for the **Hierarchical Autonomous Personal Assistant (HAPA)** framework provided below, and then generate:
1. **Comprehensive Technical Documentation** outlining the architecture, sub-systems, data flows, and security guardrails.
2. **A Prioritized, Actionable TODO List** broken down by implementation phases to guide the development and coding of the project.

---

### 1. Project Context & Objectives
HAPA is a framework-agnostic, multi-tier agent architecture designed to function as an autonomous chief of staff, handling software engineering, web automation, communications, and file operations without manual micro-step intervention[cite: 2].

**Core Design Principles:**
* **Pure Delegation:** Oversight layers (parents) only plan, allocate resources, and handle QA; they never perform heavy lifting or raw execution[cite: 2].
* **Dynamic Specialization:** Workers are instantiated on-demand with specialized toolsets tailored to incoming tasks[cite: 2].
* **Workspace Isolation & Copy-on-Write:** Agents operate on isolated folder copies or container volumes, shipping back verified diffs only after parent confirmation[cite: 2, 3].
* **Multi-Perspective Code QA:** Code changes undergo automated expert reviews (Security Auditor, Performance Optimizer, Edge-Case Tester) before surfacing[cite: 2, 3].
* **Fast-Path Routing:** Lightweight, low-risk tasks bypass middle tiers to reduce latency and token costs[cite: 2].
* **Native Visual Perception:** Specialized agents utilize screen capture and vision capabilities to interact with GUIs[cite: 2].

---

### 2. Project Directory Structure (`hapa/`)
When referencing files in your documentation and task lists, use the existing codebase layout:
* `hapa/` root contains environment and configuration files (`.env.example`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `README.md`, `config/settings.yaml`)[cite: 1].
* `src/main.py`: FastAPI application entrypoint & Uvicorn runner[cite: 1].
* `src/api/app.py`: FastAPI application factory[cite: 1, 3].
* `src/routes/`: Contains `chat.py` (POST /api/v1/chat for Web/Discord/Telegram ingress), `tasks.py` (scheduling and active tasks), `approvals.py` (human authorization gates), `observability.py` (WebSocket/SSE telemetry stream), and `health.py` (agent telemetry)[cite: 1, 3].
* `src/websocket.py`: Real-time telemetry bus implementation[cite: 3].
* `src/core/schemas.py`: Pydantic v2 models for structured hand-offs, diffs, and test reports[cite: 1, 3].
* `src/tiers/`:
  * `tier1_supervisor/`: Main Parent (Chief of Staff) containing `graph.py` (LangGraph root graph), `router.py` (fast-path conditional edges), and `state.py` (global state)[cite: 1, 2, 3].
  * `tier2_subparent/`: Sub-Parent QA Overseer containing `subgraphs.py` and `evaluator.py` (success criteria and self-correction)[cite: 1, 2, 3].
  * `tier3_execution/`: Specialized sub-agents split into `mode_a_code/` (Claude Code CLI wrappers & `multi_persona/` QA security/performance/edge-case auditors) and `mode_b_docker/` (Docker container manager, visual Playwright browser, OpenCV vision, and Copy-on-Write workspace isolation)[cite: 1, 2, 3].
* `src/persistence/`: Contains `temporal_workflows/snapshot_wf.py` (continuous 5-second workspace delta checkpointer) and `git_handler.py` (GitPython delta/diff tracking)[cite: 1, 2, 3].
* `src/integrations/`: Contains `discord_bot.py` and `telegram_bot.py`[cite: 2, 3].
* `tests/`: Comprehensive test suite (`test_api/`, `test_tiers/`, `test_persistence/`)[cite: 1].
* `scripts/entrypoint.sh`: Container startup script[cite: 1, 2].

---

### 3. Technology Stack & Framework Mapping
* **Runtime & Language:** Python 3.11+ across all backend orchestration, API gateway, and agent tiers[cite: 3, 4].
* **Data Validation:** Pydantic v2 for strict JSON schemas across structured hand-offs, status codes, and test reports[cite: 3, 4].
* **API Gateway & Ingestion:** FastAPI, Uvicorn, python-telegram-bot, discord.py[cite: 4].
* **Orchestration:** LangGraph and LangChain Core (Root supervisor and sub-graphs)[cite: 4].
* **Tier 3 Execution:** Claude Code CLI (Mode A) and Docker SDK for Python with Playwright & OpenCV (Mode B)[cite: 4].
* **Persistence & Recovery:** Temporal.io (Python SDK) and GitPython for 5-second workspace backups and long-running workflows[cite: 3, 4].

---

### 4. Implementation Phases & Roadmap
Your TODO list must follow these four sequential phases[cite: 3]:
* **Phase 1: Core Runtime, Data Validation, & Persistence Foundation:** Python 3.11+ setup, Pydantic v2 schemas, Temporal.io and GitPython state/snapshot engine[cite: 3].
* **Phase 2: Sandboxing & Execution Subsystem (Tier 3):** Copy-on-Write workspace isolation, Claude Code CLI wrappers, multi-perspective expert testing sub-layer, Docker SDK least-privilege containers, and Playwright/OpenCV visual perception[cite: 3].
* **Phase 3: Orchestration, Quality Oversight, & Routing (Tiers 1 & 2):** LangGraph sub-graphs for Tier 2 Sub-Parents, LangGraph root supervisor for Tier 1 Main Parent, fast-path conditional routing, and retry/iteration safeguards[cite: 3].
* **Phase 4: API Gateway, Ingestion, & Observability Subsystem:** FastAPI/Uvicorn ASGI container, chat endpoints for Web/Discord/Telegram, task schedulers, human-in-the-loop approval queues (`/api/v1/approvals/pending`), and WebSockets/SSE for real-time telemetry streams (`/api/v1/observability/stream`)[cite: 3].

---

### Required Deliverables
1. **Technical Documentation (`docs/architecture.md`):** A thorough explanation of the HAPA architecture, operational tiers, data flow protocols, and security guardrails referencing the specific files and modules listed above.
2. **Prioritized TODO List (`TODO.md`):** A clear, structured, step-by-step implementation checklist organized by Phases 1 through 4, detailing exact file targets and milestones.