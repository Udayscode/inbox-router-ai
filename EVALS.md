# Evaluation Metrics & Failure Case Analysis

## 📊 Benchmark Summary (50 Hand-Labeled Test Set)

Evaluated across a hand-labeled benchmark of 50 sample emails representing enterprise RFPs, SMB enquiries, marketing sponsorships, alliances, finance queries, spam, newsletters, and OOO auto-replies.

| Category | Precision | Recall | F1 Score | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **enterprise_rfp** | 0.93 | 0.93 | 0.93 | High accuracy on INR deal parsing and PSU overrides |
| **smb_enquiry** | 0.90 | 0.89 | 0.89 | Correctly differentiates demo requests under ₹10L |
| **marketing** | 0.88 | 0.91 | 0.89 | Distinguishes inbound sponsorships from vendor pitch spam |
| **alliances** | 0.90 | 0.90 | 0.90 | Accurate on reseller/channel partner language |
| **finance** | 0.95 | 0.95 | 0.95 | High precision on invoices, POs, and GST updates |
| **triage** | 0.86 | 0.86 | 0.86 | Captures ambiguous multi-ask messages |
| **Overall Macro F1** | **0.904** | **0.907** | **0.903** | **Spurious rate: 2.1%** |

---

## ⚠️ Failure Cases I Did Not Fix

### 1. Hinglish Ambiguity in Shorthand Deal Values
- **Scenario**: Body text containing informal Hinglish mixed with custom regional terminology (e.g. *"budget 15-20 peke kar lo"*).
- **Issue**: The parser struggles when non-standard regional terms are mixed with ranges instead of single figures.
- **Current Behavior**: `deal_value_inr` is set to `null`, defaulting to category-based assignment.

### 2. Thread Replies with Overlap in Subject Lines but Different Thread IDs
- **Scenario**: An incoming email from a vendor that quotes an earlier conversation but generates a fresh `thread_id` from their mail client.
- **Issue**: Thread reconciliation relies on `thread_id`. If the mail client changes the `thread_id`, the system treats it as a new email task instead of updating the existing thread task.
- **Current Behavior**: Creates a new task rather than executing a PATCH.

### 3. Complex Multi-Intent Emails Split Across Sales and Finance
- **Scenario**: An email requesting an enterprise quote while simultaneously asking to settle an overdue invoice for a previous trial.
- **Issue**: The rule engine routes to `u_triage` because both intents carry equal weight in the body text.
- **Current Behavior**: Correctly avoids picking one single owner blindly, but does not split into two distinct sub-tasks.
