import type React from "react"
import type { Metadata } from "next"
import { Analytics } from "@vercel/analytics/next"
import { TopBar } from "@/components/top-bar"
import "./globals.css"

export const metadata: Metadata = {
  title: "CustoFlow — Customer Support",
  description: "Multi-agent customer support console",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        {/* Warm Studio fonts */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap"
          rel="stylesheet"
        />
        {/* Apply saved theme before first paint */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var m=localStorage.getItem('cf-mode')||'light';document.documentElement.dataset.mode=m;})()`,
          }}
        />
      </head>
      <body>
        <TopBar />
        <main>{children}</main>
        <Analytics />
      </body>
    </html>
  )
}
