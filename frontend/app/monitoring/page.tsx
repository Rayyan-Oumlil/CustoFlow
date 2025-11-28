"use client"

import { useEffect, useState, useRef } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { ArrowUp, MessageCircle, RefreshCw, User, Bot } from "lucide-react"

interface ActiveSession {
  session_id: string
  user_id: string
  customer_id?: string
  name?: string
  message_count: number
  created_at: string
  updated_at: string
  is_active: boolean
}

export default function MonitoringPage() {
  const { initFromStorage, userId } = useStore()
  const [sessions, setSessions] = useState<ActiveSession[]>([])
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [messages, setMessages] = useState<Record<string, Message[]>>({})
  const [inputMessages, setInputMessages] = useState<Record<string, string>>({})
  const [sending, setSending] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const messagesEndRefs = useRef<Record<string, HTMLDivElement | null>>({})

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  const fetchSessions = async () => {
    try {
      const data = await apiClient.get<ActiveSession[]>("/sessions/all/active")
      setSessions(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error("Failed to fetch active sessions:", error)
      setSessions([])
    } finally {
      setLoading(false)
    }
  }

  const fetchMessages = async (sessionId: string) => {
    if (!userId) return
    
    try {
      const data = await apiClient.get(`/history/${userId}?session_id=${sessionId}`)
      
      let messagesArray: any[] = []
      if (Array.isArray(data)) {
        messagesArray = data
      } else if (data && typeof data === 'object' && 'history' in data) {
        messagesArray = Array.isArray((data as any).history) ? (data as any).history : []
      }
      
      const msgs = messagesArray.map((m: any, index: number) => {
        const isHumanAgent = m.metadata?.is_human_agent === true || 
                             m.metadata?.agent_used === "human_agent" ||
                             m.agent_used === "human_agent"
        
        return {
          id: m.id || `msg_${m.timestamp || Date.now()}_${index}`,
          role: m.role,
          content: m.content,
          agent_used: isHumanAgent ? "human_agent" : (m.metadata?.agent || m.metadata?.agent_used || m.agent_used),
          response_time: m.metadata?.response_time || m.response_time,
          timestamp: m.timestamp || m.created_at,
        }
      })
      
      setMessages(prev => ({ ...prev, [sessionId]: msgs }))
      
      // Auto-scroll to bottom
      setTimeout(() => {
        const ref = messagesEndRefs.current[sessionId]
        if (ref) {
          ref.scrollIntoView({ behavior: "smooth" })
        }
      }, 100)
    } catch (error) {
      console.error(`Failed to fetch messages for session ${sessionId}:`, error)
    }
  }

  const sendMessage = async (sessionId: string) => {
    const message = inputMessages[sessionId]?.trim()
    if (!message || sending[sessionId] || !userId) return

    const session = sessions.find(s => s.session_id === sessionId)
    if (!session) return

    setSending(prev => ({ ...prev, [sessionId]: true }))

    try {
      // Send message as human agent
      await apiClient.post("/sessions/send-message", {
        session_id: sessionId,
        user_id: session.user_id,
        customer_id: session.customer_id,
        message: message,
      })

      // Clear input
      setInputMessages(prev => ({ ...prev, [sessionId]: "" }))

      // Refresh messages
      setTimeout(() => {
        fetchMessages(sessionId)
      }, 500)
    } catch (error) {
      console.error(`Failed to send message to session ${sessionId}:`, error)
      alert("Failed to send message. Please try again.")
    } finally {
      setSending(prev => ({ ...prev, [sessionId]: false }))
    }
  }

  useEffect(() => {
    fetchSessions()
    const interval = setInterval(() => {
      fetchSessions()
      // Refresh messages for selected session
      if (selectedSession) {
        fetchMessages(selectedSession)
      }
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [selectedSession, userId])

  useEffect(() => {
    if (selectedSession) {
      fetchMessages(selectedSession)
    }
  }, [selectedSession, userId])

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
    } catch {
      return ""
    }
  }

  const selectedSessionData = sessions.find(s => s.session_id === selectedSession)
  const sessionMessages = selectedSession ? messages[selectedSession] || [] : []

  return (
    <div className="flex flex-col h-screen">
      <PageHeader 
        title="Active Sessions Monitoring" 
        description="Monitor and intervene in active customer conversations"
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Sessions List */}
        <div className="w-80 border-r bg-muted/30 flex flex-col">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold">Active Sessions ({sessions.length})</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchSessions}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
          
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-2">
              {sessions.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  {loading ? "Loading..." : "No active sessions"}
                </div>
              ) : (
                sessions.map((session) => (
                  <Card
                    key={session.session_id}
                    className={`cursor-pointer transition-colors ${
                      selectedSession === session.session_id
                        ? "bg-primary/10 border-primary"
                        : "hover:bg-muted/50"
                    }`}
                    onClick={() => setSelectedSession(session.session_id)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">
                            {session.name || `Session ${session.session_id.slice(-8)}`}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {session.customer_id ? `Customer: ${session.customer_id}` : `User: ${session.user_id?.slice(0, 8)}`}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="text-xs">
                              {session.message_count} messages
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {formatTime(session.updated_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Chat View */}
        <div className="flex-1 flex flex-col">
          {selectedSession ? (
            <>
              <div className="p-4 border-b bg-background">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">
                      {selectedSessionData?.name || `Session ${selectedSession.slice(-8)}`}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {selectedSessionData?.customer_id 
                        ? `Customer: ${selectedSessionData.customer_id}` 
                        : `User: ${selectedSessionData?.user_id?.slice(0, 8)}`}
                    </p>
                  </div>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                    Active
                  </Badge>
                </div>
              </div>

              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {sessionMessages.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">
                      No messages yet
                    </div>
                  ) : (
                    sessionMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex gap-3 ${
                          msg.role === "user" ? "justify-end" : "justify-start"
                        }`}
                      >
                        {msg.role === "assistant" && (
                          <div className="flex-shrink-0">
                            {msg.agent_used === "human_agent" ? (
                              <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                                <User className="w-4 h-4 text-green-600 dark:text-green-400" />
                              </div>
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                <Bot className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                              </div>
                            )}
                          </div>
                        )}
                        <div
                          className={`max-w-[70%] rounded-lg px-4 py-2 ${
                            msg.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : msg.agent_used === "human_agent"
                              ? "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800"
                              : "bg-muted"
                          }`}
                        >
                          {msg.role === "assistant" && msg.agent_used && (
                            <div className="mb-1">
                              <Badge
                                variant="outline"
                                className={`text-xs ${
                                  msg.agent_used === "human_agent"
                                    ? "bg-green-100 text-green-800 border-green-300"
                                    : "bg-blue-100 text-blue-800 border-blue-300"
                                }`}
                              >
                                {msg.agent_used === "human_agent" ? "👤 Human Agent" : `🤖 ${msg.agent_used}`}
                              </Badge>
                            </div>
                          )}
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          <p className="text-xs opacity-70 mt-1">
                            {formatTime(msg.timestamp)}
                          </p>
                        </div>
                        {msg.role === "user" && (
                          <div className="flex-shrink-0">
                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                              <User className="w-4 h-4 text-primary" />
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                  <div ref={(el) => { if (selectedSession) messagesEndRefs.current[selectedSession] = el }} />
                </div>
              </ScrollArea>

              <div className="p-4 border-t bg-background">
                <form
                  onSubmit={(e) => {
                    e.preventDefault()
                    sendMessage(selectedSession)
                  }}
                  className="flex gap-2"
                >
                  <Input
                    value={inputMessages[selectedSession] || ""}
                    onChange={(e) =>
                      setInputMessages(prev => ({ ...prev, [selectedSession]: e.target.value }))
                    }
                    placeholder="Type your message to intervene..."
                    disabled={sending[selectedSession]}
                    className="flex-1"
                  />
                  <Button
                    type="submit"
                    disabled={!inputMessages[selectedSession]?.trim() || sending[selectedSession]}
                    size="icon"
                  >
                    <ArrowUp className="w-4 h-4" />
                  </Button>
                </form>
                <p className="text-xs text-muted-foreground mt-2">
                  Your message will appear as from a human agent
                </p>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              Select a session to view conversation
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

