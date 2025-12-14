"use client";

import { FormEvent, useMemo, useState } from "react";
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

export default function UploadPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<IngestionJob | null>(null);
  const [loading, setLoading] = useState(false);
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

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Select a file.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const form = new FormData();
      form.append("title", title || file.name);
      if (description) form.append("description", description);
      form.append("file", file);

      const headers: Record<string, string> = {};
      if (config.token) headers["Authorization"] = `Bearer ${config.token}`;
      if (!config.token && config.devUserId) headers["X-User-Id"] = config.devUserId;

      const res = await fetch(`${config.baseUrl}/documents`, {
        method: "POST",
        body: form,
        headers,
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data: IngestionJob = await res.json();
      setJob(data);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const refreshJob = async () => {
    if (!job) return;
    try {
      const data = await getJson<{ status: string; error?: string | null; started_at?: string; finished_at?: string }>(
        config,
        `/ingestion_jobs/${job.id}/status`
      );
      setJob({ ...job, ...data });
    } catch (err: any) {
      setError(err.message || "Failed to refresh job");
    }
  };

  return (
    <main className="space-y-4">
      <h2 className="text-xl font-semibold">Upload & Jobs</h2>
      <form className="space-y-3" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm font-medium">Title</label>
          <input className="w-full border rounded px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium">Description</label>
          <input
            className="w-full border rounded px-2 py-1"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">File</label>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {job && (
        <div className="border p-3 rounded bg-white space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Job ID: {job.id}</p>
              <p className="text-sm">Document ID: {job.document_id}</p>
            </div>
            <button className="px-2 py-1 border rounded text-sm" onClick={refreshJob}>
              Refresh status
            </button>
          </div>
          <p className="text-sm">
            Status: <strong>{job.status}</strong>
          </p>
          {job.error && <p className="text-sm text-red-600">Error: {job.error}</p>}
          {job.started_at && <p className="text-xs text-slate-600">Started: {job.started_at}</p>}
          {job.finished_at && <p className="text-xs text-slate-600">Finished: {job.finished_at}</p>}
        </div>
      )}
    </main>
  );
}
