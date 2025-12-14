"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchDocuments, type ApiConfig } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type Doc = {
  id: string;
  title: string;
  description?: string | null;
  created_at?: string | null;
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { auth, setAuth } = useAuth();

  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      token: auth.token,
      devUserId: auth.devUserId,
    }),
    [auth]
  );

  const loadDocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDocuments(config);
      setDocs(data);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="stack" style={{ gap: 16 }}>
      <div className="card stack">
        <div className="stack" style={{ gap: 6 }}>
          <p className="badge">Library</p>
          <h2 className="title" style={{ margin: 0 }}>
            Documents
          </h2>
          <p className="subtitle">Browse your ingested files, IDs, and descriptions.</p>
        </div>
        <div className="grid two-col">
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">JWT (or leave blank if using dev header)</label>
            <input
              className="input"
              value={auth.token || ""}
              onChange={(e) => setAuth({ ...auth, token: e.target.value })}
              placeholder="Bearer token"
            />
          </div>
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">Dev User Id (only if JWT not set)</label>
            <input
              className="input"
              value={auth.devUserId || ""}
              onChange={(e) => setAuth({ ...auth, devUserId: e.target.value })}
              placeholder="user-123"
            />
          </div>
        </div>
        <div className="flex" style={{ display: "flex", gap: 10 }}>
          <button className="btn" onClick={loadDocs} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
        {error && <p className="subtitle" style={{ color: "#fca5a5" }}>{error}</p>}
      </div>

      <div className="list">
        {docs.length === 0 && <p className="subtitle">No documents found.</p>}
        {docs.map((doc) => (
          <div key={doc.id} className="list-item stack" style={{ gap: 6 }}>
            <p style={{ margin: 0, fontWeight: 600 }}>{doc.title}</p>
            {doc.description && <p className="subtitle" style={{ margin: 0 }}>{doc.description}</p>}
            <p className="subtitle" style={{ margin: 0, fontSize: 12 }}>ID: {doc.id}</p>
            {doc.created_at && <p className="subtitle" style={{ margin: 0, fontSize: 12 }}>Created: {doc.created_at}</p>}
          </div>
        ))}
      </div>
    </main>
  );
}
