"use client"

import type React from "react"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowUp, Plus, Trash2, LogOut, Pencil, ThumbsUp, ThumbsDown, Mic, MicOff, Volume2, VolumeX } from "lucide-react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"

interface Conversation {
  session_id: string
  name: string
  message_count: number
  created_at: string
}

export default function ChatPage() {
  const { userId, customerId, sessionId, setSessionId, setCustomerId, initFromStorage, logout } = useStore()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [editingName, setEditingName] = useState<string | null>(null)
  const [newName, setNewName] = useState("")
  const [showCustomerIdPrompt, setShowCustomerIdPrompt] = useState(false)
  const [inputCustomerId, setInputCustomerId] = useState("")
  const [customerIdError, setCustomerIdError] = useState("")
  const [feedbackGiven, setFeedbackGiven] = useState<Set<string>>(new Set())
  const [submittingFeedback, setSubmittingFeedback] = useState<string | null>(null)
  const [isFeedbackDialogOpen, setIsFeedbackDialogOpen] = useState(false)
  const [selectedMessageForFeedback, setSelectedMessageForFeedback] = useState<{ id: string; agentUsed?: string } | null>(null)
  const [feedbackType, setFeedbackType] = useState<"thumbs_up" | "thumbs_down">("thumbs_down")
  const [feedbackComment, setFeedbackComment] = useState("")
  const [feedbackReason, setFeedbackReason] = useState("")
  const [feedbackCategory, setFeedbackCategory] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [audioEnabled, setAudioEnabled] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])
  const [recordingDuration, setRecordingDuration] = useState(0)
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  useEffect(() => {
    initFromStorage()
    // Show customer ID prompt if not set
    if (!customerId) {
      setShowCustomerIdPrompt(true)
    }
  }, [customerId, initFromStorage])

  useEffect(() => {
    if (!userId || !customerId) return

    const fetchConversations = async () => {
      try {
        setLoading(true)
        // Always include customer_id as query parameter to filter sessions strictly
        const url = `/sessions/${userId}?customer_id=${encodeURIComponent(customerId)}`
        const data = await apiClient.get(url)
        console.log("Fetched sessions from API for customer_id:", customerId, "data:", data)
        
        // Handle both array and object response formats
        let sessionsArray: any[] = []
        if (Array.isArray(data)) {
          sessionsArray = data
        } else if (data && typeof data === 'object' && 'sessions' in data) {
          sessionsArray = Array.isArray((data as any).sessions) ? (data as any).sessions : []
        }
        
        // Additional client-side filter to ensure only sessions with matching customer_id are shown
        const filteredSessions = sessionsArray.filter((s: any) => {
          return s.customer_id === customerId
        })
        
        const convos = filteredSessions.map((s: any) => ({
              session_id: s.session_id,
          name: s.name || `Session ${s.session_id.slice(-8)}`, // Use name from DB or generate from last 8 chars
              message_count: s.message_count || 0,
              created_at: s.created_at,
            }))
        console.log("Mapped conversations for customer_id:", customerId, "conversations:", convos)
        setConversations(convos)
        // Clear current session if it doesn't belong to this customer
        if (sessionId && !convos.find(c => c.session_id === sessionId)) {
          setSessionId(null)
        }
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, customerId]) // Depend on both userId and customerId to refetch when customer changes

  useEffect(() => {
    if (!userId || !sessionId) return

    const fetchMessages = async () => {
      try {
        const data = await apiClient.get(`/history/${userId}?session_id=${sessionId}`)
        console.log("Fetched messages from API:", data)
        
        // Handle both array and object response formats
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
  }, [messages, sending])

  const createNewConversation = async () => {
    if (!userId || !customerId) return
    try {
      const data = await apiClient.post<any>("/sessions/create", { 
        user_id: userId,
        customer_id: customerId
      })
      const sessionId = data?.session_id as string
      if (!sessionId) {
        throw new Error("Failed to create session: no session_id returned")
      }
      const newSession: Conversation = {
        session_id: sessionId,
        name: (data?.metadata?.name as string) || `Session ${sessionId.slice(-8)}`,
        message_count: 0,
        created_at: (data?.metadata?.created_at as string) || new Date().toISOString(),
      }
      setConversations([newSession, ...conversations])
      setSessionId(sessionId)
      setMessages([])
    } catch (error) {
      console.error("Failed to create conversation:", error)
    }
  }

  const renameConversation = async (sessionIdToRename: string, newName: string) => {
    if (!newName.trim()) return
    
    try {
      await apiClient.put(`/sessions/${sessionIdToRename}/rename`, { new_name: newName.trim() })
      // Update local state
      setConversations(conversations.map(c => 
        c.session_id === sessionIdToRename 
          ? { ...c, name: newName.trim() }
          : c
      ))
      setEditingName(null)
      setNewName("")
    } catch (error) {
      console.error("Failed to rename conversation:", error)
      alert("Failed to rename conversation. Please try again.")
    }
  }

  const deleteConversation = async (sessionIdToDelete: string) => {
    if (!confirm(`Are you sure you want to delete this session? This will delete all messages in this conversation.`)) {
      return
    }
    
    try {
      await apiClient.delete(`/sessions/${sessionIdToDelete}`)
      // Remove from conversations list
      setConversations(conversations.filter(c => c.session_id !== sessionIdToDelete))
      // If deleted session was active, clear it
      if (sessionId === sessionIdToDelete) {
        setSessionId(null)
        setMessages([])
        // Select first remaining session if any
        const remaining = conversations.filter(c => c.session_id !== sessionIdToDelete)
        if (remaining.length > 0) {
          setSessionId(remaining[0].session_id)
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error)
      alert("Failed to delete session. Please try again.")
    }
  }

  // Convert WebM to WAV using Web Audio API
  const convertWebMToWAV = async (webmBlob: Blob): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = async () => {
        try {
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
            sampleRate: 16000 // Force 16kHz sample rate
          })
          
          const audioBuffer = await audioContext.decodeAudioData(reader.result as ArrayBuffer)
          console.log(`Decoded audio: ${audioBuffer.duration.toFixed(2)}s, ${audioBuffer.sampleRate}Hz, ${audioBuffer.numberOfChannels} channels`)
          
          // Check if audio is long enough
          if (audioBuffer.duration < 0.3) {
            reject(new Error("Audio too short (less than 0.3 seconds)"))
            return
          }
          
          // Convert to mono and resample to 16kHz if needed
          let processedBuffer = audioBuffer
          if (audioBuffer.numberOfChannels > 1 || audioBuffer.sampleRate !== 16000) {
            const offlineContext = new OfflineAudioContext(1, audioBuffer.duration * 16000, 16000)
            const source = offlineContext.createBufferSource()
            source.buffer = audioBuffer
            
            // Convert to mono if needed
            if (audioBuffer.numberOfChannels > 1) {
              const merger = offlineContext.createChannelMerger(1)
              source.connect(merger)
              merger.connect(offlineContext.destination)
            } else {
              source.connect(offlineContext.destination)
            }
            
            source.start()
            processedBuffer = await offlineContext.startRendering()
            console.log(`Processed audio: ${processedBuffer.duration.toFixed(2)}s, ${processedBuffer.sampleRate}Hz, ${processedBuffer.numberOfChannels} channels`)
          }
          
          // Convert to WAV
          const wav = audioBufferToWav(processedBuffer)
          const wavBlob = new Blob([wav], { type: 'audio/wav' })
          resolve(wavBlob)
        } catch (error) {
          console.error("Error converting audio:", error)
          reject(error)
        }
      }
      reader.onerror = (e) => {
        console.error("FileReader error:", e)
        reject(new Error("Failed to read audio file"))
      }
      reader.readAsArrayBuffer(webmBlob)
    })
  }
  
  // Convert AudioBuffer to WAV format
  const audioBufferToWav = (buffer: AudioBuffer): ArrayBuffer => {
    const length = buffer.length
    const numberOfChannels = buffer.numberOfChannels
    const sampleRate = buffer.sampleRate
    const bytesPerSample = 2
    const blockAlign = numberOfChannels * bytesPerSample
    const byteRate = sampleRate * blockAlign
    const dataSize = length * blockAlign
    const bufferSize = 44 + dataSize
    const arrayBuffer = new ArrayBuffer(bufferSize)
    const view = new DataView(arrayBuffer)
    
    // WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
      }
    }
    
    writeString(0, 'RIFF')
    view.setUint32(4, bufferSize - 8, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true) // fmt chunk size
    view.setUint16(20, 1, true) // audio format (1 = PCM)
    view.setUint16(22, numberOfChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, 16, true) // bits per sample
    writeString(36, 'data')
    view.setUint32(40, dataSize, true)
    
    // Convert float samples to 16-bit PCM
    let offset = 44
    for (let i = 0; i < length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]))
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
        offset += 2
      }
    }
    
    return arrayBuffer
  }

  // Audio recording functions - Google Cloud Speech-to-Text only
  const startRecording = async () => {
    // Stop any playing audio when starting to record
    stopAudioPlayback()
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      const chunks: Blob[] = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }
      
      // Start recording duration timer
      setRecordingDuration(0)
      const durationInterval = setInterval(() => {
        setRecordingDuration(prev => prev + 1)
      }, 1000)
      
      recorder.onstop = async () => {
        // Clear duration timer
        clearInterval(durationInterval)
        setRecordingDuration(0)
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        
        // Stop all tracks first
        stream.getTracks().forEach(track => track.stop())
        setMediaRecorder(null)
        setIsRecording(false)
        setAudioChunks([])
        
        // Check if audio is long enough (at least 0.5 seconds)
        if (audioBlob.size < 1000) {
          alert("Recording too short. Please record for at least 0.5 seconds.")
          return
        }
        
        try {
          console.log(`Converting audio: ${audioBlob.size} bytes, type: ${audioBlob.type}`)
          
          // Convert WebM to WAV using Web Audio API
          const wavBlob = await convertWebMToWAV(audioBlob)
          console.log(`Converted to WAV: ${wavBlob.size} bytes`)
          
          if (wavBlob.size < 1000) {
            alert("Converted audio too small. Please try recording again.")
            return
          }
          
          const audioFile = new File([wavBlob], 'recording.wav', { type: 'audio/wav' })
          
          console.log("Sending audio to server for transcription...")
          const result = await apiClient.transcribeAudio(audioFile)
          
          if (result.transcript && result.transcript.trim()) {
            console.log("Transcription successful:", result.transcript)
            setInput(result.transcript)
            inputRef.current?.focus()
          } else {
            alert("No transcription received. Please try again.")
          }
        } catch (error: any) {
          console.error("Failed to transcribe audio:", error)
          alert(`Failed to transcribe audio: ${error.message || "Unknown error"}`)
        }
      }
      
      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
    } catch (error) {
      console.error("Error starting recording:", error)
      alert("Failed to access microphone. Please check permissions.")
    }
  }
  
  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop()
      setIsRecording(false)
      setMediaRecorder(null)
      setRecordingDuration(0)
    }
  }
  
  // Format recording duration as MM:SS
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }
  
  const playAudioResponse = async (text: string) => {
    try {
      // Stop any currently playing audio
      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
        currentAudioRef.current.currentTime = 0
        currentAudioRef.current = null
      }
      
      const audioBlob = await apiClient.synthesizeSpeech(text)
      
      // Verify blob is valid
      if (!audioBlob || audioBlob.size === 0) {
        console.warn("Empty audio blob received")
        return
      }
      
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      
      // Store reference to current audio
      currentAudioRef.current = audio
      
      audio.onerror = (e) => {
        console.error("Audio playback error:", e)
        URL.revokeObjectURL(audioUrl)
        currentAudioRef.current = null
      }
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        currentAudioRef.current = null
      }
      
      await audio.play()
    } catch (error: any) {
      console.error("Failed to synthesize speech:", error)
      currentAudioRef.current = null
      // Don't show alert for audio errors, just log them
      // Audio is a nice-to-have feature, not critical
    }
  }
  
  // Stop any playing audio
  const stopAudioPlayback = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current.currentTime = 0
      currentAudioRef.current = null
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return
    
    // Create session if it doesn't exist
    let currentSessionId = sessionId
    if (!currentSessionId && userId && customerId) {
      try {
        const data = await apiClient.post<any>("/sessions/create", { 
          user_id: userId,
          customer_id: customerId
        })
        const newSessionId = data?.session_id as string
        if (!newSessionId) {
          throw new Error("Failed to create session: no session_id returned")
        }
        currentSessionId = newSessionId
        setSessionId(currentSessionId)
        const newSession: Conversation = {
          session_id: newSessionId,
          name: `Session ${newSessionId.slice(-8)}`,
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
    
    // Add user message immediately (before API call)
    const userMsg: Message = {
        id: `user_${Date.now()}`,
        role: "user",
        content: userMessage,
        timestamp: new Date().toISOString(),
    }
    setMessages([...messages, userMsg])
    
    // Show typing indicator
    setSending(true)
    
    // Keep focus on input field after sending
    setTimeout(() => {
      inputRef.current?.focus()
    }, 0)

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
        customer_id: customerId || undefined, // Include customer_id in request
      })

      // Hide typing indicator before adding response
      setSending(false)
      
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
      
      // Play audio response if enabled
      if (audioEnabled && response.response) {
        playAudioResponse(response.response)
      }
      
      // Restore focus to input field after agent responds
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
      
      // Restore focus to input field after agent responds
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)

      // Reload messages from backend to ensure consistency
      if (userId && currentSessionId) {
        setTimeout(async () => {
          try {
            const data = await apiClient.get(`/history/${userId}?session_id=${currentSessionId}`)
            console.log("Reloaded messages from API:", data)
            
            // Handle both array and object response formats
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
              agent_used: m.metadata?.is_human_agent ? "human_agent" : (m.metadata?.agent || m.agent_used),
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
      setSending(false)
      // Restore focus to input field on error
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    } finally {
      // Ensure sending is false even if there's an error
      setSending(false)
      // Keep focus on input field after sending (double-check)
      setTimeout(() => {
        inputRef.current?.focus()
      }, 150)
    }
  }

  const validateCustomerId = (id: string): { valid: boolean; error?: string } => {
    const trimmed = id.trim()
    
    // Check if empty
    if (!trimmed) {
      return { valid: false, error: "Customer ID is required" }
    }
    
    // Check minimum length (cust_001 = 8 chars minimum)
    if (trimmed.length < 6) {
      return { valid: false, error: "Customer ID is too short. Must be at least 6 characters (e.g., cust_001)" }
    }
    
    // Check maximum length
    if (trimmed.length > 50) {
      return { valid: false, error: "Customer ID is too long. Maximum 50 characters" }
    }
    
    // Pattern: Must start with "cust" (case insensitive) followed by underscore/hyphen and numbers
    // Examples: cust_001, CUST-123, cust_12345, CUST_999
    const pattern = /^cust[_\-][0-9]+$/i
    if (!pattern.test(trimmed)) {
      return { 
        valid: false, 
        error: "Invalid Customer ID format. Must be in format: cust_XXX or CUST-XXX (e.g., cust_001, CUST-123)" 
      }
    }
    
    return { valid: true }
  }

  const handleCustomerIdSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setCustomerIdError("")

    // Validate customer ID
    const validation = validateCustomerId(inputCustomerId)
    
    if (!validation.valid) {
      setCustomerIdError(validation.error || "Invalid Customer ID format")
      return // Prevent login if invalid
    }

    // Only save customer ID if validation passes
    setCustomerId(inputCustomerId.trim())
    setShowCustomerIdPrompt(false)
    setInputCustomerId("")
  }

  const handleLogout = () => {
    // Clear all state before logout
    setConversations([])
    setMessages([])
    setSessionId(null)
    setInput("")
    setFeedbackGiven(new Set())
    logout()
    setShowCustomerIdPrompt(true)
  }

  const handleFeedback = async (messageId: string, feedbackType: "thumbs_up" | "thumbs_down", agentUsed?: string) => {
    if (!sessionId || !userId || feedbackGiven.has(messageId)) {
      return
    }

    // For thumbs_up, submit immediately without dialog
    if (feedbackType === "thumbs_up") {
      try {
        setSubmittingFeedback(messageId)
        await apiClient.submitFeedback({
          session_id: sessionId,
          user_id: userId,
          feedback_type: feedbackType,
          agent_used: agentUsed,
          reason: "helpful",
          category: "helpfulness",
        })
        
        // Mark feedback as given for this message
        setFeedbackGiven(new Set([...feedbackGiven, messageId]))
      } catch (error) {
        console.error("Failed to submit feedback:", error)
        alert("Failed to submit feedback. Please try again.")
      } finally {
        setSubmittingFeedback(null)
      }
      return
    }

    // For thumbs_down, open dialog to collect more details
    setSelectedMessageForFeedback({ id: messageId, agentUsed })
    setFeedbackType(feedbackType)
    setFeedbackComment("")
    setFeedbackReason("")
    setFeedbackCategory("")
    setIsFeedbackDialogOpen(true)
  }

  const handleSubmitFeedback = async () => {
    if (!selectedMessageForFeedback || !sessionId || !userId) {
      return
    }

    try {
      setSubmittingFeedback(selectedMessageForFeedback.id)
      
      await apiClient.submitFeedback({
        session_id: sessionId,
        user_id: userId,
        feedback_type: feedbackType,
        agent_used: selectedMessageForFeedback.agentUsed,
        comment: feedbackComment || undefined,
        reason: feedbackReason || undefined,
        category: feedbackCategory || undefined,
      })
      
      // Mark feedback as given
      setFeedbackGiven(new Set([...feedbackGiven, selectedMessageForFeedback.id]))
      setIsFeedbackDialogOpen(false)
      setSelectedMessageForFeedback(null)
      setFeedbackComment("")
      setFeedbackReason("")
      setFeedbackCategory("")
    } catch (error) {
      console.error("Failed to submit feedback:", error)
      alert("Failed to submit feedback. Please try again.")
    } finally {
      setSubmittingFeedback(null)
    }
  }

  // Show customer ID prompt if not set
  if (showCustomerIdPrompt || !customerId) {
    return (
      <div className="flex flex-col h-screen">
        <PageHeader title="Chat" description="Enter your Customer ID to start chatting" />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-4">
            <div>
              <h2 className="text-2xl font-semibold mb-2">Welcome to Chat</h2>
              <p className="text-muted-foreground">
                Please enter your Customer ID to access the support chat.
              </p>
            </div>
            <form onSubmit={handleCustomerIdSubmit} className="space-y-4">
              <div>
                <Label htmlFor="customer_id">Customer ID *</Label>
                <Input
                  id="customer_id"
                  value={inputCustomerId}
                  onChange={(e) => {
                    const value = e.target.value
                    setInputCustomerId(value)
                    // Validate on change to show errors immediately
                    if (value.trim()) {
                      const validation = validateCustomerId(value)
                      if (!validation.valid) {
                        setCustomerIdError(validation.error || "")
                      } else {
                        setCustomerIdError("")
                      }
                    } else {
                      setCustomerIdError("")
                    }
                  }}
                  onBlur={(e) => {
                    // Re-validate on blur
                    if (e.target.value.trim()) {
                      const validation = validateCustomerId(e.target.value)
                      if (!validation.valid) {
                        setCustomerIdError(validation.error || "")
                      }
                    }
                  }}
                  placeholder="cust_001"
                  className={customerIdError ? "border-destructive" : ""}
                  autoFocus
                />
                {customerIdError && (
                  <p className="text-sm text-destructive mt-1">{customerIdError}</p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Format: cust_XXX or CUST-XXX (e.g., cust_001, CUST-123, cust_999)
                </p>
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                disabled={!inputCustomerId.trim() || !!customerIdError}
              >
                Start Chatting
              </Button>
            </form>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="flex items-center justify-between px-8 py-4 border-b">
        <div>
          <h1 className="text-2xl font-semibold">Chat</h1>
          <p className="text-sm text-muted-foreground">Customer ID: {customerId}</p>
        </div>
        <Button variant="outline" onClick={handleLogout}>
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </Button>
      </div>

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
                  ? (conversations.find(c => c.session_id === sessionId)?.name || `Session ${sessionId.slice(-8)}`)
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
              {sessionId && editingName === sessionId ? (
                <div className="flex items-center gap-2">
                  <Input
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        renameConversation(sessionId, newName)
                      } else if (e.key === "Escape") {
                        setEditingName(null)
                        setNewName("")
                      }
                    }}
                    className="h-8 text-sm"
                    autoFocus
                  />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => renameConversation(sessionId, newName)}
                    className="h-8 px-2"
                  >
                    ✓
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setEditingName(null)
                      setNewName("")
                    }}
                    className="h-8 px-2"
                  >
                    ✕
            </Button>
          </div>
              ) : (
                <div className="flex items-center gap-2 group">
                  <p className="text-sm font-semibold truncate flex-1">
                    {sessionId 
                      ? (conversations.find(c => c.session_id === sessionId)?.name || `Session ${sessionId.slice(-8)}`)
                      : "None selected"}
                  </p>
                  {sessionId && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        const currentName = conversations.find(c => c.session_id === sessionId)?.name || `Session ${sessionId.slice(-8)}`
                        setNewName(currentName)
                        setEditingName(sessionId)
                      }}
                      className="opacity-0 group-hover:opacity-100 h-6 w-6 p-0"
                      title="Rename conversation"
                    >
                      <Pencil className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              )}
            </div>
          <ScrollArea className="flex-1">
            <div className="space-y-2 p-4">
              {conversations.map((conv) => (
                  <div
                    key={conv.session_id}
                    className={`group flex items-center gap-2 rounded text-sm transition-colors ${
                      sessionId === conv.session_id
                        ? "bg-muted"
                        : "hover:bg-muted"
                    }`}
                  >
                    {editingName === conv.session_id ? (
                      <div className="flex-1 flex items-center gap-2 px-3 py-2">
                        <Input
                          value={newName}
                          onChange={(e) => setNewName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              renameConversation(conv.session_id, newName)
                            } else if (e.key === "Escape") {
                              setEditingName(null)
                              setNewName("")
                            }
                          }}
                          className="h-8 text-sm"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => renameConversation(conv.session_id, newName)}
                          className="h-8 px-2"
                        >
                          ✓
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setEditingName(null)
                            setNewName("")
                          }}
                          className="h-8 px-2"
                        >
                          ✕
                        </Button>
                      </div>
                    ) : (
                      <>
                <button
                  onClick={() => setSessionId(conv.session_id)}
                          className={`flex-1 text-left px-3 py-2 rounded transition-colors ${
                    sessionId === conv.session_id
                              ? "text-foreground font-medium"
                              : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <p className="truncate">{conv.name}</p>
                  <p className="text-xs mt-1">{conv.message_count} messages</p>
                </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            const currentName = conv.name
                            setNewName(currentName)
                            setEditingName(conv.session_id)
                          }}
                          className="opacity-0 group-hover:opacity-100 p-2 text-muted-foreground hover:text-primary transition-opacity"
                          title="Rename conversation"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteConversation(conv.session_id)
                          }}
                          className="opacity-0 group-hover:opacity-100 p-2 text-muted-foreground hover:text-destructive transition-opacity"
                          title="Delete session"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
              ))}
            </div>
          </ScrollArea>
        </div>

          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto">
            <div className="p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  Start a conversation by typing a message
                </div>
              ) : (
                <div className="space-y-4">
                {messages.map((msg) => (
                  <div key={msg.id} className={`group flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                    <div
                      className={`max-w-xs px-4 py-2 rounded-lg ${
                        msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                      {msg.role === "assistant" && msg.agent_used && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            msg.agent_used === "human_agent"
                              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                              : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                          }`}>
                            {msg.agent_used === "human_agent" ? (
                              <>👤 Human Agent</>
                            ) : (
                              <>🤖 {msg.agent_used}</>
                            )}
                          </span>
                          {msg.response_time && (
                            <span className="text-xs opacity-60">
                              {msg.response_time.toFixed(2)}s
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {msg.role === "assistant" && (
                      <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        {feedbackGiven.has(msg.id) ? (
                          <span className="text-xs text-muted-foreground">Thank you for your feedback!</span>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0 hover:bg-green-100 hover:text-green-600"
                              onClick={() => handleFeedback(msg.id, "thumbs_up", msg.agent_used)}
                              disabled={submittingFeedback === msg.id || !sessionId || !userId}
                              title="Helpful"
                            >
                              <ThumbsUp className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0 hover:bg-red-100 hover:text-red-600"
                              onClick={() => handleFeedback(msg.id, "thumbs_down", msg.agent_used)}
                              disabled={submittingFeedback === msg.id || !sessionId || !userId}
                              title="Not helpful"
                            >
                              <ThumbsDown className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {sending && (
                  <div className="flex flex-col items-start">
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
                </div>
              )}
              {sending && <div ref={messagesEndRef} />}
              {!sending && <div ref={messagesEndRef} />}
            </div>
            </div>

          <div className="border-t border-border p-4">
            {/* Recording indicator */}
            {isRecording && (
              <div className="mb-3 flex items-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg">
                <div className="relative">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75"></div>
                </div>
                <span className="text-sm font-medium text-red-700 dark:text-red-300">
                  Recording... {formatDuration(recordingDuration)}
                </span>
              </div>
            )}
            
            <form onSubmit={sendMessage} className="flex gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => {
                  // Stop any playing audio when user starts typing
                  if (e.target.value.length > 0 && currentAudioRef.current) {
                    stopAudioPlayback()
                  }
                  setInput(e.target.value)
                }}
                placeholder="Type your message here..."
                disabled={sending || !userId || isRecording}
                autoFocus
              />
              <Button
                type="button"
                variant={isRecording ? "destructive" : "outline"}
                size="icon"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={sending || !userId}
                title={isRecording ? "Stop recording" : "Start voice recording"}
              >
                {isRecording ? (
                  <MicOff className="w-4 h-4" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </Button>
              <Button
                type="button"
                variant={audioEnabled ? "default" : "outline"}
                size="icon"
                onClick={() => setAudioEnabled(!audioEnabled)}
                disabled={sending || !userId}
                title={audioEnabled ? "Disable audio responses" : "Enable audio responses"}
              >
                {audioEnabled ? (
                  <Volume2 className="w-4 h-4" />
                ) : (
                  <VolumeX className="w-4 h-4" />
                )}
              </Button>
              <Button type="submit" disabled={sending || !userId || !input.trim() || isRecording} size="icon">
                <ArrowUp className="w-4 h-4" />
              </Button>
            </form>
            </div>
            </div>
          </div>
        </div>

        {/* Feedback Dialog */}
        <Dialog open={isFeedbackDialogOpen} onOpenChange={setIsFeedbackDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Provide Feedback</DialogTitle>
              <DialogDescription>
                Help us improve by sharing why this response wasn't helpful.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="feedback-comment">Comment (Optional)</Label>
                <Textarea
                  id="feedback-comment"
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Tell us what was wrong or what could be improved..."
                  className="mt-2"
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="feedback-reason">Reason (Optional)</Label>
                <Select value={feedbackReason} onValueChange={setFeedbackReason}>
                  <SelectTrigger id="feedback-reason" className="mt-2">
                    <SelectValue placeholder="Select a reason" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="incorrect">Incorrect Information</SelectItem>
                    <SelectItem value="unclear">Unclear or Confusing</SelectItem>
                    <SelectItem value="missing_info">Missing Information</SelectItem>
                    <SelectItem value="slow">Too Slow</SelectItem>
                    <SelectItem value="unhelpful">Not Helpful</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="feedback-category">Category (Optional)</Label>
                <Select value={feedbackCategory} onValueChange={setFeedbackCategory}>
                  <SelectTrigger id="feedback-category" className="mt-2">
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="accuracy">Accuracy</SelectItem>
                    <SelectItem value="speed">Speed</SelectItem>
                    <SelectItem value="clarity">Clarity</SelectItem>
                    <SelectItem value="completeness">Completeness</SelectItem>
                    <SelectItem value="helpfulness">Helpfulness</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <p className="text-xs text-muted-foreground">
                Note: If you don't fill these fields, the system will try to extract them from your comment automatically.
              </p>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsFeedbackDialogOpen(false)
                  setSelectedMessageForFeedback(null)
                  setFeedbackComment("")
                  setFeedbackReason("")
                  setFeedbackCategory("")
                }}
                disabled={submittingFeedback === selectedMessageForFeedback?.id}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSubmitFeedback}
                disabled={submittingFeedback === selectedMessageForFeedback?.id}
              >
                {submittingFeedback === selectedMessageForFeedback?.id ? "Submitting..." : "Submit Feedback"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    )
  }
