import React from 'react';
import { useState } from "react";
import { generateSampleEmails } from "../api.js";

export default function EmailInput({ onBatchReady }) {
  const [raw, setRaw] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleParse() {
    setError(null);
    try {
      const parsed = JSON.parse(raw);
      const emails = Array.isArray(parsed) ? parsed : parsed.emails;
      if (!Array.isArray(emails)) throw new Error("Expected a JSON array of emails, or {emails: [...]}");
      onBatchReady(emails);
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const { emails } = await generateSampleEmails(250);
      setRaw(JSON.stringify(emails, null, 2));
      onBatchReady(emails);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setRaw(reader.result);
    reader.readAsText(file);
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <h3>1. Paste or upload a batch of emails</h3>
      <textarea
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        placeholder='[{"email_id": "em_00142", "thread_id": "th_0091", ...}]'
        rows={10}
        style={{ width: "100%", fontFamily: "monospace", fontSize: 12, boxSizing: "border-box" }}
      />
      <div style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center" }}>
        <input type="file" accept=".json" onChange={handleFile} />
        <button onClick={handleParse}>Load batch</button>
        <button onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating…" : "Generate 250 sample emails"}
        </button>
      </div>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}