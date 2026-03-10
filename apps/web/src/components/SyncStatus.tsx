/**
 * Sync Status UI — shows offline queue status and manual sync trigger.
 */

import React, { useState, useEffect } from "react";
import { getQueueStatus, processQueue } from "../lib/syncWorker";

export default function SyncStatus() {
  const [status, setStatus] = useState({ pending: 0, failed: 0, syncing: 0, conflict: 0, total: 0 });
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState("");

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  async function refresh() {
    const s = await getQueueStatus();
    setStatus(s);
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const r = await processQueue();
      setResult(`✅ Synced: ${r.synced}, Failed: ${r.failed}, Conflicts: ${r.conflicts}`);
      await refresh();
    } catch (err: any) {
      setResult(`❌ Error: ${err.message}`);
    }
    setSyncing(false);
    setTimeout(() => setResult(""), 5000);
  }

  if (status.total === 0 && !result) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "16px",
        right: "16px",
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: "12px",
        padding: "16px",
        boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
        zIndex: 9000,
        minWidth: "280px",
      }}
    >
      <h4 style={{ margin: "0 0 8px", fontSize: "14px" }}>📤 Sync Queue</h4>

      <div style={{ fontSize: "13px", marginBottom: "8px" }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Pending</span><span style={{ fontWeight: 600 }}>{status.pending}</span>
        </div>
        {status.failed > 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", color: "#dc2626" }}>
            <span>Failed</span><span style={{ fontWeight: 600 }}>{status.failed}</span>
          </div>
        )}
        {status.conflict > 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", color: "#f59e0b" }}>
            <span>Conflicts</span><span style={{ fontWeight: 600 }}>{status.conflict}</span>
          </div>
        )}
      </div>

      {result && <div style={{ fontSize: "12px", marginBottom: "8px" }}>{result}</div>}

      <button
        onClick={handleSync}
        disabled={syncing || status.total === 0}
        style={{
          width: "100%",
          padding: "8px",
          background: syncing ? "#d1d5db" : "#2563eb",
          color: "#fff",
          border: "none",
          borderRadius: "8px",
          cursor: syncing ? "default" : "pointer",
          fontWeight: 600,
          fontSize: "13px",
        }}
      >
        {syncing ? "Syncing..." : "Sync Now"}
      </button>
    </div>
  );
}
