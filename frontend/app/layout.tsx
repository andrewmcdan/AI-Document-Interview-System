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
      <body>
        <Providers>
          <div className="container">
            <div className="shell">
              <header className="stack" style={{ gap: 14 }}>
                <div className="flex" style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-start" }}>
                  <div style={{ flex: 1, minWidth: 240 }}>
                    <h1 className="title">AI Document Interview System</h1>
                    <p className="subtitle">Upload, ingest, and ask grounded questions over your documents.</p>
                  </div>
                  <div style={{ minWidth: 280 }}>
                    <AuthPanel />
                  </div>
                </div>
                <div className="divider" />
              </header>
              {children}
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
