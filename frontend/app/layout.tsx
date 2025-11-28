import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { SidebarNav } from "@/components/sidebar-nav"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "CustoFlow - Customer Support System",
  description: "Intelligent customer support dashboard",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // Force light theme - remove dark mode
                document.documentElement.classList.remove('dark');
                localStorage.setItem('custoflow_theme', 'light');
              })();
            `,
          }}
        />
      </head>
      <body className={`font-sans antialiased ${_geist.className}`}>
        <div className="flex h-screen">
          <SidebarNav />
          <div className="flex-1 overflow-hidden">{children}</div>
        </div>
        <Analytics />
      </body>
    </html>
  )
}
