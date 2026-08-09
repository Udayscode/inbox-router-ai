import React, { useState } from 'react';
import { generateSampleEmails } from '../api.js';

const card = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: '24px',
  boxShadow: 'var(--shadow)',
  marginBottom: 20,
};

const label = {
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: 'var(--text-secondary)',
  marginBottom: 8,
  display: 'block',
};

const btn = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  padding: '8px 16px',
  borderRadius: 8,
  border: '1px solid var(--border-strong)',
  background: 'var(--surface)',
  color: 'var(--text-primary)',
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
  fontFamily: 'inherit',
  transition: 'background 0.15s, opacity 0.15s',
  whiteSpace: 'nowrap',
};

const btnPrimary = {
  ...btn,
  background: 'var(--accent)',
  color: '#fff',
  border: '1px solid transparent',
};

export default function EmailInput({ onBatchReady }) {
  const [raw, setRaw] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleParse() {
    setError(null);
    try {
      const parsed = JSON.parse(raw);
      const emails = Array.isArray(parsed) ? parsed : parsed.emails;
      if (!Array.isArray(emails)) throw new Error('Expected a JSON array of emails, or { emails: [...] }');
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
    <div style={card}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <StepBadge n={1} />
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>Paste or upload a batch of emails</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 2 }}>
            JSON array matching the inbox schema — up to 250 emails
          </div>
        </div>
      </div>

      <span style={label}>JSON payload</span>
      <textarea
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        placeholder='[{"email_id": "em_00142", "thread_id": "th_0091", "subject": "RFP…", "body": "…"}]'
        rows={8}
        style={{
          width: '100%',
          fontFamily: '"SF Mono", ui-monospace, monospace',
          fontSize: 12,
          padding: '10px 12px',
          background: 'var(--surface-2)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-primary)',
          resize: 'vertical',
          lineHeight: 1.6,
          outline: 'none',
        }}
      />

      <div style={{ display: 'flex', gap: 8, marginTop: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* File upload styled */}
        <label style={{ ...btn, cursor: 'pointer' }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          Upload .json
          <input type="file" accept=".json" onChange={handleFile} style={{ display: 'none' }} />
        </label>

        <button style={btn} onClick={handleParse}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Load batch
        </button>

        <button style={{ ...btn, opacity: loading ? 0.6 : 1 }} onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <>
              <Spinner /> Generating…
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Generate 250 sample emails
            </>
          )}
        </button>
      </div>

      {error && (
        <div style={{
          marginTop: 10,
          padding: '8px 12px',
          background: 'rgba(255,59,48,0.06)',
          border: '1px solid rgba(255,59,48,0.2)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--red)',
          fontSize: 13,
        }}>
          {error}
        </div>
      )}
    </div>
  );
}

function StepBadge({ n }) {
  return (
    <div style={{
      width: 26,
      height: 26,
      borderRadius: '50%',
      background: 'var(--text-primary)',
      color: '#fff',
      fontSize: 12,
      fontWeight: 600,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
    }}>{n}</div>
  );
}

function Spinner() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      style={{ animation: 'spin 0.8s linear infinite' }}>
      <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    </svg>
  );
}