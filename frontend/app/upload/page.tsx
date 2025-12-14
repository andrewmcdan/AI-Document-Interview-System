"use client";

import { FormEvent, useMemo, useState, useEffect } from "react";
import { getJson, type ApiConfig } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type IngestionJob = {
  id: string;
  document_id: string;
  status: string;
  error?: string | null;
  created_at?: string;
  started_at?: string;
  finished_at?: string;
};

type UploadItem = {
  file: File;
  title: string;
  description: string;
};

export default function UploadPage() {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { auth } = useAuth();
  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      token: auth.token,
      devUserId: auth.devUserId,
    }),
    [auth]
  );

  const onFilesSelected = (fileList: FileList | null) => {
    const selected = Array.from(fileList ?? []);
    setItems((prev) =>
      selected.map((file) => {
        const found = prev.find((p) => p.file.name === file.name && p.file.size === file.size);
        return {
          file,
          title: found?.title || "",
          description: found?.description || "",
        };
      })
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!items.length) {
      setError("Select at least one file.");
      return;
    }
    setLoading(true);
    setError(null);
    setJobs([]);

    const headers: Record<string, string> = {};
    if (config.token) headers["Authorization"] = `Bearer ${config.token}`;
    if (!config.token && config.devUserId) headers["X-User-Id"] = config.devUserId;

    try {
      const created: IngestionJob[] = [];
      for (const item of items) {
        const form = new FormData();
        form.append("title", item.title || item.file.name);
        if (item.description) form.append("description", item.description);
        form.append("file", item.file);

        const res = await fetch(`${config.baseUrl}/documents`, {
          method: "POST",
          body: form,
          headers,
        });
        if (!res.ok) throw new Error(await res.text());
        const data: IngestionJob = await res.json();
        created.push(data);
      }
      setJobs(created);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const refreshJob = async (job: IngestionJob) => {
    try {
      const data = await getJson<{ status: string; error?: string | null; started_at?: string; finished_at?: string }>(
        config,
        `/ingestion_jobs/${job.id}/status`
      );
      setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, ...data } : j)));
    } catch (err: any) {
      setError(err.message || "Failed to refresh job");
    }
  };

  const suggestMeta = async () => {
    if (!items.length) {
      setError("Select a file first.");
      return;
    }
    setSuggesting(true);
    setError(null);
    try {
      const headers: Record<string, string> = {};
      if (config.token) headers["Authorization"] = `Bearer ${config.token}`;
      if (!config.token && config.devUserId) headers["X-User-Id"] = config.devUserId;

      const results = await Promise.all(
        items.map(async (item) => {
          const form = new FormData();
          form.append("file", item.file);
          const res = await fetch(`${config.baseUrl}/documents/describe`, {
            method: "POST",
            body: form,
            headers,
          });
          if (!res.ok) throw new Error(await res.text());
          const data: { title: string; description: string } = await res.json();
          return {
            key: item.file.name + item.file.size,
            title: data.title,
            description: data.description,
          };
        })
      );

      setItems((prev) =>
        prev.map((item) => {
          const match = results.find((r) => r.key === item.file.name + item.file.size);
          if (!match) return item;
          return {
            ...item,
            title: item.title || match.title,
            description: item.description || match.description,
          };
        })
      );
    } catch (err: any) {
      setError(err.message || "Failed to suggest metadata");
    } finally {
      setSuggesting(false);
    }
  };

  // Auto-refresh active jobs
  useEffect(() => {
    const active = jobs.filter((j) => ["pending", "running"].includes(j.status));
    if (!active.length) return;
    const id = setInterval(() => {
      active.forEach((job) => refreshJob(job));
    }, 3000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobs, config.baseUrl, config.token, config.devUserId]);

  return (
    <main className="stack" style={{ gap: 16 }}>
      <div className="card stack">
        <div className="stack" style={{ gap: 6 }}>
          <p className="badge">Ingestion</p>
          <h2 className="title" style={{ margin: 0 }}>
            Upload & Jobs
          </h2>
          <p className="subtitle">Send files to the background pipeline and poll their status.</p>
        </div>
        <form className="stack" style={{ gap: 12 }} onSubmit={handleSubmit}>
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">Files</label>
            <input className="input" type="file" multiple onChange={(e) => onFilesSelected(e.target.files)} />
            {items.length > 0 && (
              <p className="subtitle" style={{ margin: 0 }}>
                {items.length} file(s) selected
              </p>
            )}
          </div>

          {items.length > 0 && (
            <div className="stack" style={{ gap: 12 }}>
              {items.map((item, idx) => (
                <div key={item.file.name + item.file.size} className="list-item stack" style={{ gap: 10 }}>
                  <div
                    className="flex"
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                  >
                    <p style={{ margin: 0, fontWeight: 600 }}>
                      {idx + 1}. {item.file.name}
                    </p>
                    <span className="pill">{(item.file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  <div className="grid two-col">
                    <div className="stack" style={{ gap: 6 }}>
                      <label className="label">Title</label>
                      <input
                        className="input"
                        value={item.title}
                        placeholder={item.file.name}
                        onChange={(e) =>
                          setItems((prev) =>
                            prev.map((p) => (p.file === item.file ? { ...p, title: e.target.value } : p))
                          )
                        }
                      />
                    </div>
                    <div className="stack" style={{ gap: 6 }}>
                      <label className="label">Description</label>
                      <input
                        className="input"
                        value={item.description}
                        onChange={(e) =>
                          setItems((prev) =>
                            prev.map((p) => (p.file === item.file ? { ...p, description: e.target.value } : p))
                          )
                        }
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={suggestMeta}
              disabled={suggesting || items.length === 0}
            >
              {suggesting ? "Thinking..." : "Suggest title & description"}
            </button>
            <button type="submit" disabled={loading} className="btn">
              {loading ? "Uploading..." : "Upload"}
            </button>
          </div>
        </form>
        {error && <p className="subtitle" style={{ color: "#fca5a5" }}>{error}</p>}
      </div>

      {jobs.length > 0 && (
        <div className="stack" style={{ gap: 10 }}>
          {jobs.map((job) => (
            <div key={job.id} className="card stack" style={{ gap: 8 }}>
              <div className="flex" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div className="stack" style={{ gap: 4 }}>
                  <p className="label">Job ID</p>
                  <p style={{ margin: 0 }}>{job.id}</p>
                  <p className="label">Document ID</p>
                  <p style={{ margin: 0 }}>{job.document_id}</p>
                </div>
                <button
                  className="btn btn-secondary"
                  onClick={() => refreshJob(job)}
                  style={{ padding: "8px 12px" }}
                >
                  Refresh
                </button>
              </div>
              <p className="badge">
                Status: <strong style={{ color: "white" }}>{job.status}</strong>
              </p>
              {job.error && <p className="subtitle" style={{ color: "#fca5a5" }}>Error: {job.error}</p>}
              {job.started_at && <p className="subtitle">Started: {job.started_at}</p>}
              {job.finished_at && <p className="subtitle">Finished: {job.finished_at}</p>}
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
