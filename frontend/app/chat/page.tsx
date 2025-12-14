"use client";

import { FormEvent, useMemo, useState } from "react";
import { postJson, type ApiConfig, fetchDocuments } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type AnswerSource = {
  document_id: string;
  document_title?: string | null;
  chunk_id: string;
  score?: number | null;
  metadata?: Record<string, any>;
};

type QueryResponse = {
  answer: string;
  sources: AnswerSource[];
  generated_at: string;
};

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [docIds, setDocIds] = useState<string[]>([]);
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [docs, setDocs] = useState<{ id: string; title: string }[]>([]);

  const { auth } = useAuth();
  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      token: auth.token,
      devUserId: auth.devUserId,
    }),
    [auth]
  );

  const loadDocs = async () => {
    try {
      const data = await fetchDocuments(config);
      setDocs(data);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload: any = { question, top_k: 5 };
      if (docIds.length) {
        payload.document_ids = docIds;
      }
      const data = await postJson<QueryResponse>(config, "/query", payload);
      setAnswer(data);
    } catch (err: any) {
      setError(err.message || "Query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="space-y-4">
      <h2 className="text-xl font-semibold">Chat & Query</h2>
      <form className="space-y-3" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm font-medium">Question</label>
          <textarea
            className="w-full border rounded px-2 py-1"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Restrict to documents (optional)</label>
          <div className="space-y-1">
            <button
              type="button"
              onClick={loadDocs}
              className="px-2 py-1 border rounded text-sm bg-white"
              disabled={loading}
            >
              Load my documents
            </button>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {docs.map((d) => (
                <label key={d.id} className="flex items-center gap-2 border rounded p-2 bg-white">
                  <input
                    type="checkbox"
                    checked={docIds.includes(d.id)}
                    onChange={(e) => {
                      if (e.target.checked) setDocIds([...docIds, d.id]);
                      else setDocIds(docIds.filter((x) => x !== d.id));
                    }}
                  />
                  <span className="text-sm">{d.title}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {answer && (
        <div className="border p-3 rounded bg-white space-y-3">
          <p className="font-medium">Answer</p>
          <p className="whitespace-pre-wrap text-sm">{answer.answer}</p>
          <div>
            <p className="font-medium text-sm">Sources</p>
            <ul className="text-sm space-y-1">
              {answer.sources.map((s, idx) => (
                <li key={s.chunk_id || idx}>
                  [{idx + 1}] {s.document_title || s.document_id} (score: {s.score?.toFixed(3) ?? "n/a"})
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-slate-600">Generated at: {answer.generated_at}</p>
        </div>
      )}
    </main>
  );
}
