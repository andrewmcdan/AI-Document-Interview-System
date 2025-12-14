"use client";

import Link from "next/link";

const links = [
  { href: "/upload", label: "Upload & Jobs" },
  { href: "/documents", label: "Documents" },
  { href: "/chat", label: "Chat & Query" },
];

export default function Home() {
  return (
    <main className="space-y-4">
      <h2 className="text-xl font-semibold">Quick Links</h2>
      <ul className="space-y-2">
        {links.map((link) => (
          <li key={link.href}>
            <Link className="text-blue-600 hover:underline" href={link.href}>
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
      <p className="text-sm text-slate-700">
        Configure the API base URL via <code>NEXT_PUBLIC_API_BASE_URL</code>. Auth requires a JWT Bearer token (or
        dev X-User-Id if the backend allows it). See upload and chat pages for usage.
      </p>
    </main>
  );
}
