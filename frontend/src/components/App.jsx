import React, { useState, useRef, useEffect } from 'react';
import EmailInput from './EmailInput.jsx';
import EmailTable from './EmailTable.jsx';
import ChatPanel from './ChatPanel.jsx';
import { BACKEND_URL } from '../api.js';

export default function App() {
  const [emails, setEmails] = useState([]);
  const [routed, setRouted] = useState(false);
  const [batchNumber, setBatchNumber] = useState(1);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'online' | 'offline'
  const [retrySecs, setRetrySecs] = useState(5);
  const chatRef = useRef(null);

  useEffect(() => {
    let countdownTimer;

    async function checkHealth() {
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        if (res.ok) {
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      } catch (err) {
        setBackendStatus('offline');
      }
    }

    if (backendStatus === 'checking') {
      checkHealth();
    } else if (backendStatus === 'offline') {
      setRetrySecs(5);
      countdownTimer = setInterval(() => {
        setRetrySecs((prev) => {
          if (prev <= 1) {
            clearInterval(countdownTimer);
            setBackendStatus('checking');
            return 5;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      clearInterval(countdownTimer);
    };
  }, [backendStatus]);

  function handleBatchReady(emails) {
    setEmails(emails);
    setRouted(false);
  }

  function handleIngested() {
    setRouted(true);
    setBatchNumber(prev => prev + 1);
    setTimeout(() => chatRef.current?.scrollIntoView({ behavior: 'smooth' }), 300);
  }

  return (
    <div>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 40,
        paddingBottom: 24,
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: 9,
            background: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 1.27h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.41a16 16 0 0 0 5.68 5.68l.91-.91a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7a2 2 0 0 1 1.72 2.03z"/>
            </svg>
          </div>
          <div>
            <h1 style={{ fontSize: 17, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
              Sales Inbox Router
            </h1>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
              Alumnx AI Labs · Powered by Gemini
            </p>
          </div>
        </div>

        {/* Live status badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: backendStatus === 'online' ? 'var(--green)' : (backendStatus === 'checking' ? 'var(--orange)' : 'var(--red)'),
            display: 'inline-block',
            animation: backendStatus === 'checking' ? 'pulse 1.2s infinite' : 'none'
          }} />
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
            {backendStatus === 'online' ? 'Connected' : (backendStatus === 'checking' ? 'Connecting...' : 'Offline')}
          </span>
          <style>{`
            @keyframes pulse {
              0% { opacity: 0.3; }
              50% { opacity: 1; }
              100% { opacity: 0.3; }
            }
          `}</style>
        </div>
      </header>

      {backendStatus === 'online' ? (
        <>
          <EmailInput onBatchReady={handleBatchReady} />
          {emails.length > 0 && <EmailTable emails={emails} batchNumber={batchNumber} onIngested={handleIngested} />}
          {routed && <div ref={chatRef}><ChatPanel /></div>}
        </>
      ) : (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          boxShadow: 'var(--shadow)',
          padding: '40px 24px',
          textAlign: 'center',
          maxWidth: 480,
          margin: '40px auto 0',
        }}>
          {backendStatus === 'checking' ? (
            <div>
              <Spinner large />
              <div style={{ fontWeight: 600, fontSize: 15, marginTop: 16 }}>Connecting to backend service...</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 6 }}>
                Establishing secure connection
              </div>
            </div>
          ) : (
            <div>
              <div style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: 'rgba(255,59,48,0.06)',
                border: '1px solid rgba(255,59,48,0.15)',
                color: 'var(--red)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
              }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Backend Offline</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 8, marginBottom: 20, lineHeight: 1.5 }}>
                Could not establish connection to the server. Render free-tier databases and web services spin down after inactivity and can take up to 50 seconds to boot.
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  Retrying in <strong>{retrySecs}s</strong>...
                </span>
                <button
                  onClick={() => setBackendStatus('checking')}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-strong)',
                    background: 'var(--surface)',
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  Check Now
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Spinner({ large }) {
  const size = large ? 24 : 13;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      style={{ animation: 'spin 0.8s linear infinite', margin: '0 auto' }}>
      <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    </svg>
  );
}