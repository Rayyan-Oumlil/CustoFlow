"use client"

import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import { MOCK_ACTIVE_SESSIONS } from "@/lib/mock-data"

const AGENT_COLORS: Record<string, string> = {
  orchestrator:     "#c4663f",
  faq_agent:        "#4f8a5b",
  order_agent:      "#c0902f",
  sentiment_agent:  "#5a7d9a",
  escalation_agent: "#7c5fa0",
}

const AGENT_DEFS = [
  { id: "orchestrator",     name: "Orchestrator",  role: "Router",    status: "ok"    },
  { id: "faq_agent",        name: "FAQ Agent",      role: "Knowledge", status: "ok"    },
  { id: "order_agent",      name: "Order Agent",    role: "Orders",    status: "ok"    },
  { id: "sentiment_agent",  name: "Sentiment",      role: "Emotion",   status: "ok"    },
  { id: "escalation_agent", name: "Escalation",     role: "Handoff",   status: "watch" },
]

function formatAge(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  return `${Math.floor(diff / 3600)}h`
}

export default function MonitoringPage() {
  const [sessions, setSessions] = useState<any[]>(MOCK_ACTIVE_SESSIONS)
  const [metrics, setMetrics]   = useState<any>({})
  const [loading, setLoading]   = useState(true)
  const [sending, setSending]   = useState<Record<string, boolean>>({})
  const [replies, setReplies]   = useState<Record<string, string>>({})

  const load = async () => {
    try {
      const [s, m] = await Promise.all([
        apiClient.get<any[]>("/sessions/all/active").catch(() => null),
        apiClient.get<any>("/metrics").catch(() => null),
      ])
      if (Array.isArray(s) && s.length) setSessions(s)
      setMetrics(m || {})
    } catch { /* ignore */ } finally { setLoading(false) }
  }

  useEffect(() => { load(); const iv = setInterval(load, 5000); return () => clearInterval(iv) }, [])

  const sendMessage = async (sessionId: string, userId: string) => {
    const msg = replies[sessionId]?.trim()
    if (!msg) return
    setSending(prev => ({ ...prev, [sessionId]: true }))
    try {
      await apiClient.post<any>("/sessions/send-message", {
        session_id: sessionId, user_id: userId, message: msg,
      })
      setReplies(prev => ({ ...prev, [sessionId]: "" }))
      await load()
    } catch { /* ignore */ } finally {
      setSending(prev => ({ ...prev, [sessionId]: false }))
    }
  }

  const closeSession = async (sessionId: string) => {
    try {
      await apiClient.closeSession(sessionId)
      await load()
    } catch { /* ignore */ }
  }

  return (
    <div className="ws-page">
      <div className="ws-phead">
        <div>
          <div className="ws-h1">Monitoring</div>
          <div className="ws-sub">
            {sessions.length} active session{sessions.length !== 1 ? "s" : ""} · refreshes every 5s
          </div>
        </div>
        <div className="ws-chips">
          <div className="ws-chip" style={{ cursor: "pointer" }} onClick={load}>
            ↻ Refresh
          </div>
        </div>
      </div>

      {/* Agent health cards */}
      <div className="ws-agcards">
        {AGENT_DEFS.map(ag => (
          <div className="ws-card ws-agcard" key={ag.id}>
            <div className="ws-aghead">
              <div style={{
                width: 28, height: 28, borderRadius: 8,
                background: AGENT_COLORS[ag.id] ?? "#c4663f",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: "#fff", fontFamily: "Newsreader, serif", fontWeight: 600, fontSize: 13,
              }}>
                {ag.name[0]}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--foreground)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {ag.name}
                </div>
                <div style={{ fontSize: 11, color: "var(--ws-dim)" }}>{ag.role}</div>
              </div>
              <div className={`ws-agstat ${ag.status}`}>{ag.status}</div>
            </div>
            <div className="ws-agmetric"><span>Uptime</span><b>99.9%</b></div>
            <div className="ws-agmetric"><span>Accuracy</span><b>{ag.id === "escalation_agent" ? "90" : ag.id === "sentiment_agent" ? "88" : "93"}%</b></div>
            <div className="ws-agmetric"><span>Latency</span><b>{ag.id === "order_agent" ? "2.3" : ag.id === "faq_agent" ? "1.1" : "0.6"}s</b></div>
          </div>
        ))}
      </div>

      {/* Live session feed */}
      <div className="ws-wrap">
        <div className="ws-card">
          <div className="ws-ch">
            <div className="ws-ct">Live sessions</div>
            <div className="ws-cmeta">
              {sessions.length} active
            </div>
          </div>
          <div className="ws-feed">
            {loading && (
              <div style={{ padding: 32, textAlign: "center", color: "var(--ws-mut)", fontSize: 14 }}>
                Loading sessions…
              </div>
            )}
            {!loading && sessions.length === 0 && (
              <div style={{ padding: 32, textAlign: "center", color: "var(--ws-mut)", fontSize: 14 }}>
                No active sessions right now
              </div>
            )}
            {sessions.map(s => {
              const isWaiting = !s.is_active || s.message_count === 0
              return (
                <div key={s.session_id}>
                  <div className="ws-frow">
                    <div className={`ws-ldot ${isWaiting ? "wait" : ""}`} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--foreground)", display: "flex", gap: 8, alignItems: "center" }}>
                        <span className="ws-mono" style={{ fontSize: 12, color: "var(--ws-dim)" }}>
                          {s.customer_id || s.user_id || "unknown"}
                        </span>
                        {s.name && <span style={{ color: "var(--ws-dim)" }}>· {s.name}</span>}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--ws-dim)", marginTop: 3 }}>
                        {s.message_count || 0} messages · session {s.session_id?.slice(-8)}
                      </div>
                      {/* Human agent reply box */}
                      <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
                        <input
                          value={replies[s.session_id] ?? ""}
                          onChange={e => setReplies(prev => ({ ...prev, [s.session_id]: e.target.value }))}
                          onKeyDown={e => { if (e.key === "Enter") sendMessage(s.session_id, s.user_id) }}
                          placeholder="Reply as human agent…"
                          style={{
                            flex: 1, border: "1px solid var(--ws-line)",
                            background: "var(--ws-soft)", borderRadius: 9,
                            padding: "7px 12px", fontSize: 12.5,
                            fontFamily: "inherit", color: "var(--foreground)",
                          }}
                        />
                        <button
                          onClick={() => sendMessage(s.session_id, s.user_id)}
                          disabled={sending[s.session_id] || !replies[s.session_id]?.trim()}
                          style={{
                            background: "var(--ws-acc)", color: "#fff", border: "none",
                            borderRadius: 9, padding: "7px 14px", fontSize: 12, fontWeight: 700,
                            cursor: "pointer", fontFamily: "inherit",
                            opacity: (sending[s.session_id] || !replies[s.session_id]?.trim()) ? 0.45 : 1,
                          }}
                        >
                          Send
                        </button>
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: "var(--ws-mut)", fontWeight: 600, whiteSpace: "nowrap" }}>
                      {s.updated_at ? formatAge(s.updated_at) : "—"}
                    </div>
                    <button
                      onClick={() => closeSession(s.session_id)}
                      title="Close session"
                      style={{
                        background: "var(--ws-negbg)", color: "var(--ws-neg)", border: "none",
                        borderRadius: 8, padding: "6px 12px", fontSize: 11.5, fontWeight: 700,
                        cursor: "pointer", fontFamily: "inherit", whiteSpace: "nowrap",
                      }}
                    >
                      Close
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
