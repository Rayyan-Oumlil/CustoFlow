"use client"

import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Order, type Ticket } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface TicketWithSummary extends Ticket {
  summary?: string
}

export default function OrdersPage() {
  const { initFromStorage } = useStore()
  const [orders, setOrders] = useState<Order[]>([])
  const [tickets, setTickets] = useState<TicketWithSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [ticketSummaries, setTicketSummaries] = useState<Record<string, string>>({})

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [ordersResponse, ticketsResponse] = await Promise.all([
          apiClient.get<any>("/orders").catch(() => ({ orders: [] })),
          apiClient.get<any>("/tickets").catch(() => ({ tickets: [] })),
        ])
        // Backend returns {orders: [...], count: ...} or {tickets: [...], count: ...}
        const ordersList = Array.isArray(ordersResponse?.orders) ? ordersResponse.orders : []
        const ticketsList = Array.isArray(ticketsResponse?.tickets) ? ticketsResponse.tickets : []
        
        setOrders(ordersList)
        setTickets(ticketsList)
        
        // Fetch summaries for all tickets
        const summaries: Record<string, string> = {}
        await Promise.all(
          ticketsList.map(async (ticket: Ticket) => {
            try {
              const summaryData = await apiClient.get<any>(`/tickets/${ticket.ticket_id}/summary`).catch(() => null)
              if (summaryData && summaryData.summary) {
                summaries[ticket.ticket_id] = summaryData.summary
              }
            } catch (error) {
              console.error(`Failed to fetch summary for ${ticket.ticket_id}:`, error)
            }
          })
        )
        setTicketSummaries(summaries)
      } catch (error) {
        console.error("Failed to fetch data:", error)
        setOrders([])
        setTickets([])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      processing: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      shipped: "bg-purple-500/20 text-purple-700 dark:text-purple-300",
      delivered: "bg-green-500/20 text-green-700 dark:text-green-300",
      cancelled: "bg-red-500/20 text-red-700 dark:text-red-300",
      open: "bg-red-500/20 text-red-700 dark:text-red-300",
      in_progress: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      resolved: "bg-green-500/20 text-green-700 dark:text-green-300",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  const getPriorityBadgeColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      normal: "bg-gray-500/20 text-gray-700 dark:text-gray-300",
      high: "bg-orange-500/20 text-orange-700 dark:text-orange-300",
      urgent: "bg-red-500/20 text-red-700 dark:text-red-300",
    }
    return colors[priority] || "bg-muted text-muted-foreground"
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Orders & Tickets" description="Manage orders and support tickets" />

      <div className="flex-1 overflow-auto px-8 py-8">
        <Tabs defaultValue="orders" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-xs">
            <TabsTrigger value="orders">Orders</TabsTrigger>
            <TabsTrigger value="tickets">Tickets</TabsTrigger>
          </TabsList>

          <TabsContent value="orders" className="mt-6">
            {loading ? (
              <p className="text-muted-foreground">Loading orders...</p>
            ) : orders.length === 0 ? (
              <p className="text-muted-foreground">No orders found</p>
            ) : (
              <div className="space-y-3">
                {orders.map((order) => (
                  <Card key={order.order_id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-medium">Order {order.order_id.slice(0, 8)}</p>
                        <p className="text-sm text-muted-foreground">Customer: {order.customer_id}</p>
                        {order.items && order.items.length > 0 && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {order.items.length} item{order.items.length > 1 ? "s" : ""}
                            {order.tracking_number && ` • Tracking: ${order.tracking_number}`}
                          </p>
                        )}
                      </div>
                      <div className="text-right ml-4">
                        <p className="font-semibold">${order.total?.toFixed(2) || "0.00"}</p>
                        <Badge className={getStatusBadgeColor(order.status)}>{order.status}</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      {order.created_at 
                        ? (() => {
                            try {
                              const date = new Date(order.created_at)
                              return isNaN(date.getTime()) ? "N/A" : date.toLocaleDateString()
                            } catch {
                              return "N/A"
                            }
                          })()
                        : "N/A"}
                    </p>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="tickets" className="mt-6">
            {loading ? (
              <p className="text-muted-foreground">Loading tickets...</p>
            ) : tickets.length === 0 ? (
              <p className="text-muted-foreground">No tickets found</p>
            ) : (
              <div className="space-y-3">
                {tickets.map((ticket) => (
                  <Card key={ticket.ticket_id} className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium">Ticket {ticket.ticket_id.slice(0, 8)}</p>
                        <p className="text-sm mt-1">{ticket.issue}</p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {ticket.customer_id && ticket.customer_id !== "unknown" && `Customer: ${ticket.customer_id}`}
                          {ticket.session_id && ` • Session: ${ticket.session_id.slice(0, 8)}`}
                          {ticket.user_id && ` • User: ${ticket.user_id.slice(0, 8)}`}
                        </p>
                        {ticketSummaries[ticket.ticket_id] && (
                          <div className="mt-3 p-2 bg-muted rounded text-xs">
                            <p className="font-medium mb-1">Summary:</p>
                            <p className="text-muted-foreground">{ticketSummaries[ticket.ticket_id]}</p>
                          </div>
                        )}
                      </div>
                      <div className="text-right space-y-2 ml-4">
                        <Badge className={getStatusBadgeColor(ticket.status)}>{ticket.status}</Badge>
                        <Badge className={getPriorityBadgeColor(ticket.priority)}>{ticket.priority}</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-3">
                      {ticket.created_at 
                        ? (() => {
                            try {
                              const date = new Date(ticket.created_at)
                              return isNaN(date.getTime()) ? "N/A" : date.toLocaleDateString()
                            } catch {
                              return "N/A"
                            }
                          })()
                        : "N/A"}
                    </p>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
