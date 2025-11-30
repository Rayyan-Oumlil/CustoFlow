const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// API URL configuration (only log in development)
if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
  console.log("🔗 API_BASE_URL:", API_BASE_URL)
}

async function safeFetch<T>(
  fetchFn: () => Promise<Response>,
  retries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error | null = null
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchFn()
      if (!response.ok) {
        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          const errorText = await response.text().catch(() => response.statusText)
          throw new Error(`API error (${response.status}): ${errorText}`)
        }
        // Retry on server errors (5xx) and rate limits (429)
        if (attempt < retries) {
          const waitTime = delay * Math.pow(2, attempt) // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, waitTime))
          continue
        }
        const errorText = await response.text().catch(() => response.statusText)
        throw new Error(`API error (${response.status}): ${errorText}`)
      }
      return response.json()
    } catch (error) {
      lastError = error as Error
      
      // Network errors - retry with exponential backoff
      if (error instanceof TypeError && error.message === "Failed to fetch") {
        if (attempt < retries) {
          const waitTime = delay * Math.pow(2, attempt) // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, waitTime))
          continue
        }
        throw new Error(
          `Cannot connect to backend at ${API_BASE_URL} after ${retries + 1} attempts. ` +
          `Make sure the backend is running: python -m api.server`
        )
      }
      
      // If it's the last attempt, throw the error
      if (attempt === retries) {
        throw error
      }
      
      // Wait before retrying
      const waitTime = delay * Math.pow(2, attempt)
      await new Promise(resolve => setTimeout(resolve, waitTime))
    }
  }
  
  throw lastError || new Error("Unknown error occurred")
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

  async analyzeDocument(
    file: File,
    analysisType: string = "auto",
    context?: string
  ): Promise<{
    status: string
    document_type?: string
    extracted_data?: any
    text_content?: string
    summary?: string
    confidence?: number
    error_message?: string
  }> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("analysis_type", analysisType)
    if (context) {
      formData.append("context", context)
    }

    return safeFetch<{
      status: string
      document_type?: string
      extracted_data?: any
      text_content?: string
      summary?: string
      confidence?: number
      error_message?: string
    }>(() =>
      fetch(`${API_BASE_URL}/documents/analyze`, {
        method: "POST",
        body: formData,
      })
    )
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
  ticket_id?: string  // Optional ticket ID to link feedback to a ticket
}
