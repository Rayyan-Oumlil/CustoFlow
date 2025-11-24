"use client"

import type React from "react"

import { BarChart3, Home, MessageSquare, Package } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  { label: "Home", href: "/", icon: <Home className="w-4 h-4" /> },
  { label: "Chat", href: "/chat", icon: <MessageSquare className="w-4 h-4" /> },
  { label: "Orders", href: "/orders", icon: <Package className="w-4 h-4" /> },
  { label: "Analytics", href: "/analytics", icon: <BarChart3 className="w-4 h-4" /> },
]

export function SidebarNav() {
  const pathname = usePathname()

  return (
    <div className="w-64 border-r border-border bg-sidebar text-sidebar-foreground flex flex-col min-h-screen">
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-sidebar-primary rounded-lg flex items-center justify-center text-sidebar-primary-foreground font-bold">
            C
          </div>
          <div>
            <h1 className="font-semibold text-sm">CustoFlow</h1>
            <p className="text-xs text-sidebar-foreground/60">Customer Support</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded text-sm transition-colors",
              pathname === item.href
                ? "bg-sidebar-primary text-sidebar-primary-foreground font-medium"
                : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            {item.icon}
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-sidebar-border text-xs text-sidebar-foreground/60">
        <p>v0.1.0</p>
      </div>
    </div>
  )
}
