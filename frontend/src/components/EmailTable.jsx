import React, { useState } from 'react';
import { ingestEmails } from '../api.js';

const card = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  boxShadow: 'var(--shadow)',
  marginBottom: 20,
  overflow: 'hidden',
};

const COLS = ['from_name', 'from_email', 'subject', 'received_at', 'thread_id', 'body preview'];

function truncate(text, n = 60) {
  if (!text) return '';
  return text.length > n ? text.slice(0, n) + '…' : text;
}

function fmt(dateStr) {
  try {
    return new Date(dateStr).toLocaleString('en-IN', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch { return dateStr; }
}
export default function EmailTable({ emails, batchNumber = 1, onIngested }) {
  const [ingesting, setIngesting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  const [emailsInCurrentChunk, setEmailsInCurrentChunk] = useState(0);
  const [processedInCurrentChunk, setProcessedInCurrentChunk] = useState(0);

  if (!emails || emails.length === 0) return null;

  async function handleRoute() {
    setIngesting(true);
    setError(null);
    setResult(null);

    // Render's free tier has a 100-second request timeout limit.
    // 20 emails * 4.1s sleep = 82s max per request (safely under 100s).
    // This chunks the emails into batches to never timeout or trigger 429 rate limit exceptions.
    const CHUNK_SIZE = 20;
    const chunks = [];
    for (let i = 0; i < emails.length; i += CHUNK_SIZE) {
      chunks.push(emails.slice(i, i + CHUNK_SIZE));
    }
    setTotalChunks(chunks.length);

    let totals = { processed: 0, tasks_created: 0, tasks_updated: 0, skipped: 0, errors: [] };

    try {
      for (let idx = 0; idx < chunks.length; idx++) {
        setCurrentChunk(idx + 1);
        const chunk = chunks[idx];
        setEmailsInCurrentChunk(chunk.length);
        setProcessedInCurrentChunk(0);

        // Start a timer that ticks to simulate email-by-email progress within this chunk
        // since the backend sleeps 4.1s between Gemini classifications.
        const timer = setInterval(() => {
          setProcessedInCurrentChunk(prev => {
            if (prev < chunk.length) {
              return prev + 1;
            }
            return prev;
          });
        }, 4200);

        try {
          const r = await ingestEmails(chunk);
          clearInterval(timer);
          setProcessedInCurrentChunk(chunk.length); // complete the chunk

          totals.processed += r.processed;
          totals.tasks_created += r.tasks_created;
          totals.tasks_updated += r.tasks_updated;
          totals.skipped += r.skipped;
          totals.errors.push(...r.errors);

          // Update progress intermediate result
          setResult({ ...totals });
        } catch (err) {
          clearInterval(timer);
          throw err;
        }
      }
      onIngested?.(totals);
    } catch (e) {
      setError(e.message);
    } finally {
      setIngesting(false);
      setCurrentChunk(0);
      setEmailsInCurrentChunk(0);
      setProcessedInCurrentChunk(0);
    }
  }
  return (
    <div style={card}>
      {/* Card header */}
      <div style={{
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)',
        flexWrap: 'wrap',
        gap: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <StepBadge n={2} />
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>Raw batch preview</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              {emails.length} emails — before any routing
            </div>
          </div>
        </div>

        <button
          onClick={handleRoute}
          disabled={ingesting}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 18px',
            borderRadius: 8,
            border: '1px solid transparent',
            background: ingesting ? 'var(--text-tertiary)' : 'var(--text-primary)',
            color: '#fff',
            fontSize: 13,
            fontWeight: 500,
            cursor: ingesting ? 'default' : 'pointer',
            fontFamily: 'inherit',
            transition: 'background 0.15s',
          }}
        >
          {ingesting ? (
            <><Spinner />Routing…</>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
              Route this batch
            </>
          )}
        </button>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', maxHeight: 320, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
          <thead>
            <tr style={{ background: 'var(--surface-2)', position: 'sticky', top: 0, zIndex: 1 }}>
              {COLS.map((h) => (
                <th key={h} style={{
                  padding: '8px 14px',
                  textAlign: 'left',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  borderBottom: '1px solid var(--border)',
                  whiteSpace: 'nowrap',
                  letterSpacing: '0.01em',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {emails.map((e, idx) => (
              <tr key={e.email_id} style={{
                borderBottom: '1px solid var(--border)',
                background: idx % 2 === 0 ? 'var(--surface)' : 'var(--surface-2)',
                transition: 'background 0.1s',
              }}
                onMouseEnter={ev => ev.currentTarget.style.background = 'var(--accent-light)'}
                onMouseLeave={ev => ev.currentTarget.style.background = idx % 2 === 0 ? 'var(--surface)' : 'var(--surface-2)'}
              >
                <td style={{ padding: '7px 14px', fontWeight: 500 }}>{e.from_name}</td>
                <td style={{ padding: '7px 14px', color: 'var(--text-secondary)' }}>{e.from_email}</td>
                <td style={{ padding: '7px 14px' }}>{e.subject}</td>
                <td style={{ padding: '7px 14px', color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{fmt(e.received_at)}</td>
                <td style={{ padding: '7px 14px', fontFamily: 'monospace', fontSize: 11, color: 'var(--text-secondary)' }}>{e.thread_id}</td>
                <td style={{ padding: '7px 14px', color: 'var(--text-tertiary)', maxWidth: 200 }}>{truncate(e.body, 55)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer with results or progress */}
      {(error || result || ingesting) && (
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', background: 'var(--surface-2)' }}>
          {error && (
            <div style={{ color: 'var(--red)', fontSize: 13, marginBottom: 10 }}>{error}</div>
          )}

          {/* Active Ingest Progress Bar */}
          {ingesting && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                <span>Email <strong>{processedInCurrentChunk}</strong> of <strong>Batch {currentChunk}</strong></span>
                <span>{Math.round((processedInCurrentChunk / (emailsInCurrentChunk || 1)) * 100)}% ({processedInCurrentChunk}/{emailsInCurrentChunk})</span>
              </div>
              <div style={{
                height: 6,
                background: 'var(--border)',
                borderRadius: 3,
                overflow: 'hidden',
                position: 'relative'
              }}>
                <div style={{
                  height: '100%',
                  width: `${(processedInCurrentChunk / (emailsInCurrentChunk || 1)) * 100}%`,
                  background: 'var(--accent)',
                  borderRadius: 3,
                  transition: 'width 0.4s ease',
                }} />
              </div>
              <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                Pacing requests to respect Gemini API rate limits (15 RPM) and prevent server timeouts. Please keep this tab open.
              </div>
            </div>
          )}

          {result && (
            <div>
              <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                <Stat label="Processed" value={result.processed} />
                <Stat label="Created" value={result.tasks_created} color="var(--green)" />
                <Stat label="Updated" value={result.tasks_updated} color="var(--accent)" />
                <Stat label="Skipped" value={result.skipped} color="var(--text-secondary)" />
                <Stat label="Errors" value={result.errors.length} color={result.errors.length > 0 ? 'var(--orange)' : undefined} />
              </div>

              {/* Stats Descriptions Legend */}
              <div style={{
                marginTop: 14,
                paddingTop: 12,
                borderTop: '1px dashed var(--border)',
                marginBottom: 16,
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: 12,
                fontSize: 11,
                color: 'var(--text-secondary)',
                lineHeight: 1.4,
              }}>
                <div><strong>Processed:</strong> Total batch size loaded.</div>
                <div><strong style={{ color: 'var(--green)' }}>Created:</strong> New tasks added to database.</div>
                <div><strong style={{ color: 'var(--accent)' }}>Updated:</strong> Thread replies mapped to existing tasks.</div>
                <div><strong style={{ color: 'var(--text-secondary)' }}>Skipped:</strong> Non-actionable OOO, spam and news ignored.</div>
              </div>

              {/* Categorized errors */}
              {result.errors.filter(e => /429|ResourceExhausted|quota/i.test(e.error)).length > 0 && (
                <div style={{
                  background: 'rgba(255,149,0,0.06)',
                  border: '1px solid rgba(255,149,0,0.2)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  marginBottom: 12,
                  fontSize: 13,
                  color: 'var(--text-primary)',
                  lineHeight: 1.5,
                }}>
                  <div style={{ fontWeight: 600, color: 'var(--orange)', marginBottom: 4 }}>
                    ⚠️ Gemini API Rate Limit Exceeded (429)
                  </div>
                  <div>
                    {result.errors.filter(e => /429|ResourceExhausted|quota/i.test(e.error)).length} email(s) failed ingestion because of Gemini API rate limits (15 RPM free tier). The backend automatically retries with exponential backoff, but if your quota has been completely exhausted for the day, some emails will fail.
                  </div>
                </div>
              )}

              {result.errors.filter(e => /API_KEY_INVALID|API key|unauthorized/i.test(e.error)).length > 0 && (
                <div style={{
                  background: 'rgba(255,59,48,0.06)',
                  border: '1px solid rgba(255,59,48,0.2)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  marginBottom: 12,
                  fontSize: 13,
                  color: 'var(--text-primary)',
                  lineHeight: 1.5,
                }}>
                  <div style={{ fontWeight: 600, color: 'var(--red)', marginBottom: 4 }}>
                    ⚠️ Invalid or Missing Gemini API Key
                  </div>
                  <div>
                    {result.errors.filter(e => /API_KEY_INVALID|API key|unauthorized/i.test(e.error)).length} email(s) failed because the Gemini API key was unauthorized or invalid. Please configure the correct <code>GEMINI_API_KEY</code> environment variable on your backend server.
                  </div>
                </div>
              )}

              {result.errors.filter(e => !/429|ResourceExhausted|quota|API_KEY_INVALID|API key|unauthorized/i.test(e.error)).length > 0 && (
                <div style={{
                  background: 'rgba(29,29,31,0.03)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  fontSize: 13,
                  color: 'var(--text-primary)',
                }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    Other Processing Failures ({result.errors.filter(e => !/429|ResourceExhausted|quota|API_KEY_INVALID|API key|unauthorized/i.test(e.error)).length})
                  </div>
                  <div style={{ maxHeight: 120, overflowY: 'auto', fontSize: 12, fontFamily: 'monospace', display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {result.errors.filter(e => !/429|ResourceExhausted|quota|API_KEY_INVALID|API key|unauthorized/i.test(e.error)).map((e, idx) => (
                      <div key={idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.04)', paddingBottom: 4 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>[{e.email_id}]:</span> {e.error}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</span>
      <span style={{ fontSize: 18, fontWeight: 600, color: color || 'var(--text-primary)', letterSpacing: '-0.02em' }}>{value}</span>
    </div>
  );
}

function StepBadge({ n }) {
  return (
    <div style={{
      width: 26, height: 26, borderRadius: '50%',
      background: 'var(--text-primary)', color: '#fff',
      fontSize: 12, fontWeight: 600,
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    }}>{n}</div>
  );
}

function Spinner() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      style={{ animation: 'spin 0.8s linear infinite', marginRight: 4 }}>
      <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}