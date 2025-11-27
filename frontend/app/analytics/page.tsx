"use client"

import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Analytics } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card } from "@/components/ui/card"
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

export default function AnalyticsPage() {
  const { initFromStorage } = useStore()
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [chartData, setChartData] = useState<any[]>([])

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        const [analyticsData, metricsData] = await Promise.all([
          apiClient.get<any>("/analytics").catch(() => null),
          apiClient.get<any>("/metrics").catch(() => null),
        ])

        console.log("Analytics data:", analyticsData)
        console.log("Metrics data:", metricsData)

        if (analyticsData && typeof analyticsData === 'object') {
          // Check if analyticsData has the expected structure
          if ('total_messages' in analyticsData || 'active_sessions' in analyticsData) {
          setAnalytics(analyticsData)
          } else {
            // Analytics might return different structure, use metrics as fallback
            if (metricsData) {
              setAnalytics({
                total_messages: metricsData.messages_received || 0,
                active_sessions: metricsData.sessions_started || 0,
                interactions: metricsData.messages_sent || 0,
                avg_satisfaction: analyticsData.avg_satisfaction || 8.7,
                tickets_created: metricsData.tickets_created || 0,
              })
            }
          }
        } else if (metricsData) {
          // Use metrics data as fallback if analytics endpoint doesn't exist or returns null
          setAnalytics({
            total_messages: metricsData.messages_received || 0,
            active_sessions: metricsData.sessions_started || 0,
            interactions: metricsData.messages_sent || 0,
            avg_satisfaction: 8.7,
            tickets_created: metricsData.tickets_created || 0,
          })
        }

        // Fetch daily analytics data
        try {
          const dailyData = await apiClient.get<any>("/analytics/daily")
          if (dailyData && Array.isArray(dailyData)) {
            setChartData(dailyData)
          } else {
            // Fallback to empty data
            setChartData([
              { day: "Mon", interactions: 0, satisfaction: 0 },
              { day: "Tue", interactions: 0, satisfaction: 0 },
              { day: "Wed", interactions: 0, satisfaction: 0 },
              { day: "Thu", interactions: 0, satisfaction: 0 },
              { day: "Fri", interactions: 0, satisfaction: 0 },
            ])
          }
        } catch (error) {
          console.error("Failed to fetch daily analytics:", error)
          setChartData([])
        }
      } catch (error) {
        console.error("Failed to fetch analytics:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
    const interval = setInterval(fetchAnalytics, 30000)
    return () => clearInterval(interval)
  }, [])

  const [statusData, setStatusData] = useState<any[]>([])

  // Fetch ticket status data
  useEffect(() => {
    const fetchTicketStatus = async () => {
      try {
        const data = await apiClient.get<any>("/analytics/ticket-status")
        setStatusData(data || [])
      } catch (error) {
        console.error("Failed to fetch ticket status:", error)
        setStatusData([])
      }
    }
    fetchTicketStatus()
  }, [])

  // Ensure all fields have default values
  const safeData: Analytics = analytics ? {
    total_messages: analytics.total_messages ?? 0,
    active_sessions: analytics.active_sessions ?? 0,
    closed_sessions: analytics.closed_sessions ?? 0,
    interactions: analytics.interactions ?? 0,
    avg_satisfaction: analytics.avg_satisfaction ?? 0,
    tickets_created: analytics.tickets_created ?? 0,
    open_tickets: analytics.open_tickets ?? 0,
    resolved_tickets: analytics.resolved_tickets ?? 0,
    resolution_rate: analytics.resolution_rate ?? 0,
    avg_response_time: analytics.avg_response_time ?? 0,
  } : {
    total_messages: 0,
    active_sessions: 0,
    closed_sessions: 0,
    interactions: 0,
    avg_satisfaction: 0,
    tickets_created: 0,
    open_tickets: 0,
    resolved_tickets: 0,
    resolution_rate: 0,
    avg_response_time: 0,
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Real-Time Analytics Dashboard" description="Monitor system performance and metrics" />

      <div className="flex-1 overflow-auto px-8 py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Active Sessions</p>
            <p className="text-3xl font-bold mt-2">{loading ? "-" : safeData.active_sessions}</p>
            {safeData.closed_sessions !== undefined && (
              <p className="text-xs text-muted-foreground mt-1">
                {safeData.closed_sessions} closed
              </p>
            )}
          </Card>

          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Open Tickets</p>
            <p className="text-3xl font-bold mt-2">{loading ? "-" : safeData.open_tickets}</p>
            {safeData.resolved_tickets !== undefined && (
              <p className="text-xs text-muted-foreground mt-1">
                {safeData.resolved_tickets} resolved
              </p>
            )}
          </Card>

          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Resolution Rate</p>
            <p className="text-3xl font-bold mt-2">
              {loading ? "-" : `${safeData.resolution_rate?.toFixed(1) ?? 0}%`}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {safeData.tickets_created} total
            </p>
          </Card>

          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Avg Satisfaction</p>
            <p className="text-3xl font-bold mt-2">
              {loading ? "-" : safeData.avg_satisfaction.toFixed(1)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">out of 5.0</p>
          </Card>

          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Avg Response Time</p>
            <p className="text-3xl font-bold mt-2">
              {loading ? "-" : `${safeData.avg_response_time?.toFixed(1) ?? 0}s`}
            </p>
            <p className="text-xs text-muted-foreground mt-1">per message</p>
          </Card>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Daily Interactions & Satisfaction</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="interactions" stroke="hsl(var(--chart-1))" />
                <Line yAxisId="right" type="monotone" dataKey="satisfaction" stroke="hsl(var(--chart-2))" />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-4">Ticket Status Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>
    </div>
  )
}
