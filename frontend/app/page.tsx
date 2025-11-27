"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { apiClient, type Analytics } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, ShoppingCart, BarChart3, Ticket, TrendingUp, Users, Clock } from "lucide-react"
import Link from "next/link"

interface DashboardStats {
  analytics: Analytics | null
  ordersCount: number
  ticketsCount: number
  recentOrders: any[]
  recentTickets: any[]
}

export default function HomePage() {
  const router = useRouter()
  const { userId, customerId, initFromStorage } = useStore()
  const [stats, setStats] = useState<DashboardStats>({
    analytics: null,
    ordersCount: 0,
    ticketsCount: 0,
    recentOrders: [],
    recentTickets: [],
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        const [analyticsData, ordersData, ticketsData] = await Promise.all([
          apiClient.get<any>("/analytics").catch(() => null),
          apiClient.get<any>("/orders").catch(() => null),
          apiClient.get<any>("/tickets").catch(() => null),
        ])

        const orders = Array.isArray(ordersData?.orders) ? ordersData.orders : []
        const tickets = Array.isArray(ticketsData?.tickets) ? ticketsData.tickets : []

        setStats({
          analytics: analyticsData || null,
          ordersCount: orders.length,
          ticketsCount: tickets.length,
          recentOrders: orders.slice(0, 5),
          recentTickets: tickets.slice(0, 5),
        })
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const analytics = stats.analytics

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Dashboard" description="Overview of your customer support system" />

      <div className="flex-1 overflow-auto px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Messages</p>
                <p className="text-3xl font-bold mt-2">{loading ? "-" : analytics?.total_messages || 0}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-blue-500" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Sessions</p>
                <p className="text-3xl font-bold mt-2">{loading ? "-" : analytics?.active_sessions || 0}</p>
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Tickets Created</p>
                <p className="text-3xl font-bold mt-2">{loading ? "-" : analytics?.tickets_created || 0}</p>
              </div>
              <Ticket className="h-8 w-8 text-orange-500" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg Satisfaction</p>
                <p className="text-3xl font-bold mt-2">
                  {loading ? "-" : analytics?.avg_satisfaction ? `${analytics.avg_satisfaction.toFixed(1)}/10` : "N/A"}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push("/chat")}>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold">Start Chat</h3>
                <p className="text-sm text-muted-foreground">Begin a new conversation</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push("/orders")}>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <ShoppingCart className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold">Manage Orders</h3>
                <p className="text-sm text-muted-foreground">{stats.ordersCount} orders available</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push("/analytics")}>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <BarChart3 className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold">View Analytics</h3>
                <p className="text-sm text-muted-foreground">Performance metrics</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Orders */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <ShoppingCart className="h-5 w-5" />
                Recent Orders
              </h2>
              <Button variant="ghost" size="sm" onClick={() => router.push("/orders")}>
                View All
              </Button>
            </div>
            {loading ? (
              <p className="text-muted-foreground text-sm">Loading...</p>
            ) : stats.recentOrders.length === 0 ? (
              <p className="text-muted-foreground text-sm">No orders yet</p>
            ) : (
              <div className="space-y-3">
                {stats.recentOrders.map((order: any) => (
                  <div key={order.order_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Order {order.order_id}</p>
                      <p className="text-xs text-muted-foreground">Customer: {order.customer_id}</p>
                    </div>
                    <Badge className={order.status === "delivered" ? "bg-green-500" : order.status === "delivery_soon" ? "bg-orange-500" : "bg-blue-500"}>
                      {order.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Recent Tickets */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Ticket className="h-5 w-5" />
                Recent Tickets
              </h2>
              <Button variant="ghost" size="sm" onClick={() => router.push("/orders")}>
                View All
              </Button>
            </div>
            {loading ? (
              <p className="text-muted-foreground text-sm">Loading...</p>
            ) : stats.recentTickets.length === 0 ? (
              <p className="text-muted-foreground text-sm">No tickets yet</p>
            ) : (
              <div className="space-y-3">
                {stats.recentTickets.map((ticket: any) => (
                  <div key={ticket.ticket_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{ticket.issue?.substring(0, 50)}...</p>
                      <p className="text-xs text-muted-foreground mt-1">Priority: {ticket.priority}</p>
                    </div>
                    <Badge className={ticket.status === "resolved" ? "bg-green-500" : "bg-red-500"}>
                      {ticket.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
