"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api-client"
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts"

const AGENT_COLORS: Record<string, string> = {
  orchestrator: "#c4663f",
  faq:          "#4f8a5b",
  order:        "#c0902f",
  sentiment:    "#5a7d9a",
  escalation:   "#7c5fa0",
}

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

function MiniSpark({ data, color }: { data: number[]; color: string }) {
  if (!data?.length) return null
  const min = Math.min(...data), max = Math.max(...data)
  const range = max - min || 1
  const W = 52, H = 22
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W
    const y = H - ((v - min) / range) * H
    return `${x},${y}`
  }).join(" ")
  return (
    <svg width={W} height={H} style={{ overflow: "visible" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

interface Analytics {
  total_messages?: number
  active_sessions?: number
  closed_sessions?: number
  avg_satisfaction?: number
  avg_response_time?: number
  resolution_rate?: number
  tickets_created?: number
  open_tickets?: number
}

interface DailyRow { day: string; interactions: number; satisfaction: number }

export default function OverviewPage() {
  const router = useRouter()
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [daily, setDaily] = useState<DailyRow[]>([])
  const [tickets, setTickets] = useState<any[]>([])
  const [agents] = useState([
    { id: "orchestrator", name: "Orchestrator", role: "Router",    share: 100 },
    { id: "faq",          name: "FAQ Agent",    role: "Knowledge", share: 42  },
    { id: "order",        name: "Order Agent",  role: "Orders",    share: 28  },
    { id: "sentiment",    name: "Sentiment",    role: "Emotion",   share: 14  },
    { id: "escalation",   name: "Escalation",   role: "Handoff",   share: 9   },
  ])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [a, d, t] = await Promise.all([
          apiClient.get<Analytics>("/analytics").catch(() => null),
          apiClient.get<DailyRow[]>("/analytics/daily").catch(() => []),
          apiClient.get<any>("/tickets").catch(() => null),
        ])
        if (a) setAnalytics(a)
        if (Array.isArray(d)) setDaily(d)
        if (t?.tickets) setTickets(t.tickets.slice(0, 5))
      } finally {
        setLoading(false)
      }
    }
    load()
    const iv = setInterval(load, 30000)
    return () => clearInterval(iv)
  }, [])

  const kpis = [
    {
      label: "Messages handled",
      value: analytics?.total_messages?.toLocaleString() ?? "—",
      delta: "+12.4", good: true,
      spark: [180, 210, 240, 225, 260, 300, 355],
    },
    {
      label: "Active sessions",
      value: analytics?.active_sessions ?? "—",
      delta: "+6", good: true,
      spark: [22, 28, 31, 26, 33, 35, 38],
    },
    {
      label: "Avg. satisfaction",
      value: analytics?.avg_satisfaction ? analytics.avg_satisfaction.toFixed(1) : "—",
      unit: "/5", delta: "+0.2", good: true,
      spark: [4.1, 4.2, 4.3, 4.3, 4.4, 4.5, 4.6],
    },
    {
      label: "Avg. response",
      value: analytics?.avg_response_time ? analytics.avg_response_time.toFixed(1) : "—",
      unit: "s", delta: "-1.4", good: true,
      spark: [12, 11.3, 10.8, 9.9, 9.1, 8.6, 8.2],
    },
    {
      label: "Resolution rate",
      value: analytics?.resolution_rate ? `${analytics.resolution_rate}` : "—",
      unit: "%", delta: "+2.0", good: true,
      spark: [80, 81, 83, 84, 85, 86, 87],
    },
    {
      label: "Tickets created",
      value: analytics?.tickets_created ?? "—",
      delta: "+3", good: false,
      spark: [8, 12, 9, 14, 11, 13, 15],
    },
  ]

  return (
    <div className="ws-page">
      {/* Page header */}
      <div className="ws-phead">
        <div>
          <div className="ws-h1">Good morning</div>
          <div className="ws-sub">Here's how support is doing across all agents today.</div>
        </div>
        <div className="ws-chips">
          <div className="ws-chip">Last 7 days <span className="mu">▾</span></div>
          <button
            className="ws-chip acc"
            style={{ border: "none", cursor: "pointer" }}
            onClick={() => router.push("/tickets")}
          >
            ＋ New ticket
          </button>
        </div>
      </div>

      <div className="ws-wrap">
        {/* KPI grid */}
        <div className="ws-kpis">
          {kpis.map((k, i) => (
            <div className="ws-card ws-kc" key={i}>
              <div className="ws-kl">{k.label}</div>
              <div className="ws-kv">
                {loading ? <span style={{ opacity: 0.3 }}>—</span> : k.value}
                {k.unit && <span className="ws-ku">{k.unit}</span>}
              </div>
              <div className="ws-kr">
                <span className={`ws-pill ${k.good ? "up" : "dn"}`}>
                  {k.good ? "↑" : "↓"} {k.delta.replace(/[+-]/, "")}
                </span>
                <MiniSpark
                  data={k.spark}
                  color={k.good ? "var(--ws-pos)" : "var(--ws-neg)"}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Row 1: chart + agents */}
        <div className="ws-row ws-r1">
          {/* Area chart */}
          <div className="ws-card">
            <div className="ws-ch">
              <div>
                <div className="ws-ct">Interactions &amp; satisfaction</div>
                <div className="ws-cmeta">Last 7 days</div>
              </div>
              <div className="ws-legend">
                <span className="ws-lg">
                  <span className="ws-ld" style={{ background: "var(--ws-acc)" }} />
                  Interactions
                </span>
                <span className="ws-lg">
                  <span className="ws-ld" style={{ background: "var(--ws-warn)" }} />
                  CSAT
                </span>
              </div>
            </div>
            <div style={{ padding: "4px 16px 16px" }}>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={daily} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <defs>
                    <linearGradient id="intGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--ws-acc)"  stopOpacity={0.15} />
                      <stop offset="95%" stopColor="var(--ws-acc)"  stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="satGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--ws-warn)" stopOpacity={0.12} />
                      <stop offset="95%" stopColor="var(--ws-warn)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "var(--ws-mut)" }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left"  tick={{ fontSize: 11, fill: "var(--ws-mut)" }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: "var(--ws-mut)" }} axisLine={false} tickLine={false} domain={[3, 5]} />
                  <Tooltip
                    contentStyle={{ background: "var(--card)", border: "1px solid var(--ws-line)", borderRadius: 10, fontSize: 12 }}
                    labelStyle={{ color: "var(--ws-dim)" }}
                  />
                  <Area yAxisId="left"  type="monotone" dataKey="interactions" stroke="var(--ws-acc)"  fill="url(#intGrad)" strokeWidth={2} dot={false} />
                  <Area yAxisId="right" type="monotone" dataKey="satisfaction"  stroke="var(--ws-warn)" fill="url(#satGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Agent list */}
          <div className="ws-card">
            <div className="ws-ch">
              <div className="ws-ct">Your agents</div>
              <div className="ws-cmeta">5 active</div>
            </div>
            <div className="ws-alist">
              {agents.map((a) => (
                <div className="ws-arow" key={a.id}>
                  <div className="ws-ab" style={{ background: AGENT_COLORS[a.id] }}>
                    {a.name[0]}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div className="ws-an">{a.name}</div>
                    <div className="ws-arole">{a.role}</div>
                    <div className="ws-abar">
                      <i style={{ width: `${a.share}%`, background: AGENT_COLORS[a.id] }} />
                    </div>
                  </div>
                  <div>
                    <div className="ws-ap ws-num">{a.share}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Row 2: tickets */}
        <div className="ws-card" style={{ marginBottom: 0 }}>
          <div className="ws-ch">
            <div className="ws-ct">Needs attention</div>
            <div className="ws-cmeta">
              {analytics?.open_tickets ?? "—"} open · {tickets.filter(t => t.priority === "urgent").length} urgent
            </div>
          </div>
          <div className="ws-tlist">
            {loading && (
              <div style={{ padding: 24, textAlign: "center", color: "var(--ws-mut)", fontSize: 13.5 }}>
                Loading…
              </div>
            )}
            {!loading && tickets.length === 0 && (
              <div style={{ padding: 24, textAlign: "center", color: "var(--ws-mut)", fontSize: 13.5 }}>
                No open tickets
              </div>
            )}
            {tickets.map((t) => {
              const [bg, fg] = STATUS_BADGE[t.status] ?? ["#faf5ec", "#a99b86"]
              return (
                <div
                  className="ws-trow"
                  key={t.ticket_id}
                  onClick={() => router.push("/tickets")}
                >
                  <span className="ws-pdot" style={{ background: PRIORITY_COLOR[t.priority] }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="ws-ti">{t.issue}</div>
                    <div className="ws-tm">
                      <span className="ws-mono">{t.ticket_id}</span>
                      <span>·</span>
                      <span>{t.customer_id || t.user_id}</span>
                      <span>·</span>
                      <span style={{ textTransform: "capitalize" }}>{t.priority}</span>
                    </div>
                  </div>
                  <span className="ws-badge" style={{ background: bg, color: fg }}>
                    {t.status.replace("_", " ")}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
