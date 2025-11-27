const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function safeFetch<T>(fetchFn: () => Promise<Response>): Promise<T> {
  try {
    const response = await fetchFn()
    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText)
      throw new Error(`API error (${response.status}): ${errorText}`)
    }
    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new Error(
        `Cannot connect to backend at ${API_BASE_URL}. ` +
        `Make sure the backend is running: python -m api.server`
      )
    }
    throw error
  }
}

export const apiClient = {
  async get<T>(endpoint: string): Promise<T> {
    return safeFetch<T>(() => fetch(`${API_BASE_URL}${endpoint}`))
  },

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return safeFetch<T>(() =>
      fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
    )
  },

  async delete<T>(endpoint: string): Promise<T> {
    return safeFetch<T>(() =>
      fetch(`${API_BASE_URL}${endpoint}`, {
        method: "DELETE",
      })
    )
  },

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return safeFetch<T>(() =>
      fetch(`${API_BASE_URL}${endpoint}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
    )
  },

  async submitFeedback(data: FeedbackRequest): Promise<{ status: string; message: string; feedback_id?: string }> {
    return this.post<{ status: string; message: string; feedback_id?: string }>("/feedback", data)
  },
  
  async sendTicketMessage(ticketId: string, message: string): Promise<{ status: string; message: string }> {
    return this.post<{ status: string; message: string }>(`/tickets/${ticketId}/message`, { message })
  },
  
  async transcribeAudio(audioFile: File, languageCode: string = "en-US"): Promise<{ status: string; transcript: string }> {
    const formData = new FormData()
    formData.append("audio", audioFile)
    formData.append("language_code", languageCode)
    
    return safeFetch<{ status: string; transcript: string }>(() =>
      fetch(`${API_BASE_URL}/speech/transcribe`, {
        method: "POST",
        body: formData,
      })
    )
  },
  
  async synthesizeSpeech(text: string, languageCode: string = "en-US", voiceName?: string): Promise<Blob> {
    try {
      const response = await fetch(`${API_BASE_URL}/speech/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language_code: languageCode, voice_name: voiceName }),
      })
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText)
        throw new Error(`Failed to synthesize speech: ${errorText}`)
      }
      
      const blob = await response.blob()
      
      // Verify it's actually audio data
      if (blob.size === 0 || !blob.type.startsWith('audio/')) {
        throw new Error("Invalid audio data received from server")
      }
      
      return blob
    } catch (error) {
      if (error instanceof TypeError && error.message === "Failed to fetch") {
        throw new Error(
          `Cannot connect to backend at ${API_BASE_URL}. ` +
          `Make sure the backend is running: python -m api.server`
        )
      }
      throw error
    }
  },

  async closeSession(sessionId: string) {
    return this.put<{ status: string; message: string }>(`/sessions/${sessionId}/close`, {})
  },

  async reopenSession(sessionId: string) {
    return this.put<{ status: string; message: string }>(`/sessions/${sessionId}/reopen`, {})
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
  closed_sessions?: number
  interactions: number
  avg_satisfaction: number
  tickets_created: number
  open_tickets?: number
  resolved_tickets?: number
  resolution_rate?: number
  avg_response_time?: number
}

export interface FeedbackRequest {
  session_id: string
  feedback_type: "thumbs_up" | "thumbs_down" | "rating"
  rating?: number
  comment?: string
  user_id?: string
  reason?: string
  category?: string
  agent_used?: string
}
