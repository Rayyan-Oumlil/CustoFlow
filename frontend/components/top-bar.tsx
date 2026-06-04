"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"

const NAV = [
  { label: "Overview",   href: "/" },
  { label: "Chat",       href: "/chat" },
  { label: "Orders",     href: "/orders" },
  { label: "Tickets",    href: "/tickets" },
  { label: "Monitoring", href: "/monitoring" },
  { label: "Analytics",  href: "/analytics" },
  { label: "Learning",   href: "/agent-refinements" },
]

export function TopBar() {
  const pathname = usePathname()
  const { theme, setTheme, initFromStorage } = useStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    initFromStorage()
    setMounted(true)
  }, [initFromStorage])

  const toggleTheme = () => setTheme(theme === "light" ? "dark" : "light")

  return (
    <header className="ws-topbar">
      {/* Brand */}
      <div className="ws-brand">
        <div className="ws-mark">C</div>
        <span className="ws-brand-name">CustoFlow</span>
      </div>

      {/* Nav pills */}
      <nav className="ws-nav">
        {NAV.map(({ label, href }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href)
          return (
            <Link key={href} href={href} className={isActive ? "active" : ""}>
              {label}
              {label === "Tickets" && !isActive && <span className="nbadge" />}
            </Link>
          )
        })}
      </nav>

      <div style={{ flex: 1 }} />

      {/* Search bar (cosmetic — ⌘K shortcut) */}
      <div className="ws-search" role="button" aria-label="Search">
        <span style={{ fontSize: 16, color: "var(--ws-mut)" }}>⌕</span>
        <span>Search…</span>
        <span className="ws-kbd">⌘K</span>
      </div>

      {/* Theme toggle */}
      {mounted && (
        <button
          className="ws-icbtn"
          onClick={toggleTheme}
          title="Toggle theme"
          aria-label="Toggle dark mode"
        >
          {theme === "light" ? "☾" : "☀"}
        </button>
      )}

      {/* Avatar */}
      <div className="ws-avatar">R</div>
    </header>
  )
}
