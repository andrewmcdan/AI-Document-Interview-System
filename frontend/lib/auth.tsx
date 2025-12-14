"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type AuthState = {
  token?: string;
  devUserId?: string;
};

type AuthContextType = {
  auth: AuthState;
  setAuth: (value: AuthState) => void;
  clear: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "aidoc-auth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuthState] = useState<AuthState>({});

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setAuthState(JSON.parse(stored));
      } catch {
        // ignore parse errors
      }
    }
  }, []);

  const setAuth = (value: AuthState) => {
    setAuthState(value);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    }
  };

  const clear = () => {
    setAuthState({});
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  };

  return <AuthContext.Provider value={{ auth, setAuth, clear }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
