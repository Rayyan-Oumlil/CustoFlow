"use client"

import type React from "react"

import { useEffect, useState, useRef } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowUp, Plus } from "lucide-react"

interface Conversation {
  session_id: string
  name: string
  message_count: number
  created_at: string
}

export default function ChatPage() {
  const { userId, sessionId, setSessionId, initFromStorage } = useStore()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  useEffect(() => {
    if (!userId) return

    const fetchConversations = async () => {
      try {
        setLoading(true)
        const data = await apiClient.get(`/sessions/${userId}`)
        const convos = Array.isArray(data)
          ? data.map((s: any) => ({
              session_id: s.session_id,
              name: `Session ${s.session_id.slice(0, 8)}`,
              message_count: s.message_count || 0,
              created_at: s.created_at,
            }))
          : []
        setConversations(convos)
        if (convos.length > 0 && !sessionId) {
          setSessionId(convos[0].session_id)
        } else if (convos.length === 0 && !sessionId && userId) {
          // Auto-create a session if none exists
          createNewConversation()
        }
      } catch (error) {
        console.error("Failed to fetch conversations:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchConversations()
  }, [userId, sessionId, setSessionId])

  useEffect(() => {
    if (!userId || !sessionId) return

    const fetchMessages = async () => {
      try {
        const data = await apiClient.get(`/history/${userId}?session_id=${sessionId}`)
        console.log("Fetched messages from API:", data)
        
        // Handle both array and object response formats
        let messagesArray = []
        if (Array.isArray(data)) {
          messagesArray = data
        } else if (data && typeof data === 'object' && 'history' in data) {
          messagesArray = data.history || []
        }
        
        const msgs = messagesArray.map((m: any, index: number) => ({
          id: m.id || `msg_${m.timestamp || Date.now()}_${index}`,
          role: m.role,
          content: m.content,
          agent_used: m.metadata?.agent || m.agent_used,
          response_time: m.metadata?.response_time || m.response_time,
          timestamp: m.timestamp || m.created_at,
        }))
        console.log("Mapped messages:", msgs)
        setMessages(msgs)
      } catch (error) {
        console.error("Failed to fetch messages:", error)
        setMessages([]) // Set empty array on error to prevent stale data
      }
    }

    fetchMessages()
  }, [userId, sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const createNewConversation = async () => {
    if (!userId) return
    try {
      const data = await apiClient.post("/sessions/create", { user_id: userId })
      const newSession = {
        session_id: data.session_id,
        name: `Session ${data.session_id.slice(0, 8)}`,
        message_count: 0,
        created_at: new Date().toISOString(),
      }
      setConversations([newSession, ...conversations])
      setSessionId(data.session_id)
      setMessages([])
    } catch (error) {
      console.error("Failed to create conversation:", error)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return
    
    // Create session if it doesn't exist
    let currentSessionId = sessionId
    if (!currentSessionId && userId) {
      try {
        const data = await apiClient.post("/sessions/create", { user_id: userId })
        currentSessionId = data.session_id
        setSessionId(currentSessionId)
        const newSession = {
          session_id: currentSessionId,
          name: `Session ${currentSessionId.slice(0, 8)}`,
          message_count: 0,
          created_at: new Date().toISOString(),
        }
        setConversations([newSession, ...conversations])
      } catch (error) {
        console.error("Failed to create session:", error)
        return
      }
    }
    
    if (!currentSessionId) return

    const userMessage = input
    setInput("")
    setSending(true)

    try {
      const response = await apiClient.post<{
        response: string
        session_id: string
        agent_used?: string
        response_time?: number
      }>("/chat", {
        user_id: userId,
        session_id: currentSessionId,
        message: userMessage,
      })

      // Add user message immediately
      const userMsg: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content: userMessage,
        timestamp: new Date().toISOString(),
      }
      setMessages([...messages, userMsg])

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

      // Reload messages from backend to ensure consistency
      if (userId && currentSessionId) {
        setTimeout(async () => {
          try {
            const data = await apiClient.get(`/history/${userId}?session_id=${currentSessionId}`)
            console.log("Reloaded messages from API:", data)
            
            // Handle both array and object response formats
            let messagesArray = []
            if (Array.isArray(data)) {
              messagesArray = data
            } else if (data && typeof data === 'object' && 'history' in data) {
              messagesArray = data.history || []
            }
            
            const msgs = messagesArray.map((m: any, index: number) => ({
              id: m.id || `msg_${m.timestamp || Date.now()}_${index}`,
              role: m.role,
              content: m.content,
              agent_used: m.metadata?.agent || m.agent_used,
              response_time: m.metadata?.response_time || m.response_time,
              timestamp: m.timestamp || m.created_at,
            }))
            console.log("Reloaded mapped messages:", msgs)
            setMessages(msgs) // Always set, even if empty
          } catch (error) {
            console.error("Failed to reload messages:", error)
          }
        }, 1000) // Increased delay to ensure backend has saved
      }
    } catch (error: any) {
      console.error("Failed to send message:", error)
      const errorMsg: Message = {
        id: `error_${Date.now()}`,
        role: "assistant",
        content: `Error: ${error.message || "Failed to send message. Please try again."}`,
        timestamp: new Date().toISOString(),
      }
      setMessages([...messages, errorMsg])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Chat" description="Manage customer conversations" />

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="border-b border-border p-4">
          <Select
            value={sessionId || "new"}
            onValueChange={(value) => {
              if (value === "new") {
                createNewConversation()
              } else {
                setSessionId(value)
              }
            }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select conversation">
                {sessionId 
                  ? (conversations.find(c => c.session_id === sessionId)?.name || `Session ${sessionId.slice(0, 8)}`)
                  : "New Conversation"}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="new">
                <div className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  <span>New Conversation</span>
                </div>
              </SelectItem>
              {conversations.map((conv) => (
                <SelectItem key={conv.session_id} value={conv.session_id}>
                  <div className="flex flex-col">
                    <span>{conv.name}</span>
                    <span className="text-xs text-muted-foreground">{conv.message_count} messages</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 overflow-hidden flex">
          <div className="w-64 border-r border-border flex flex-col">
            <div className="p-4 border-b border-border bg-muted/50">
              <p className="text-xs font-medium text-muted-foreground mb-1">Current Conversation:</p>
              <p className="text-sm font-semibold truncate">
                {sessionId 
                  ? (conversations.find(c => c.session_id === sessionId)?.name || `Session ${sessionId.slice(0, 8)}`)
                  : "None selected"}
              </p>
            </div>
            <ScrollArea className="flex-1">
              <div className="space-y-2 p-4">
                {conversations.map((conv) => (
                  <button
                    key={conv.session_id}
                    onClick={() => setSessionId(conv.session_id)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      sessionId === conv.session_id
                        ? "bg-muted text-foreground font-medium"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    <p className="truncate">{conv.name}</p>
                    <p className="text-xs mt-1">{conv.message_count} messages</p>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </div>

          <div className="flex-1 flex flex-col">
            <ScrollArea className="flex-1">
              <div className="p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    Start a conversation by typing a message
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-xs px-4 py-2 rounded-lg ${
                          msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                        {msg.role === "assistant" && msg.agent_used && (
                          <p className="text-xs mt-1 opacity-70">
                            {msg.agent_used} • {msg.response_time?.toFixed(2)}s
                          </p>
                        )}
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="border-t border-border p-4">
              <form onSubmit={sendMessage} className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message here..."
                  disabled={sending || !userId}
                  autoFocus
                />
                <Button type="submit" disabled={sending || !userId || !input.trim()} size="icon">
                  <ArrowUp className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
