"use client"

import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"
import { apiClient } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckCircle2, XCircle, Clock, Play, TestTube } from "lucide-react"

const AGENTS = [
  { value: "orchestrator", label: "Orchestrator" },
  { value: "faq_agent", label: "FAQ Agent" },
  { value: "order_agent", label: "Order Agent" },
  { value: "escalation_agent", label: "Escalation Agent" },
  { value: "sentiment_agent", label: "Sentiment Agent" },
]

interface Refinement {
  refinement_key: string
  agent_name: string
  refinement_type: string
  changes: {
    suggested_improvement: string
    customer_feedback?: string
    rating?: number
  }
  feedback_sources: string[]
  status: "pending" | "applied" | "rejected" | "active"
  created_at?: string
  updated_at?: string
  user_input?: string
  agent_response?: string
  learning_reason?: string
}

export default function AgentRefinementsPage() {
  const { initFromStorage } = useStore()
  const [selectedAgent, setSelectedAgent] = useState<string>("order_agent")
  const [refinements, setRefinements] = useState<Refinement[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  
  // Test injection
  const [testMessage, setTestMessage] = useState("")
  const [testResponse, setTestResponse] = useState("")
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  useEffect(() => {
    fetchRefinements()
  }, [selectedAgent])

  const fetchRefinements = async () => {
    try {
      setLoading(true)
      const data = await apiClient.get<any>(`/agent-refinements/${selectedAgent}`)
      setRefinements(data.pending_refinements || [])
      setSummary(data.summary || {})
    } catch (error) {
      console.error("Failed to fetch refinements:", error)
    } finally {
      setLoading(false)
    }
  }

  const applyRefinements = async () => {
    try {
      setApplying(true)
      const result = await apiClient.post<any>(`/agent-refinements/${selectedAgent}/apply`, {})
      alert(`✅ ${result.message || `Applied ${result.refinements_applied || 0} refinements`}`)
      await fetchRefinements()
    } catch (error: any) {
      alert(`❌ Error: ${error.message || "Failed to apply refinements"}`)
    } finally {
      setApplying(false)
    }
  }

  const testInjection = async () => {
    if (!testMessage.trim()) {
      alert("Please enter a test message")
      return
    }

    try {
      setTesting(true)
      setTestResponse("")
      
      // Test with injection
      const response = await apiClient.post<{ response: string }>("/chat", {
        message: testMessage,
        user_id: "test_user",
        inject_refinements: true, // Enable injection
      })
      
      setTestResponse(response.response)
    } catch (error: any) {
      setTestResponse(`Error: ${error.message || "Failed to test"}`)
    } finally {
      setTesting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "applied":
        return <Badge variant="default" className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />Applied</Badge>
      case "pending":
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />Pending</Badge>
      case "rejected":
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Rejected</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader 
        title="Agent Refinements & Auto-Learning" 
        description="Visualize and manage agent improvements based on customer feedback"
      />

      <div className="flex-1 overflow-auto px-8 py-8">
        {/* Agent Selection */}
        <Card className="p-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Select Agent</label>
              <Select value={selectedAgent} onValueChange={setSelectedAgent}>
                <SelectTrigger className="w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AGENTS.map((agent) => (
                    <SelectItem key={agent.value} value={agent.value}>
                      {agent.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Button 
                onClick={applyRefinements} 
                disabled={applying || refinements.filter(r => r.status === "pending").length === 0}
                className="min-w-[150px]"
              >
                {applying ? "Applying..." : `Apply Pending (${refinements.filter(r => r.status === "pending").length})`}
              </Button>
            </div>
          </div>
        </Card>

        {/* Summary */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Total Refinements</p>
              <p className="text-2xl font-bold">{summary.total_refinements || 0}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">{summary.pending || 0}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Applied</p>
              <p className="text-2xl font-bold text-green-600">{summary.applied || 0}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Rejected</p>
              <p className="text-2xl font-bold text-red-600">{summary.rejected || 0}</p>
            </Card>
          </div>
        )}

        {/* Refinements List */}
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Refinements</h2>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : refinements.length === 0 ? (
            <p className="text-muted-foreground">No refinements found for this agent.</p>
          ) : (
            <div className="space-y-4">
              {refinements.map((refinement) => (
                <Card key={refinement.refinement_key} className="p-4 border-l-4 border-l-blue-500">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getStatusBadge(refinement.status)}
                        <span className="text-sm text-muted-foreground">
                          {refinement.refinement_type}
                        </span>
                        {refinement.learning_reason && (
                          <Badge variant="outline" className="text-xs">
                            Reason: {refinement.learning_reason}
                          </Badge>
                        )}
                      </div>
                      <p className="font-medium mb-2">
                        {refinement.changes.suggested_improvement}
                      </p>
                      {refinement.changes.customer_feedback && (
                        <p className="text-sm text-muted-foreground mb-2">
                          <strong>Customer Feedback:</strong> {refinement.changes.customer_feedback}
                        </p>
                      )}
                      {refinement.user_input && (
                        <div className="mt-2 p-2 bg-muted rounded text-sm">
                          <p><strong>User Input:</strong> {refinement.user_input}</p>
                          {refinement.agent_response && (
                            <p className="mt-1"><strong>Agent Response:</strong> {refinement.agent_response}</p>
                          )}
                        </div>
                      )}
                      {refinement.created_at && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Created: {new Date(refinement.created_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </Card>

        {/* Test Injection */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <TestTube className="w-5 h-5" />
            Test Refinement Injection
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            Test how refinements are injected into agent responses. Enter a message and see the result with refinements applied.
          </p>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Test Message</label>
              <Input
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Enter a test message..."
                className="mb-2"
              />
              <Button 
                onClick={testInjection} 
                disabled={testing || !testMessage.trim()}
                className="w-full"
              >
                {testing ? "Testing..." : "Test with Refinements Injected"}
              </Button>
            </div>
            
            {testResponse && (
              <div>
                <label className="text-sm font-medium mb-2 block">Agent Response (with refinements)</label>
                <Textarea
                  value={testResponse}
                  readOnly
                  className="min-h-[200px] font-mono text-sm"
                />
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

