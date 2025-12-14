import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import AuthPanel from "../components/AuthPanel";

export const metadata: Metadata = {
  title: "AI Document Interview System",
  description: "Upload documents and ask questions with grounded answers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <Providers>
          <div className="max-w-5xl mx-auto p-6 space-y-6">
            <header className="border-b pb-4 flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h1 className="text-2xl font-semibold">AI Document Interview System</h1>
                <p className="text-sm text-slate-600">MVP frontend for upload, job status, and chat.</p>
              </div>
              <AuthPanel />
            </header>
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
