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
    set({ customerId: id })
    if (typeof window !== "undefined") {
      if (id) {
        localStorage.setItem("custoflow_customer_id", id)
      } else {
        localStorage.removeItem("custoflow_customer_id")
      }
    }
  },
  setSessionId: (id) => set({ sessionId: id }),
  setTheme: (theme) => set({ theme }),
  initFromStorage: () => {
    if (typeof window === "undefined") return
    const savedUserId = localStorage.getItem("custoflow_user_id") || `user_${Date.now()}`
    const savedCustomerId = localStorage.getItem("custoflow_customer_id")
    const savedTheme = (localStorage.getItem("custoflow_theme") as "light" | "dark") || "light"
    localStorage.setItem("custoflow_user_id", savedUserId)
    localStorage.setItem("custoflow_theme", savedTheme)
    set({ userId: savedUserId, customerId: savedCustomerId, theme: savedTheme })
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("custoflow_customer_id")
    }
    set({ customerId: null, sessionId: null })
  },
}))
