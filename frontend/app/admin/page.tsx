"use client";

import { useMemo, useState } from "react";
import { postJson, type ApiConfig } from "../../lib/api";
import { useAuth } from "../../lib/auth";

export default function AdminPage() {
  const { auth } = useAuth();
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      token: auth.token,
      devUserId: auth.devUserId,
    }),
    [auth]
  );

  const handleReset = async () => {
    setLoading(true);
    setError(null);
    setStatus(null);
    try {
      const res = await postJson<{ status: string }>(config, "/admin/reset", {});
      setStatus(res.status);
    } catch (err: any) {
      setError(err.message || "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="stack" style={{ gap: 16 }}>
      <div className="card stack">
        <div className="stack" style={{ gap: 6 }}>
          <p className="badge">Danger (dev)</p>
          <h2 className="title" style={{ margin: 0 }}>
            Admin Reset
          </h2>
          <p className="subtitle">
            Dev-only purge of documents, chunks, conversations, query logs, vector store, and object storage. Works only in development/test.
          </p>
        </div>
        <div className="flex" style={{ display: "flex", gap: 10 }}>
          <button
            onClick={handleReset}
            disabled={loading}
            className="btn"
            style={{ background: "linear-gradient(135deg, #f87171, #ef4444)", color: "#0b1021" }}
          >
            {loading ? "Resetting..." : "Purge all data"}
          </button>
        </div>
        {status && <p className="subtitle" style={{ color: "#86efac" }}>{status}</p>}
        {error && <p className="subtitle" style={{ color: "#fca5a5" }}>{error}</p>}
      </div>
    </main>
  );
}
