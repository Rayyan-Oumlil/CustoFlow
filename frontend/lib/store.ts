import { create } from "zustand"

interface StoreState {
  userId: string
  customerId: string | null
  sessionId: string | null
  theme: "light" | "dark"
  setUserId: (id: string) => void
  setCustomerId: (id: string | null) => void
  setSessionId: (id: string | null) => void
  setTheme: (theme: "light" | "dark") => void
  initFromStorage: () => void
  logout: () => void
}

export const useStore = create<StoreState>((set) => ({
  userId: "",
  customerId: null,
  sessionId: null,
  theme: "light",
  setUserId: (id) => set({ userId: id }),
  setCustomerId: (id) => {
    // Normalize customer_id to lowercase for consistency with backend
    const normalizedId = id ? id.toLowerCase() : null
    set({ customerId: normalizedId })
    if (typeof window !== "undefined") {
      if (normalizedId) {
        localStorage.setItem("custoflow_customer_id", normalizedId)
      } else {
        localStorage.removeItem("custoflow_customer_id")
      }
    }
  },
  setSessionId: (id) => set({ sessionId: id }),
  setTheme: (theme) => {
    // Force light theme only - ignore dark theme requests
    const forcedTheme = "light"
    set({ theme: forcedTheme })
    if (typeof window !== "undefined") {
      localStorage.setItem("custoflow_theme", forcedTheme)
      document.documentElement.classList.remove("dark")
    }
  },
  initFromStorage: () => {
    if (typeof window === "undefined") return
    const savedUserId = localStorage.getItem("custoflow_user_id") || `user_${Date.now()}`
    const savedCustomerId = localStorage.getItem("custoflow_customer_id")
    // Normalize saved customer_id to lowercase
    const normalizedCustomerId = savedCustomerId ? savedCustomerId.toLowerCase() : null
    // Force light theme - ignore saved theme
    const forcedTheme = "light"
    localStorage.setItem("custoflow_user_id", savedUserId)
    localStorage.setItem("custoflow_theme", forcedTheme)
    document.documentElement.classList.remove("dark")
    set({ userId: savedUserId, customerId: normalizedCustomerId, theme: forcedTheme })
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("custoflow_customer_id")
    }
    set({ customerId: null, sessionId: null })
  },
}))
