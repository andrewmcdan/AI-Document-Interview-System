"use client";

import { FormEvent, useMemo, useState, useEffect } from "react";
import { postJson, type ApiConfig, fetchDocuments, getJson } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { Markdown } from "../../components/Markdown";

type AnswerSource = {
  document_id: string;
  document_title?: string | null;
  chunk_id: string;
  score?: number | null;
  metadata?: Record<string, any>;
};

type QueryResponse = {
  answer: string;
  sources: AnswerSource[];
  generated_at: string;
};

type Conversation = {
  id: string;
  title?: string | null;
  updated_at?: string | null;
};

type Message = {
  id: string;
  role: string;
  content: string;
  created_at?: string;
};

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [docIds, setDocIds] = useState<string[]>([]);
  const [streamingText, setStreamingText] = useState("");
  const [sources, setSources] = useState<AnswerSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [docs, setDocs] = useState<{ id: string; title: string }[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [showDocs, setShowDocs] = useState(true);
  const [editTitle, setEditTitle] = useState("");

  const { auth } = useAuth();
  const config: ApiConfig = useMemo(
    () => ({
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
      token: auth.token,
      devUserId: auth.devUserId,
    }),
    [auth]
  );

  const loadDocs = async () => {
    try {
      const data = await fetchDocuments(config);
      setDocs(data);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    }
  };

  const loadConversations = async () => {
    try {
      const data = await getJson<Conversation[]>(config, "/conversations");
      setConversations(data);
    } catch (err: any) {
      setError(err.message || "Failed to load conversations");
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const data = await getJson<Message[]>(config, `/conversations/${conversationId}/messages`);
      setMessages(data);
    } catch (err: any) {
      setError(err.message || "Failed to load messages");
    }
  };

  useEffect(() => {
    if (config.token || config.devUserId) {
      loadConversations();
    }
  }, [config.token, config.devUserId]);

  const handleSelectConversation = (conversationId: string | null) => {
    setSelectedConversation(conversationId);
    setMessages([]);
    setEditTitle("");
    if (conversationId) {
      loadMessages(conversationId);
      const found = conversations.find((c) => c.id === conversationId);
      if (found) setEditTitle(found.title || "");
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setStreamingText("");
    setSources([]);

    const payload: any = { question, top_k: 5 };
    if (docIds.length) payload.document_ids = docIds;

    const url = selectedConversation
      ? `/conversations/${selectedConversation}/query/stream`
      : "/query/stream";

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (config.token) headers["Authorization"] = `Bearer ${config.token}`;
    if (!config.token && config.devUserId) headers["X-User-Id"] = config.devUserId;

    try {
      const res = await fetch(`${config.baseUrl}${url}`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      if (!res.ok || !res.body) {
        throw new Error(await res.text());
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const processBuffer = () => {
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const evt of events) {
          const line = evt.trim();
          if (!line.startsWith("data:")) continue;
          const dataStr = line.replace(/^data:\s*/, "");
          if (!dataStr) continue;
          try {
            const payload = JSON.parse(dataStr);
            if (payload.type === "sources") {
              setSources(payload.sources || []);
            } else if (payload.type === "chunk") {
              setStreamingText((prev) => prev + (payload.delta || ""));
            } else if (payload.type === "done") {
              if (payload.conversation_id) {
                handleSelectConversation(payload.conversation_id);
                loadConversations();
              }
              setQuestion("");
            }
          } catch {
            // ignore parse errors
          }
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        processBuffer();
      }
      setStreamingText("");
      await loadConversations();
      if (selectedConversation) {
        await loadMessages(selectedConversation);
      }
      setLoading(false);
    } catch (err: any) {
      setError(err.message || "Query failed");
      setLoading(false);
    }
  };

  const allMessages = [
    ...(streamingText
      ? [{ id: "streaming", role: "assistant", content: streamingText, created_at: new Date().toISOString() }]
      : []),
    ...[...messages].reverse(),
  ];

  return (
    <main className="grid" style={{ gap: 12, gridTemplateColumns: "320px 1fr" }}>
      <aside className="card stack" style={{ gap: 10, minHeight: "70vh" }}>
        <div className="flex" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <p className="title" style={{ margin: 0, fontSize: 18 }}>
            Conversations
          </p>
          <div className="flex" style={{ display: "flex", gap: 6 }}>
            <button className="btn btn-secondary" style={{ padding: "6px 10px" }} onClick={loadConversations}>
              Refresh
            </button>
            <button className="btn" style={{ padding: "6px 10px" }} onClick={() => handleSelectConversation(null)}>
              New
            </button>
          </div>
        </div>
        <div className="list" style={{ flex: 0, display: "flex", flexDirection: "column", gap: 10 }}>
            {conversations.length === 0 && <p className="subtitle">No conversations yet.</p>}
            {conversations.map((c) => (
              <button
                key={c.id}
                className="list-item"
                style={{
                  textAlign: "left",
                  borderColor: selectedConversation === c.id ? "#8b5cf6" : undefined,
                  height: 80,
                  display: "flex",
                  alignItems: "flex-start",
                }}
                onClick={() => handleSelectConversation(c.id)}
              >
                <div className="stack" style={{ gap: 4 }}>
                  <p style={{ margin: 0, fontWeight: 600, color: "#f8fafc" }}>
                    {c.title || "Untitled conversation"}
                  </p>
                  {c.updated_at && (
                    <p className="subtitle" style={{ margin: 0, fontSize: 12 }}>
                      {new Date(c.updated_at).toLocaleString()}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
      </aside>

      <section className="stack" style={{ gap: 12 }}>
        <div className="card stack" style={{ gap: 8 }}>
          <p className="badge">Chat</p>
          {selectedConversation && (
            <div className="flex" style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input
                className="input"
                style={{ flex: 1 }}
                value={editTitle}
                placeholder="Conversation title"
                onChange={(e) => setEditTitle(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: "8px 12px" }}
                disabled={!editTitle.trim()}
                onClick={async () => {
                  if (!selectedConversation) return;
                  try {
                    const headers: Record<string, string> = { "Content-Type": "application/json" };
                    if (config.token) headers["Authorization"] = `Bearer ${config.token}`;
                    if (!config.token && config.devUserId) headers["X-User-Id"] = config.devUserId;
                    const res = await fetch(
                      `${config.baseUrl}/conversations/${selectedConversation}/title`,
                      {
                        method: "PATCH",
                        headers,
                        body: JSON.stringify({ title: editTitle }),
                      }
                    );
                    if (!res.ok) throw new Error(await res.text());
                    await loadConversations();
                  } catch (err: any) {
                    setError(err.message || "Failed to update title");
                  }
                }}
              >
                Save title
              </button>
            </div>
          )}
          <form
            className="stack"
            style={{ gap: 12 }}
            onSubmit={handleSubmit}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.ctrlKey) {
                e.preventDefault();
                handleSubmit(e as any);
              }
            }}
          >
            <div className="stack" style={{ gap: 6 }}>
              <label className="label">Question</label>
              <textarea
                className="textarea"
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                required
              />
            </div>
            <div className="stack" style={{ gap: 6 }}>
              <div className="flex" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label className="label">Restrict to documents (optional)</label>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: "6px 10px" }}
                  onClick={() => setShowDocs((v) => !v)}
                >
                  {showDocs ? "Hide" : "Show"}
                </button>
              </div>
              {showDocs && (
                <>
                  <div className="flex" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={loadDocs}
                      className="btn btn-secondary"
                      disabled={loading}
                      style={{ padding: "8px 12px" }}
                    >
                      Load my documents
                    </button>
                    {docIds.length > 0 && <span className="pill">{docIds.length} selected</span>}
                  </div>
                  <div className="grid two-col">
                    {docs.map((d) => (
                      <label
                        key={d.id}
                        className="list-item"
                        style={{ display: "flex", gap: 10, alignItems: "flex-start" }}
                      >
                        <input
                          type="checkbox"
                          checked={docIds.includes(d.id)}
                          onChange={(e) => {
                            if (e.target.checked) setDocIds([...docIds, d.id]);
                            else setDocIds(docIds.filter((x) => x !== d.id));
                          }}
                          style={{ marginTop: 4 }}
                        />
                        <div className="stack" style={{ gap: 4 }}>
                          <p style={{ margin: 0, fontWeight: 600 }}>{d.title}</p>
                          <p className="subtitle" style={{ margin: 0, fontSize: 12 }}>
                            {d.id}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                </>
              )}
            </div>
            <div className="flex" style={{ display: "flex", gap: 10 }}>
              <button type="submit" disabled={loading} className="btn">
                {loading ? "Streaming..." : "Ask"}
              </button>
            </div>
          </form>
          {error && <p className="subtitle" style={{ color: "#fca5a5" }}>{error}</p>}
        </div>

        <div className="card stack" style={{ gap: 10, minHeight: "300px" }}>
          <p className="badge">History</p>
          <div className="stack" style={{ gap: 10 }}>
            {allMessages.length === 0 && <p className="subtitle">No messages yet.</p>}
            {allMessages.map((m) => (
              <div key={m.id} className="list-item">
                <p className="label" style={{ marginBottom: 6 }}>
                  {m.role === "assistant" ? "Assistant" : "You"}{" "}
                  {m.created_at ? `• ${new Date(m.created_at).toLocaleTimeString()}` : ""}
                </p>
                <Markdown content={m.content} />
              </div>
            ))}
          </div>

          {sources.length > 0 && (
            <div className="stack" style={{ gap: 6 }}>
              <p className="label">Sources</p>
              <ul className="list" style={{ margin: 0, padding: 0, listStyle: "none" }}>
                {sources.map((s, idx) => (
                  <li key={s.chunk_id || idx} className="list-item">
                    <div className="stack" style={{ gap: 4 }}>
                      <p style={{ margin: 0, fontWeight: 600 }}>
                        [{idx + 1}] {s.document_title || s.document_id}
                      </p>
                      <p className="subtitle" style={{ margin: 0 }}>
                        score: {s.score?.toFixed(3) ?? "n/a"}
                      </p>
                      {s.metadata?.text_snippet && (
                        <div className="subtitle" style={{ margin: 0 }}>
                          <Markdown content={s.metadata.text_snippet} />
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
