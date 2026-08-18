# Alumnx Sales Inbox Router

**Candidate ID**: `uday.jhariyaa@gmail.com`  
**Backend API Base URL**: `https://inbox-router-ai.onrender.com`  
**Frontend App URL**: `https://inbox-router-ai.vercel.app`  

---

## 🚀 Overview

An autonomous, rule-grounded email ingestion and routing engine built for B2B sales inboxes receiving high-volume requests (RFPs, SMB enquiries, sponsorships, partnerships, billing, and spam).

The system features:
1. **Deterministic & LLM Hybrid Pipeline**: Dual-pass classification (Gemini 2.0 Flash) combined with deterministic post-processing rules (PSU/Govt tender overrides, INR deal value parsing, 72h deadline escalation).
2. **Task API Compliance**: Complete implementation of §5 specification (`POST /tasks`, `PATCH /tasks/{id}`, `GET /tasks`, `DELETE /tasks/{id}`, `GET /users`).
3. **Thread Reconciliation & Idempotency**: Deduplicates batch re-ingestion and reconciles thread replies to existing tasks rather than creating duplicate records.
4. **Grounded Conversational Interface**: A 3-tier NL-to-SQL query pipeline (`nl_to_query` → SQL execution → `phrase_answer`) ensuring exact data-backed answers without AI hallucinations.

---

## 🛠️ Quickstart

### Docker (Recommended)
```bash
cp .env.example .env   # add your GEMINI_API_KEY
docker compose up --build
```
Backend → `http://localhost:8000` · Frontend → `http://localhost:3000`

### Manual
```bash
# Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:
```env
CANDIDATE_ID=uday.jhariyaa@gmail.com
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
DATABASE_URL=sqlite:///./data/local_dev.db
FRONTEND_ORIGIN=*
```

---

## ☁️ Cloud Deployment (Render & Gemini Guidelines)

### 1. Database Persistence on Render
Because SQLite runs in-memory/in-file, container restarts will wipe task data. To persist tasks across deployments and restarts on Render:
1. Under **Disks** in your Render service dashboard, click **Add Disk**.
2. Mount the disk at Mount Path: `/app/data` (size: `1 GB` is plenty).
3. Set your service's `DATABASE_URL` environment variable to: `sqlite:///./data/local_dev.db` (which resolves inside `/app/data/local_dev.db`).

### 2. Gemini Rate Limiting (15 RPM)
* **Backend Pacing:** The backend uses an automated `time.sleep(4.1)` between email classifications to safely stay under the free-tier Gemini rate limits.
* **Frontend Chunking:** To prevent Render's hard **100-second HTTP request timeout**, the frontend automatically chunks ingestion payloads into batches of 15 and routes them sequentially. This guarantees you never hit gateway timeouts or rate limits during large batch ingests.

