# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (uv-based Python)

```bash
cd backend

# Develop
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8888

# Lint & format
uv run ruff check app/
uv run ruff format app/

# Test (88 test cases)
uv run pytest
uv run pytest tests/test_models.py -k "test_create_user"  # single test

# Install deps
uv sync --group dev

# Database migration
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

### Frontend (bun-based)

```bash
cd frontend

# Develop (port 3000, proxy /api -> :8888)
bun run dev

# Build & preview
bun run build
bun run preview

# Test
bun run test              # vitest run
bun run test:watch        # vitest watch

# Lint (if configured)
bun run lint
```

### Full stack (Docker)

```bash
docker compose up -d    # PG + Redis + MinIO
```

## Architecture Overview

### Full-stack layout

```
visagent/
├── docker-compose.yml   # PG (pgvector), Redis, MinIO
├── backend/
│   ├── main.py          # FastAPI app entry, lifespan, router registration
│   ├── app/
│   │   ├── api/         # 8 route modules (46 endpoints)
│   │   │   ├── auth.py       # register / login / me / logout
│   │   │   ├── chat.py       # sessions CRUD, SSE-streamed messages
│   │   │   ├── detection.py  # single / batch / folder / video / scenes
│   │   │   ├── training.py   # tasks lifecycle, dataset convert, model upload/validate
│   │   │   ├── dashboard.py  # ECharts data endpoints
│   │   │   ├── camera.py     # camera scene management
│   │   │   ├── knowledge.py  # upload / search / delete docs
│   │   │   └── health.py     # service health checks
│   │   ├── config/           # pydantic-settings (Settings singleton)
│   │   ├── core/             # security (JWT/bcrypt), logger, exceptions, rate_limit
│   │   ├── database/         # session (SQLAlchemy engine), seed data
│   │   ├── entity/           # ORM models (14 tables), Pydantic schemas (5 files)
│   │   ├── middleware/       # request logging middleware
│   │   ├── services/         # Business logic layer (9 modules)
│   │   └── storage/          # MinIO client, Redis client
│   ├── alembic/              # DB migrations (1 initial migration)
│   └── tests/                # 88 model tests (conftest provides SQLite db fixture)
└── frontend/
    └── src/
        ├── api/              # Axios wrappers per module
        ├── stores/           # Pinia stores (user, agent)
        ├── router/           # Vue Router + auth guard
        ├── utils/            # request.js, stream.js, markdown.js, format.js
        └── views/            # 8 pages (Chat, Detection, Training, History, Dashboard, Login, Register, Profile)
```

### Backend layering pattern

All routes follow: **API route** → **Service singleton** → **DB/Storage**

Services are global singletons (instantiated at module level):
- `detection_service` (`app/services/detection_service.py`) — YOLO model management (lazy-loaded `self.models: Dict[int, YOLO]`), single/batch/video detection
- `training_service` (`app/services/training_service.py`) — background thread training via `_train_worker`, status flags via `threading.Event`, startup recovery for interrupted tasks
- `chat_service` (`app/services/chat_service.py`) — session CRUD, SSE-stream via LangGraph `astream_events`
- `knowledge_service` (`app/services/knowledge_service.py`) — lazy-init LangChain pipelines (embeddings, vector store, text splitter)
- `user_service` (`app/services/user_service.py`) — auth helpers

### Multi-agent orchestration (LangGraph)

Defined in `app/services/agent_graph.py`:

```
supervisor ──route_to_agent()──→ detection_agent ──→ supervisor (loop back)
                                 analysis_agent  ──→ supervisor (loop back)
                                 qa_agent        ──→ END
                                 end             ──→ END
```

- `AgentState` = `{ messages, next_agent, detection_results, analysis_report, current_task }`
- Supervisor uses keyword matching on LLM output to route (detection/analysis/qa/end)
- All agents get full tool sets from `agent_tools.py` (detect_objects, query_history, get_statistics, search_knowledge, get_scenes)
- SSE streaming in `ChatService.send_message_stream` uses `graph.astream_events()` with `recursion_limit=10`

### Database (14 tables, 5 domains)

Defined in `app/entity/db_models.py`:
- **User & RBAC**: User, Role, Permission, UserRole, RolePermission
- **Detection**: DetectionScene (config per scene), DetectionTask (per operation), DetectionResult (per object)
- **Training**: TrainingTask (lifecycle mgmt), TrainingMetric (per-epoch metrics), ModelVersion (versioned model artifacts)
- **Chat**: ChatSession, ChatMessage (with agent_used, tool_calls metadata)
- **Ops**: OperationLog (audit trail)

Key models note: `TrainingService._recover_interrupted_tasks()` resumes `running` tasks to `failed` on startup.

### API patterns

- All responses use `ApiResponse(code, message, data)` schema from `app/entity/schemas.py`
- Auth via `Depends(get_current_user)` — token read from Authorization header first, then HttpOnly cookie fallback
- DB session via `Depends(get_db)` — yields `SessionLocal` from `app/database/session.py`
- Redis caching used in `GET /api/detection/scenes` (1h TTL)
- File uploads saved to temp files, cleaned in `finally` blocks

### Frontend patterns

- Token stored in HttpOnly cookie only (more XSS-resistant) — user info in localStorage for state
- Axios interceptor in `utils/request.js` handles 401 → auto logout, 422 → validation errors
- SSE streaming via `utils/stream.js` — `fetch` + `ReadableStream` reader, parses `data:` SSE lines
- Chat state via Pinia store `agent.js` — messages, session list, abort controller
- Vite proxy routes `/api` → `http://localhost:8888` (configured in `vite.config.js`)

### Testing

- Backend: pytest with SQLite in-memory (conftest provides `db` fixture), 88 test cases in `tests/test_models.py` and `tests/test_security.py`
- Frontend: Vitest + jsdom in `src/utils/__tests__/`

### Key dependencies & constraints

- **numpy<2**: PyTorch 2.2.2 compiled against NumPy 1.x ABI
- **torch==2.2.2** / **torchvision==0.17.2**: macOS Intel CPU max supported version
- uv's `required-environments` in pyproject.toml handles macOS x86_64 PyTorch CPU variation
