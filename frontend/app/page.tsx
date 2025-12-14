"use client";

import Link from "next/link";

const links = [
  { href: "/upload", label: "Upload & Jobs", blurb: "Send files to the ingestion pipeline and track job status." },
  { href: "/chat", label: "Chat & Query", blurb: "Ask grounded questions over your ingested documents." },
  { href: "/documents", label: "Documents", blurb: "Browse document metadata and IDs for filtering." },
  { href: "/login", label: "Login (demo JWT)", blurb: "Get a signed token for local testing." },
  { href: "/admin", label: "Admin Reset", blurb: "Dev-only purge to return to a clean state." },
];

export default function Home() {
  return (
    <main className="stack" style={{ gap: 18 }}>
      <div className="hero card">
        <div className="stack" style={{ gap: 10 }}>
          <p className="badge">MVP dashboard</p>
          <h2 className="title" style={{ margin: 0 }}>
            Ship documents in, get grounded answers out.
          </h2>
          <p className="subtitle" style={{ maxWidth: 720 }}>
            Use the uploader to ingest PDFs/TXT/DOCX, then chat with citations. Configure the API base URL via{" "}
            <code>NEXT_PUBLIC_API_BASE_URL</code>. Auth expects a JWT (or dev header if enabled).
          </p>
        </div>
        <div className="hero-actions">
          <Link className="btn" href="/upload">
            Upload a document
          </Link>
          <Link className="btn btn-secondary" href="/chat">
            Open chat
          </Link>
        </div>
      </div>

      <div className="card-grid">
        {links.map((link) => (
          <Link key={link.href} href={link.href} className="card" style={{ display: "block" }}>
            <div className="stack" style={{ gap: 8 }}>
              <div className="flex" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <p style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{link.label}</p>
                <span className="pill">Go</span>
              </div>
              <p className="subtitle" style={{ margin: 0 }}>{link.blurb}</p>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
