# PRD: Construction Workflow & Project Monitoring System (Hackathon MVP)

**Problem statement:** Building an enhanced workflow management and construction project monitoring system for improved infrastructure delivery.

**Time budget:** 7–8 hours total. A working end-to-end product beats a broad, half-working one.

---

## 0. Instructions for the coding agent (read first)

1. Build **only** what is in this document. Do not add features from the "Out of Scope" list.
2. **No Docker.** Backend, frontend and database are run directly on the host. The database is a plain PostgreSQL connection via `DATABASE_URL` (local Postgres or a cloud one such as Neon/Supabase).
3. Use a **modular monolith**: one FastAPI backend, one React frontend, one PostgreSQL database.
4. Keep business logic **out of route handlers**. Routes call services; services call the scheduling engine.
5. Keep the scheduling engine **pure and deterministic** (no DB access inside the algorithm functions) so it is unit-testable.
6. Keep the app **runnable after every step**. Verify each stage (server starts, migration runs, seed works, endpoint responds) before moving on.
7. Prefer simple working code over abstractions. Do not write documentation until the core flow works.
8. Follow the build order in Section 14.

---

## 1. Product Summary

A web app where a **Project Manager** plans a construction project as a work breakdown structure (WBS) of tasks with dependencies, and **Site Engineers** report progress and issues. The system automatically:

- computes the schedule and **critical path** (CPM),
- detects **delayed tasks**,
- propagates delays through **dependent tasks**,
- decides whether the **project completion date actually shifts**,
- raises **alerts**, and
- shows everything on a monitoring **dashboard** with a GREEN / AMBER / RED health indicator.

### The single story the demo must tell

> Create project → break into tasks → define dependencies → assign tasks → update progress → automatically detect delays → identify affected downstream tasks → show project health on a dashboard.

### Headline demo interaction

Foundation is planned to finish on day X. The user marks it completed 4 days late. The system instantly:

- shifts Columns, Beams, Slab, Electrical, Plumbing and Finishing forward by 4 days,
- moves the forecast project completion date by +4 days,
- turns project health **GREEN → RED**,
- lists the affected downstream tasks,
- creates a **Project Delay** alert,
- keeps non-critical branches (e.g. Steel Procurement, Drainage) unaffected.

---

## 2. Goals and Non-Goals

### Goals (P0, must ship)

| # | Capability |
|---|---|
| 1 | JWT login with two roles (Project Manager, Site Engineer) |
| 2 | Projects CRUD |
| 3 | Hierarchical WBS and tasks (parent/child) |
| 4 | Task assignment |
| 5 | Finish-to-Start dependencies with cycle detection |
| 6 | Task workflow with a predecessor guard |
| 7 | Progress updates with history |
| 8 | Issues/blockers against tasks |
| 9 | CPM engine: ES/EF/LS/LF, float, critical path |
| 10 | Delay detection and downstream impact analysis |
| 11 | Alerts generated automatically |
| 12 | Dashboard with health, forecast, critical path |
| 13 | Gantt/timeline and dependency graph visualisations |
| 14 | Seed script with a realistic demo project |

### Stretch (only if core is finished and time remains)

- Simple resource-conflict detection (same assignee has overlapping active tasks).
- AI "Why is this project delayed?" explanation (Section 12).

### Out of Scope (do NOT build)

Docker / Docker Compose, Redis, Celery, MinIO/S3, Kafka, microservices, LangGraph, RAG, vector DB, embeddings, document management, finance / EVM / BOQ / contracts / inventory / procurement modules, MFA, offline PWA, public citizen portal, maps/GIS, Hindi/i18n, hash-chain audit, SS/FF/SF dependency types, working-day calendars, resource levelling, complex government compliance features, complex enterprise RBAC.

---

## 3. Users and Roles

| Role | Permissions |
|---|---|
| `PROJECT_MANAGER` | Create/edit projects; create/edit/delete tasks; create/delete dependencies; assign tasks; view dashboard; resolve issues; acknowledge alerts; trigger recalculation |
| `SITE_ENGINEER` | View projects and their own assigned tasks; update progress; change task status; create issues; view dashboard (read-only) |

Enforce roles in the backend via a dependency/decorator (e.g. `require_role("PROJECT_MANAGER")`). The frontend hides actions the role cannot perform, but the backend is the source of truth.

**Seeded users**

| Email | Password | Role |
|---|---|---|
| `pm@demo.com` | `demo1234` | PROJECT_MANAGER |
| `engineer1@demo.com` | `demo1234` | SITE_ENGINEER |
| `engineer2@demo.com` | `demo1234` | SITE_ENGINEER |

---

## 4. Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, PostgreSQL (psycopg), JWT (`python-jose` or `pyjwt`), `passlib[bcrypt]`, pytest.

**Frontend:** React, Vite, TypeScript, Tailwind CSS, React Router, TanStack Query, Recharts, React Flow (dependency graph).

- **Gantt:** build a simple custom Gantt with CSS/SVG. Do not integrate a heavy Gantt library.
- **Graph layout:** compute layers by topological depth (or use `dagre` if convenient).

**Environment variables (`backend/.env`)**

```env
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
JWT_SECRET=change-me
JWT_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:5173
# Optional (stretch AI feature only)
GEMINI_API_KEY=
```

**Local ports:** frontend `5173`, backend `8000`, Postgres `5432` (or cloud).

---

## 5. Architecture

```
React + Vite (5173)
        │  REST + JWT
        ▼
FastAPI backend (8000)
  ├─ auth
  ├─ projects
  ├─ tasks        (WBS, workflow, progress)
  ├─ scheduling   (CPM, delay propagation, health)  ← pure engine + service
  ├─ issues
  ├─ alerts
  └─ dashboard
        │
        ▼
   PostgreSQL
```

### Backend layout

```
backend/
  app/
    main.py
    core/            # config, db session, security, deps
    auth/            # router, schemas, service
    projects/
    tasks/
    scheduling/
      engine.py      # PURE functions: graph, cycle check, topo sort, CPM, impact
      service.py     # loads DB → engine → persists results, health, alerts
      health.py
    issues/
    alerts/
    dashboard/
    seed.py
  alembic/
  tests/
    test_scheduling_engine.py
    test_workflow_guards.py
  requirements.txt
```

### Frontend layout

```
frontend/src/
  api/               # axios/fetch client, typed endpoints
  lib/               # date utils, constants
  components/        # shared UI (Card, Badge, HealthPill, Table, Modal)
  pages/             # Login, Projects, ProjectDetail, MyTasks
  features/
    auth/
    projects/
    tasks/
    dashboard/
    issues/
```

---

## 6. Conventions

- **Dates** are calendar dates (`YYYY-MM-DD`). **Durations are in calendar days.** No working-day calendars in the MVP.
- **Scheduling convention:** a task occupies `[start, start + duration)`. So `finish = start + duration` and a Finish-to-Start successor may start on `predecessor.finish + lag_days`.
- "Today" is `date.today()` on the server. The seed script and the engine accept an optional `today` parameter so tests are deterministic.
- All timestamps are UTC.
- API is JSON. Errors use `{ "detail": "human readable message" }` with proper status codes (400 validation/guard, 401, 403, 404, 409 cycle).

---

## 7. Data Model

Keep the schema to these tables. Use UUID or integer PKs consistently (integers are fine).

### `users`
`id, name, email (unique), password_hash, role (PROJECT_MANAGER | SITE_ENGINEER), created_at`

### `projects`
```
id, name, description, location,
start_date,
baseline_end           -- planned project completion (computed from leaf tasks' planned_end, max)
forecast_end           -- computed by scheduling engine
delay_days             -- forecast_end - baseline_end (computed, can be <= 0)
health                 -- GREEN | AMBER | RED (computed)
status                 -- PLANNING | ACTIVE | COMPLETED
budget (nullable, display only)
created_by, created_at, updated_at
```

### `tasks`
```
id, project_id, parent_id (nullable → WBS hierarchy),
name, description,
is_summary (bool)      -- true if it has children (WBS group)
-- baseline (set by PM / seed)
planned_start, planned_end, duration (days)
-- actuals
actual_start (nullable), actual_end (nullable)
progress (0-100), status, priority (LOW|MEDIUM|HIGH|CRITICAL),
assignee_id (nullable),
-- computed by scheduling engine (persisted on each recalculation)
forecast_start, forecast_end,
early_start, early_finish, late_start, late_finish,
total_float, is_critical (bool), delay_days (forecast_end - planned_end),
created_at, updated_at
```

**Summary (WBS group) tasks:** roll up from children (min start, max end, duration-weighted progress). They cannot have dependencies and are excluded from CPM. Only **leaf tasks** participate in scheduling.

### `task_dependencies`
```
id, predecessor_task_id, successor_task_id,
dependency_type   -- only 'FS' in MVP
lag_days          -- int, default 0
UNIQUE(predecessor_task_id, successor_task_id)
```

### `task_progress`
```
id, task_id, progress (0-100), note, reported_by, reported_at
```

### `issues`
```
id, project_id, task_id (nullable), title, description,
severity (LOW|MEDIUM|HIGH|CRITICAL),
is_blocking (bool),
status (OPEN|RESOLVED),
reported_by, resolved_by (nullable), created_at, resolved_at
```

### `alerts`
```
id, project_id, task_id (nullable),
type (TASK_DELAYED | PROJECT_DELAY | TASK_BLOCKED | CRITICAL_ISSUE | RESOURCE_CONFLICT),
severity (INFO|WARNING|CRITICAL),
message, details (JSON text, e.g. affected task ids),
status (ACTIVE|ACKNOWLEDGED|RESOLVED),
created_at
```

---

## 8. Task Workflow

### States

`NOT_STARTED → ASSIGNED → IN_PROGRESS → BLOCKED → COMPLETED`

### Allowed transitions

| From | To | Notes |
|---|---|---|
| NOT_STARTED | ASSIGNED | Happens automatically when an assignee is set |
| ASSIGNED | IN_PROGRESS | **Predecessor guard applies** |
| NOT_STARTED | IN_PROGRESS | Only if assigned; otherwise 400 |
| IN_PROGRESS | BLOCKED | Manual, or auto when a blocking issue is opened |
| BLOCKED | IN_PROGRESS | Only when no open blocking issues remain on the task |
| IN_PROGRESS | COMPLETED | Sets progress = 100, records `actual_end` |
| COMPLETED | (none) | Terminal for MVP |

### Guards

1. **Start guard (the key rule):** to move a task to `IN_PROGRESS`, every FS predecessor must be `COMPLETED`. Otherwise reject with 400:
   `"Task cannot start because predecessor 'Foundation' is not completed."`
   (List all incomplete predecessors.)
2. **Complete guard:** a task can only be completed if all predecessors are `COMPLETED`.
3. **Unblock guard:** cannot leave `BLOCKED` while an open `is_blocking` issue exists on the task.
4. **Progress guard:** progress can only be updated on `IN_PROGRESS` tasks. Setting progress to 100 does not auto-complete; completion is an explicit action (so the PM/engineer confirms the actual finish date).
5. On first move to `IN_PROGRESS`, set `actual_start` (default today, optionally provided).
6. On `COMPLETED`, `actual_end` defaults to today but **may be supplied** (`actual_end` date, needed for the demo and for back-dated site reports). It must be >= `actual_start`. For the MVP, do **not** reject a future `actual_end` (this lets the demo simulate a late finish).

### Side effects (after any workflow/progress/duration/dependency change)

Call `scheduling.service.recalculate_project(project_id)`, which:
1. recomputes the schedule (Section 9),
2. persists forecast/float/critical flags on tasks,
3. updates `projects.forecast_end`, `delay_days`, `health`,
4. creates/updates alerts (Section 10).

---

## 9. Scheduling Engine (the technical core)

Implement as `scheduling/engine.py` with **pure functions** operating on plain dataclasses/dicts. `service.py` handles DB IO.

### 9.1 Inputs

- Leaf tasks: `id, planned_start, planned_end, duration, status, progress, actual_start, actual_end`
- Dependencies: `(predecessor_id, successor_id, lag_days)` (all FS)
- `project_start`, `today`

### 9.2 Required functions

| Function | Behaviour |
|---|---|
| `build_graph(tasks, deps)` | Adjacency lists for successors and predecessors |
| `detect_cycle(tasks, deps)` | Returns the cycle path or `None`. Also used to validate a *proposed* dependency before insert (reject with 409 and the cycle path) |
| `topological_sort(graph)` | Kahn's algorithm; raises on cycle |
| `forward_pass(...)` | Computes forecast start/finish per task (rules below) |
| `backward_pass(...)` | Computes late start/finish |
| `compute_float(...)` | `total_float = late_start - early_start` (days) |
| `critical_path(...)` | Tasks with `total_float == 0`, ordered topologically, plus the ordered chain(s) from a start to the project end |
| `downstream_impact(changed_task_ids, ...)` | Set of tasks reachable from delayed tasks whose forecast dates moved later than baseline, with `shift_days` each |
| `project_forecast(...)` | `forecast_end = max(forecast_end of all leaf tasks)`; `delay_days = forecast_end - baseline_end` |

### 9.3 Forward pass rules (forecast dates)

Process tasks in topological order. For each task:

- **COMPLETED:** `forecast_start = actual_start`, `forecast_end = actual_end`. Actuals always win.
- **IN_PROGRESS / BLOCKED:**
  - `forecast_start = actual_start`
  - `remaining = ceil(duration * (1 - progress/100))`
  - `forecast_end = max(actual_start + duration, today + remaining)`
    (an in-progress task that is overdue can never forecast to finish before today + remaining work)
- **NOT_STARTED / ASSIGNED:**
  - `earliest_from_preds = max(pred.forecast_end + lag_days)` over FS predecessors (if none: `planned_start`)
  - `forecast_start = max(earliest_from_preds, today)` (a task cannot start in the past)
  - **Constraint:** a task with no predecessors uses `max(planned_start, today)`.
  - `forecast_end = forecast_start + duration`

Set `early_start/early_finish` equal to `forecast_start/forecast_end` (this is the forward pass).

### 9.4 Backward pass

- Anchor the project finish at `forecast_end` (max of all leaf `forecast_end`).
- For tasks with no successors: `late_finish = project_forecast_end`.
- Otherwise: `late_finish = min(succ.late_start - lag_days)`.
- `late_start = late_finish - duration`.
- `total_float = late_start - early_start` (>= 0).
- `is_critical = total_float == 0`.

For COMPLETED tasks, still compute float for display, but they are shown as "done" in the critical path visual.

### 9.5 Delay detection

For each leaf task:
- `delay_days = forecast_end - planned_end` (positive = late).
- `is_delayed = delay_days > 0` **or** (`status != COMPLETED` and `today > planned_end`).

### 9.6 CRITICAL RULE: do not over-report project delay

Not every delayed task delays the project. Report a **project** delay **only** if `project.forecast_end > project.baseline_end`. A delayed task that has float to absorb the delay must be flagged as "delayed, absorbed by float" and **must not** turn the project red on its own.

### 9.7 Downstream impact

Given the tasks that are delayed, walk successors (BFS). For each reachable task with `forecast_start > planned_start`, record:
`{ task_id, name, shift_days = forecast_start - planned_start, is_critical }`.
The dashboard shows the count and names of affected activities and the root delayed task(s) (the "cause").

### 9.8 Baseline

The engine also needs a way to compute planned dates. For P0, planned dates are entered by the PM and by the seed. **P1:** `POST /projects/{id}/baseline` runs a forward pass from `project_start` with no actuals, writes `planned_start/planned_end`, and updates `projects.baseline_end`.

### 9.9 Required unit tests (`tests/test_scheduling_engine.py`)

1. Simple linear chain produces correct ES/EF and all tasks critical.
2. Branching graph produces correct float; the shorter branch has float > 0.
3. Cycle is detected (including a self-dependency and a 3-node cycle).
4. Delaying a critical task shifts project `forecast_end` by the same number of days.
5. Delaying a **non-critical** task **within its float** does **not** change `forecast_end`.
6. Delaying a non-critical task **beyond its float** shifts `forecast_end` by (delay − float).
7. Completed tasks use actual dates; not-started tasks never forecast into the past.
8. Downstream impact returns exactly the reachable successors that moved.

---

## 10. Health and Alerts (deterministic rules)

### Project health

| Health | Condition |
|---|---|
| 🔴 **RED** | `delay_days >= 3`, **or** a critical-path task is `BLOCKED` by an open blocking issue |
| 🟠 **AMBER** | `delay_days` in 1–2, **or** any task is delayed (absorbed by float), **or** any open HIGH/CRITICAL issue |
| 🟢 **GREEN** | Otherwise |

Put the thresholds in constants so they are easy to change.

### Alert generation

Generated inside `recalculate_project`. **Deduplicate**: don't create a new ACTIVE alert if an identical (project, task, type) ACTIVE alert exists; update its message instead. Auto-resolve alerts whose condition has cleared.

| Type | Trigger | Severity |
|---|---|---|
| `PROJECT_DELAY` | `project.delay_days > 0` and changed since the last recalculation | CRITICAL if `>= 3`, else WARNING |
| `TASK_DELAYED` | A leaf task `is_delayed` | CRITICAL if critical task, WARNING otherwise (message notes "absorbed by float" if so) |
| `TASK_BLOCKED` | Task moved to `BLOCKED` | WARNING (CRITICAL if critical task) |
| `CRITICAL_ISSUE` | Open issue with severity `CRITICAL` or `HIGH` | CRITICAL / WARNING |
| `RESOURCE_CONFLICT` *(stretch)* | Same assignee has overlapping active tasks | WARNING |

**Example messages**
- `Project delayed: forecast completion moved from 30 Oct to 03 Nov (+4 days). Root cause: Foundation completed 4 days late. 6 downstream activities affected.`
- `Foundation is 4 days behind plan (critical path task).`

---

## 11. API Specification

All routes prefixed with `/api`. JWT in `Authorization: Bearer <token>`. Swagger at `/docs`.

### Auth
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/auth/login` | public | `{email, password}` → `{access_token, user}` |
| GET | `/auth/me` | any | Current user |
| GET | `/users` | any | List users (for assignment dropdown) |

### Projects
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects` | any | List with summary (health, progress, delay_days) |
| POST | `/projects` | PM | Create |
| GET | `/projects/{id}` | any | Detail |
| PUT | `/projects/{id}` | PM | Update |
| GET | `/projects/{id}/dashboard` | any | Dashboard payload (below) |
| POST | `/projects/{id}/recalculate` | PM | Force recalculation |

### Tasks / WBS
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects/{id}/tasks` | any | Flat list including computed fields and `parent_id` (frontend builds tree) |
| POST | `/projects/{id}/tasks` | PM | Create task or WBS group |
| GET | `/tasks/{id}` | any | Detail incl. predecessors, successors, progress history, issues |
| PUT | `/tasks/{id}` | PM | Edit fields (name, dates, duration, priority, assignee) → triggers recalculation |
| DELETE | `/tasks/{id}` | PM | Delete (also removes its dependencies) |
| POST | `/tasks/{id}/assign` | PM | `{assignee_id}` |
| POST | `/tasks/{id}/status` | assignee or PM | `{status, actual_start?, actual_end?}` → runs guards |
| POST | `/tasks/{id}/progress` | assignee or PM | `{progress, note}` → writes `task_progress` |
| GET | `/me/tasks` | any | Tasks assigned to current user |

### Dependencies
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects/{id}/dependencies` | any | All dependencies |
| POST | `/tasks/{id}/dependencies` | PM | `{predecessor_id, lag_days?}`; validates same project, leaf tasks, no duplicate, **no cycle (409 with path)** |
| DELETE | `/dependencies/{id}` | PM | Remove |

### Issues
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects/{id}/issues` | any | Filter `?status=OPEN` |
| POST | `/projects/{id}/issues` | any | `{task_id?, title, description, severity, is_blocking}`; if blocking and task in progress → task becomes BLOCKED |
| POST | `/issues/{id}/resolve` | PM | Resolve; if task was blocked and no more blocking issues → back to IN_PROGRESS |

### Alerts
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects/{id}/alerts` | any | Filter `?status=ACTIVE` |
| POST | `/alerts/{id}/acknowledge` | PM | Acknowledge |

### System
| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{status:"ok", db:"ok"}` |

### Dashboard payload (`GET /projects/{id}/dashboard`)

```json
{
  "project": {"id": 1, "name": "Riverfront Bridge Construction"},
  "health": "RED",
  "planned_completion": "2026-10-30",
  "forecast_completion": "2026-11-03",
  "delay_days": 4,
  "overall_progress": 46.5,
  "planned_progress": 52.0,
  "counts": {"total": 11, "completed": 4, "active": 1, "delayed": 7, "blocked": 0},
  "critical_path": [{"id": 1, "name": "Site Survey", "status": "COMPLETED", "forecast_start": "...", "forecast_end": "..."}],
  "root_delayed_tasks": [{"id": 3, "name": "Foundation", "delay_days": 4}],
  "affected_tasks": [{"id": 4, "name": "Columns", "shift_days": 4, "is_critical": true}],
  "active_issues": [],
  "active_alerts": [],
  "progress_series": [{"date": "2026-09-01", "planned": 0, "actual": 0}]
}
```

**Progress calculations**
- `overall_progress` = duration-weighted average of leaf task progress.
- `planned_progress` = duration-weighted average of `clamp((today - planned_start) / duration, 0, 1) * 100` over leaf tasks.
- `progress_series` can be a simple approximation (planned S-curve from baseline; actual from `task_progress` history + completions). Keep it simple.

---

## 12. Stretch: AI Delay Explanation (only if core is done)

`POST /projects/{id}/explain-delay`

- Backend builds a compact JSON context: health, delay_days, planned vs forecast completion, root delayed tasks, critical path, affected tasks, open issues.
- Sends it to Gemini (or OpenAI) with a prompt: *"Explain in 3–4 sentences why this project is delayed and what should be done. Use only the provided data."*
- If no API key is set or the call fails, **fall back to a deterministic template** built from the same context, so the button always works.
- UI: an "Explain delay" button on the dashboard showing the response in a card.

No RAG, no embeddings, no agents, no LangGraph.

---

## 13. Frontend Requirements

Clean, professional construction/project-management look. Responsive. Don't over-engineer.

### Pages

1. **Login**: email/password; demo credentials hint.
2. **Projects list**: cards/table with name, progress bar, health pill, forecast vs planned, delay days. "New project" (PM only).
3. **Project detail** (tabs): **Overview/Dashboard · Tasks · Timeline · Dependencies · Issues · Alerts**.
4. **My Tasks**: for Site Engineers, tasks assigned to them with quick "Start", "Update progress", "Complete", "Report issue" actions.

### Dashboard tab (the hero screen)

- **Health banner**: 🟢/🟠/🔴 with text such as "⚠ Project delay detected: forecast 4 days late", showing root cause task and count of affected downstream activities.
- **KPI cards**: overall progress (with planned progress marker), total tasks, completed, active, delayed, blocked.
- **Dates card**: planned completion, forecast completion, delay in days.
- **Critical path strip**: ordered chips (`Excavation → Foundation → Columns → …`), colour-coded by status; delayed ones in red.
- **Progress chart** (Recharts): planned vs actual over time.
- **Active alerts** list with severity icons.
- **Active issues** list.
- Optional "Explain delay" button (stretch).

### Tasks tab

- WBS **tree table** (collapsible groups) with columns: name, assignee, status badge, progress bar, planned dates, forecast dates, delay, float, critical flag.
- PM actions: add task/group, edit, assign, delete, add dependency.
- Status action buttons run the workflow; **show guard errors clearly** (toast/modal with the backend message).
- Completing a task opens a small dialog with an **actual finish date** field (defaults to today) — required for the demo.

### Timeline (Gantt) tab

Custom CSS/SVG Gantt:
- Rows = leaf tasks (grouped under WBS groups), horizontal axis = dates with a "today" line.
- Two bars per task: **planned** (light/outlined) and **forecast/actual** (solid, with progress fill).
- Critical tasks highlighted (e.g. red/orange), delayed portion visibly extending past the planned bar.
- Simple dependency arrows or connector hints between bars are a nice-to-have.

### Dependencies tab

React Flow graph: nodes = leaf tasks (colour by status, red border for critical), edges = FS dependencies (critical edges highlighted). Layered layout. PM can add a dependency by choosing a predecessor from a dropdown (graph drag-to-connect is optional). Cycle errors from the backend are shown to the user.

### Issues & Alerts tabs

Tables with filters, severity badges, create-issue modal, resolve button (PM), acknowledge button (PM).

### General

- Auth token stored in memory/localStorage; axios/fetch interceptor for 401 → redirect to login.
- TanStack Query for data; **invalidate dashboard, tasks, alerts queries after any mutation** so the dashboard visibly updates after each action.

---

## 14. Build Order (follow strictly; keep runnable at every step)

| Time | Milestone | Verify |
|---|---|---|
| 0:00–0:30 | **Setup**: repo structure, FastAPI app, `/health`, DB connection via `DATABASE_URL`, Vite React app running | Both servers start; `/health` returns db ok |
| 0:30–1:15 | **Models + migrations + auth**: SQLAlchemy models, Alembic migration, JWT login, seed users | `alembic upgrade head` works; login returns token |
| 1:15–2:00 | **Core APIs**: projects, tasks (WBS), dependencies (no cycle check yet), issues, alerts CRUD | Swagger flows work |
| 2:00–3:30 | **Scheduling engine + tests**: cycle detection, topo sort, CPM, float, critical path, delay & impact, health, alert generation; wire `recalculate_project` into all mutations; workflow guards | `pytest` passes all engine tests |
| 3:30–4:00 | **Seed script** with demo project (Section 15) and dashboard endpoint | Dashboard JSON is correct for baseline and delayed scenarios |
| 4:00–5:30 | **Frontend core**: login, projects list, project detail, dashboard tab, tasks tab with workflow actions | Can log in, complete a task, see dashboard update |
| 5:30–6:30 | **Visualisations**: Gantt, dependency graph, critical-path strip, progress chart | Visual demo works |
| 6:30–7:15 | **Polish**: issues/alerts tabs, error toasts, empty/loading states, role-based UI, My Tasks page | Full demo script passes |
| 7:15–8:00 | **Stretch only**: AI explanation or resource conflicts. Otherwise: bug fixing, README with run steps | — |

If less than 30 minutes remain, skip stretch and harden the demo.

---

## 15. Seed Data

Run with `python -m app.seed [--scenario baseline|delayed] [--reset]`. `--reset` drops and recreates the demo project so the demo can be repeated. **All dates are computed relative to today** so the demo is always "live".

### Project

**Riverfront Bridge Construction**, start = `today − 15 days`, location "Ahmedabad, Gujarat", budget ₹45 crore (display only).

### WBS and tasks (durations in days; day 0 = project start)

| # | Task | Parent group | Duration | Predecessors (FS) | Baseline start → end (day) | Assignee |
|---|---|---|---|---|---|---|
| G1 | **Site Preparation** | — | (rollup) | — | — | — |
| 1 | Site Survey & Mobilisation | G1 | 5 | — | 0 → 5 | engineer1 |
| 2 | Excavation | G1 | 6 | 1 | 5 → 11 | engineer1 |
| 3 | Steel Procurement | G1 | 12 | — | 0 → 12 | engineer2 |
| 4 | Drainage Works | G1 | 8 | 2 | 11 → 19 | engineer2 |
| G2 | **Structure** | — | (rollup) | — | — | — |
| 5 | Foundation | G2 | 10 | 2 | 11 → 21 | engineer1 |
| 6 | Columns | G2 | 8 | 5, 3 | 21 → 29 | engineer1 |
| 7 | Beams | G2 | 7 | 6 | 29 → 36 | engineer2 |
| 8 | Slab | G2 | 9 | 7 | 36 → 45 | engineer2 |
| G3 | **MEP & Finishing** | — | (rollup) | — | — | — |
| 9 | Electrical Rough-in | G3 | 7 | 8 | 45 → 52 | engineer2 |
| 10 | Plumbing | G3 | 5 | 8 | 45 → 50 | engineer1 |
| 11 | Finishing | G3 | 10 | 9, 10, 4 | 52 → 62 | engineer1 |

**Expected baseline critical path:** Site Survey → Excavation → Foundation → Columns → Beams → Slab → Electrical → Finishing (62 days).
**Expected float:** Steel Procurement 9, Plumbing 2, Drainage Works 33.

### Scenario `baseline` (default; use for the live demo)

- Site Survey, Excavation, Steel Procurement: **COMPLETED** on time (actuals equal plan).
- Drainage Works: IN_PROGRESS, started on plan (day 11), progress 50%, planned end day 19.
- Foundation: **IN_PROGRESS**, started on plan (day 11), progress 40%, planned end day 21 (6 days from today). Forecast equals plan.
- Everything else NOT_STARTED/ASSIGNED.
- Project health **GREEN**, delay 0.
- Two OPEN low/medium issues (e.g. "Crane availability next week", "Minor water seepage in pit") to make the issues tab realistic.

### Scenario `delayed` (pre-loaded delay for screenshots / fallback demo)

Same as baseline, except **Foundation is COMPLETED with `actual_end = planned_end + 4 days`**. After recalculation:

- Foundation delay = +4, on critical path
- Columns, Beams, Slab, Electrical, Plumbing, Finishing shifted +4 (affected = 6; Plumbing is shifted but non-critical with float still 2)
- Steel Procurement and Drainage Works unaffected (non-critical)
- Forecast completion = baseline + 4 days, health **RED**
- Active alerts: `PROJECT_DELAY` (critical), `TASK_DELAYED` for Foundation (critical) and dependents, plus the seeded issues.

The seed must call `recalculate_project` after inserting data so computed fields, health and alerts are populated.

### Live demo script

1. Login as PM → dashboard is GREEN, forecast = planned.
2. Open Tasks → Foundation → **Complete** with actual finish = planned end + 4 days. (Alternative trigger that needs no future date: edit Foundation's duration from 10 to 14 days.)
3. Dashboard updates: RED, +4 days, affected activities listed, critical path highlighted, new alert.
4. Show Gantt: bars for Columns → Finishing shifted right.
5. Show Dependencies graph: critical chain highlighted; Steel/Drainage untouched.
6. Try starting **Columns** before Foundation is done (use a `--reset` first) → guard error message.
7. (Stretch) Click "Explain delay".

---

## 16. Acceptance Criteria

- [ ] `alembic upgrade head` and `python -m app.seed` run cleanly on an empty database.
- [ ] Login works for both roles; PM-only endpoints return 403 to engineers.
- [ ] Creating a dependency that forms a cycle returns 409 with a clear message.
- [ ] Starting a task with an incomplete predecessor returns 400: *"Task cannot start because predecessor 'X' is not completed."*
- [ ] Completing Foundation 4 days late updates forecast dates of all downstream tasks, sets `delay_days = 4`, health RED, creates a `PROJECT_DELAY` alert.
- [ ] Delaying a non-critical task within its float does **not** change project forecast or turn health RED.
- [ ] Critical path and float values match Section 15 for the baseline scenario.
- [ ] Dashboard reflects any change immediately without a manual page refresh.
- [ ] Gantt shows planned vs forecast bars and a today line; dependency graph highlights the critical path.
- [ ] Site Engineer can update progress, change status and report issues but cannot create tasks/dependencies.
- [ ] `pytest` engine tests (Section 9.9) pass.
- [ ] App runs with **no Docker**, using only `DATABASE_URL` and `.env`.

---

## 17. First Task for the Coding Agent

Before implementing any feature, do only this:

1. Create the `backend/` and `frontend/` project structure from Section 5.
2. Implement the FastAPI app with a `/api/health` endpoint.
3. Configure the PostgreSQL connection from `DATABASE_URL` (SQLAlchemy 2.x).
4. Create the SQLAlchemy models for: `User`, `Project`, `Task`, `TaskDependency`, `TaskProgress`, `Issue`, `Alert`.
5. Configure Alembic and generate/run the initial migration.
6. Implement JWT auth (`/auth/login`, `/auth/me`) and seed the three demo users.
7. Run the backend and **verify** the DB connection, migration and login work.
8. Scaffold the Vite + React + TS + Tailwind frontend and confirm it loads and can call `/api/health`.

Then continue through the Build Order (Section 14) one milestone at a time, verifying each before moving on. Do **not** start visualisations or the AI feature until the scheduling engine and its tests pass.
