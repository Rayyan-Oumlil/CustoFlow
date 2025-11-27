"use client"

import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"
import { apiClient } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Ticket, MessageSquare, Search, Filter, MessageCircle } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { ChatPanel } from "@/components/chat-panel"

interface TicketWithSummary {
  ticket_id: string
  customer_id?: string
  user_id?: string
  session_id?: string
  issue: string
  priority: string
  status: string
  created_at: string
  updated_at: string
  summary?: string
}

function formatDateOnly(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
  } catch {
    return dateString
  }
}

function formatSummary(summary: string): string[] {
  if (!summary) return []
  return summary
    .split("\n")
    .map((line) => line.trim())
    .filter((p) => p.length > 0)
}

export default function TicketsPage() {
  const { initFromStorage, userId } = useStore()
  const [tickets, setTickets] = useState<TicketWithSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [isMessageDialogOpen, setIsMessageDialogOpen] = useState(false)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [selectedTicket, setSelectedTicket] = useState<TicketWithSummary | null>(null)
  const [ticketMessage, setTicketMessage] = useState("")
  const [sendingMessage, setSendingMessage] = useState(false)
  const [filters, setFilters] = useState({
    status: "all",
    priority: "all",
    search: "",
  })

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  const fetchData = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get<any>("/tickets")
      const ticketsList = response.tickets || []
      setTickets(ticketsList)
    } catch (error) {
      console.error("Failed to fetch tickets:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      open: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      in_progress: "bg-yellow-500/20 text-yellow-700 dark:text-yellow-300",
      resolved: "bg-green-500/20 text-green-700 dark:text-green-300",
      closed: "bg-gray-500/20 text-gray-700 dark:text-gray-300",
    }
    return colors[status.toLowerCase()] || "bg-muted text-muted-foreground"
  }

  const getPriorityBadgeColor = (priority: string) => {
    const colors: Record<string, string> = {
      urgent: "bg-red-500/20 text-red-700 dark:text-red-300",
      high: "bg-orange-500/20 text-orange-700 dark:text-orange-300",
      normal: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      low: "bg-gray-500/20 text-gray-700 dark:text-gray-300",
    }
    return colors[priority.toLowerCase()] || "bg-muted text-muted-foreground"
  }

  const filteredTickets = tickets.filter((ticket) => {
    if (filters.status !== "all" && ticket.status.toLowerCase() !== filters.status.toLowerCase()) {
      return false
    }
    if (filters.priority !== "all" && ticket.priority.toLowerCase() !== filters.priority.toLowerCase()) {
      return false
    }
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      return (
        ticket.ticket_id.toLowerCase().includes(searchLower) ||
        ticket.issue.toLowerCase().includes(searchLower) ||
        (ticket.customer_id && ticket.customer_id.toLowerCase().includes(searchLower))
      )
    }
    return true
  })

  const handleSendMessage = async () => {
    if (!selectedTicket || !ticketMessage.trim() || !selectedTicket.user_id || !selectedTicket.session_id) {
      alert("Please select a ticket and enter a message.")
      return
    }
    setSendingMessage(true)
    try {
      await apiClient.sendTicketMessage(selectedTicket.ticket_id, ticketMessage)
      alert("Message sent successfully!")
      setTicketMessage("")
      setIsMessageDialogOpen(false)
      fetchData() // Refresh tickets
    } catch (error: any) {
      console.error("Failed to send message:", error)
      alert(`Failed to send message: ${error.message || "Unknown error"}`)
    } finally {
      setSendingMessage(false)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <PageHeader
        title="Support Tickets"
        description="Manage and respond to customer support tickets"
        icon={<Ticket className="h-6 w-6" />}
      />

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="search">Search</Label>
              <div className="relative mt-2">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search tickets..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="pl-10"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="status-filter">Status</Label>
              <Select value={filters.status} onValueChange={(value) => setFilters({ ...filters, status: value })}>
                <SelectTrigger id="status-filter" className="mt-2">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="priority-filter">Priority</Label>
              <Select value={filters.priority} onValueChange={(value) => setFilters({ ...filters, priority: value })}>
                <SelectTrigger id="priority-filter" className="mt-2">
                  <SelectValue placeholder="All priorities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => setFilters({ status: "all", priority: "all", search: "" })}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tickets List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            Tickets ({filteredTickets.length} of {tickets.length})
          </h2>
        </div>

        {loading ? (
          <div className="text-center text-muted-foreground py-8">Loading tickets...</div>
        ) : filteredTickets.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No tickets found.
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTickets.map((ticket) => (
              <Card key={ticket.ticket_id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-sm font-medium">Ticket {ticket.ticket_id}</CardTitle>
                    <div className="flex gap-2">
                      <Badge className={getStatusBadgeColor(ticket.status)}>{ticket.status}</Badge>
                      <Badge className={getPriorityBadgeColor(ticket.priority)} variant="outline">
                        {ticket.priority}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm font-medium mb-1">Issue</p>
                    <p className="text-sm text-muted-foreground line-clamp-2">{ticket.issue}</p>
                  </div>
                  {ticket.summary && (
                    <div>
                      <p className="text-sm font-medium mb-1">Summary</p>
                      <div className="text-sm text-muted-foreground space-y-1">
                        {formatSummary(ticket.summary).slice(0, 3).map((line, idx) => (
                          <p key={idx} className="line-clamp-1">
                            {line}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p>Customer: {ticket.customer_id || "N/A"}</p>
                    <p>Created: {formatDateOnly(ticket.created_at)}</p>
                    <p>Updated: {formatDateOnly(ticket.updated_at)}</p>
                  </div>
                  {ticket.user_id && ticket.session_id && ticket.customer_id && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => {
                          setSelectedTicket(ticket)
                          setIsChatOpen(true)
                        }}
                        className="flex-1"
                      >
                        <MessageCircle className="w-4 h-4 mr-2" />
                        Open Chat
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedTicket(ticket)
                          setIsMessageDialogOpen(true)
                        }}
                        className="flex-1"
                      >
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Quick Reply
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Send Message Dialog */}
      <Dialog open={isMessageDialogOpen} onOpenChange={setIsMessageDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Send Message to Customer</DialogTitle>
            <DialogDescription>
              Send a message to the customer for ticket {selectedTicket?.ticket_id}. The message will appear in their
              chat as if from a human agent.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="ticket-message">Message</Label>
              <Textarea
                id="ticket-message"
                className="w-full mt-2 min-h-[120px] resize-none"
                placeholder="Type your message to the customer..."
                value={ticketMessage}
                onChange={(e) => setTicketMessage(e.target.value)}
                disabled={sendingMessage}
              />
            </div>
            {selectedTicket && (
              <div className="text-sm text-muted-foreground space-y-1">
                <p>Customer: {selectedTicket.customer_id || "N/A"}</p>
                <p>Session: {selectedTicket.session_id?.slice(-8) || "N/A"}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsMessageDialogOpen(false)
                setTicketMessage("")
                setSelectedTicket(null)
              }}
              disabled={sendingMessage}
            >
              Cancel
            </Button>
            <Button onClick={handleSendMessage} disabled={sendingMessage || !ticketMessage.trim()}>
              {sendingMessage ? "Sending..." : "Send Message"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Chat Panel */}
      <Sheet open={isChatOpen} onOpenChange={setIsChatOpen}>
        <SheetContent side="right" className="w-full sm:max-w-2xl p-0">
          <SheetHeader className="sr-only">
            <SheetTitle>Chat with Customer</SheetTitle>
            <SheetDescription>
              Continue the conversation with the customer for ticket {selectedTicket?.ticket_id}
            </SheetDescription>
          </SheetHeader>
          {selectedTicket && selectedTicket.customer_id && selectedTicket.session_id && userId && (
            <ChatPanel
              customerId={selectedTicket.customer_id}
              sessionId={selectedTicket.session_id}
              userId={userId}
              ticketId={selectedTicket.ticket_id}
            />
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}

