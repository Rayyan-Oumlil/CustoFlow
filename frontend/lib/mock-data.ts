/* Mock data used as fallback when the backend is unreachable.
   Shapes match the real API responses exactly. */

export const MOCK_ANALYTICS = {
  total_messages:   12847,
  active_sessions:  38,
  closed_sessions:  214,
  interactions:     6423,
  avg_satisfaction: 4.6,
  tickets_created:  47,
  open_tickets:     24,
  resolved_tickets: 18,
  resolution_rate:  87,
  avg_response_time: 8.2,
}

export const MOCK_DAILY = [
  { day: "Mon", interactions: 1620, satisfaction: 4.3 },
  { day: "Tue", interactions: 1840, satisfaction: 4.4 },
  { day: "Wed", interactions: 1730, satisfaction: 4.2 },
  { day: "Thu", interactions: 2010, satisfaction: 4.5 },
  { day: "Fri", interactions: 2280, satisfaction: 4.6 },
  { day: "Sat", interactions: 1490, satisfaction: 4.7 },
  { day: "Sun", interactions: 1877, satisfaction: 4.6 },
]

export const MOCK_TICKETS = [
  { ticket_id: "TICKET-FD45", customer_id: "cust_004", user_id: "cust_004", issue: "Order order_042 marked delivered but not received", priority: "urgent", status: "open",        created_at: new Date(Date.now() - 8 * 60000).toISOString(),  session_id: "sess_001" },
  { ticket_id: "TICKET-1A21", customer_id: "cust_009", user_id: "cust_009", issue: "Refund of $129.00 still pending after 9 days",       priority: "high",   status: "in_progress", created_at: new Date(Date.now() - 41 * 60000).toISOString(), session_id: "sess_002" },
  { ticket_id: "TICKET-632B", customer_id: "cust_017", user_id: "cust_017", issue: "Wrong item received — sent size M, ordered L",        priority: "normal", status: "open",        created_at: new Date(Date.now() - 1 * 3600000).toISOString(), session_id: "sess_003" },
  { ticket_id: "TICKET-7C19", customer_id: "cust_022", user_id: "cust_022", issue: "Cannot apply discount code at checkout",              priority: "normal", status: "in_progress", created_at: new Date(Date.now() - 2 * 3600000).toISOString(), session_id: "sess_004" },
  { ticket_id: "TICKET-DCD7", customer_id: "cust_031", user_id: "cust_031", issue: "Requesting invoice copy for order_038",               priority: "low",    status: "resolved",    created_at: new Date(Date.now() - 3 * 3600000).toISOString(), session_id: "sess_005" },
  { ticket_id: "TICKET-9AB2", customer_id: "cust_015", user_id: "cust_015", issue: "Package shows delivered but tracking stopped updating", priority: "high", status: "open",        created_at: new Date(Date.now() - 4 * 3600000).toISOString(), session_id: "sess_006" },
  { ticket_id: "TICKET-3CE8", customer_id: "cust_028", user_id: "cust_028", issue: "Duplicate charge on last order",                      priority: "urgent", status: "in_progress", created_at: new Date(Date.now() - 5 * 3600000).toISOString(), session_id: "sess_007" },
]

export const MOCK_ORDERS = [
  { order_id: "order_042", customer_id: "cust_004", status: "delivery_soon", total: 248.00, items: [{ name: "Wireless Headphones", quantity: 1, price: 149 }, { name: "USB-C Cable", quantity: 2, price: 29 }], estimated_delivery: "2026-06-05", order_date: "2026-05-28" },
  { order_id: "order_041", customer_id: "cust_017", status: "shipped",       total: 89.50,  items: [{ name: "Phone Case", quantity: 1, price: 89.50 }], estimated_delivery: "2026-06-07", order_date: "2026-06-01" },
  { order_id: "order_040", customer_id: "cust_022", status: "processing",    total: 412.20, items: [{ name: "Smart Watch", quantity: 1, price: 299 }, { name: "Screen Protector", quantity: 2, price: 14 }, { name: "Band", quantity: 3, price: 28 }], estimated_delivery: "2026-06-10", order_date: "2026-06-03" },
  { order_id: "order_039", customer_id: "cust_009", status: "delivered",     total: 129.00, items: [{ name: "Bluetooth Speaker", quantity: 1, price: 99 }, { name: "Aux Cable", quantity: 1, price: 30 }], estimated_delivery: "2026-06-01", order_date: "2026-05-25" },
  { order_id: "order_038", customer_id: "cust_031", status: "delivered",     total: 64.99,  items: [{ name: "Desk Lamp", quantity: 1, price: 64.99 }], estimated_delivery: "2026-05-31", order_date: "2026-05-24" },
  { order_id: "order_037", customer_id: "cust_015", status: "shipped",       total: 199.00, items: [{ name: "Mechanical Keyboard", quantity: 1, price: 199 }], estimated_delivery: "2026-06-08", order_date: "2026-06-02" },
  { order_id: "order_036", customer_id: "cust_028", status: "delivered",     total: 344.50, items: [{ name: "Monitor Stand", quantity: 1, price: 89 }, { name: "LED Strip", quantity: 2, price: 45 }, { name: "Webcam", quantity: 1, price: 165.50 }], estimated_delivery: "2026-06-02", order_date: "2026-05-27" },
  { order_id: "order_035", customer_id: "cust_007", status: "cancelled",     total: 78.00,  items: [{ name: "Gaming Mouse", quantity: 1, price: 78 }], estimated_delivery: null, order_date: "2026-05-30" },
  { order_id: "order_034", customer_id: "cust_011", status: "processing",    total: 55.99,  items: [{ name: "USB Hub", quantity: 1, price: 55.99 }], estimated_delivery: "2026-06-11", order_date: "2026-06-04" },
]

export const MOCK_SESSIONS = [
  { session_id: "session_cust_004_a1b2c3d4", user_id: "cust_004", customer_id: "cust_004", name: "Order issue — cust_004", message_count: 6, is_active: true,  created_at: new Date(Date.now() - 12 * 60000).toISOString(), updated_at: new Date(Date.now() - 1 * 60000).toISOString() },
  { session_id: "session_cust_009_e5f6g7h8", user_id: "cust_009", customer_id: "cust_009", name: "Refund follow-up",       message_count: 4, is_active: true,  created_at: new Date(Date.now() - 45 * 60000).toISOString(), updated_at: new Date(Date.now() - 3 * 60000).toISOString() },
  { session_id: "session_cust_017_i9j0k1l2", user_id: "cust_017", customer_id: "cust_017", name: "Return policy query",    message_count: 3, is_active: true,  created_at: new Date(Date.now() - 18 * 60000).toISOString(), updated_at: new Date(Date.now() - 2 * 60000).toISOString() },
  { session_id: "session_cust_022_m3n4o5p6", user_id: "cust_022", customer_id: "cust_022", name: "Address change request", message_count: 2, is_active: true,  created_at: new Date(Date.now() - 65 * 60000).toISOString(), updated_at: new Date(Date.now() - 5 * 60000).toISOString() },
  { session_id: "session_cust_031_q7r8s9t0", user_id: "cust_031", customer_id: "cust_031", name: "Shipping tracker help",  message_count: 2, is_active: false, created_at: new Date(Date.now() - 3 * 3600000).toISOString(), updated_at: new Date(Date.now() - 2 * 3600000).toISOString() },
]

export const MOCK_ACTIVE_SESSIONS = MOCK_SESSIONS.filter(s => s.is_active)

export const MOCK_MESSAGES: Record<string, any[]> = {
  "session_cust_004_a1b2c3d4": [
    { id: "1", role: "user",      content: "Hi, my order says delivered but I never got it. This is order_042.", timestamp: new Date(Date.now() - 10 * 60000).toISOString(), metadata: {} },
    { id: "2", role: "assistant", content: "I'm sorry to hear that! I can see order_042 ($248.00, 2 items) was marked delivered at 8:12 AM today. Let me pull the carrier scan.", timestamp: new Date(Date.now() - 9 * 60000).toISOString(), metadata: { agent: "order_agent", response_time: 1.8 } },
    { id: "3", role: "assistant", content: "The carrier shows it was left at a side entrance. I can file a missing-package claim and ship a replacement today at no cost — would you like me to do that?", timestamp: new Date(Date.now() - 9 * 60000).toISOString(), metadata: { agent: "order_agent", response_time: 0.4 } },
    { id: "4", role: "user",      content: "Yes please, a replacement would be great.", timestamp: new Date(Date.now() - 7 * 60000).toISOString(), metadata: {} },
    { id: "5", role: "assistant", content: "Done! I've filed the claim and a replacement will ship within 24 hours. You'll get a new tracking number by email. Is there anything else I can help with?", timestamp: new Date(Date.now() - 6 * 60000).toISOString(), metadata: { agent: "order_agent", response_time: 2.1 } },
  ],
  "session_cust_009_e5f6g7h8": [
    { id: "6", role: "user",      content: "It's been 9 days and my $129 refund still hasn't shown up.", timestamp: new Date(Date.now() - 43 * 60000).toISOString(), metadata: {} },
    { id: "7", role: "assistant", content: "I completely understand the frustration. I've escalated this to our payments team with priority — you'll see the refund within 24 hours. I've also added a 15% credit to your account for the trouble.", timestamp: new Date(Date.now() - 42 * 60000).toISOString(), metadata: { agent: "escalation_agent", response_time: 2.3 } },
    { id: "8", role: "user",      content: "Thank you, I really appreciate that.", timestamp: new Date(Date.now() - 40 * 60000).toISOString(), metadata: {} },
  ],
}

export const MOCK_REFINEMENTS = {
  orchestrator: {
    agent_name: "orchestrator",
    pending_refinements: [
      { id: "ref_001", agent_name: "orchestrator", refinement_text: "When a customer mentions both an order issue and a refund in the same message, route to escalation_agent first to assess priority before handing off to order_agent.", status: "pending", created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
      { id: "ref_002", agent_name: "orchestrator", refinement_text: "Add a sentiment check before routing to FAQ agent — if frustration score > 0.7, route directly to escalation.", status: "pending", created_at: new Date(Date.now() - 4 * 3600000).toISOString() },
    ],
  },
  order_agent: {
    agent_name: "order_agent",
    pending_refinements: [
      { id: "ref_003", agent_name: "order_agent", refinement_text: "When providing order status, always include the estimated delivery date and the last carrier scan location for better customer clarity.", status: "pending", created_at: new Date(Date.now() - 1 * 3600000).toISOString() },
      { id: "ref_004", agent_name: "order_agent", refinement_text: "Proactively offer replacement or refund option when order status is 'delivery_soon' and customer has contacted support 2+ times.", status: "pending", created_at: new Date(Date.now() - 5 * 3600000).toISOString() },
    ],
  },
  faq_agent: {
    agent_name: "faq_agent",
    pending_refinements: [
      { id: "ref_005", agent_name: "faq_agent", refinement_text: "Always mention both the 30-day full refund and 60-day store credit options when discussing return policy, not just the shorter window.", status: "pending", created_at: new Date(Date.now() - 3 * 3600000).toISOString() },
    ],
  },
}

export const MOCK_INSIGHTS = {
  insights: [
    { id: "ins_001", agent_name: "order_agent", learning_type: "insight", content: "Customers asking about delivery status are 3x more likely to escalate if no tracking number is provided in first response.", status: "active", created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
    { id: "ins_002", agent_name: "faq_agent",   learning_type: "insight", content: "Return policy questions spike on Mondays — consider proactive KB enrichment for weekend-purchase returns.", status: "active", created_at: new Date(Date.now() - 8 * 3600000).toISOString() },
  ],
  refinements: [
    { id: "ref_001", agent_name: "orchestrator", learning_type: "refinement", content: "Route multi-issue messages to escalation first.", status: "pending", created_at: new Date().toISOString() },
    { id: "ref_003", agent_name: "order_agent",  learning_type: "refinement", content: "Include carrier scan location in status updates.", status: "pending", created_at: new Date().toISOString() },
  ],
  kb_updates: [
    { id: "kb_001", learning_type: "kb_update", content: { customer_comment: "What happens if my package is lost in transit?", reason: "missing_info" }, status: "pending", created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
    { id: "kb_002", learning_type: "kb_update", content: { customer_comment: "Can I change my delivery address after ordering?", reason: "missing_info" }, status: "pending", created_at: new Date(Date.now() - 4 * 3600000).toISOString() },
    { id: "kb_003", learning_type: "kb_update", content: { customer_comment: "How do I track an international order?", reason: "missing_info" }, status: "pending", created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
  ],
  total_insights:    14,
  total_refinements: 6,
  total_kb_updates:  3,
}

export const MOCK_KB_UPDATES = MOCK_INSIGHTS.kb_updates.map(u => ({
  update_id: u.id,
  content: u.content,
  status: u.status,
  created_at: u.created_at,
  agent_name: "faq_agent",
}))
