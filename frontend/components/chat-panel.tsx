"use client"

import { useEffect, useState, useRef } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
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
        
        const msgs = messagesArray.map((m: any, index: number) => ({
          id: m.id || `msg_${m.timestamp || Date.now()}_${index}`,
          role: m.role,
          content: m.content,
          agent_used: m.metadata?.agent || m.agent_used,
          response_time: m.metadata?.response_time || m.response_time,
          timestamp: m.timestamp || m.created_at,
        }))
        setMessages(msgs)
      } catch (error) {
        console.error("Failed to fetch messages:", error)
        setMessages([])
      }
    }

    fetchMessages()
    const interval = setInterval(fetchMessages, 2000) // Refresh every 2 seconds
    return () => clearInterval(interval)
  }, [userId, sessionId])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return

    const userMessage = input
    setInput("")

    // Add user message immediately
    const userMsg: Message = {
      id: `user_${Date.now()}`,
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])

    setSending(true)

    try {
      const response = await apiClient.post<{
        response: string
        session_id: string
        agent_used?: string
        response_time?: number
      }>("/chat", {
        user_id: userId,
        session_id: sessionId,
        message: userMessage,
        customer_id: customerId,
      })

      // Add assistant response
      const assistantMsg: Message = {
        id: `assistant_${Date.now()}`,
        role: "assistant",
        content: response.response,
        agent_used: response.agent_used,
        response_time: response.response_time,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])
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
      setSending(false)
      if (inputRef.current) {
        setTimeout(() => {
          inputRef.current?.focus()
        }, 0)
      }
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4 bg-muted/50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Chat with Customer</h3>
            <p className="text-xs text-muted-foreground">
              {customerId} {ticketId && `• Ticket ${ticketId}`}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {msg.role === "user" ? (
                      <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    ) : (
                      <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                      {msg.role === "assistant" && msg.agent_used && (
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            {msg.agent_used === "human_agent" ? "Human Agent" : msg.agent_used}
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
            ))
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
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4 bg-background">
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

