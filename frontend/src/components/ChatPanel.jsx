import React from 'react';
import { useState } from "react";
import { askChat } from "../api.js";

const SAMPLE_QUESTIONS = [
  "How many emails were proposal or RFP related?",
  "How many were marketing versus actual spam we correctly ignored?",
  "Show me everything sitting in triage and why.",
  "What's our spurious rate so far?",
  "Which tasks are high priority but low confidence?",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(query) {
    if (!query.trim()) return;
    setMessages((m) => [...m, { role: "user", text: query }]);
    setInput("");
    setLoading(true);
    try {
      const { answer, supporting_data } = await askChat(query);
      setMessages((m) => [...m, { role: "assistant", text: answer, supporting_data }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h3>3. Ask about this batch</h3>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
        {SAMPLE_QUESTIONS.map((q) => (
          <button key={q} onClick={() => send(q)} style={{ fontSize: 12 }}>{q}</button>
        ))}
      </div>
      <div style={{ border: "1px solid #ddd", minHeight: 200, maxHeight: 320, overflow: "auto", padding: 8 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <strong>{m.role === "user" ? "You" : "System"}:</strong> {m.text}
            {m.supporting_data && Object.keys(m.supporting_data).length > 0 && (
              <pre style={{ background: "#f3f3f3", fontSize: 11, padding: 6, marginTop: 4 }}>
                {JSON.stringify(m.supporting_data, null, 2)}
              </pre>
            )}
          </div>
        ))}
        {loading && <p style={{ color: "#888" }}>Thinking…</p>}
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Ask a question about this batch…"
          style={{ flex: 1, padding: 6 }}
        />
        <button onClick={() => send(input)}>Send</button>
      </div>
    </div>
  );
}