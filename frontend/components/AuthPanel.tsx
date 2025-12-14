"use client";

import { useAuth } from "../lib/auth";

export default function AuthPanel() {
  const { auth, setAuth, clear } = useAuth();

  return (
    <div className="border rounded bg-white p-3 space-y-2 min-w-[280px]">
      <div>
        <label className="block text-xs font-medium">JWT (Bearer token)</label>
        <input
          className="w-full border rounded px-2 py-1 text-xs"
          value={auth.token || ""}
          onChange={(e) => setAuth({ ...auth, token: e.target.value })}
          placeholder="eyJhbGciOi..."
        />
      </div>
      <div>
        <label className="block text-xs font-medium">Dev User Id (only if no JWT)</label>
        <input
          className="w-full border rounded px-2 py-1 text-xs"
          value={auth.devUserId || ""}
          onChange={(e) => setAuth({ ...auth, devUserId: e.target.value })}
          placeholder="user-123"
        />
      </div>
      <button className="text-xs text-blue-600 underline" onClick={clear}>
        Clear
      </button>
    </div>
  );
}
