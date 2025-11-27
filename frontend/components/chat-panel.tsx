"use client"

import { useEffect, useState, useRef } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowUp, Bot, User } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface ChatPanelProps {
  customerId: string
  sessionId: string
  userId: string
  ticketId?: string
}

export function ChatPanel({ customerId, sessionId, userId, ticketId }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Fetch messages when session changes
  useEffect(() => {
    if (!userId || !sessionId) return

    const fetchMessages = async () => {
      try {
        const data = await apiClient.get(`/history/${userId}?session_id=${sessionId}`)
        
        let messagesArray: any[] = []
        if (Array.isArray(data)) {
          messagesArray = data
        } else if (data && typeof data === 'object' && 'history' in data) {
          messagesArray = Array.isArray((data as any).history) ? (data as any).history : []
        }
        
        const msgs = messagesArray.map((m: any, index: number) => {
          // Check for human agent in multiple ways
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
        setMessages(msgs)
      } catch (error) {
        console.error("Failed to fetch messages:", error)
        setMessages([])
      }
    }

    fetchMessages()
    // Poll every 5 seconds (reduced from 2s to reduce server load)
    const interval = setInterval(fetchMessages, 5000)
    return () => clearInterval(interval)
  }, [userId, sessionId])

  // Auto-scroll to bottom only if user is already at bottom (don't force scroll)
  useEffect(() => {
    // Find the scrollable container (the div with overflow-y-auto)
    const messagesContainer = document.querySelector('.flex-1.overflow-y-auto')
    if (messagesContainer) {
      const container = messagesContainer as HTMLElement
      const isNearBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100
      // Only auto-scroll if user is already near the bottom
      if (isNearBottom) {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
        }, 100)
      }
    } else {
      // Fallback: scroll if container not found (first load)
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
      }, 100)
    }
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending || !ticketId) return

    const userMessage = input
    setInput("")

    // Don't show typing indicator - human agent is typing, not AI
    // setSending(true) - REMOVED

    try {
      // Send message via ticket endpoint (human agent response)
      await apiClient.sendTicketMessage(ticketId, userMessage)
      
      // Add human agent message immediately with label
      // Message will also appear via polling, but add immediately for instant feedback
      const agentMsg: Message = {
        id: `agent_${Date.now()}`,
        role: "assistant",
        content: userMessage,
        agent_used: "human_agent",
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, agentMsg])
    } catch (error: any) {
      console.error("Failed to send message:", error)
      const errorMsg: Message = {
        id: `error_${Date.now()}`,
        role: "assistant",
        content: `Error: ${error.message || "Failed to send message. Please try again."}`,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      // setSending(false) - REMOVED (was never set to true)
      if (inputRef.current) {
        setTimeout(() => {
          inputRef.current?.focus()
        }, 0)
      }
    }
  }

  return (
    <div className="flex flex-col h-full max-h-full overflow-hidden">
      {/* Header */}
      <div className="border-b p-4 bg-muted/50 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Chat with Customer</h3>
            <p className="text-xs text-muted-foreground">
              Customer: {customerId} {ticketId && `• Ticket ${ticketId}`}
            </p>
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">
              👤 You are responding as a Human Agent
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((msg) => {
              // Invert perspective: user messages (customer) on left, assistant messages (agent) on right
              const isFromAgent = msg.role === "assistant"
              const isFromCustomer = msg.role === "user"
              
              return (
                <div
                  key={msg.id}
                  className={`flex ${isFromCustomer ? "justify-start" : "justify-end"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      isFromCustomer
                        ? "bg-muted text-foreground"
                        : isFromAgent && msg.agent_used === "human_agent"
                        ? "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-foreground"
                        : "bg-primary text-primary-foreground"
                    }`}
                  >
                    {/* Show Human Agent label at the top for human agent messages */}
                    {isFromAgent && msg.agent_used === "human_agent" && (
                      <div className="mb-2 pb-2 border-b border-green-200 dark:border-green-800">
                        <Badge className="text-xs bg-green-600 text-white dark:bg-green-700 dark:text-green-100 border-0">
                          👤 Human Agent
                        </Badge>
                      </div>
                    )}
                    <div className="flex items-start gap-2">
                      {isFromCustomer ? (
                        <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      ) : (
                        <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className={`text-sm whitespace-pre-wrap break-words ${
                          isFromAgent && msg.agent_used === "human_agent" ? "text-foreground" : ""
                        }`}>{msg.content}</p>
                        {isFromAgent && msg.agent_used && msg.agent_used !== "human_agent" && (
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs">
                              {msg.agent_used}
                            </Badge>
                            {msg.response_time && (
                              <span className="text-xs text-muted-foreground">
                                {msg.response_time.toFixed(2)}s
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
          {sending && (
            <div className="flex justify-start">
              <div className="max-w-xs px-4 py-2 rounded-lg bg-muted text-foreground">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-xs text-muted-foreground">Agent is typing...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t p-4 bg-background flex-shrink-0">
        <form onSubmit={sendMessage} className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={sending}
            className="flex-1"
          />
          <Button type="submit" disabled={sending || !input.trim()} size="icon">
            <ArrowUp className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}

