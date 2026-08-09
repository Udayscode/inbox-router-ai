import React from 'react';
import { useState } from "react";
import EmailInput from "./EmailInput.jsx";
import EmailTable from "./EmailTable.jsx";
import ChatPanel from "./ChatPanel.jsx";

export default function App() {
  const [emails, setEmails] = useState([]);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: 24 }}>
      <h1 style={{ fontSize: 22 }}>Sales Inbox → Task Router</h1>
      <EmailInput onBatchReady={setEmails} />
      <EmailTable emails={emails} />
      <ChatPanel />
    </div>
  );
}