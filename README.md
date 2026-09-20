# ConstructFlow 🏗️

ConstructFlow is an advanced, AI-powered Construction Project Management system designed to handle complex project scheduling, critical path calculation, role-based workflows, and automated risk analysis. It bridges the gap between on-site execution and high-level project oversight.

---

## 🌟 Key Features

1. **Dynamic Scheduling Engine (CPM)**
   - Automatically calculates the **Critical Path Method (CPM)** for tasks.
   - Computes early/late start dates, early/late finish dates, and total float.
   - Instantly recalculates project forecasts whenever a task is delayed or modified.

2. **Role-Based Access Control (RBAC) & Organizational Hierarchy**
   - Supports 8 distinct personas (Project Director, Project Manager, Site Engineer, Quality Inspector, Contractor, Store Keeper, Finance Officer, Auditor).
   - Enforces strict API-level boundaries and customized frontend navigation based on user roles.

3. **AI-Powered Risk & Delay Analysis**
   - Integrates with Large Language Models (LLMs) via Hugging Face/OpenAI-compatible APIs or Google Gemini.
   - Reads deterministic project data to provide natural-language insights into current risks, impacts, and areas needing attention.
   
4. **Strict Approval Workflows & Change Management**
   - **Baseline Scheduling**: Project baseline must be explicitly approved by a Project Director.
   - **Change Requests**: Major delays or scope changes require a formal Change Request (Draft → Submitted → Approved/Rejected).
   - **Task Execution**: Site Engineers submit work; Quality Inspectors/PMs approve and mark as completed.

5. **Tamper-Proof Audit Logging**
   - Every state-changing action (updates, status changes, approvals) is recorded in a centralized Audit Log.
   - Independent Auditors can monitor the log for full non-repudiation and compliance.

6. **Interactive Dashboards & Public Portals**
   - Rich visualizations (Gantt-style bar charts) using Recharts.
   - Public view for stakeholders to observe high-level progress without needing authentication.

---

## 🏗️ Architecture & Flow

The system is built on a **Client-Server Architecture**.

- **Frontend (Client)**: A React-based Single Page Application (SPA). It maintains user sessions via JWT (JSON Web Tokens) and provides role-aware rendering (hiding/showing buttons and routes based on permissions).
- **Backend (Server)**: A fast, asynchronous Python API built with FastAPI. It handles the core business logic, including the recursive scheduling engine for the CPM calculations. 
- **Database Layer**: Relational database (SQLite/PostgreSQL) managed by SQLAlchemy ORM and Alembic migrations.
- **Workflow / Flow**: 
  1. **Planning**: A PM creates tasks and dependencies. The Director approves the baseline.
  2. **Execution**: Engineers log daily progress and mark tasks as "Submitted".
  3. **Quality Gate**: Inspectors review and mark tasks as "Completed".
  4. **Dynamic Adjustment**: If a task takes longer than planned, the CPM engine recalculates down-stream impacts. If delays breach thresholds, automated alerts are fired.
  5. **AI Insight**: At any time, a PM can request an AI summary which reads the current CPM state and explains the project health.

---

## 👥 Organizational Hierarchy

| Role | Responsibilities & Capabilities |
|------|--------------------------------|
| **Project Director** | High-level oversight. Approves project baselines and reviews Change Requests. Can view everything. |
| **Project Manager (PM)** | Plans the WBS, assigns tasks, creates Change Requests, triggers AI analysis. Approves completed tasks. |
| **Site Engineer** | Executes tasks, reports issues, logs daily progress, and submits tasks for approval. |
| **Contractor** | Similar to Site Engineer but typically restricted to specific assigned modules/tasks. |
| **Quality Inspector** | Reviews work submitted by Engineers/Contractors and officially approves/completes the tasks. |
| **Auditor** | Read-only oversight. Views the Audit Logs to ensure compliance and traceability. |
| **Finance / Store** | Specialized roles for tracking budget variances and inventory (expandable modules). |
| **Public** | Unauthenticated users who can view read-only dashboards for "Public" projects. |

---

## 💻 Tech Stack

### Frontend
* **React 18** (Vite)
* **TypeScript**
* **Tailwind CSS** (Styling & Responsive UI)
* **React Router** (Navigation)
* **Recharts** (Data Visualization)
* **Lucide React** (Icons)
* **React Query / Axios** (Data fetching)

### Backend
* **Python 3.10+**
* **FastAPI** (High-performance API framework)
* **SQLAlchemy** (ORM) & **Alembic** (Migrations)
* **SQLite** (Default DB, swapable to PostgreSQL)
* **Pydantic** (Data validation & serialization)
* **Passlib / JWT** (Authentication)

### Integrations
* **OpenAI / Hugging Face / Google Gemini SDKs** (For AI Analysis features)

---

## 🚀 Getting Started

### 1. Backend Setup
Navigate to the `backend/` directory:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file in the `backend/` directory:
```env
JWT_SECRET_KEY=your_super_secret_key
AI_PROVIDER=huggingface
HF_TOKEN=your_huggingface_token
AI_MODEL=openai/gpt-oss-120b:fastest
```

**Database Seeding & Starting:**
```bash
# Seed the database with demo users, roles, and a sample project
python -m app.seed --reset

# Start the API server
uvicorn app.main:app --reload
```
*API will run on `http://127.0.0.1:8000`*

### 2. Frontend Setup
Navigate to the `frontend/` directory:
```bash
cd frontend
npm install

# Start the frontend development server
npm run dev
```
*App will run on `http://localhost:5173`*

### 3. Testing the Application
Open the frontend application. On the login page, you will see a **Quick Login (Testing)** panel. Clicking any of the personas (e.g., Project Director, Site Engineer) will auto-fill their credentials (`demo1234`), allowing you to seamlessly test the role-based boundaries.
