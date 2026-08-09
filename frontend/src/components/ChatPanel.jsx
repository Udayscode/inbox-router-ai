import React, { useState, useRef, useEffect } from 'react';
import { askChat } from '../api.js';

const SAMPLE_QUESTIONS = [
  'How many emails were proposal or RFP related?',
  'Show me everything sitting in triage and why.',
  "What's our spurious rate so far?",
  'Which tasks are high priority but low confidence?',
  "What's the total deal value of all open RFPs?",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function send(query) {
    if (!query.trim() || loading) return;
    setMessages((m) => [...m, { role: 'user', text: query }]);
    setInput('');
    setLoading(true);
    try {
      const { answer, supporting_data } = await askChat(query);
      setMessages((m) => [...m, { role: 'assistant', text: answer, supporting_data }]);
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: `Error: ${e.message}`, error: true }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow)',
      overflow: 'hidden',
    }}>
      {/* Chat header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'var(--surface-2)',
      }}>
        <StepBadge n={3} />
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>Ask about this batch</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 2 }}>
            Grounded answers — backed by real query data, never hallucinated
          </div>
        </div>
      </div>

      {/* Suggestion chips */}
      <div style={{
        display: 'flex',
        gap: 6,
        flexWrap: 'wrap',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface-2)',
      }}>
        {SAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => send(q)}
            disabled={loading}
            style={{
              padding: '5px 12px',
              borderRadius: 20,
              border: '1px solid var(--border-strong)',
              background: 'var(--surface)',
              color: 'var(--text-primary)',
              fontSize: 12,
              fontWeight: 400,
              cursor: 'pointer',
              fontFamily: 'inherit',
              opacity: loading ? 0.5 : 1,
              transition: 'background 0.1s',
            }}
            onMouseEnter={e => !loading && (e.currentTarget.style.background = 'var(--accent-light)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'var(--surface)')}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div style={{
        minHeight: 200,
        maxHeight: 380,
        overflowY: 'auto',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}>
        {messages.length === 0 && (
          <div style={{
            textAlign: 'center',
            color: 'var(--text-tertiary)',
            fontSize: 13,
            paddingTop: 40,
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: 8, display: 'block', margin: '0 auto 8px' }}>
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Ask a question or pick one above
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{
            display: 'flex',
            flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
            gap: 8,
            alignItems: 'flex-start',
          }}>
            {/* Avatar */}
            <div style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: m.role === 'user' ? 'var(--accent)' : 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              fontSize: 11,
              fontWeight: 600,
              color: '#fff',
            }}>
              {m.role === 'user' ? 'You' : 'AI'}
            </div>

            <div style={{ maxWidth: '78%' }}>
              <div style={{
                padding: '10px 14px',
                borderRadius: m.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
                background: m.role === 'user' ? 'var(--accent)' : 'var(--surface-2)',
                border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                color: m.role === 'user' ? '#fff' : (m.error ? 'var(--red)' : 'var(--text-primary)'),
                fontSize: 13.5,
                lineHeight: 1.55,
              }}>
                {m.text}
              </div>

              {m.supporting_data && Object.keys(m.supporting_data).length > 0 && (
                <pre style={{
                  marginTop: 6,
                  padding: '8px 12px',
                  background: 'var(--surface-2)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 11.5,
                  fontFamily: '"SF Mono", ui-monospace, monospace',
                  color: 'var(--text-secondary)',
                  overflowX: 'auto',
                  lineHeight: 1.6,
                }}>
                  {JSON.stringify(m.supporting_data, null, 2)}
                </pre>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: 'var(--text-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, fontSize: 11, fontWeight: 600, color: '#fff',
            }}>AI</div>
            <div style={{
              padding: '10px 16px',
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              borderRadius: '12px 12px 12px 4px',
              color: 'var(--text-secondary)',
              fontSize: 13,
            }}>
              <TypingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        gap: 8,
        background: 'var(--surface-2)',
      }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send(input)}
          placeholder="Ask a question about this batch…"
          disabled={loading}
          style={{
            flex: 1,
            padding: '9px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-strong)',
            background: 'var(--surface)',
            color: 'var(--text-primary)',
            fontSize: 13.5,
            fontFamily: 'inherit',
            outline: 'none',
          }}
        />
        <button
          onClick={() => send(input)}
          disabled={loading || !input.trim()}
          style={{
            padding: '9px 16px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background: input.trim() && !loading ? 'var(--accent)' : 'var(--text-tertiary)',
            color: '#fff',
            fontSize: 13,
            fontWeight: 500,
            cursor: input.trim() && !loading ? 'pointer' : 'default',
            fontFamily: 'inherit',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            transition: 'background 0.15s',
            whiteSpace: 'nowrap',
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          Send
        </button>
      </div>
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

function TypingDots() {
  return (
    <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
      <style>{`
        @keyframes blink { 0%,80%,100% { opacity:0.2 } 40% { opacity:1 } }
        .dot { width:5px; height:5px; border-radius:50%; background:var(--text-tertiary); animation: blink 1.2s infinite; }
        .dot:nth-child(2) { animation-delay:0.2s }
        .dot:nth-child(3) { animation-delay:0.4s }
      `}</style>
      <span className="dot" /><span className="dot" /><span className="dot" />
    </span>
  );
}