import { create } from "zustand"

interface StoreState {
  userId: string
  sessionId: string | null
  theme: "light" | "dark"
  setUserId: (id: string) => void
  setSessionId: (id: string | null) => void
  setTheme: (theme: "light" | "dark") => void
  initFromStorage: () => void
}

export const useStore = create<StoreState>((set) => ({
  userId: "",
  sessionId: null,
  theme: "light",
  setUserId: (id) => set({ userId: id }),
  setSessionId: (id) => set({ sessionId: id }),
  setTheme: (theme) => set({ theme }),
  initFromStorage: () => {
    if (typeof window === "undefined") return
    const savedUserId = localStorage.getItem("custoflow_user_id") || `user_${Date.now()}`
    const savedTheme = (localStorage.getItem("custoflow_theme") as "light" | "dark") || "light"
    localStorage.setItem("custoflow_user_id", savedUserId)
    localStorage.setItem("custoflow_theme", savedTheme)
    set({ userId: savedUserId, theme: savedTheme })
  },
}))
