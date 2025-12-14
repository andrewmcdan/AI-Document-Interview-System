"use client";

import { FormEvent, useMemo, useState } from "react";
import { postJson, type ApiConfig } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type TokenResponse = { access_token: string; token_type: string };

export default function LoginPage() {
  const [userId, setUserId] = useState("");
  const [expires, setExpires] = useState(60);
  const [error, setError] = useState<string | null>(null);
  const { setAuth } = useAuth();

  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    }),
    []
  );

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const data = await postJson<TokenResponse>(config, "/auth/login", {
        user_id: userId,
        expires_in_minutes: expires,
      });
      setAuth({ token: data.access_token, devUserId: undefined });
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  };

  return (
    <main className="stack" style={{ gap: 16 }}>
      <div className="card stack">
        <div className="stack" style={{ gap: 6 }}>
          <p className="badge">Auth</p>
          <h2 className="title" style={{ margin: 0 }}>
            Login (Demo JWT)
          </h2>
          <p className="subtitle">
            Issues a JWT using the backend secret. For dev/testing only.
          </p>
        </div>
        <form className="stack" style={{ gap: 12 }} onSubmit={handleSubmit}>
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">User ID</label>
            <input
              className="input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="user-123"
              required
            />
          </div>
          <div className="stack" style={{ gap: 6 }}>
            <label className="label">Expires in minutes</label>
            <input
              type="number"
              min={5}
              max={1440}
              className="input"
              value={expires}
              onChange={(e) => setExpires(Number(e.target.value))}
            />
          </div>
          <div className="flex" style={{ display: "flex", gap: 10 }}>
            <button type="submit" className="btn">
              Get token
            </button>
          </div>
        </form>
        {error && <p className="subtitle" style={{ color: "#fca5a5" }}>{error}</p>}
      </div>
    </main>
  );
}
