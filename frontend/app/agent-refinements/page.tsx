"use client"

import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import { MOCK_REFINEMENTS, MOCK_INSIGHTS, MOCK_KB_UPDATES } from "@/lib/mock-data"

const AGENTS = ["orchestrator", "faq_agent", "order_agent", "sentiment_agent", "escalation_agent"]

const AGENT_LABELS: Record<string, string> = {
  orchestrator:     "Orchestrator",
  faq_agent:        "FAQ Agent",
  order_agent:      "Order Agent",
  sentiment_agent:  "Sentiment",
  escalation_agent: "Escalation",
}

const AGENT_COLORS: Record<string, string> = {
  orchestrator:     "#c4663f",
  faq_agent:        "#4f8a5b",
  order_agent:      "#c0902f",
  sentiment_agent:  "#5a7d9a",
  escalation_agent: "#7c5fa0",
}

interface Refinement {
  id: string
  agent_name: string
  refinement_text?: string
  content?: string
  created_at: string
  status: string
}

export default function LearningPage() {
  const [insights, setInsights]       = useState<any>(null)
  const [refinements, setRefinements] = useState<Refinement[]>([])
  const [kbUpdates, setKbUpdates]     = useState<any[]>([])
  const [loading, setLoading]         = useState(true)
  const [activeAgent, setActiveAgent] = useState<string>("all")
  const [applied, setApplied]         = useState<Set<string>>(new Set())
  const [dismissed, setDismissed]     = useState<Set<string>>(new Set())
  const [running, setRunning]         = useState(false)

  const load = async () => {
    try {
      const [ins, refs] = await Promise.all([
        apiClient.get<any>("/auto-learning/insights").catch(() => null),
        Promise.all(AGENTS.map(a =>
          apiClient.get<any>(`/agent-refinements/${a}`).catch(() => null)
        )),
      ])
      setInsights(ins ?? MOCK_INSIGHTS)
      const allRefs: Refinement[] = []
      let anyRefs = false
      refs.forEach((r: any, i: number) => {
        if (r?.pending_refinements?.length) {
          anyRefs = true
          r.pending_refinements.forEach((ref: any) => allRefs.push({ ...ref, agent_name: AGENTS[i] }))
        }
      })
      if (!anyRefs) {
        Object.values(MOCK_REFINEMENTS).forEach(agentData => {
          agentData.pending_refinements.forEach(ref => allRefs.push(ref as Refinement))
        })
      }
      setRefinements(allRefs)

      const kb = await apiClient.get<any>("/kb-updates").catch(() => null)
      setKbUpdates(kb?.updates ?? MOCK_KB_UPDATES)
    } catch { /* ignore */ } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const applyRefinement = async (agentName: string, refId: string) => {
    try {
      await apiClient.post<any>(`/agent-refinements/${agentName}/apply`, {})
      setApplied(prev => new Set([...prev, refId]))
    } catch { /* ignore */ }
  }

  const runImprovements = async () => {
    setRunning(true)
    try {
      await apiClient.post<any>("/improvements/run-now", {})
      await load()
    } catch { /* ignore */ } finally { setRunning(false) }
  }

  const applyKbUpdate = async (updateId: string) => {
    try {
      await apiClient.post<any>(`/kb-updates/${updateId}/apply`, {})
      setKbUpdates(prev => prev.filter(u => u.update_id !== updateId))
    } catch { /* ignore */ }
  }

  const rejectKbUpdate = async (updateId: string) => {
    try {
      await apiClient.post<any>(`/kb-updates/${updateId}/reject`, {})
      setKbUpdates(prev => prev.filter(u => u.update_id !== updateId))
    } catch { /* ignore */ }
  }

  const visibleRefs = refinements.filter(r => {
    if (dismissed.has(r.id)) return false
    if (activeAgent === "all") return true
    return r.agent_name === activeAgent
  })

  return (
    <div className="ws-page">
      <div className="ws-phead">
        <div>
          <div className="ws-h1">Learning</div>
          <div className="ws-sub">Agent refinements and knowledge base updates from customer feedback</div>
        </div>
        <div className="ws-chips">
          <button
            className="ws-chip acc"
            style={{ border: "none", cursor: "pointer", opacity: running ? .6 : 1 }}
            onClick={runImprovements}
            disabled={running}
          >
            {running ? "Running…" : "▶ Run improvements now"}
          </button>
        </div>
      </div>

      <div className="ws-wrap">
        {/* Learning stat grid */}
        <div className="ws-card" style={{ marginBottom: 15 }}>
          <div className="ws-ch">
            <div className="ws-ct">Today's learning loop</div>
            <div className="ws-cmeta">Auto-updated from feedback</div>
          </div>
          <div className="ws-lgrid">
            {[
              { v: insights?.total_insights ?? "—",     l: "Feedback insights",      n: "Across all agents" },
              { v: insights?.total_refinements ?? "—",  l: "Pending refinements",    n: visibleRefs.length ? `${visibleRefs.length} actionable` : "All clear" },
              { v: insights?.total_kb_updates ?? "—",   l: "KB update suggestions",  n: kbUpdates.length ? `${kbUpdates.length} awaiting approval` : "None pending" },
              { v: "Daily",                              l: "Auto-run schedule",      n: "2:00 AM server time" },
            ].map(s => (
              <div className="ws-lcell" key={s.l}>
                <div className="ws-lcv">{s.v}</div>
                <div className="ws-lcl">{s.l}</div>
                <div className="ws-lcn">{s.n}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="ws-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
          {/* Refinement queue */}
          <div className="ws-card">
            <div className="ws-ch">
              <div className="ws-ct">Agent refinements</div>
              <div className="ws-cmeta">{visibleRefs.length} pending</div>
            </div>

            {/* Agent filter */}
            <div style={{ display: "flex", gap: 6, padding: "0 14px 12px", flexWrap: "wrap" }}>
              {["all", ...AGENTS].map(a => (
                <div
                  key={a}
                  className={`ws-fchip${activeAgent === a ? " on" : ""}`}
                  style={{ padding: "5px 12px", fontSize: 12 }}
                  onClick={() => setActiveAgent(a)}
                >
                  {a === "all" ? "All agents" : AGENT_LABELS[a]}
                </div>
              ))}
            </div>

            <div className="ws-reflist">
              {loading && (
                <div style={{ padding: 28, textAlign: "center", color: "var(--ws-mut)", fontSize: 13.5 }}>
                  Loading refinements…
                </div>
              )}
              {!loading && visibleRefs.length === 0 && (
                <div style={{ padding: 28, textAlign: "center", color: "var(--ws-mut)", fontSize: 13.5 }}>
                  ✓ No pending refinements
                </div>
              )}
              {visibleRefs.slice(0, 10).map(r => {
                const isDone = applied.has(r.id)
                const text = r.refinement_text || r.content || "Refinement pending review"
                return (
                  <div className="ws-refrow" key={r.id}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <div style={{
                          width: 20, height: 20, borderRadius: 6,
                          background: AGENT_COLORS[r.agent_name] ?? "var(--ws-acc)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          color: "#fff", fontSize: 10, fontWeight: 700, flexShrink: 0,
                        }}>
                          {AGENT_LABELS[r.agent_name]?.[0] ?? "?"}
                        </div>
                        <span style={{ fontSize: 11, color: "var(--ws-dim)", fontWeight: 600 }}>
                          {AGENT_LABELS[r.agent_name] ?? r.agent_name}
                        </span>
                      </div>
                      <div className="ws-reft">{text.slice(0, 100)}{text.length > 100 ? "…" : ""}</div>
                      <div className="ws-refm">
                        {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                      </div>
                    </div>
                    <div className="ws-refacts">
                      {isDone ? (
                        <span className="ws-rbtn done">✓ Applied</span>
                      ) : (
                        <>
                          <button className="ws-rbtn acc" onClick={() => applyRefinement(r.agent_name, r.id)}>
                            Approve
                          </button>
                          <button className="ws-rbtn" onClick={() => setDismissed(prev => new Set([...prev, r.id]))}>
                            Dismiss
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* KB updates */}
          <div className="ws-card">
            <div className="ws-ch">
              <div className="ws-ct">KB update suggestions</div>
              <div className="ws-cmeta">Require manual approval</div>
            </div>
            <div className="ws-reflist">
              {loading && (
                <div style={{ padding: 28, textAlign: "center", color: "var(--ws-mut)", fontSize: 13.5 }}>
                  Loading…
                </div>
              )}
              {!loading && kbUpdates.length === 0 && (
                <div style={{ padding: 28, textAlign: "center", color: "var(--ws-mut)", fontSize: 13.5 }}>
                  ✓ No KB updates pending
                </div>
              )}
              {kbUpdates.slice(0, 8).map(u => {
                const content = u.content ?? {}
                const comment = content.customer_comment || content.summary || JSON.stringify(content).slice(0, 80)
                return (
                  <div className="ws-refrow" key={u.update_id}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="ws-reft">{comment.slice(0, 90)}{comment.length > 90 ? "…" : ""}</div>
                      <div className="ws-refm">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                        {u.agent_name && ` · ${AGENT_LABELS[u.agent_name] ?? u.agent_name}`}
                      </div>
                    </div>
                    <div className="ws-refacts">
                      <button className="ws-rbtn acc" onClick={() => applyKbUpdate(u.update_id)}>
                        Add to FAQ
                      </button>
                      <button className="ws-rbtn" onClick={() => rejectKbUpdate(u.update_id)}>
                        Reject
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
