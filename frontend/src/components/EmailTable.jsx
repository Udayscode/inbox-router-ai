import React from 'react';
import { useState } from "react";
import { ingestEmails } from "../api.js";

function truncate(text, n = 80) {
  if (!text) return "";
  return text.length > n ? text.slice(0, n) + "…" : text;
}

export default function EmailTable({ emails, onIngested }) {
  const [ingesting, setIngesting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!emails || emails.length === 0) return null;

  async function handleRoute() {
    setIngesting(true);
    setError(null);
    try {
      // Respect the 100-per-batch /ingest limit — chunk if needed.
      const chunks = [];
      for (let i = 0; i < emails.length; i += 100) chunks.push(emails.slice(i, i + 100));
      let totals = { processed: 0, tasks_created: 0, tasks_updated: 0, skipped: 0, errors: [] };
      for (const chunk of chunks) {
        const r = await ingestEmails(chunk);
        totals.processed += r.processed;
        totals.tasks_created += r.tasks_created;
        totals.tasks_updated += r.tasks_updated;
        totals.skipped += r.skipped;
        totals.errors.push(...r.errors);
      }
      setResult(totals);
      onIngested?.(totals);
    } catch (e) {
      setError(e.message);
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <h3>2. Raw batch — {emails.length} emails (before any routing)</h3>
      <div style={{ maxHeight: 300, overflow: "auto", border: "1px solid #ddd" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead style={{ position: "sticky", top: 0, background: "#eee" }}>
            <tr>
              {["from_name", "from_email", "subject", "received_at", "thread_id", "body preview"].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: 6, borderBottom: "1px solid #ccc" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {emails.map((e) => (
              <tr key={e.email_id} style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: 6 }}>{e.from_name}</td>
                <td style={{ padding: 6 }}>{e.from_email}</td>
                <td style={{ padding: 6 }}>{e.subject}</td>
                <td style={{ padding: 6 }}>{e.received_at}</td>
                <td style={{ padding: 6 }}>{e.thread_id}</td>
                <td style={{ padding: 6, color: "#666" }}>{truncate(e.body, 60)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 8 }}>
        <button onClick={handleRoute} disabled={ingesting}>
          {ingesting ? "Routing…" : "Route this batch"}
        </button>
      </div>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {result && (
        <p style={{ fontSize: 13 }}>
          Processed {result.processed} · Created {result.tasks_created} · Updated {result.tasks_updated} ·
          Skipped {result.skipped} · Errors {result.errors.length}
        </p>
      )}
    </div>
  );
}