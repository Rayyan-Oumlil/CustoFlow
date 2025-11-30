"use client"

import type React from "react"

import { useEffect, useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { apiClient, type Message } from "@/lib/api-client"
import { cache, CACHE_KEYS } from "@/lib/cache"
import { PageHeader } from "@/components/page-header"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowUp, Plus, Trash2, LogOut, Pencil, ThumbsUp, ThumbsDown, Mic, MicOff, Volume2, VolumeX, Paperclip, X } from "lucide-react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"

interface Conversation {
  session_id: string
  name: string
  message_count: number
  created_at: string
  is_active?: boolean
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
  const [feedbackType, setFeedbackType] = useState<"thumbs_up" | "thumbs_down" | "rating">("thumbs_down")
  const [feedbackRating, setFeedbackRating] = useState<number>(0)
  const [feedbackComment, setFeedbackComment] = useState("")
  const [feedbackReason, setFeedbackReason] = useState("")
  const [feedbackCategory, setFeedbackCategory] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadingDocument, setUploadingDocument] = useState(false)
  const [documentAnalysisResult, setDocumentAnalysisResult] = useState<any>(null)
  const [isSessionClosed, setIsSessionClosed] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const sendingStateRef = useRef(false) // Track sending state to prevent polling interference
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  // Track which message is currently playing TTS
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null)
  const messageAudioRefs = useRef<Record<string, HTMLAudioElement>>({})

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
        // Check cache first (30 second TTL for conversations)
        const cacheKey = customerId 
          ? CACHE_KEYS.sessions(customerId)
          : `sessions:${userId}`
        const cached = cache.get<Conversation[]>(cacheKey)
        if (cached) {
          setConversations(cached)
          setLoading(false)
          // Still check session status
          if (sessionId) {
            const currentSession = cached.find(c => c.session_id === sessionId)
            if (currentSession) {
              setIsSessionClosed(currentSession.is_active === false)
            }
          }
          return
        }
        
        setLoading(true)
        // Get sessions by customer_id only (user_id is ignored when customer_id is provided)
        // Use the new endpoint that searches only by customer_id
        const url = customerId 
          ? `/sessions/by-customer/${encodeURIComponent(customerId)}`
          : `/sessions/${userId}`
        const data = await apiClient.get(url)
        // Fetched sessions from API
        
        // Handle both array and object response formats
        let sessionsArray: any[] = []
        if (Array.isArray(data)) {
          sessionsArray = data
        } else if (data && typeof data === 'object') {
          // Try 'sessions' property first, then check if data itself is the array
          if ('sessions' in data && Array.isArray((data as any).sessions)) {
            sessionsArray = (data as any).sessions
          } else if (Array.isArray(data)) {
            sessionsArray = data
          }
        }
        // Extracted sessions array
        
        // Client-side filter: show sessions that match customer_id OR have null/undefined customer_id
        // This handles cases where sessions might not have customer_id set
        // Use case-insensitive comparison to handle "Cust_001" vs "cust_001"
        const filteredSessions = sessionsArray.filter((s: any) => {
          const sessionCustomerId = s.customer_id
          if (!sessionCustomerId) return true // Show sessions with no customer_id
          // Case-insensitive comparison: "Cust_001" === "cust_001"
          return sessionCustomerId.toLowerCase() === customerId.toLowerCase()
        })
        
        const convos = filteredSessions.map((s: any) => ({
              session_id: s.session_id,
          name: s.name || `Session ${s.session_id.slice(-8)}`, // Use name from DB or generate from last 8 chars
              message_count: s.message_count || 0,
              created_at: s.created_at,
              is_active: s.is_active !== false, // Default to true if not specified
            }))
        // Mapped conversations
        setConversations(convos)
        
        // Cache conversations (30 second TTL)
        cache.set(cacheKey, convos, 30000)
        
        // Check if current session is closed
        if (sessionId) {
          const currentSession = convos.find(c => c.session_id === sessionId)
          if (currentSession) {
            setIsSessionClosed(currentSession.is_active === false)
          } else {
            setIsSessionClosed(false) // Session not found, assume active
          }
        } else {
          setIsSessionClosed(false)
        }
        
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

  // Utility function to remove duplicate messages
  // ROOT CAUSE FIX: Messages are duplicated because:
  // 1. Local message created with temp ID (user_1234567890) BEFORE server save
  // 2. Server saves with auto-incremented ID (1, 2, 3...) 
  // 3. When polling, server message has different ID than local
  // 4. Both coexist because IDs don't match
  // SOLUTION: Match by content+role+timestamp (more lenient timestamp window)
  const deduplicateMessages = (messages: Message[]): Message[] => {
    const seen = new Map<string, Message>()
    
    for (const msg of messages) {
      // Normalize content (remove extra spaces, lowercase)
      const normalizedContent = msg.content.trim().toLowerCase().replace(/\s+/g, ' ')
      
      // Create signature with more lenient timestamp matching (5 second window)
      // This handles cases where local and server timestamps differ slightly
      const timestamp = new Date(msg.timestamp).getTime()
      const roundedTime = Math.floor(timestamp / 5000) * 5000 // Round to nearest 5 seconds
      const signature = `${msg.role}:${normalizedContent}:${roundedTime}`
      
      if (!seen.has(signature)) {
        seen.set(signature, msg)
      } else {
        // We have a duplicate - prefer server message (has proper ID) over local (temp ID)
        const existing = seen.get(signature)!
        const existingIsLocal = existing.id && (
          existing.id.startsWith('user_') || 
          existing.id.startsWith('assistant_') || 
          existing.id.startsWith('error_') ||
          existing.id.startsWith('agent_')
        )
        const currentIsLocal = msg.id && (
          msg.id.startsWith('user_') || 
          msg.id.startsWith('assistant_') || 
          msg.id.startsWith('error_') ||
          msg.id.startsWith('agent_')
        )
        
        // Prefer server message (non-local ID) over local message
        if (existingIsLocal && !currentIsLocal) {
          seen.set(signature, msg) // Replace local with server
        } else if (!existingIsLocal && currentIsLocal) {
          // Keep existing (server message)
        } else {
          // Both are same type - prefer numeric ID (server) or keep first
          const existingIsNumeric = existing.id && /^\d+$/.test(String(existing.id))
          const currentIsNumeric = msg.id && /^\d+$/.test(String(msg.id))
          if (currentIsNumeric && !existingIsNumeric) {
            seen.set(signature, msg) // Prefer numeric ID
          }
        }
      }
    }
    
    return Array.from(seen.values()).sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  }

  useEffect(() => {
    if (!userId || !sessionId) return

    // Track if component is mounted to prevent state updates after unmount
    let isMounted = true

    const fetchMessages = async (mergeWithLocal: boolean = false) => {
      if (!isMounted) return
      
      // Check cache first (5 second TTL for messages) - only for non-merge requests
      const cacheKey = CACHE_KEYS.messages(userId, sessionId)
      if (!mergeWithLocal) {
        const cached = cache.get<Message[]>(cacheKey)
        if (cached && isMounted) {
          setMessages(cached)
          return
        }
      }
      
      try {
        const data = await apiClient.get(`/history/${userId}?session_id=${sessionId}`)
        if (!isMounted) return // Check again after async operation
        
        // Fetched messages from API
        
        // Handle both array and object response formats
        let messagesArray: any[] = []
        if (Array.isArray(data)) {
          messagesArray = data
        } else if (data && typeof data === 'object' && 'history' in data) {
          messagesArray = Array.isArray((data as any).history) ? (data as any).history : []
        }
        
        const serverMsgs = messagesArray.map((m: any, index: number) => {
          // Check for human agent in multiple ways
          const isHumanAgent = m.metadata?.is_human_agent === true || 
                               m.metadata?.agent_used === "human_agent" ||
                               m.agent_used === "human_agent"
          
          return {
            id: m.id || `msg_${m.timestamp || Date.now()}_${index}`,
            role: m.role,
            content: m.content,
            agent_used: isHumanAgent ? "human_agent" : (m.metadata?.agent || m.agent_used),
            response_time: m.metadata?.response_time || m.response_time,
            timestamp: m.timestamp || m.created_at,
          }
        })
        
        if (mergeWithLocal) {
          // Merge with local messages: replace local messages with server versions
          // Local user messages (temp IDs) will be replaced by server messages (proper IDs)
          // This prevents duplicates while keeping optimistic updates
          setMessages((prev) => {
            // Create a map of server messages by content+role+timestamp for quick lookup
            const serverMap = new Map<string, Message>()
            for (const msg of serverMsgs) {
              const timestamp = new Date(msg.timestamp).getTime()
              const roundedTime = Math.floor(timestamp / 5000) * 5000
              const normalizedContent = msg.content.trim().toLowerCase().replace(/\s+/g, ' ')
              const signature = `${msg.role}:${normalizedContent}:${roundedTime}`
              serverMap.set(signature, msg)
            }
            
            // Replace local messages with server versions if they match
            const updated = prev.map(localMsg => {
              const timestamp = new Date(localMsg.timestamp).getTime()
              const roundedTime = Math.floor(timestamp / 5000) * 5000
              const normalizedContent = localMsg.content.trim().toLowerCase().replace(/\s+/g, ' ')
              const signature = `${localMsg.role}:${normalizedContent}:${roundedTime}`
              
              // If server has a matching message, use server version (has proper ID)
              if (serverMap.has(signature)) {
                return serverMap.get(signature)!
              }
              return localMsg // Keep local message if no server match (not saved yet)
            })
            
            // Add any server messages that don't have local matches (new messages)
            const localSignatures = new Set(
              prev.map(m => {
                const t = new Date(m.timestamp).getTime()
                const rt = Math.floor(t / 5000) * 5000
                const nc = m.content.trim().toLowerCase().replace(/\s+/g, ' ')
                return `${m.role}:${nc}:${rt}`
              })
            )
            
            for (const serverMsg of serverMsgs) {
              const t = new Date(serverMsg.timestamp).getTime()
              const rt = Math.floor(t / 5000) * 5000
              const nc = serverMsg.content.trim().toLowerCase().replace(/\s+/g, ' ')
              const sig = `${serverMsg.role}:${nc}:${rt}`
              if (!localSignatures.has(sig)) {
                updated.push(serverMsg)
              }
            }
            
            // Sort by timestamp and deduplicate
            return deduplicateMessages(updated.sort((a, b) => 
              new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
            ))
          })
        } else {
          // Initial load: deduplicate server messages
          if (isMounted) {
            const deduplicated = deduplicateMessages(serverMsgs)
            setMessages(deduplicated)
            // Cache the messages (5 second TTL - short because messages change frequently)
            cache.set(cacheKey, deduplicated, 5000)
          }
        }
      } catch (error) {
        if (!isMounted) return
        console.error("Failed to fetch messages:", error)
        // On error, try to use cached data if available
        const cached = cache.get<Message[]>(cacheKey)
        if (cached && isMounted) {
          setMessages(cached)
        } else if (!mergeWithLocal) {
          setMessages([])
        }
      }
    }

    fetchMessages()
    
    // Check session status when sessionId changes
    if (sessionId) {
      const currentSession = conversations.find(c => c.session_id === sessionId)
      if (currentSession) {
        setIsSessionClosed(currentSession.is_active === false)
      } else {
        // If session not in conversations list, check via API
        apiClient.get(`/sessions/${sessionId}/metadata`).then((data: any) => {
          if (isMounted && data) {
            setIsSessionClosed(data.is_active === false)
          }
        }).catch(() => {
          // If metadata not found, assume active
          if (isMounted) setIsSessionClosed(false)
        })
      }
    } else {
      setIsSessionClosed(false)
    }
    
    // Adaptive polling: fast when active (2s), slow when inactive (15s)
    // Pauses when tab is hidden
    let pollingInterval: NodeJS.Timeout | null = null
    let isActive = true
    let lastActivity = Date.now()
    
    const startPolling = () => {
      if (!isMounted || !userId || !sessionId) return
      
      const poll = () => {
        if (!isMounted || !userId || !sessionId) return
        // Don't poll if tab is hidden
        if (document.hidden) return
        // Don't poll if we're currently sending a message (prevents interference)
        if (sendingStateRef.current) return
        
        fetchMessages(true) // Merge with local messages
        
        // Update interval based on activity
        const timeSinceActivity = Date.now() - lastActivity
        const newInterval = timeSinceActivity > 30000 ? 15000 : 2000 // 15s if inactive, 2s if active
        
        if (pollingInterval) {
          clearInterval(pollingInterval)
        }
        pollingInterval = setInterval(poll, newInterval)
      }
      
      // Initial poll
      poll()
      
      // Check activity periodically and adjust interval
      const activityCheck = setInterval(() => {
        if (!isMounted) return
        const timeSinceActivity = Date.now() - lastActivity
        const shouldBeActive = timeSinceActivity <= 30000
        if (shouldBeActive !== isActive) {
          isActive = shouldBeActive
          // Restart polling with new interval
          if (pollingInterval) {
            clearInterval(pollingInterval)
          }
          poll()
        }
      }, 5000) // Check every 5 seconds
      
      return () => {
        if (pollingInterval) clearInterval(pollingInterval)
        clearInterval(activityCheck)
      }
    }
    
    // Track user activity
    const handleActivity = () => {
      lastActivity = Date.now()
      isActive = true
    }
    
    // Listen for user activity
    const events = ['mousedown', 'keypress', 'scroll', 'touchstart', 'focus', 'click']
    events.forEach(event => {
      window.addEventListener(event, handleActivity, { passive: true })
    })
    
    const cleanup = startPolling()
    
    return () => {
      isMounted = false
      if (cleanup) cleanup()
      events.forEach(event => {
        window.removeEventListener(event, handleActivity)
      })
    }
  }, [userId, sessionId, conversations])

  useEffect(() => {
    // Auto-scroll to bottom only if user is already at bottom (don't force scroll when scrolling up)
    const messagesContainer = document.querySelector('.flex-1.overflow-y-auto') as HTMLElement
    if (messagesContainer) {
      const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop <= messagesContainer.clientHeight + 100
      // Only auto-scroll if user is already near the bottom
      if (isNearBottom) {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
        }, 100)
      }
    } else {
      // Fallback: if container not found, scroll anyway (initial load)
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
      }, 100)
    }
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
          // Audio decoded successfully
          
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
            // Audio processed successfully
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
    stopAllAudio()
    
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
          // Converting audio to WAV format
          
          // Convert WebM to WAV using Web Audio API
          const wavBlob = await convertWebMToWAV(audioBlob)
          // Audio converted to WAV
          
          if (wavBlob.size < 1000) {
            alert("Converted audio too small. Please try recording again.")
            return
          }
          
          const audioFile = new File([wavBlob], 'recording.wav', { type: 'audio/wav' })
          
          // Sending audio for transcription
          const result = await apiClient.transcribeAudio(audioFile)
          
          if (result.transcript && result.transcript.trim()) {
            // Transcription successful
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
  
  // Play TTS for a specific message
  const playMessageAudio = async (messageId: string, text: string) => {
    try {
      // Stop any currently playing audio
      stopAllAudio()
      
      const audioBlob = await apiClient.synthesizeSpeech(text)
      
      // Verify blob is valid
      if (!audioBlob || audioBlob.size === 0) {
        console.warn("Empty audio blob received")
        return
      }
      
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      
      // Store reference to this message's audio
      messageAudioRefs.current[messageId] = audio
      setPlayingMessageId(messageId)
      
      audio.onerror = (e) => {
        console.error("Audio playback error:", e)
        URL.revokeObjectURL(audioUrl)
        delete messageAudioRefs.current[messageId]
        setPlayingMessageId(null)
      }
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        delete messageAudioRefs.current[messageId]
        setPlayingMessageId(null)
      }
      
      await audio.play()
    } catch (error: any) {
      console.error("Failed to synthesize speech:", error)
      delete messageAudioRefs.current[messageId]
      setPlayingMessageId(null)
    }
  }
  
  // Stop all playing audio
  const stopAllAudio = () => {
    // Stop all message audios
    Object.values(messageAudioRefs.current).forEach(audio => {
      audio.pause()
      audio.currentTime = 0
    })
    messageAudioRefs.current = {}
    setPlayingMessageId(null)
    
    // Also stop legacy audio ref if exists
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current.currentTime = 0
      currentAudioRef.current = null
    }
  }
  
  // Legacy function for backward compatibility (not used anymore)
  const playAudioResponse = async (text: string) => {
    // This is no longer used - messages have individual TTS buttons
  }
  
  // Legacy function for backward compatibility
  const stopAudioPlayback = () => {
    stopAllAudio()
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending || isSessionClosed) return
    
    // Stop any playing audio when user sends a message
    stopAllAudio()
    
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

    let userMessage = input
    
    // Include document analysis results in message if available (backend only, not visible to user)
    if (documentAnalysisResult && uploadedFile) {
      // Build analysis data for backend (not shown to user)
      const analysisData = {
        document_uploaded: uploadedFile.name,
        analysis_result: documentAnalysisResult
      }
      
      // Include analysis in message for backend processing (hidden from user view)
      // Format: [DOCUMENT_ANALYSIS: {...}] - this will be parsed by backend
      const analysisJson = JSON.stringify(analysisData)
      userMessage = `${userMessage}\n\n[DOCUMENT_ANALYSIS: ${analysisJson}]`
    }
    
    // Save input value before clearing
    const messageContent = input.trim()
    
    // Clear input IMMEDIATELY and keep it clear (no flickering)
    setInput("")
    setUploadedFile(null)
    setDocumentAnalysisResult(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
    
    // Check if last message was from human agent BEFORE sending
    const lastAssistantMsg = [...messages].reverse().find(m => m.role === "assistant")
    const isContinuingWithHuman = lastAssistantMsg?.agent_used === "human_agent"
    
    // Add user message IMMEDIATELY for better UX (optimistic update)
    // Use a stable ID that won't conflict with server messages
    const userMsgId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const displayMessage = messageContent || "Uploaded document"
    const userMsg: Message = {
        id: userMsgId,
        role: "user",
        content: displayMessage,
        timestamp: new Date().toISOString(),
    }
    
    // Add user message immediately - this is the source of truth
    setMessages((prev) => [...prev, userMsg])
    
    // Keep focus on input field after sending (input is already cleared)
    setTimeout(() => {
      inputRef.current?.focus()
    }, 0)

    // Mark that we're sending (prevents polling interference)
    sendingStateRef.current = true
    
    try {
      let response: {
        response: string
        session_id: string
        agent_used?: string
        response_time?: number
      }
      
      if (isContinuingWithHuman) {
        // Human agent is handling - use regular /chat endpoint
        // The backend will detect human agent takeover and not respond with AI
        // The message will be saved correctly as "user" role
        // Don't show typing indicator - human agent will respond via polling
        response = await apiClient.post<{
          response: string
          session_id: string
          agent_used?: string
          response_time?: number
        }>("/chat", {
          user_id: userId,
          session_id: currentSessionId,
          message: userMessage,
          customer_id: customerId || undefined,
        })
        // Backend will return early if human agent has taken over
        // So response might be the "human agent handling" message
        // We'll just return here, no need to display it
        return
      } else {
        // Regular chat with AI agent - show typing indicator
        setSending(true)
        // Regular chat with AI agent
        response = await apiClient.post<{
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
      }

      // Hide typing indicator
      setSending(false)
      
      // Add assistant response IMMEDIATELY from the API response
      // This ensures strict flow: user message → agent response (no waiting, no polling interference)
      if (response.response) {
        const assistantMsg: Message = {
          id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: "assistant",
          content: response.response,
          agent_used: response.agent_used,
          response_time: response.response_time,
          timestamp: new Date().toISOString(),
        }
        
        // Add assistant message immediately after user message
        // Replace user message with server version if available, then add assistant response
        setMessages((prev) => {
          // Find and replace the optimistic user message with server version (if different)
          const updated = prev.map(msg => {
            // If this is our optimistic user message, keep it (will be replaced by polling later)
            if (msg.id === userMsgId) {
              return msg
            }
            return msg
          })
          
          // Add assistant response
          return [...updated, assistantMsg]
        })
      }
      
      // Restore focus to input field immediately
      setTimeout(() => {
        inputRef.current?.focus()
      }, 50)
      
      // Re-enable polling after a short delay (ensures server has saved)
      setTimeout(() => {
        sendingStateRef.current = false
      }, 1000)
    } catch (error: any) {
      console.error("Failed to send message:", error)
      const errorMsg: Message = {
          id: `error_${Date.now()}`,
          role: "assistant",
        content: `Error: ${error.message || "Failed to send message. Please try again."}`,
          timestamp: new Date().toISOString(),
      }
      // Add error message and deduplicate
      setMessages((prev) => deduplicateMessages([...prev, errorMsg]))
      setSending(false)
      // Restore focus to input field on error
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    } finally {
      // Ensure sending is false even if there's an error
      setSending(false)
      sendingStateRef.current = false // Re-enable polling
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

    // For thumbs_up, open dialog to optionally add rating
    if (feedbackType === "thumbs_up") {
      setSelectedMessageForFeedback({ id: messageId, agentUsed })
      setFeedbackType(feedbackType)
      setFeedbackRating(0)
      setFeedbackComment("")
      setFeedbackReason("helpful")
      setFeedbackCategory("helpfulness")
      setIsFeedbackDialogOpen(true)
      return
    }

    // For thumbs_down, open dialog to collect more details
    setSelectedMessageForFeedback({ id: messageId, agentUsed })
    setFeedbackType(feedbackType)
    setFeedbackRating(0)
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
        rating: feedbackType === "rating" ? feedbackRating : undefined,
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
                      className={`max-w-xs px-4 py-3 rounded-lg ${
                        msg.role === "user" 
                          ? "bg-primary text-primary-foreground" 
                          : msg.role === "assistant" && msg.agent_used === "human_agent"
                          ? "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-foreground"
                          : "bg-muted text-foreground"
                      }`}
                    >
                      {/* Show Human Agent label at the top for human agent messages */}
                      {msg.role === "assistant" && msg.agent_used === "human_agent" && (
                        <div className="mb-2 pb-2 border-b border-green-200 dark:border-green-800">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-600 text-white dark:bg-green-700 dark:text-green-100 border-0">
                            👤 Human Agent
                          </span>
                        </div>
                      )}
                      <p className="text-sm">{msg.content}</p>
                      {msg.role === "assistant" && msg.agent_used && msg.agent_used !== "human_agent" && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            msg.agent_used === "human_agent"
                              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                              : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                          }`}>
                            <>🤖 {msg.agent_used}</>
                          </span>
                          {msg.response_time && (
                            <span className="text-xs opacity-60">
                              {msg.response_time.toFixed(2)}s
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {/* Action buttons for assistant messages */}
                    {msg.role === "assistant" && (
                      <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        {/* TTS Button */}
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0 hover:bg-blue-100 hover:text-blue-600"
                          onClick={() => {
                            if (playingMessageId === msg.id) {
                              // Stop if currently playing
                              stopAllAudio()
                            } else {
                              // Play this message
                              playMessageAudio(msg.id, msg.content)
                            }
                          }}
                          title={playingMessageId === msg.id ? "Stop audio" : "Play audio"}
                        >
                          {playingMessageId === msg.id ? (
                            <VolumeX className="w-4 h-4" />
                          ) : (
                            <Volume2 className="w-4 h-4" />
                          )}
                        </Button>
                        
                        {/* Feedback buttons */}
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
                    
                    {/* TTS Button for user messages too */}
                    {msg.role === "user" && (
                      <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 w-8 p-0 hover:bg-blue-100 hover:text-blue-600"
                          onClick={() => {
                            if (playingMessageId === msg.id) {
                              stopAllAudio()
                            } else {
                              playMessageAudio(msg.id, msg.content)
                            }
                          }}
                          title={playingMessageId === msg.id ? "Stop audio" : "Play audio"}
                        >
                          {playingMessageId === msg.id ? (
                            <VolumeX className="w-4 h-4" />
                          ) : (
                            <Volume2 className="w-4 h-4" />
                          )}
                        </Button>
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
            
            {/* Session closed notice */}
            {isSessionClosed && (
              <div className="mb-3 px-4 py-3 bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  ⚠️ This conversation has been closed. You cannot send new messages. Please start a new conversation if you need further assistance.
                </p>
              </div>
            )}

            {/* Uploaded file preview */}
            {uploadedFile && (
              <div className="mb-3 flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <Paperclip className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-sm text-blue-700 dark:text-blue-300 flex-1 truncate">
                  {uploadedFile.name}
                  {uploadingDocument && (
                    <span className="ml-2 text-xs opacity-70">(Analyzing...)</span>
                  )}
                  {documentAnalysisResult && documentAnalysisResult.status === "success" && (
                    <span className="ml-2 text-xs text-green-600 dark:text-green-400">✓ Analyzed</span>
                  )}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() => {
                    setUploadedFile(null)
                    setDocumentAnalysisResult(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            )}

            <form onSubmit={sendMessage} className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0]
                  if (!file) return
                  
                  // Validate file type
                  const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf"]
                  if (!validTypes.includes(file.type)) {
                    alert("Unsupported file type. Please upload JPG, PNG, WebP, or PDF files.")
                    return
                  }
                  
                  // Validate file size (20MB max)
                  if (file.size > 20 * 1024 * 1024) {
                    alert("File too large. Maximum size: 20MB")
                    return
                  }
                  
                  setUploadedFile(file)
                  
                  // Auto-analyze document silently (don't modify input)
                  try {
                    setUploadingDocument(true)
                    const result = await apiClient.analyzeDocument(file, "auto")
                    
                    if (result.status === "success") {
                      setDocumentAnalysisResult(result)
                      // Don't modify input - let user type their own message
                      // Results will be included when message is sent
                    }
                  } catch (error: any) {
                    console.error("Failed to analyze document:", error)
                    // Don't block - user can still send the file
                  } finally {
                    setUploadingDocument(false)
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={sending || !userId || isRecording || uploadingDocument || isSessionClosed}
                title="Upload document (receipt, invoice, photo)"
              >
                {uploadingDocument ? (
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Paperclip className="w-4 h-4" />
                )}
              </Button>
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => {
                  // Stop any playing audio when user starts typing
                  if (e.target.value.length > 0) {
                    stopAllAudio()
                  }
                  setInput(e.target.value)
                }}
                placeholder={isSessionClosed ? "This conversation has been closed" : "Type your message here..."}
                disabled={sending || !userId || isRecording || isSessionClosed}
                autoFocus
              />
              <Button
                type="button"
                variant={isRecording ? "destructive" : "outline"}
                size="icon"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={sending || !userId || isSessionClosed}
                title={isRecording ? "Stop recording" : "Start voice recording"}
              >
                {isRecording ? (
                  <MicOff className="w-4 h-4" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </Button>
              <Button type="submit" disabled={sending || !userId || !input.trim() || isRecording || isSessionClosed} size="icon">
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
                Help us improve by rating this response and sharing your thoughts.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {/* Rating Option */}
              <div>
                <Label>Rating (Optional)</Label>
                <div className="flex items-center gap-2 mt-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => {
                        setFeedbackType("rating")
                        setFeedbackRating(star)
                      }}
                      className={`text-2xl transition-colors ${
                        feedbackType === "rating" && feedbackRating >= star
                          ? "text-yellow-400"
                          : "text-gray-300 hover:text-yellow-300"
                      }`}
                    >
                      ★
                    </button>
                  ))}
                  {feedbackType === "rating" && feedbackRating > 0 && (
                    <span className="text-sm text-muted-foreground ml-2">
                      {feedbackRating}/5
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Click stars to rate (1-5). You can also use thumbs up/down below.
                </p>
              </div>

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
                  setFeedbackRating(0)
                  setFeedbackType("thumbs_down")
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
