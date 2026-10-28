# ConsultOS — Production-Level Frontend

Autonomous Business Investigation & Workflow Platform built with React, Vite, and Tailwind CSS, aligned with the ConsultOS FastAPI backend architecture and Antigravity CLI integration.

---

## 1. Quickstart & Installation

```bash
# 1. Install dependencies
npm install

# 2. Configure environment variables (optional, defaults to http://localhost:8000)
cp .env.example .env

# 3. Start development server
npm run dev

# 4. Compile production build
npm run build
```

---

## 2. API Integration Map

The centralized API client (`src/services/api.ts` and `src/services/investigations.ts`) connects to the FastAPI backend using standard REST and SSE execution streams:

| Method | Endpoint | Description & Usage |
|---|---|---|
| `GET` | `/api/health` | Backend connectivity check & version telemetry |
| `GET` | `/api/investigations` | Lists investigations for dashboard metrics and history |
| `POST` | `/api/investigations` | Creates investigation; supports JSON or `multipart/form-data` with CSV file |
| `GET` | `/api/investigations/{id}` | Fetches investigation details and plan version |
| `POST` | `/api/investigations/{id}/run` | Starts autonomous DAG execution |
| `GET` | `/api/investigations/{id}/tasks` | Loads topological task graph nodes and statuses |
| `GET` | `/api/investigations/{id}/evidence` | Loads empirical evidence records and lineage |
| `GET` | `/api/investigations/{id}/events` | Loads persisted event history |
| `GET` | `/api/investigations/{id}/report` | Loads final synthesized executive report (`ready` / `partial` / `not_ready`) |
| `POST` | `/api/investigations/{id}/retry/{task_id}` | Retries an eligible failed task node |
| `POST` | `/api/investigations/{id}/cancel` | Requests graceful cancellation of running investigation |
| `GET` | `/api/investigations/{id}/events/stream` | Native Server-Sent Events (SSE) live execution channel |

---

## 3. High-Trust Architecture & Offline Fallback

- **Real Backend Contract**: Points to `VITE_API_BASE_URL` (default: `http://localhost:8000`). If the backend server is reachable, the application renders 100% live backend data.
- **Offline / Sandbox Mode**: When the FastAPI server is not currently running (e.g., initial standalone UI preview), ConsultOS automatically detects backend unavailability, warns with a clear non-alarming status indicator, and provides a deterministic simulation engine (`src/services/mockEngine.ts`) demonstrating:
  - Creating new investigations with CSV validation
  - Executing directed analytical tasks
  - **Dynamic Replanning**: Plan v1 falsifies hypothesis, triggering a revision to Plan v2 and dynamically injecting new tasks
  - Retrying failed tasks and cancellation
  - Clickable evidence citations and verifiable Markdown report export (`.md`)
- **Backend Switcher**: Click the connection pill or settings icon in the top header at any time to point to any custom FastAPI URL or test connection health.

---

## 4. Antigravity Integration Checklist

1. Import this frontend folder into the existing ConsultOS repository (`/frontend`).
2. Run backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
3. Run frontend in a second terminal:
   ```bash
   cd frontend
   npm run dev
   ```
4. Verify backend CORS allows `http://localhost:3000` or `http://localhost:5173`.

---

## 5. UI Design System

The interface uses a light, analyst-grade theme. All tokens live in `src/index.css` under `@theme`, and shared
building blocks (`.card`, `.btn`, `.btn-primary`, `.input`, `.id-chip`, `.code-block` …) live in `@layer components`.

| Token | Value | Use |
|---|---|---|
| `canvas` / `surface` | `#F4F6FA` / `#FFFFFF` | Page background / cards |
| `navy-900` | `#0B1F3A` | Sidebar chrome, code blocks |
| `brand-600` | `#1F55D6` | Primary actions, links, focus |
| `ink` / `body` / `muted` | `#0F1B2D` / `#334155` / `#64748B` | Headings / text / secondary text |
| `line` | `#E4E9F0` | Borders and dividers |
| emerald · amber · rose · sky | Tailwind 50/200/800 | Status (success, warning, danger, info) |

- **Typography:** IBM Plex Sans for UI text, IBM Plex Mono for IDs, code and data only. Minimum text size is 12px.
- **Spacing:** 40px page gutters on desktop, 40px between page sections, 24–32px inside cards.
- **Status colours** are defined once in `src/utils/status.ts`.
- Only presentation files were changed; `src/services`, `src/hooks` and `src/types` are untouched, so every backend
  endpoint behaves exactly as before.

> Note: `npm install` may report a peer-dependency conflict (`esbuild` vs `vite`). If so, run
> `npm install --legacy-peer-deps`.
