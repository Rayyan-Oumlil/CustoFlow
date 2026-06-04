"use client"

import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import { MOCK_TICKETS } from "@/lib/mock-data"

const PRIORITY_COLOR: Record<string, string> = {
  urgent: "#c5503e",
  high:   "#c0902f",
  normal: "#5a7d9a",
  low:    "#a99b86",
}

const STATUS_BADGE: Record<string, [string, string]> = {
  open:        ["#fbe9e4", "#c5503e"],
  in_progress: ["#f7eed7", "#c0902f"],
  resolved:    ["#e8f1e6", "#4f8a5b"],
  closed:      ["#faf5ec", "#a99b86"],
}

type Filter = "all" | "open" | "in_progress" | "resolved" | "urgent"

export default function TicketsPage() {
  const [tickets, setTickets] = useState<any[]>(MOCK_TICKETS)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter]   = useState<Filter>("all")
  const [selected, setSelected] = useState<any | null>(null)
  const [replyText, setReplyText] = useState("")
  const [sending, setSending] = useState(false)

  const load = async () => {
    try {
      const data = await apiClient.get<any>("/tickets").catch(() => null)
      if (data?.tickets?.length) setTickets(data.tickets)
    } catch { /* ignore */ } finally { setLoading(false) }
  }

  useEffect(() => { load(); const iv = setInterval(load, 15000); return () => clearInterval(iv) }, [])

  const updateStatus = async (ticketId: string, status: string) => {
    try {
      await apiClient.put(`/tickets/${ticketId}/status`, { status })
      setTickets(prev => prev.map(t => t.ticket_id === ticketId ? { ...t, status } : t))
      if (selected?.ticket_id === ticketId) setSelected((prev: any) => prev ? { ...prev, status } : null)
    } catch { /* ignore */ }
  }

  const sendReply = async () => {
    if (!selected || !replyText.trim()) return
    setSending(true)
    try {
      await apiClient.post<any>(`/tickets/${selected.ticket_id}/message`, { message: replyText.trim() })
      setReplyText("")
    } catch { /* ignore */ } finally { setSending(false) }
  }

  const FILTERS: [Filter, string][] = [
    ["all", "All"],
    ["open", "Open"],
    ["in_progress", "In progress"],
    ["resolved", "Resolved"],
    ["urgent", "Urgent"],
  ]

  const visible = tickets.filter(t =>
    filter === "all"    ? true :
    filter === "urgent" ? t.priority === "urgent" :
    t.status === filter
  )

  const urgentCount = tickets.filter(t => t.priority === "urgent" && t.status === "open").length

  return (
    <div className="ws-page">
      <div className="ws-phead">
        <div>
          <div className="ws-h1">Tickets</div>
          <div className="ws-sub">
            {tickets.filter(t => t.status === "open" || t.status === "in_progress").length} open
            {urgentCount > 0 && ` · ${urgentCount} urgent`}
          </div>
        </div>
        <div className="ws-chips">
          <div className="ws-chip">Sort: Recent <span className="mu">▾</span></div>
        </div>
      </div>

      <div className="ws-filters">
        {FILTERS.map(([key, label]) => (
          <div
            key={key}
            className={`ws-fchip${filter === key ? " on" : ""}`}
            onClick={() => setFilter(key)}
          >
            {label}
            {key !== "all" && (
              <span style={{ marginLeft: 6, opacity: .6 }}>
                {key === "urgent"
                  ? tickets.filter(t => t.priority === "urgent").length
                  : tickets.filter(t => t.status === key).length}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="ws-wrap" style={{ display: "grid", gridTemplateColumns: selected ? "1fr 380px" : "1fr", gap: 16 }}>
        {/* Ticket list */}
        <div className="ws-card">
          <div className="ws-tlist" style={{ padding: "8px 12px 14px" }}>
            {loading && (
              <div style={{ padding: 32, textAlign: "center", color: "var(--ws-mut)", fontSize: 14 }}>Loading…</div>
            )}
            {!loading && visible.length === 0 && (
              <div style={{ padding: 32, textAlign: "center", color: "var(--ws-mut)", fontSize: 14 }}>
                No tickets in this view
              </div>
            )}
            {visible.map(t => {
              const [bg, fg] = STATUS_BADGE[t.status] ?? ["#faf5ec", "#a99b86"]
              const isSelected = selected?.ticket_id === t.ticket_id
              return (
                <div
                  key={t.ticket_id}
                  className="ws-trow"
                  style={{
                    padding: "14px 12px",
                    background: isSelected ? "var(--ws-accbg)" : undefined,
                    borderRadius: isSelected ? 13 : undefined,
                  }}
                  onClick={() => setSelected(isSelected ? null : t)}
                >
                  <span className="ws-pdot" style={{ background: PRIORITY_COLOR[t.priority] }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="ws-ti">{t.issue}</div>
                    <div className="ws-tm">
                      <span className="ws-mono">{t.ticket_id}</span>
                      <span>·</span>
                      <span>{t.customer_id || t.user_id || "—"}</span>
                      <span>·</span>
                      <span style={{ textTransform: "capitalize" }}>{t.priority}</span>
                    </div>
                  </div>
                  <span className="ws-badge" style={{ background: bg, color: fg }}>
                    {t.status.replace("_", " ")}
                  </span>
                  <span className="ws-ts">{t.created_at ? new Date(t.created_at).toLocaleDateString() : "—"}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="ws-card" style={{ display: "flex", flexDirection: "column", maxHeight: "calc(100vh - 200px)", overflow: "hidden" }}>
            <div style={{ padding: "18px 20px 14px", borderBottom: "1px solid var(--ws-line)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div className="ws-ct" style={{ fontSize: 15 }}>{selected.ticket_id}</div>
                  <div style={{ fontSize: 12, color: "var(--ws-mut)", marginTop: 2, fontFamily: "JetBrains Mono, monospace" }}>
                    {selected.customer_id || selected.user_id}
                  </div>
                </div>
                <button
                  onClick={() => setSelected(null)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ws-mut)", fontSize: 18 }}
                >
                  ✕
                </button>
              </div>
              <div style={{ marginTop: 12, fontSize: 13.5, color: "var(--foreground)" }}>{selected.issue}</div>
              <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
                {["open", "in_progress", "resolved", "closed"].map(s => (
                  <button
                    key={s}
                    onClick={() => updateStatus(selected.ticket_id, s)}
                    style={{
                      fontSize: 11.5, fontWeight: 700, padding: "4px 12px",
                      borderRadius: 999, border: "none", cursor: "pointer",
                      background: selected.status === s ? STATUS_BADGE[s]?.[0] : "var(--ws-soft)",
                      color: selected.status === s ? STATUS_BADGE[s]?.[1] : "var(--ws-dim)",
                      fontFamily: "inherit",
                    }}
                  >
                    {s.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ padding: "14px 20px 18px", borderTop: "1px solid var(--ws-line)", marginTop: "auto" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ws-mut)", textTransform: "uppercase", letterSpacing: ".4px", marginBottom: 10 }}>
                Reply to customer
              </div>
              <textarea
                className="ws-cinput"
                value={replyText}
                onChange={e => setReplyText(e.target.value)}
                placeholder="Type your reply…"
                rows={3}
                style={{ width: "100%", marginBottom: 10 }}
              />
              <button
                onClick={sendReply}
                disabled={sending || !replyText.trim()}
                style={{
                  background: "var(--ws-acc)", color: "#fff", border: "none",
                  borderRadius: 10, padding: "9px 18px", fontSize: 13, fontWeight: 700,
                  cursor: "pointer", fontFamily: "inherit",
                  opacity: (sending || !replyText.trim()) ? 0.45 : 1,
                }}
              >
                {sending ? "Sending…" : "Send reply"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
