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
DATABASE_URL=sqlite:///./local_dev.db
FRONTEND_ORIGIN=*
```
