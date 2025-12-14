"use client";

import { useAuth } from "../lib/auth";

export default function AuthPanel() {
  const { auth, setAuth, clear } = useAuth();

  return (
    <div className="card stack">
      <div className="stack" style={{ gap: 6 }}>
        <label className="label">JWT (Bearer token)</label>
        <input
          className="input"
          value={auth.token || ""}
          onChange={(e) => setAuth({ ...auth, token: e.target.value })}
          placeholder="eyJhbGciOi..."
        />
      </div>
      <div className="stack" style={{ gap: 6 }}>
        <label className="label">Dev User Id (only if no JWT)</label>
        <input
          className="input"
          value={auth.devUserId || ""}
          onChange={(e) => setAuth({ ...auth, devUserId: e.target.value })}
          placeholder="user-123"
        />
      </div>
      <div className="flex" style={{ display: "flex", gap: 8 }}>
        <button className="btn btn-secondary" style={{ padding: "8px 12px", borderRadius: 10 }} onClick={clear}>
          Clear
        </button>
      </div>
    </div>
  );
}
