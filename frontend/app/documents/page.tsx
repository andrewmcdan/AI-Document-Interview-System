"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchDocuments, type ApiConfig } from "../../lib/api";

type Doc = {
  id: string;
  title: string;
  description?: string | null;
  created_at?: string | null;
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [token, setToken] = useState("");
  const [devUserId, setDevUserId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      token: token || undefined,
      devUserId: devUserId || undefined,
    }),
    [token, devUserId]
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
    <main className="space-y-4">
      <h2 className="text-xl font-semibold">Documents</h2>
      <div className="space-y-3 border p-3 rounded bg-white">
        <div>
          <label className="block text-sm font-medium">JWT (or leave blank if using dev header)</label>
          <input
            className="w-full border rounded px-2 py-1"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Bearer token"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Dev User Id (only if JWT not set)</label>
          <input
            className="w-full border rounded px-2 py-1"
            value={devUserId}
            onChange={(e) => setDevUserId(e.target.value)}
            placeholder="user-123"
          />
        </div>
        <button
          className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
          onClick={loadDocs}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </div>

      <div className="space-y-2">
        {docs.length === 0 && <p className="text-sm text-slate-600">No documents found.</p>}
        {docs.map((doc) => (
          <div key={doc.id} className="border p-3 rounded bg-white">
            <p className="font-medium">{doc.title}</p>
            {doc.description && <p className="text-sm text-slate-700">{doc.description}</p>}
            <p className="text-xs text-slate-500">ID: {doc.id}</p>
            {doc.created_at && <p className="text-xs text-slate-500">Created: {doc.created_at}</p>}
          </div>
        ))}
      </div>
    </main>
  );
}
