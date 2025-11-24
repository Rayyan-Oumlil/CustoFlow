"use client"

import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"
import { apiClient } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card } from "@/components/ui/card"

interface Stats {
  sessions: number
  active_session: boolean
  message_count: number
}

export default function HomePage() {
  const { userId, initFromStorage } = useStore()
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  useEffect(() => {
    if (!userId) return

    const fetchStats = async () => {
      try {
        const [sessions, health] = await Promise.all([apiClient.get(`/sessions/${userId}`), apiClient.get("/health")])
        setStats({
          sessions: Array.isArray(sessions) ? sessions.length : 0,
          active_session: true,
          message_count: Array.isArray(sessions)
            ? sessions.reduce((sum, s: any) => sum + (s.message_count || 0), 0)
            : 0,
        })
      } catch (error) {
        console.error("Failed to fetch stats:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [userId])

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Welcome to CustoFlow" description="Your Intelligent Customer Support System" />

      <div className="flex-1 overflow-auto px-8 py-8">
        <div className="grid grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Total Sessions</p>
            <p className="text-3xl font-bold mt-2">{loading ? "-" : stats?.sessions || 0}</p>
          </Card>

          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Active Session</p>
            <p className="text-3xl font-bold mt-2">{loading ? "-" : stats?.active_session ? "Yes" : "No"}</p>
          </Card>

          <Card className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Messages</p>
            <p className="text-3xl font-bold mt-2">{loading ? "-" : stats?.message_count || 0}</p>
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Navigation</h2>
          <p className="text-muted-foreground text-sm">
            Use the sidebar to navigate between Chat for conversations, Orders to manage customer orders and support
            tickets, and Analytics for real-time performance metrics.
          </p>
        </Card>
      </div>
    </div>
  )
}
