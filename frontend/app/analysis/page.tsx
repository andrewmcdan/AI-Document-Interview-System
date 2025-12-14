"use client";

import { useEffect, useMemo, useState } from "react";
import { getJson, postJson, type ApiConfig, fetchDocuments } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { Markdown } from "../../components/Markdown";

type AnalysisJob = {
  id: string;
  status: string;
  task_type: string;
  question?: string | null;
  document_ids?: string[] | null;
  result?: any;
  error?: string | null;
  created_at?: string;
  started_at?: string;
  finished_at?: string;
};

export default function AnalysisPage() {
  const { auth } = useAuth();
  const [docIds, setDocIds] = useState<string[]>([]);
  const [docs, setDocs] = useState<{ id: string; title: string }[]>([]);
  const [question, setQuestion] = useState("");
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const loadJobs = async () => {
    try {
      const data = await getJson<AnalysisJob[]>(config, "/analysis");
      setJobs(data);
    } catch (err: any) {
      setError(err.message || "Failed to load analysis jobs");
    }
  };

  useEffect(() => {
    if (config.token || config.devUserId) {
      loadDocs();
      loadJobs();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.token, config.devUserId]);

  const startJob = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: any = { task_type: "summary", question: question || null };
      if (docIds.length) payload.document_ids = docIds;
      const job = await postJson<AnalysisJob>(config, "/analysis", payload);
      setJobs((prev) => [job, ...prev]);
    } catch (err: any) {
      setError(err.message || "Failed to start analysis");
    } finally {
      setLoading(false);
    }
  };

  const pollJob = async (jobId: string) => {
    try {
      const job = await getJson<AnalysisJob>(config, `/analysis/${jobId}`);
      setJobs((prev) => prev.map((j) => (j.id === job.id ? job : j)));
    } catch (err: any) {
      setError(err.message || "Failed to refresh job");
    }
  };

  return (
    <main className="stack" style={{ gap: 16 }}>
      <div className="card stack">
        <p className="badge">Analysis</p>
        <h2 className="title" style={{ margin: 0 }}>
          Deep Analysis
        </h2>
        <p className="subtitle">Run background analysis across documents to find common themes.</p>

        <div className="stack" style={{ gap: 12 }}>
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">Question / focus</label>
            <input
              className="input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Common rules across all handbooks"
            />
          </div>
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">Documents (optional)</label>
            <div className="grid two-col">
              {docs.map((d) => (
                <label
                  key={d.id}
                  className="list-item"
                  style={{ display: "flex", gap: 10, alignItems: "flex-start" }}
                >
                  <input
                    type="checkbox"
                    checked={docIds.includes(d.id)}
                    onChange={(e) => {
                      if (e.target.checked) setDocIds([...docIds, d.id]);
                      else setDocIds(docIds.filter((x) => x !== d.id));
                    }}
                    style={{ marginTop: 4 }}
                  />
                  <div className="stack" style={{ gap: 4 }}>
                    <p style={{ margin: 0, fontWeight: 600 }}>{d.title}</p>
                    <p className="subtitle" style={{ margin: 0, fontSize: 12 }}>
                      {d.id}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>
          <div className="flex" style={{ display: "flex", gap: 10 }}>
            <button className="btn" onClick={startJob} disabled={loading}>
              {loading ? "Starting..." : "Start analysis"}
            </button>
            <button className="btn btn-secondary" onClick={loadJobs}>
              Refresh jobs
            </button>
          </div>
          {error && <p className="subtitle" style={{ color: "#fca5a5" }}>{error}</p>}
        </div>
      </div>

      <div className="stack" style={{ gap: 10 }}>
        {jobs.length === 0 && <p className="subtitle">No analysis jobs yet.</p>}
        {jobs.map((job) => (
          <div key={job.id} className="card stack" style={{ gap: 8 }}>
            <div className="flex" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div className="stack" style={{ gap: 4 }}>
                <p className="label">Job</p>
                <p style={{ margin: 0, fontWeight: 600 }}>{job.id}</p>
                <p className="subtitle" style={{ margin: 0 }}>{job.question || "No question provided"}</p>
              </div>
              <div className="pill">Status: {job.status}</div>
              <button className="btn btn-secondary" style={{ padding: "8px 12px" }} onClick={() => pollJob(job.id)}>
                Refresh
              </button>
            </div>
            {job.error && <p className="subtitle" style={{ color: "#fca5a5" }}>{job.error}</p>}
            {job.result && (
              <div className="stack" style={{ gap: 6 }}>
                <p className="label">Answer</p>
                <Markdown content={job.result.answer} />
                {job.result.themes && (
                  <div className="stack" style={{ gap: 4 }}>
                    <p className="label">Themes</p>
                    <ul className="list" style={{ margin: 0, padding: 0, listStyle: "none" }}>
                      {job.result.themes.map((t: string, idx: number) => (
                        <li key={idx} className="list-item">
                          <Markdown content={t} />
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
