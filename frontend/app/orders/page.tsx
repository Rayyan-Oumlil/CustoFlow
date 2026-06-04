"use client"

import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"

const STATUS_STYLE: Record<string, { bg: string; fg: string; label: string }> = {
  processing:    { bg: "#e8eef3", fg: "#5a7d9a", label: "Processing" },
  shipped:       { bg: "#f7eed7", fg: "#c0902f", label: "Shipped" },
  delivering:    { bg: "#f7eed7", fg: "#c0902f", label: "Delivering" },
  delivery_soon: { bg: "#fbe9e4", fg: "#c5503e", label: "Delivery soon" },
  delivered:     { bg: "#e8f1e6", fg: "#4f8a5b", label: "Delivered" },
  cancelled:     { bg: "#faf5ec", fg: "#a99b86", label: "Cancelled" },
}

type SortField = "order_id" | "customer_id" | "total" | "status"

export default function OrdersPage() {
  const [orders, setOrders]       = useState<any[]>([])
  const [loading, setLoading]     = useState(true)
  const [sortField, setSortField] = useState<SortField>("order_id")
  const [sortDir, setSortDir]     = useState<"asc" | "desc">("asc")
  const [filter, setFilter]       = useState("all")

  const load = async () => {
    try {
      const data = await apiClient.get<any>("/orders")
      if (data?.orders) setOrders(data.orders)
    } catch { /* ignore */ } finally { setLoading(false) }
  }

  useEffect(() => {
    load()
    const iv = setInterval(load, 30000)
    return () => clearInterval(iv)
  }, [])

  const toggleSort = (field: SortField) => {
    if (sortField === field) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortField(field); setSortDir("asc") }
  }

  const statuses = ["all", "processing", "shipped", "delivery_soon", "delivered", "cancelled"]

  const visible = orders
    .filter(o => filter === "all" || o.status === filter)
    .sort((a, b) => {
      let va: any = a[sortField], vb: any = b[sortField]
      if (sortField === "total") { va = parseFloat(va); vb = parseFloat(vb) }
      if (va < vb) return sortDir === "asc" ? -1 : 1
      if (va > vb) return sortDir === "asc" ?  1 : -1
      return 0
    })

  const arrow = (f: SortField) => sortField === f ? (sortDir === "asc" ? " ↑" : " ↓") : ""

  const exportCSV = () => {
    const rows = ["order_id,customer_id,status,total"]
    orders.forEach(o => rows.push(`${o.order_id},${o.customer_id},${o.status},${o.total}`))
    const a = document.createElement("a")
    a.href = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" }))
    a.download = "orders.csv"
    a.click()
  }

  return (
    <div className="ws-page">
      <div className="ws-phead">
        <div>
          <div className="ws-h1">Orders</div>
          <div className="ws-sub">{orders.length} orders · all agents have access</div>
        </div>
        <div className="ws-chips">
          <button className="ws-chip acc" style={{ border: "none", cursor: "pointer" }} onClick={exportCSV}>
            Export CSV
          </button>
        </div>
      </div>

      {/* Status filters */}
      <div className="ws-filters">
        {statuses.map(s => (
          <div key={s} className={`ws-fchip${filter === s ? " on" : ""}`} onClick={() => setFilter(s)}>
            {s === "all" ? "All" : (STATUS_STYLE[s]?.label ?? s)}
            {s !== "all" && (
              <span style={{ marginLeft: 6, opacity: .6 }}>
                {orders.filter(o => o.status === s).length}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="ws-wrap">
        <div className="ws-card" style={{ overflow: "hidden" }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: "center", color: "var(--ws-mut)", fontSize: 14 }}>
              Loading orders…
            </div>
          ) : (
            <table className="ws-table">
              <thead>
                <tr>
                  {(["order_id", "customer_id", "total", "status"] as SortField[]).map(f => (
                    <th key={f} onClick={() => toggleSort(f)} style={{ cursor: "pointer", userSelect: "none" }}>
                      {f === "order_id" ? "Order" : f === "customer_id" ? "Customer" : f.charAt(0).toUpperCase() + f.slice(1)}
                      {arrow(f)}
                    </th>
                  ))}
                  <th>Items</th>
                  <th>Est. delivery</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", color: "var(--ws-mut)", padding: 40 }}>
                      No orders in this view
                    </td>
                  </tr>
                )}
                {visible.map(o => {
                  const s = STATUS_STYLE[o.status] ?? { bg: "#faf5ec", fg: "#a99b86", label: o.status }
                  const itemCount = Array.isArray(o.items) ? o.items.length : (o.items ?? 0)
                  return (
                    <tr key={o.order_id}>
                      <td>
                        <span className="ws-mono" style={{ fontWeight: 600, color: "var(--ws-acc)" }}>
                          {o.order_id}
                        </span>
                      </td>
                      <td>
                        <span className="ws-mono" style={{ color: "var(--ws-dim)", fontSize: 12.5 }}>
                          {o.customer_id}
                        </span>
                      </td>
                      <td>
                        <span className="ws-tnum">${parseFloat(o.total ?? 0).toFixed(2)}</span>
                      </td>
                      <td>
                        <span className="ws-badge" style={{ background: s.bg, color: s.fg }}>
                          {s.label}
                        </span>
                      </td>
                      <td style={{ color: "var(--ws-dim)" }}>
                        {itemCount} {itemCount === 1 ? "item" : "items"}
                      </td>
                      <td style={{ color: "var(--ws-dim)", fontSize: 12.5 }}>
                        {o.estimated_delivery || "—"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
