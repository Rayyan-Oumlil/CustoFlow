"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/lib/store"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"

export default function LoginPage() {
  const router = useRouter()
  const { customerId, setCustomerId, initFromStorage } = useStore()
  const [inputCustomerId, setInputCustomerId] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    initFromStorage()
    // If already logged in, redirect to chat
    if (customerId) {
      router.push("/chat")
    }
  }, [customerId, router, initFromStorage])

  const validateCustomerId = (id: string): boolean => {
    // Pattern: ^[A-Za-z0-9_-]{1,50}$
    const pattern = /^[A-Za-z0-9_-]{1,50}$/
    return pattern.test(id.trim())
  }

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!inputCustomerId.trim()) {
      setError("Customer ID is required")
      return
    }

    if (!validateCustomerId(inputCustomerId)) {
      setError("Invalid Customer ID format. Must be 1-50 characters, alphanumeric with underscores or hyphens (e.g., cust_001, CUST-123)")
      return
    }

    // Save customer ID and redirect
    setCustomerId(inputCustomerId.trim())
    router.push("/chat")
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Customer Support" description="Enter your Customer ID to access support" />
      
      <div className="flex-1 flex items-center justify-center p-8">
        <Card className="w-full max-w-md p-6">
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-semibold mb-2">Welcome</h2>
              <p className="text-muted-foreground">
                Please enter your Customer ID to access the support chat.
              </p>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="customer_id">Customer ID *</Label>
                <Input
                  id="customer_id"
                  value={inputCustomerId}
                  onChange={(e) => {
                    setInputCustomerId(e.target.value)
                    setError("")
                  }}
                  placeholder="cust_001"
                  className={error ? "border-destructive" : ""}
                  autoFocus
                />
                {error && (
                  <p className="text-sm text-destructive mt-1">{error}</p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Format: 1-50 characters, alphanumeric + underscores/hyphens (e.g., cust_001, CUST-123)
                </p>
              </div>

              <Button type="submit" className="w-full" disabled={!inputCustomerId.trim()}>
                Access Support Chat
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  )
}

