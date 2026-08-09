# Engineering Decisions & Architecture Tradeoffs

### 1. Handling Gemini Rate Limits & Retries
- **Design Choice**: Implemented adaptive backoff in `backend/gemini.py` for API calls. On 429 quota errors the sleep time scales as `5s × (attempt + 1)` (5s, 10s, 15s…) across 6 attempts. For other transient errors standard exponential backoff (`2^attempt`) is used. Additionally, a `4.1s` pacing sleep is inserted between every email in the ingestion loop to stay within the 15 RPM free-tier limit.
- **Cheap Heuristic Prefilter**: Applied `cheap_prefilter()` in `rules.py` prior to invoking the LLM. Obvious out-of-office auto-replies and newsletters with standard footer signatures (`unsubscribe`, `manage subscription`) are filtered deterministically. This saves ~15-20% of API call volume and prevents quota exhaustion during large batch ingestions.

### 2. Enforcing Idempotency & Thread Reconciliation
- **Idempotency**: Indexed `EmailLog` by `(candidate_id, email_id)`. Re-posting an identical email short-circuits the pipeline immediately without calling Gemini or mutating existing tasks.
- **Thread Reconciliation**: Indexed `Task` by `(candidate_id, thread_id)`. When an incoming email matches an existing `thread_id`, the pipeline executes an in-place `PATCH`/update on the existing task rather than creating a duplicate task record. Quoted historical text is excluded from re-extraction.

### 3. Backend Data Model & Instantly Answerable Analytics
- **Separate Logging Storage**: Created `EmailLog` alongside `Task`. While the Task API spec (§5) only records actionable tasks, `EmailLog` persists decision outcomes (`created`, `updated`, `skipped`), category classifications, skip reasons (`spam`, `out_of_office`, `newsletter`), and confidence scores for ALL processed emails.
- **Instant Query Execution**: `GET /api/stats` and `/api/chat` query `EmailLog` and `Task` tables directly via SQLModel aggregations. Zero LLM re-classification is needed to answer statistical questions.

### 4. Preventing Conversational LLM Hallucination
- **3-Stage Grounded Query Architecture**:
  1. **Stage 1 (NL → Intent)**: `gemini.nl_to_query()` translates the user's natural language question into a strictly validated query schema (`query_type` + `params`).
  2. **Stage 2 (Deterministic Execution)**: `query_engine.run_query()` runs the query directly against SQLite/Postgres and returns raw numerical/array facts.
  3. **Stage 3 (Grounded Synthesis)**: `gemini.phrase_answer()` receives ONLY `query_result` data (never raw email text) with instructions to state zero/unsupported when appropriate.
- **Result**: Zero-count queries (e.g. "GST refunds") return `0` with supporting data rather than fabricated numbers. Out-of-scope requests (e.g. "Send Aarti an email") are rejected cleanly.

### 5. Known Limitations & What We Would Build with 2 More Weeks
- **Multi-Ask Ambiguity Handling**: Genuinely ambiguous emails with two distinct asks (e.g., Example 11 with an RFP request and a marketing webinar request) are routed to `u_triage` with low confidence. With two more weeks, we would implement sub-task creation or multi-assignee tracking.
- **Enhanced INR Shorthand Parsing**: Expanded support for regional number formatting variations and currency symbols in Hinglish body text.
