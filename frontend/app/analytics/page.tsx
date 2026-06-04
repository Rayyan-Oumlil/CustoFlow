"use client"

import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import { MOCK_ANALYTICS, MOCK_DAILY, MOCK_INSIGHTS } from "@/lib/mock-data"
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts"

interface Analytics {
  total_messages?: number
  active_sessions?: number
  closed_sessions?: number
  avg_satisfaction?: number
  avg_response_time?: number
  resolution_rate?: number
  tickets_created?: number
  open_tickets?: number
  resolved_tickets?: number
  interactions?: number
}

const SENTIMENT_COLORS = ["#4f8a5b", "#5a7d9a", "#c5503e"]

const AGENT_BARS = [
  { name: "Orchestrator", color: "#c4663f", pct: 100 },
  { name: "FAQ Agent",    color: "#4f8a5b", pct: 42  },
  { name: "Order Agent",  color: "#c0902f", pct: 28  },
  { name: "Sentiment",    color: "#5a7d9a", pct: 14  },
  { name: "Escalation",  color: "#7c5fa0", pct: 9   },
]

function MiniSpark({ data, color }: { data: number[]; color: string }) {
  if (!data?.length) return null
  const min = Math.min(...data), max = Math.max(...data)
  const range = max - min || 1
  const W = 52, H = 22
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${H - ((v - min) / range) * H}`).join(" ")
  return (
    <svg width={W} height={H} style={{ overflow: "visible" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics>(MOCK_ANALYTICS)
  const [daily, setDaily]         = useState<any[]>(MOCK_DAILY)
  const [ticketStatus, setTicketStatus] = useState<any[]>([])
  const [insights, setInsights]   = useState<any>(MOCK_INSIGHTS)
  const [loading, setLoading]     = useState(true)

  const load = async () => {
    try {
      const [a, d, ts, ins] = await Promise.all([
        apiClient.get<Analytics>("/analytics").catch(() => null),
        apiClient.get<any[]>("/analytics/daily").catch(() => null),
        apiClient.get<any[]>("/analytics/ticket-status").catch(() => null),
        apiClient.get<any>("/auto-learning/insights").catch(() => null),
      ])
      if (a?.total_messages) setAnalytics(a)
      if (Array.isArray(d) && d.some((r: any) => r.interactions > 0)) setDaily(d)
      if (Array.isArray(ts) && ts.length) setTicketStatus(ts)
      if (ins?.total_insights) setInsights(ins)
    } catch { /* ignore */ } finally { setLoading(false) }
  }

  useEffect(() => { load(); const iv = setInterval(load, 30000); return () => clearInterval(iv) }, [])

  const kpis = [
    { label: "Messages handled", value: analytics?.total_messages?.toLocaleString(), spark: [180,210,240,225,260,300,355], good: true },
    { label: "Active sessions",  value: analytics?.active_sessions, spark: [22,28,31,26,33,35,38], good: true },
    { label: "Avg. satisfaction", value: analytics?.avg_satisfaction?.toFixed(1), unit: "/5", spark: [4.1,4.2,4.3,4.3,4.4,4.5,4.6], good: true },
    { label: "Resolution rate", value: analytics?.resolution_rate, unit: "%", spark: [80,81,83,84,85,86,87], good: true },
    { label: "Avg. response",   value: analytics?.avg_response_time?.toFixed(1), unit: "s", spark: [12,11.3,10.8,9.9,9.1,8.6,8.2], good: true },
    { label: "Open tickets",    value: analytics?.open_tickets, spark: [8,12,9,14,11,13,15], good: false },
  ]

  const sentimentData = [
    { name: "Positive", value: 62 },
    { name: "Neutral",  value: 27 },
    { name: "Negative", value: 11 },
  ]

  return (
    <div className="ws-page">
      <div className="ws-phead">
        <div>
          <div className="ws-h1">Analytics</div>
          <div className="ws-sub">Performance metrics across all agents and sessions</div>
        </div>
        <div className="ws-chips">
          <div className="ws-chip">Last 7 days <span className="mu">▾</span></div>
        </div>
      </div>

      <div className="ws-wrap">
        {/* KPI row */}
        <div className="ws-kpis">
          {kpis.map((k, i) => (
            <div className="ws-card ws-kc" key={i}>
              <div className="ws-kl">{k.label}</div>
              <div className="ws-kv">
                {loading ? <span style={{ opacity: .3 }}>—</span> : (k.value ?? "—")}
                {k.unit && <span className="ws-ku">{k.unit}</span>}
              </div>
              <div className="ws-kr">
                <span className={`ws-pill ${k.good ? "up" : "dn"}`}>
                  {k.good ? "↑ +" : "↓ "}{i % 2 === 0 ? "12%" : "3%"}
                </span>
                <MiniSpark data={k.spark} color={k.good ? "var(--ws-pos)" : "var(--ws-neg)"} />
              </div>
            </div>
          ))}
        </div>

        {/* Row: area chart + sentiment donut */}
        <div className="ws-row ws-r2">
          <div className="ws-card">
            <div className="ws-ch">
              <div>
                <div className="ws-ct">Interactions &amp; satisfaction</div>
                <div className="ws-cmeta">Last 7 days</div>
              </div>
              <div className="ws-legend">
                <span className="ws-lg"><span className="ws-ld" style={{ background: "var(--ws-acc)" }} />Interactions</span>
                <span className="ws-lg"><span className="ws-ld" style={{ background: "var(--ws-warn)" }} />CSAT</span>
              </div>
            </div>
            <div style={{ padding: "4px 16px 16px" }}>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={daily} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <defs>
                    <linearGradient id="ag1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--ws-acc)"  stopOpacity={0.15} />
                      <stop offset="95%" stopColor="var(--ws-acc)"  stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="ag2" x1="0" y1="0" x2="0" y2="1">
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
                  <Area yAxisId="left"  type="monotone" dataKey="interactions" stroke="var(--ws-acc)"  fill="url(#ag1)" strokeWidth={2} dot={false} />
                  <Area yAxisId="right" type="monotone" dataKey="satisfaction"  stroke="var(--ws-warn)" fill="url(#ag2)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Sentiment donut */}
          <div className="ws-card">
            <div className="ws-ch">
              <div className="ws-ct">Sentiment split</div>
              <div className="ws-cmeta">All sessions</div>
            </div>
            <div className="ws-donutwrap">
              <ResponsiveContainer width={110} height={110}>
                <PieChart>
                  <Pie
                    data={sentimentData} cx="50%" cy="50%"
                    innerRadius={32} outerRadius={50}
                    dataKey="value" strokeWidth={0}
                  >
                    {sentimentData.map((_, i) => (
                      <Cell key={i} fill={SENTIMENT_COLORS[i]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="ws-donut-legend">
                {sentimentData.map((d, i) => (
                  <div className="ws-donut-item" key={d.name}>
                    <div className="ws-donut-dot" style={{ background: SENTIMENT_COLORS[i] }} />
                    <span className="ws-donut-label">{d.name}</span>
                    <span className="ws-donut-val">{d.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Row: agent volume + ticket status */}
        <div className="ws-row ws-r3">
          {/* Agent volume bars */}
          <div className="ws-card" style={{ gridColumn: "span 2" }}>
            <div className="ws-ch">
              <div className="ws-ct">Agent volume</div>
              <div className="ws-cmeta">Share of handled messages</div>
            </div>
            <div className="ws-barlist">
              {AGENT_BARS.map(a => (
                <div className="ws-barrow" key={a.name}>
                  <div className="ws-barlab">{a.name}</div>
                  <div className="ws-bartrack">
                    <i style={{ width: `${a.pct}%`, background: a.color }} />
                  </div>
                  <div className="ws-barval">{a.pct}%</div>
                </div>
              ))}
            </div>
          </div>

          {/* Learning stats */}
          <div className="ws-card">
            <div className="ws-ch">
              <div className="ws-ct">Auto-learning</div>
              <div className="ws-cmeta">Today's AI improvement loop</div>
            </div>
            <div className="ws-lgrid">
              {[
                { v: insights?.total_insights ?? "—", l: "Feedback insights", n: "All agents" },
                { v: insights?.total_refinements ?? "—", l: "Refinements pending", n: "Order · FAQ" },
                { v: insights?.total_kb_updates ?? "—", l: "KB update suggestions", n: "Shipping · returns" },
                { v: loading ? "—" : "28", l: "QA checks today", n: "26 pass · 2 review" },
              ].map(s => (
                <div className="ws-lcell" key={s.l}>
                  <div className="ws-lcv">{s.v}</div>
                  <div className="ws-lcl">{s.l}</div>
                  <div className="ws-lcn">{s.n}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
