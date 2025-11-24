const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const apiClient = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`)
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  },

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  },
}

export interface Session {
  user_id: string
  session_id: string
  message_count: number
  created_at: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  agent_used?: string
  response_time?: number
  timestamp: string
}

export interface Order {
  order_id: string
  customer_id: string
  status: "processing" | "shipped" | "delivered" | "cancelled"
  total: number
  items?: Array<{ name: string; quantity: number; price: number }>
  tracking_number?: string
  estimated_delivery?: string
  created_at: string
}

export interface Ticket {
  ticket_id: string
  customer_id?: string
  user_id?: string
  session_id?: string
  issue: string
  priority: "low" | "normal" | "high" | "urgent"
  status: "open" | "in_progress" | "resolved"
  created_at: string
}

export interface Analytics {
  total_messages: number
  active_sessions: number
  interactions: number
  avg_satisfaction: number
  tickets_created: number
}
