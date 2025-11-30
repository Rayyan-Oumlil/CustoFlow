"use client"

import { useEffect, useState } from "react"
import { useStore } from "@/lib/store"
import { apiClient, type Order } from "@/lib/api-client"
import { PageHeader } from "@/components/page-header"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Trash2, Pencil, DollarSign, CheckCircle, XCircle, Clock } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/components/ui/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface Refund {
  refund_id: string
  order_id: string
  customer_id: string
  amount: number
  reason: string
  status: "pending" | "approved" | "rejected" | "processed"
  requested_at: string
  processed_at?: string
  created_at: string
  updated_at: string
}

// Format date string (YYYY-MM-DD) to locale date without timezone conversion
function formatDateOnly(dateString: string): string {
  if (!dateString) return "N/A"
  try {
    // Parse YYYY-MM-DD format directly to avoid timezone issues
    const [year, month, day] = dateString.split("T")[0].split("-")
    if (!year || !month || !day) return dateString
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
    return date.toLocaleDateString()
  } catch {
    return dateString
  }
}

// Format summary text for better readability - split into paragraphs and format
function formatSummary(summary: string): string[] {
  if (!summary) return []
  
  // Split by double newlines (paragraphs) or single newlines if no double newlines
  const paragraphs = summary.includes('\n\n') 
    ? summary.split(/\n\n+/)
    : summary.split('\n')
  
  return paragraphs
    .map(p => p.trim())
    .filter(p => p.length > 0)
}

interface Customer {
  customer_id: string
  name?: string
}

export default function OrdersPage() {
  const { initFromStorage } = useStore()
  const { toast } = useToast()
  const [orders, setOrders] = useState<Order[]>([])
  const [refunds, setRefunds] = useState<Refund[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefundStatusDialogOpen, setIsRefundStatusDialogOpen] = useState(false)
  const [selectedRefund, setSelectedRefund] = useState<Refund | null>(null)
  const [newRefundStatus, setNewRefundStatus] = useState<string>("")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isCreateCustomerDialogOpen, setIsCreateCustomerDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingOrder, setEditingOrder] = useState<Order | null>(null)
  const [newCustomerId, setNewCustomerId] = useState("")
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [orderToDelete, setOrderToDelete] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    status: "all",
    customer_id: "",
    order_id: "",
  })
  const [newOrder, setNewOrder] = useState({
    order_id: "", // Will be auto-generated if empty
    customer_id: "", // Will be selected from dropdown or auto-generated
    status: "processing" as const,
    items: [{ name: "", quantity: 1, price: 0 }],
    total: 0,
    order_date: new Date().toISOString().split("T")[0],
    tracking_number: "",
    estimated_delivery: "",
  })

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

    const fetchData = async () => {
      try {
        setLoading(true)
        const [ordersResponse, refundsResponse, customersResponse] = await Promise.all([
          apiClient.get<any>("/orders").catch(() => ({ orders: [] })),
          apiClient.get<Refund[]>("/refunds").catch(() => []),
          apiClient.get<{ customers: Customer[] }>("/customers").catch(() => ({ customers: [] })),
        ])
        const ordersList = Array.isArray(ordersResponse?.orders) ? ordersResponse.orders : []
        const refundsList = Array.isArray(refundsResponse) ? refundsResponse : []
        const customersList = Array.isArray(customersResponse?.customers) ? customersResponse.customers : []
        
        setOrders(ordersList)
        setRefunds(refundsList)
        setCustomers(customersList)
      } catch (error) {
        console.error("Failed to fetch data:", error)
        setOrders([])
        setRefunds([])
        setCustomers([])
      } finally {
        setLoading(false)
      }
    }

  useEffect(() => {
    fetchData()
  }, [])

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      processing: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      shipped: "bg-purple-500/20 text-purple-700 dark:text-purple-300",
      delivering: "bg-indigo-500/20 text-indigo-700 dark:text-indigo-300",
      delivery_soon: "bg-orange-500/20 text-orange-700 dark:text-orange-300",
      delivered: "bg-green-500/20 text-green-700 dark:text-green-300",
      cancelled: "bg-red-500/20 text-red-700 dark:text-red-300",
      open: "bg-red-500/20 text-red-700 dark:text-red-300",
      in_progress: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      resolved: "bg-green-500/20 text-green-700 dark:text-green-300",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  const getPriorityBadgeColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      normal: "bg-gray-500/20 text-gray-700 dark:text-gray-300",
      high: "bg-orange-500/20 text-orange-700 dark:text-orange-300",
      urgent: "bg-red-500/20 text-red-700 dark:text-red-300",
    }
    return colors[priority] || "bg-muted text-muted-foreground"
  }

  const getRefundStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-yellow-500/20 text-yellow-700 dark:text-yellow-300",
      approved: "bg-blue-500/20 text-blue-700 dark:text-blue-300",
      rejected: "bg-red-500/20 text-red-700 dark:text-red-300",
      processed: "bg-green-500/20 text-green-700 dark:text-green-300",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  const handleUpdateRefundStatus = async () => {
    if (!selectedRefund || !newRefundStatus) return
    
    try {
      await apiClient.put(`/refunds/${selectedRefund.refund_id}/status`, {
        status: newRefundStatus,
      })
      setIsRefundStatusDialogOpen(false)
      setSelectedRefund(null)
      setNewRefundStatus("")
      await fetchData()
      alert("Refund status updated successfully!")
    } catch (error: any) {
      console.error("Failed to update refund status:", error)
      alert(`Failed to update refund status: ${error.message || "Unknown error"}`)
    }
  }

  const handleDeleteOrder = (orderId: string) => {
    setOrderToDelete(orderId)
    setDeleteConfirmOpen(true)
  }

  const confirmDeleteOrder = async () => {
    if (!orderToDelete) return
    
    try {
      await apiClient.delete(`/orders/${orderToDelete}`)
      toast({
        title: "Order deleted",
        description: `Order ${orderToDelete} has been deleted successfully.`,
      })
      await fetchData()
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to delete order. Please try again.",
        variant: "destructive",
      })
    } finally {
      setDeleteConfirmOpen(false)
      setOrderToDelete(null)
    }
  }

  const handleUpdateOrder = async () => {
    if (!editingOrder) return
    
    try {
      await apiClient.put(`/orders/${editingOrder.order_id}`, {
        status: editingOrder.status,
        tracking_number: editingOrder.tracking_number || null,
        estimated_delivery: editingOrder.estimated_delivery || null,
      })
      toast({
        title: "Order updated",
        description: `Order ${editingOrder.order_id} has been updated successfully.`,
      })
      setIsEditDialogOpen(false)
      setEditingOrder(null)
      await fetchData()
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to update order. Please try again.",
        variant: "destructive",
      })
    }
  }

  // Validation functions matching backend patterns
  const validateOrderId = (orderId: string): string | null => {
    if (!orderId || !orderId.trim()) {
      return "Order ID cannot be empty"
    }
    // Pattern: ^[A-Za-z0-9-]{3,20}$
    const pattern = /^[A-Za-z0-9-]{3,20}$/
    if (!pattern.test(orderId.trim())) {
      return "Order ID must be 3-20 characters, alphanumeric with hyphens only (e.g., 12345, ORDER-123)"
    }
    return null
  }

  const validateCustomerId = (customerId: string): string | null => {
    if (!customerId || !customerId.trim()) {
      return "Customer ID cannot be empty"
    }
    // Pattern: ^[A-Za-z0-9_-]{1,50}$
    const pattern = /^[A-Za-z0-9_-]{1,50}$/
    if (!pattern.test(customerId.trim())) {
      return "Customer ID must be 1-50 characters, alphanumeric with underscores or hyphens (e.g., cust_001, CUST-123)"
    }
    return null
  }

  const handleCreateCustomer = async () => {
    try {
      const customerData: any = {}
      if (newCustomerId.trim()) {
        customerData.customer_id = newCustomerId.trim()
      }
      // If empty, backend will auto-generate
      
      const response = await apiClient.post<{ status: string; customer_id: string; message: string }>("/customers", customerData)
      setIsCreateCustomerDialogOpen(false)
      setNewCustomerId("")
      await fetchData() // Refresh customers list
      // Auto-select the newly created customer
      setNewOrder({ ...newOrder, customer_id: response.customer_id })
      toast({
        title: "Customer created",
        description: `Customer ${response.customer_id} has been created successfully.`,
      })
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to create customer. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleCreateOrder = async () => {
    // Order ID and Customer ID are now optional - backend will auto-generate if empty
    // But if provided, validate them
    
    if (newOrder.order_id.trim()) {
      const orderIdError = validateOrderId(newOrder.order_id)
      if (orderIdError) {
        alert(orderIdError)
        return
      }
    }

    if (newOrder.customer_id.trim()) {
      const customerIdError = validateCustomerId(newOrder.customer_id)
      if (customerIdError) {
        alert(customerIdError)
        return
      }
    }

    // Validate items
    if (newOrder.items.length === 0 || newOrder.items.some(item => !item.name.trim())) {
      alert("Please add at least one item with a name")
      return
    }

    try {
      // Calculate total from items
      const total = newOrder.items.reduce((sum, item) => sum + (item.price * item.quantity), 0)
      
      const orderData: any = {
        ...newOrder,
        total,
        created_at: newOrder.order_date,
      }
      
      // Remove empty IDs - backend will generate them
      if (!orderData.order_id || !orderData.order_id.trim()) {
        delete orderData.order_id
      }
      if (!orderData.customer_id || !orderData.customer_id.trim()) {
        delete orderData.customer_id
      }
      
      const response = await apiClient.post<{ status: string; message: string; order: any }>("/orders", orderData)
      const createdOrderId = response.order?.order_id || orderData.order_id || "order"
      toast({
        title: "Order created",
        description: `Order ${createdOrderId} has been created successfully.`,
      })
      setIsCreateDialogOpen(false)
      setNewOrder({
        order_id: "",
        customer_id: "",
        status: "processing",
        items: [{ name: "", quantity: 1, price: 0 }],
        total: 0,
        order_date: new Date().toISOString().split("T")[0],
        tracking_number: "",
        estimated_delivery: "",
      })
      await fetchData()
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to create order. Please try again.",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Orders" description="Manage orders and refunds" />

      <div className="flex-1 overflow-auto px-8 py-8">
        <Tabs defaultValue="orders" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="orders">Orders</TabsTrigger>
            <TabsTrigger value="refunds">Refunds</TabsTrigger>
          </TabsList>

          <TabsContent value="orders" className="mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Orders</h2>
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Order
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Create New Order</DialogTitle>
                    <DialogDescription>Add a new order to the system</DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="order_id">Order ID (Auto-generated if empty)</Label>
                        <Input
                          id="order_id"
                          value={newOrder.order_id}
                          onChange={(e) => setNewOrder({ ...newOrder, order_id: e.target.value })}
                          placeholder="Leave empty for auto-generation"
                          className={newOrder.order_id && validateOrderId(newOrder.order_id) ? "border-destructive" : ""}
                        />
                        {newOrder.order_id && validateOrderId(newOrder.order_id) && (
                          <p className="text-xs text-destructive mt-1">
                            {validateOrderId(newOrder.order_id)}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1">
                          Leave empty to auto-generate (order_001, order_002, ...) or enter custom ID
                        </p>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <Label htmlFor="customer_id">Customer *</Label>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setIsCreateCustomerDialogOpen(true)}
                          >
                            <Plus className="w-3 h-3 mr-1" />
                            New Customer
                          </Button>
                        </div>
                        <Select
                          value={newOrder.customer_id}
                          onValueChange={(value) => setNewOrder({ ...newOrder, customer_id: value })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select customer or leave empty for auto-generation" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Auto-generate new customer</SelectItem>
                            {customers.map((customer) => (
                              <SelectItem key={customer.customer_id} value={customer.customer_id}>
                                {customer.name || customer.customer_id}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {newOrder.customer_id && validateCustomerId(newOrder.customer_id) && (
                          <p className="text-xs text-destructive mt-1">
                            {validateCustomerId(newOrder.customer_id)}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1">
                          Select existing customer or leave empty to auto-generate (cust_001, cust_002, ...)
                        </p>
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="status">Status *</Label>
                      <Select
                        value={newOrder.status}
                        onValueChange={(value: any) => setNewOrder({ ...newOrder, status: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="processing">Processing</SelectItem>
                          <SelectItem value="shipped">Shipped</SelectItem>
                          <SelectItem value="delivering">Delivering</SelectItem>
                          <SelectItem value="delivery_soon">Delivery Soon</SelectItem>
                          <SelectItem value="delivered">Delivered</SelectItem>
                          <SelectItem value="cancelled">Cancelled</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Items *</Label>
                      {newOrder.items.map((item, index) => (
                        <div key={index} className="grid grid-cols-3 gap-2 mt-2">
                          <Input
                            placeholder="Item name"
                            value={item.name}
                            onChange={(e) => {
                              const items = [...newOrder.items]
                              items[index].name = e.target.value
                              setNewOrder({ ...newOrder, items })
                            }}
                          />
                          <Input
                            type="number"
                            placeholder="Quantity"
                            value={item.quantity}
                            onChange={(e) => {
                              const items = [...newOrder.items]
                              items[index].quantity = parseInt(e.target.value) || 0
                              setNewOrder({ ...newOrder, items })
                            }}
                          />
                          <Input
                            type="number"
                            step="0.01"
                            placeholder="Price"
                            value={item.price}
                            onChange={(e) => {
                              const items = [...newOrder.items]
                              items[index].price = parseFloat(e.target.value) || 0
                              setNewOrder({ ...newOrder, items })
                            }}
                          />
                        </div>
                      ))}
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="mt-2"
                        onClick={() => setNewOrder({ ...newOrder, items: [...newOrder.items, { name: "", quantity: 1, price: 0 }] })}
                      >
                        Add Item
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="tracking_number">Tracking Number</Label>
                        <Input
                          id="tracking_number"
                          value={newOrder.tracking_number}
                          onChange={(e) => setNewOrder({ ...newOrder, tracking_number: e.target.value })}
                          placeholder="TRACK123456"
                        />
                      </div>
                      <div>
                        <Label htmlFor="estimated_delivery">Estimated Delivery</Label>
                        <Input
                          id="estimated_delivery"
                          type="date"
                          value={newOrder.estimated_delivery}
                          onChange={(e) => setNewOrder({ ...newOrder, estimated_delivery: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>Cancel</Button>
                    <Button 
                      onClick={handleCreateOrder}
                      disabled={
                        (newOrder.order_id.trim() && !!validateOrderId(newOrder.order_id)) ||
                        (newOrder.customer_id.trim() && !!validateCustomerId(newOrder.customer_id)) ||
                        newOrder.items.length === 0 ||
                        newOrder.items.some(item => !item.name.trim() || item.quantity <= 0 || item.price <= 0)
                      }
                    >
                      Create Order
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              {/* Create Customer Dialog */}
              <Dialog open={isCreateCustomerDialogOpen} onOpenChange={setIsCreateCustomerDialogOpen}>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create New Customer</DialogTitle>
                    <DialogDescription>Create a new customer for testing. Customer ID will be auto-generated if left empty.</DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div>
                      <Label htmlFor="new_customer_id">Customer ID (Optional)</Label>
                      <Input
                        id="new_customer_id"
                        value={newCustomerId}
                        onChange={(e) => setNewCustomerId(e.target.value)}
                        placeholder="Leave empty for auto-generation (cust_001, cust_002, ...)"
                      />
                      {newCustomerId && validateCustomerId(newCustomerId) && (
                        <p className="text-xs text-destructive mt-1">
                          {validateCustomerId(newCustomerId)}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground mt-1">
                        Leave empty to auto-generate or enter custom ID (e.g., cust_001, CUST-123)
                      </p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsCreateCustomerDialogOpen(false)}>Cancel</Button>
                    <Button 
                      onClick={handleCreateCustomer}
                      disabled={newCustomerId.trim() && !!validateCustomerId(newCustomerId)}
                    >
                      Create Customer
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
            {loading ? (
              <p className="text-muted-foreground">Loading orders...</p>
            ) : orders.length === 0 ? (
              <p className="text-muted-foreground">No orders found</p>
            ) : (
              <div className="space-y-4">
                {/* Filters */}
                <Card className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="filter-order-id" className="text-sm font-medium mb-2 block">Order ID</Label>
                      <Input
                        id="filter-order-id"
                        placeholder="Filter by Order ID"
                        value={filters.order_id}
                        onChange={(e) => setFilters({ ...filters, order_id: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="filter-customer-id" className="text-sm font-medium mb-2 block">Customer ID</Label>
                      <Input
                        id="filter-customer-id"
                        placeholder="Filter by Customer ID"
                        value={filters.customer_id}
                        onChange={(e) => setFilters({ ...filters, customer_id: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="filter-status" className="text-sm font-medium mb-2 block">Status</Label>
                      <Select value={filters.status} onValueChange={(value) => setFilters({ ...filters, status: value })}>
                        <SelectTrigger id="filter-status">
                          <SelectValue placeholder="All statuses" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All statuses</SelectItem>
                          <SelectItem value="processing">Processing</SelectItem>
                          <SelectItem value="shipped">Shipped</SelectItem>
                          <SelectItem value="delivering">Delivering</SelectItem>
                          <SelectItem value="delivery_soon">Delivery Soon</SelectItem>
                          <SelectItem value="delivered">Delivered</SelectItem>
                          <SelectItem value="cancelled">Cancelled</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  {(filters.order_id || filters.customer_id || (filters.status && filters.status !== "all")) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-3"
                      onClick={() => setFilters({ status: "all", customer_id: "", order_id: "" })}
                    >
                      Clear filters
                    </Button>
                  )}
                </Card>
                
                {/* Filtered Orders */}
                <div className="space-y-3">
                  {(() => {
                    const filteredOrders = orders.filter((order) => {
                      if (filters.order_id && !order.order_id.toLowerCase().includes(filters.order_id.toLowerCase())) {
                        return false
                      }
                      if (filters.customer_id && !order.customer_id.toLowerCase().includes(filters.customer_id.toLowerCase())) {
                        return false
                      }
                      if (filters.status && filters.status !== "all" && order.status !== filters.status) {
                        return false
                      }
                      return true
                    })
                    
                    if (filteredOrders.length === 0) {
                      return <p className="text-muted-foreground text-center py-8">No orders match the current filters</p>
                    }
                    
                    return filteredOrders.map((order) => (
                      <Card key={order.order_id} className="p-4 cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => {
                        setEditingOrder(order)
                        setIsEditDialogOpen(true)
                      }}>
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="font-medium">Order {order.order_id}</p>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDeleteOrder(order.order_id)
                                }}
                                title="Delete order"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                            <p className="text-sm text-muted-foreground">Customer: {order.customer_id}</p>
                            {order.items && order.items.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs text-muted-foreground mb-1">
                                  {order.items.length} item{order.items.length > 1 ? "s" : ""}
                                  {order.tracking_number && ` • Tracking: ${order.tracking_number}`}
                                  {order.estimated_delivery && ` • Delivery: ${formatDateOnly(order.estimated_delivery)}`}
                                </p>
                                <div className="text-xs text-muted-foreground">
                                  <p className="font-medium mb-1">Products:</p>
                                  <div className="space-y-0.5">
                                    {order.items.slice(0, 3).map((item, idx) => (
                                      <p key={idx}>
                                        • {item.quantity}x {item.name} (${(item.price * item.quantity).toFixed(2)})
                                      </p>
                                    ))}
                                    {order.items.length > 3 && (
                                      <p className="italic">+ {order.items.length - 3} more item{order.items.length - 3 > 1 ? "s" : ""}</p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                          <div className="text-right ml-4">
                            <p className="font-semibold">${order.total?.toFixed(2) || "0.00"}</p>
                            <Badge className={getStatusBadgeColor(order.status)}>{order.status}</Badge>
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          {order.created_at
                            ? (() => {
                                try {
                                  const date = new Date(order.created_at)
                                  return isNaN(date.getTime()) ? "Date not available" : date.toLocaleDateString()
                                } catch {
                                  return "Date not available"
                                }
                              })()
                            : "Date not available"}
                        </p>
                      </Card>
                    ))
                  })()}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Edit Order Dialog */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Edit Order {editingOrder?.order_id}</DialogTitle>
                <DialogDescription>Update order details</DialogDescription>
              </DialogHeader>
              {editingOrder && (
                <div className="space-y-4">
                  {/* Order Details Section */}
                  <div className="border-b pb-4">
                    <h3 className="text-sm font-semibold mb-3">Order Information</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Order ID</p>
                        <p className="font-medium">{editingOrder.order_id}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Customer ID</p>
                        <p className="font-medium">{editingOrder.customer_id}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Total Amount</p>
                        <p className="font-semibold text-lg">${editingOrder.total?.toFixed(2) || "0.00"}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Order Date</p>
                        <p className="font-medium">
                          {editingOrder.created_at
                            ? (() => {
                                try {
                                  const date = new Date(editingOrder.created_at)
                                  return isNaN(date.getTime()) ? "N/A" : date.toLocaleDateString()
                                } catch {
                                  return "N/A"
                                }
                              })()
                            : "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Products/Items Section */}
                  <div className="border-b pb-4">
                    <h3 className="text-sm font-semibold mb-3">Products</h3>
                    {editingOrder.items && editingOrder.items.length > 0 ? (
                      <div className="space-y-2">
                        <div className="grid grid-cols-4 gap-4 text-sm font-medium text-muted-foreground border-b pb-2">
                          <div>Product Name</div>
                          <div className="text-right">Quantity</div>
                          <div className="text-right">Unit Price</div>
                          <div className="text-right">Subtotal</div>
                        </div>
                        {editingOrder.items.map((item, index) => (
                          <div key={index} className="grid grid-cols-4 gap-4 text-sm py-2 border-b last:border-0">
                            <div className="font-medium">{item.name || "Unnamed Item"}</div>
                            <div className="text-right">{item.quantity || 0}</div>
                            <div className="text-right">${(item.price || 0).toFixed(2)}</div>
                            <div className="text-right font-semibold">
                              ${((item.quantity || 0) * (item.price || 0)).toFixed(2)}
                            </div>
                          </div>
                        ))}
                        <div className="pt-2 mt-2 border-t">
                          <div className="flex justify-end">
                            <div className="text-right">
                              <p className="text-sm text-muted-foreground">Total</p>
                              <p className="text-lg font-bold">${editingOrder.total?.toFixed(2) || "0.00"}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No items in this order</p>
                    )}
                  </div>

                  {/* Shipping Information */}
                  <div className="border-b pb-4">
                    <h3 className="text-sm font-semibold mb-3">Shipping Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="edit-status">Status</Label>
                        <Select
                          value={editingOrder.status}
                          onValueChange={(value) => setEditingOrder({ ...editingOrder, status: value as any })}
                        >
                          <SelectTrigger id="edit-status">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="processing">Processing</SelectItem>
                            <SelectItem value="shipped">Shipped</SelectItem>
                            <SelectItem value="delivering">Delivering</SelectItem>
                            <SelectItem value="delivery_soon">Delivery Soon</SelectItem>
                            <SelectItem value="delivered">Delivered</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="edit-tracking">Tracking Number</Label>
                        <Input
                          id="edit-tracking"
                          value={editingOrder.tracking_number || ""}
                          onChange={(e) => setEditingOrder({ ...editingOrder, tracking_number: e.target.value })}
                          placeholder="TRACK123456"
                        />
                      </div>
                    </div>
                    <div className="mt-4">
                      <Label htmlFor="edit-delivery">Estimated Delivery</Label>
                      <Input
                        id="edit-delivery"
                        type="date"
                        value={editingOrder.estimated_delivery ? editingOrder.estimated_delivery.split("T")[0] : ""}
                        onChange={(e) => setEditingOrder({ ...editingOrder, estimated_delivery: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button variant="outline" onClick={() => {
                  setIsEditDialogOpen(false)
                  setEditingOrder(null)
                }}>Cancel</Button>
                <Button onClick={handleUpdateOrder}>Save Changes</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <TabsContent value="refunds" className="mt-6">
            <div className="space-y-4">
              {refunds.length === 0 ? (
                <Card>
                  <CardContent className="pt-6">
                    <p className="text-center text-muted-foreground">No refund requests found.</p>
                  </CardContent>
                </Card>
              ) : (
                refunds.map((refund) => (
                  <Card key={refund.refund_id} className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <DollarSign className="w-5 h-5 text-muted-foreground" />
                          <h3 className="font-semibold">{refund.refund_id}</h3>
                          <Badge className={getRefundStatusBadgeColor(refund.status)}>
                            {refund.status.toUpperCase()}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                          <div>
                            <p className="text-muted-foreground">Order ID</p>
                            <p className="font-medium">{refund.order_id}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Customer ID</p>
                            <p className="font-medium">{refund.customer_id}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Amount</p>
                            <p className="font-bold text-lg">${refund.amount.toFixed(2)}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Requested</p>
                            <p className="font-medium">
                              {refund.requested_at 
                                ? new Date(refund.requested_at).toLocaleDateString()
                                : "N/A"}
                            </p>
                          </div>
                        </div>
                        {refund.reason && (
                          <div className="mt-3">
                            <p className="text-muted-foreground text-sm">Reason</p>
                            <p className="text-sm mt-1">{refund.reason}</p>
                          </div>
                        )}
                      </div>
                      <div className="ml-4 flex flex-col gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedRefund(refund)
                            setNewRefundStatus(refund.status)
                            setIsRefundStatusDialogOpen(true)
                          }}
                        >
                          <Pencil className="w-4 h-4 mr-2" />
                          Update Status
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Refund Status Dialog */}
        <Dialog open={isRefundStatusDialogOpen} onOpenChange={setIsRefundStatusDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Update Refund Status</DialogTitle>
              <DialogDescription>
                Change the status of refund {selectedRefund?.refund_id}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {selectedRefund && (
                <div className="space-y-2">
                  <div>
                    <Label>Refund ID</Label>
                    <Input value={selectedRefund.refund_id} readOnly />
                  </div>
                  <div>
                    <Label>Order ID</Label>
                    <Input value={selectedRefund.order_id} readOnly />
                  </div>
                  <div>
                    <Label>Amount</Label>
                    <Input value={`$${selectedRefund.amount.toFixed(2)}`} readOnly />
                  </div>
                  <div>
                    <Label htmlFor="refund-status">New Status</Label>
                    <Select value={newRefundStatus} onValueChange={setNewRefundStatus}>
                      <SelectTrigger id="refund-status">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Pending
                          </div>
                        </SelectItem>
                        <SelectItem value="approved">
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" />
                            Approved
                          </div>
                        </SelectItem>
                        <SelectItem value="rejected">
                          <div className="flex items-center gap-2">
                            <XCircle className="w-4 h-4" />
                            Rejected
                          </div>
                        </SelectItem>
                        <SelectItem value="processed">
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" />
                            Processed
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsRefundStatusDialogOpen(false)
                  setSelectedRefund(null)
                  setNewRefundStatus("")
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleUpdateRefundStatus}
                disabled={!newRefundStatus || newRefundStatus === selectedRefund?.status}
              >
                Update Status
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Order</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete order <strong>{orderToDelete}</strong>? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmDeleteOrder} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  )
}
