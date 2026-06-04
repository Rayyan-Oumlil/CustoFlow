"use client"

import React, { useEffect, useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { cache, CACHE_KEYS } from "@/lib/cache"
import { MOCK_SESSIONS, MOCK_MESSAGES } from "@/lib/mock-data"

const AGENT_COLORS: Record<string, string> = {
  orchestrator: "#c4663f",
  faq_agent:    "#4f8a5b",
  order_agent:  "#c0902f",
  sentiment_agent: "#5a7d9a",
  escalation_agent: "#7c5fa0",
  human_agent:  "#2a7a4f",
}

interface Conversation {
  session_id: string
  name: string
  message_count: number
  created_at: string
  is_active?: boolean
}

// ── Customer ID gate ─────────────────────────────────────────────
function CustomerGate({ onSubmit }: { onSubmit: (id: string) => void }) {
  const [value, setValue] = useState("")
  const [error, setError] = useState("")

  const validate = (id: string) => {
    const t = id.trim()
    if (!t) return "Customer ID is required"
    if (t.length < 6) return "Too short — minimum 6 characters (e.g. cust_001)"
    if (t.length > 50) return "Too long — maximum 50 characters"
    if (!/^cust[_-][0-9]+$/i.test(t)) return "Format: cust_XXX or CUST-XXX (e.g. cust_001)"
    return ""
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const err = validate(value)
    if (err) { setError(err); return }
    onSubmit(value.trim().toLowerCase())
  }

  return (
    <div className="ws-page" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: "100%", maxWidth: 400, padding: "0 24px" }}>
        <div className="ws-h1" style={{ marginBottom: 6 }}>Welcome</div>
        <div className="ws-sub" style={{ marginBottom: 28 }}>Enter your Customer ID to access support chat.</div>
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ws-mut)", textTransform: "uppercase", letterSpacing: ".4px", display: "block", marginBottom: 7 }}>
              Customer ID
            </label>
            <input
              value={value}
              onChange={e => { setValue(e.target.value); if (error) setError(validate(e.target.value)) }}
              placeholder="cust_001"
              autoFocus
              style={{
                width: "100%", border: `1px solid ${error ? "var(--ws-neg)" : "var(--ws-line)"}`,
                background: "var(--ws-soft)", borderRadius: 12, padding: "12px 14px",
                fontSize: 14, fontFamily: "inherit", color: "var(--foreground)",
              }}
            />
            {error && <p style={{ fontSize: 12, color: "var(--ws-neg)", marginTop: 6 }}>{error}</p>}
            <p style={{ fontSize: 11.5, color: "var(--ws-mut)", marginTop: 6 }}>Format: cust_XXX or CUST-XXX</p>
          </div>
          <button
            type="submit"
            disabled={!value.trim() || !!error}
            style={{
              background: "var(--ws-acc)", color: "#fff", border: "none",
              borderRadius: 12, padding: "12px 0", fontSize: 14, fontWeight: 700,
              cursor: "pointer", opacity: (!value.trim() || !!error) ? 0.45 : 1,
              fontFamily: "inherit",
            }}
          >
            Start chatting
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Main chat ────────────────────────────────────────────────────
export default function ChatPage() {
  const { userId, customerId, sessionId, setSessionId, setCustomerId, initFromStorage, logout } = useStore()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<"all" | "open" | "waiting">("all")
  const [isSessionClosed, setIsSessionClosed] = useState(false)
  const [feedbackGiven, setFeedbackGiven] = useState<Set<string>>(new Set())
  const [resolved, setResolved] = useState<Set<string>>(new Set())
  const [toast, setToast] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sendingRef = useRef(false)
  const router = useRouter()

  useEffect(() => { initFromStorage() }, [initFromStorage])

  // Load conversations when customer changes
  useEffect(() => {
    if (!userId || !customerId) return
    const load = async () => {
      setLoading(true)
      try {
        const cacheKey = customerId ? CACHE_KEYS.sessions(customerId) : `sessions:${userId}`
        const cached = cache.get<Conversation[]>(cacheKey)
        if (cached) { setConversations(cached); setLoading(false); return }

        const url = customerId ? `/sessions/by-customer/${encodeURIComponent(customerId)}` : `/sessions/${userId}`
        const data = await apiClient.get<any>(url).catch(() => null)
        let arr: any[] = Array.isArray(data) ? data : data?.sessions ?? []
        if (!arr.length) {
          arr = MOCK_SESSIONS.slice(0, 2).map(s => ({
            ...s, customer_id: customerId, user_id: userId,
            name: `Session ${s.session_id.slice(-8)}`,
          }))
        }
        arr = arr.filter((s: any) => !s.customer_id || s.customer_id.toLowerCase() === customerId.toLowerCase())
        const convos: Conversation[] = arr.map((s: any) => ({
          session_id: s.session_id,
          name: s.name || `Session ${s.session_id.slice(-8)}`,
          message_count: s.message_count || 0,
          created_at: s.created_at,
          is_active: s.is_active !== false,
        }))
        setConversations(convos)
        cache.set(cacheKey, convos, 30000)
        if (!sessionId && convos.length > 0) setSessionId(convos[0].session_id)
        if (convos.length === 0) createNewConversation()
      } catch { /* ignore */ } finally { setLoading(false) }
    }
    load()
  }, [userId, customerId]) // eslint-disable-line react-hooks/exhaustive-deps

  // Deduplicate messages
  const dedup = useCallback((msgs: Message[]): Message[] => {
    const seen = new Map<string, Message>()
    for (const m of msgs) {
      const key = `${m.role}:${m.content.trim().toLowerCase().replace(/\s+/g, " ")}:${Math.floor(new Date(m.timestamp).getTime() / 10000) * 10000}`
      if (!seen.has(key)) seen.set(key, m)
      else {
        const ex = seen.get(key)!
        const exLocal = ex.id?.startsWith("user_") || ex.id?.startsWith("assistant_") || ex.id?.startsWith("error_")
        const curLocal = m.id?.startsWith("user_") || m.id?.startsWith("assistant_") || m.id?.startsWith("error_")
        if (exLocal && !curLocal) seen.set(key, m)
      }
    }
    return Array.from(seen.values()).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }, [])

  // Load messages
  const fetchMessages = useCallback(async (merge = false) => {
    if (!userId || !sessionId) return
    try {
      const data = await apiClient.get<any>(`/history/${userId}?session_id=${sessionId}`).catch(() => null)
      const mockFallback = MOCK_MESSAGES[sessionId] ?? []
      const arr: any[] = data ? (Array.isArray(data) ? data : data?.history ?? []) : mockFallback
      const serverMsgs: Message[] = arr.map((m: any, i: number) => {
        const isHuman = m.metadata?.is_human_agent || m.metadata?.agent_used === "human_agent" || m.agent_used === "human_agent"
        return {
          id: m.id || `msg_${m.timestamp || Date.now()}_${i}`,
          role: m.role,
          content: m.content,
          agent_used: isHuman ? "human_agent" : (m.metadata?.agent || m.agent_used),
          response_time: m.metadata?.response_time || m.response_time,
          timestamp: m.timestamp || m.created_at,
        }
      })
      setMessages(prev => dedup(merge ? [...prev.filter(p => Date.now() - new Date(p.timestamp).getTime() < 2000), ...serverMsgs] : serverMsgs))
    } catch { /* ignore */ }
  }, [userId, sessionId, dedup])

  useEffect(() => {
    fetchMessages()
    const poll = setInterval(() => { if (!sendingRef.current) fetchMessages(true) }, 3000)
    return () => clearInterval(poll)
  }, [fetchMessages])

  // Auto-scroll on send
  useEffect(() => {
    if (sending) setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100)
  }, [sending, messages])

  // Show toast helper
  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  const createNewConversation = async () => {
    if (!userId || !customerId) return
    try {
      const data = await apiClient.post<any>("/sessions/create", { user_id: userId, customer_id: customerId })
      const sid = data?.session_id as string
      if (!sid) return
      const newConv: Conversation = {
        session_id: sid,
        name: data?.metadata?.name || `Session ${sid.slice(-8)}`,
        message_count: 0,
        created_at: data?.metadata?.created_at || new Date().toISOString(),
      }
      setConversations(prev => [newConv, ...prev])
      setSessionId(sid)
      setMessages([])
    } catch { /* ignore */ }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending || isSessionClosed) return
    if (!sessionId && userId && customerId) { await createNewConversation(); return }
    if (!sessionId) return

    const text = input.trim()
    setInput("")
    setSending(true)
    sendingRef.current = true

    const optimisticId = `user_${Date.now()}`
    setMessages(prev => [...prev, { id: optimisticId, role: "user", content: text, timestamp: new Date().toISOString() }])

    try {
      await apiClient.post("/chat", { user_id: userId, session_id: sessionId, message: text, customer_id: customerId || undefined })
      setTimeout(() => { sendingRef.current = false; fetchMessages(true) }, 1200)
    } catch (err: any) {
      setMessages(prev => dedup([...prev, { id: `error_${Date.now()}`, role: "assistant", content: `Error: ${err.message || "Failed to send"}`, timestamp: new Date().toISOString() }]))
      sendingRef.current = false
    } finally {
      setSending(false)
    }
  }

  const resolveConversation = () => {
    if (!sessionId) return
    setResolved(prev => new Set([...prev, sessionId]))
    showToast("✓ Conversation resolved")
  }

  const handleLogout = () => { setConversations([]); setMessages([]); setSessionId(null); logout() }

  // Customer ID gate
  if (!customerId) {
    return <CustomerGate onSubmit={id => setCustomerId(id)} />
  }

  const filteredConvs = conversations.filter(c => {
    if (tab === "open")    return c.is_active !== false
    if (tab === "waiting") return c.message_count > 0
    return true
  })

  const activeConv = conversations.find(c => c.session_id === sessionId)
  const isResolved = sessionId ? resolved.has(sessionId) : false

  // Active session customer info
  const currentCustomer = customerId

  return (
    <div className="ws-fill">
      {/* ── Left: conversation list ── */}
      <div className="ws-clist">
        <div className="ws-clhead">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div className="ws-clt">Conversations</div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={createNewConversation}
                style={{
                  background: "var(--ws-acc)", color: "#fff", border: "none",
                  borderRadius: 9, padding: "6px 12px", fontSize: 12, fontWeight: 600,
                  cursor: "pointer", fontFamily: "inherit",
                }}
              >
                ＋ New
              </button>
              <button
                onClick={handleLogout}
                title="Log out"
                style={{
                  background: "var(--ws-soft)", color: "var(--ws-dim)", border: "1px solid var(--ws-line)",
                  borderRadius: 9, padding: "6px 10px", fontSize: 12, cursor: "pointer", fontFamily: "inherit",
                }}
              >
                ↩
              </button>
            </div>
          </div>
          <div className="ws-sub" style={{ marginTop: 6 }}>{customerId}</div>
          <div className="ws-ctabs" style={{ marginTop: 13 }}>
            {(["all", "open", "waiting"] as const).map(t => (
              <a key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </a>
            ))}
          </div>
        </div>

        <div className="ws-convs">
          {loading && <div style={{ padding: 20, textAlign: "center", color: "var(--ws-mut)", fontSize: 13 }}>Loading…</div>}
          {!loading && filteredConvs.length === 0 && (
            <div style={{ padding: 20, textAlign: "center", color: "var(--ws-mut)", fontSize: 13 }}>
              No conversations yet
            </div>
          )}
          {filteredConvs.map(c => (
            <div
              key={c.session_id}
              className={`ws-citem ${sessionId === c.session_id ? "on" : ""}`}
              onClick={() => setSessionId(c.session_id)}
            >
              <div className="ws-cav" style={{ background: AGENT_COLORS.orchestrator }}>
                {(c.name || "S")[0].toUpperCase()}
                <span className="ws-md" style={{ background: c.is_active !== false ? "var(--ws-pos)" : "var(--ws-mut)" }} />
              </div>
              <div style={{ minWidth: 0 }}>
                <div className="ws-cn">{c.name}</div>
                <div className="ws-cpv">{c.message_count} messages</div>
              </div>
              <div>
                <div className="ws-crt">{c.is_active === false ? "closed" : "active"}</div>
                {c.message_count > 0 && sessionId !== c.session_id && (
                  <div className="ws-cunread">{Math.min(c.message_count, 9)}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Center: message thread ── */}
      <div className="ws-thread">
        {!sessionId ? (
          <div className="ws-emptypane">
            <div className="ws-emptyic">💬</div>
            <div className="ws-emptyt">Select a conversation</div>
            <div style={{ fontSize: 13.5, color: "var(--ws-mut)" }}>or start a new one above</div>
          </div>
        ) : (
          <>
            <div className="ws-thead">
              <div className="ws-cav" style={{ background: AGENT_COLORS.orchestrator, width: 38, height: 38, borderRadius: 11 }}>
                {(activeConv?.name || "S")[0].toUpperCase()}
              </div>
              <div>
                <div className="ws-thn">{activeConv?.name || sessionId.slice(-8)}</div>
                <div className="ws-thm">
                  <span className="ws-mono" style={{ fontSize: 11 }}>{sessionId.slice(-12)}</span>
                  {isSessionClosed && <span style={{ color: "var(--ws-neg)", fontWeight: 700 }}>• Closed</span>}
                  {isResolved && <span style={{ color: "var(--ws-pos)", fontWeight: 700 }}>• Resolved</span>}
                </div>
              </div>
              <div className="ws-tactions">
                {isResolved ? (
                  <button
                    className="ws-tbtn"
                    onClick={() => { if (sessionId) { setResolved(prev => { const s = new Set(prev); s.delete(sessionId); return s }) } }}
                  >
                    Reopen
                  </button>
                ) : (
                  <button className="ws-tbtn acc" onClick={resolveConversation}>Resolve</button>
                )}
              </div>
            </div>

            {isResolved && (
              <div className="ws-resolved-banner">
                ✓ Conversation marked as resolved
              </div>
            )}

            <div className="ws-msgs">
              {messages.length === 0 && !sending && (
                <div className="ws-emptypane">
                  <div className="ws-emptyic">✉</div>
                  <div className="ws-emptyt">Start the conversation</div>
                </div>
              )}
              {messages.map((msg) => {
                const isHuman = msg.agent_used === "human_agent"
                return (
                  <div key={msg.id} className={`ws-msg ${msg.role === "user" ? "cust" : "agent"}`}>
                    {msg.role === "assistant" && isHuman && (
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ws-pos)", marginBottom: 4 }}>
                        👤 Human Agent
                      </div>
                    )}
                    <div
                      className="ws-bub"
                      style={
                        msg.role === "assistant" && isHuman
                          ? { background: "var(--ws-posbg)", border: "1px solid var(--ws-pos)", color: "var(--foreground)", borderBottomLeftRadius: 5 }
                          : undefined
                      }
                    >
                      {msg.content}
                    </div>
                    {msg.role === "assistant" && msg.agent_used && !isHuman && (
                      <div style={{ fontSize: 10.5, color: "var(--ws-mut)", marginTop: 3, display: "flex", gap: 6, alignItems: "center" }}>
                        <span style={{ background: "var(--ws-accbg)", color: "var(--ws-acc)", borderRadius: 999, padding: "2px 8px", fontWeight: 700, fontSize: 10.5 }}>
                          🤖 {msg.agent_used}
                        </span>
                        {msg.response_time && <span>{msg.response_time.toFixed(1)}s</span>}
                      </div>
                    )}
                    <div className="ws-mt">{new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
                  </div>
                )
              })}
              {sending && (
                <div className="ws-msg agent">
                  <div className="ws-bub" style={{ display: "flex", gap: 5, alignItems: "center", padding: "12px 18px" }}>
                    {[0, 150, 300].map(delay => (
                      <div key={delay} style={{ width: 6, height: 6, borderRadius: "50%", background: "rgba(255,255,255,.7)", animation: `bounce 1s ${delay}ms infinite` }} />
                    ))}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Composer */}
            <div className="ws-composer">
              <textarea
                className="ws-cinput"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(e as any) } }}
                placeholder={isSessionClosed || isResolved ? "This conversation is closed" : "Type your message… (Enter to send)"}
                disabled={sending || isSessionClosed || isResolved}
                rows={1}
              />
              <button
                className="ws-send"
                onClick={sendMessage}
                disabled={sending || !input.trim() || isSessionClosed || isResolved}
              >
                ↑
              </button>
            </div>

            {/* Toast */}
            {toast && <div className="ws-toast">{toast}</div>}
          </>
        )}
      </div>

      {/* ── Right: context rail ── */}
      <div className="ws-ctx">
        <div className="ws-ctxsec">
          <div className="ws-ctxh">Customer</div>
          <div className="ws-pf">
            <div className="ws-pfav" style={{ background: AGENT_COLORS.orchestrator }}>
              {currentCustomer?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div>
              <div className="ws-pfn">{currentCustomer || "—"}</div>
              <div className="ws-pfid">{currentCustomer || "no id"}</div>
            </div>
          </div>
          <div style={{ marginTop: 14 }}>
            {[
              ["Session", sessionId ? sessionId.slice(-8) : "—"],
              ["Messages", activeConv?.message_count ?? messages.length],
              ["Status", isResolved ? "Resolved" : isSessionClosed ? "Closed" : "Active"],
            ].map(([lab, val]) => (
              <div className="ws-kvrow" key={String(lab)}>
                <span className="lab">{lab}</span>
                <span className="val">{String(val)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="ws-ctxsec">
          <div className="ws-ctxh">Suggested actions</div>
          {[
            { icon: "📋", title: "Check order status", meta: "Look up recent orders" },
            { icon: "↩", title: "Start return", meta: "Initiate return flow" },
            { icon: "🎫", title: "Escalate to human", meta: "Create support ticket" },
          ].map(s => (
            <div className="ws-sugg" key={s.title}>
              <div className="ws-suggi">{s.icon}</div>
              <div>
                <div className="ws-suggt">{s.title}</div>
                <div className="ws-suggm">{s.meta}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50%       { transform: translateY(-5px); }
        }
      `}</style>
    </div>
  )
}
