/* Mock data — full demo dataset shown when Supabase is offline. */

export const MOCK_ANALYTICS = {
  total_messages:    24631,
  active_sessions:   53,
  closed_sessions:   389,
  interactions:      12315,
  avg_satisfaction:  4.6,
  tickets_created:   83,
  open_tickets:      31,
  resolved_tickets:  47,
  resolution_rate:   87,
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
  { ticket_id: "TICKET-FD45", customer_id: "cust_004", user_id: "cust_004", issue: "Order order_042 marked delivered but not received", priority: "urgent", status: "open",        created_at: new Date(Date.now() - 8   * 60000).toISOString() },
  { ticket_id: "TICKET-1A21", customer_id: "cust_009", user_id: "cust_009", issue: "Refund of $129.00 still pending after 9 days",       priority: "high",   status: "in_progress", created_at: new Date(Date.now() - 41  * 60000).toISOString() },
  { ticket_id: "TICKET-632B", customer_id: "cust_017", user_id: "cust_017", issue: "Wrong item received — sent size M, ordered L",        priority: "normal", status: "open",        created_at: new Date(Date.now() - 62  * 60000).toISOString() },
  { ticket_id: "TICKET-7C19", customer_id: "cust_022", user_id: "cust_022", issue: "Cannot apply discount code at checkout",              priority: "normal", status: "in_progress", created_at: new Date(Date.now() - 120 * 60000).toISOString() },
  { ticket_id: "TICKET-DCD7", customer_id: "cust_031", user_id: "cust_031", issue: "Requesting invoice copy for order_038",               priority: "low",    status: "resolved",    created_at: new Date(Date.now() - 180 * 60000).toISOString() },
  { ticket_id: "TICKET-9AB2", customer_id: "cust_015", user_id: "cust_015", issue: "Package shows delivered but tracking stopped updating", priority: "high",  status: "open",        created_at: new Date(Date.now() - 240 * 60000).toISOString() },
  { ticket_id: "TICKET-3CE8", customer_id: "cust_028", user_id: "cust_028", issue: "Duplicate charge on last order",                       priority: "urgent", status: "in_progress", created_at: new Date(Date.now() - 300 * 60000).toISOString() },
  { ticket_id: "TICKET-B77F", customer_id: "cust_003", user_id: "cust_003", issue: "Item arrived damaged — need replacement",              priority: "high",   status: "open",        created_at: new Date(Date.now() - 360 * 60000).toISOString() },
  { ticket_id: "TICKET-C44A", customer_id: "cust_011", user_id: "cust_011", issue: "Subscription not cancelled after request",             priority: "normal", status: "open",        created_at: new Date(Date.now() - 420 * 60000).toISOString() },
  { ticket_id: "TICKET-E12D", customer_id: "cust_019", user_id: "cust_019", issue: "Wrong address on confirmed order — needs update",      priority: "urgent", status: "open",        created_at: new Date(Date.now() - 480 * 60000).toISOString() },
  { ticket_id: "TICKET-F93B", customer_id: "cust_007", user_id: "cust_007", issue: "Gift wrapping not applied despite paid option",        priority: "low",    status: "resolved",    created_at: new Date(Date.now() - 600 * 60000).toISOString() },
  { ticket_id: "TICKET-A08C", customer_id: "cust_033", user_id: "cust_033", issue: "Promo code applied but discount not showing",          priority: "normal", status: "resolved",    created_at: new Date(Date.now() - 720 * 60000).toISOString() },
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
  { order_id: "order_033", customer_id: "cust_003", status: "shipped",       total: 189.00, items: [{ name: "Noise-cancelling Earbuds", quantity: 1, price: 189 }], estimated_delivery: "2026-06-09", order_date: "2026-06-02" },
  { order_id: "order_032", customer_id: "cust_019", status: "processing",    total: 320.00, items: [{ name: "4K Webcam", quantity: 1, price: 220 }, { name: "Ring Light", quantity: 1, price: 100 }], estimated_delivery: "2026-06-12", order_date: "2026-06-04" },
  { order_id: "order_031", customer_id: "cust_033", status: "delivered",     total: 47.50,  items: [{ name: "Phone Stand", quantity: 1, price: 47.50 }], estimated_delivery: "2026-05-30", order_date: "2026-05-23" },
  { order_id: "order_030", customer_id: "cust_006", status: "delivered",     total: 599.00, items: [{ name: "Ergonomic Chair Cushion", quantity: 1, price: 299 }, { name: "Lumbar Support", quantity: 1, price: 300 }], estimated_delivery: "2026-05-29", order_date: "2026-05-22" },
  { order_id: "order_029", customer_id: "cust_014", status: "shipped",       total: 144.00, items: [{ name: "Portable Charger", quantity: 2, price: 72 }], estimated_delivery: "2026-06-08", order_date: "2026-06-01" },
  { order_id: "order_028", customer_id: "cust_025", status: "delivery_soon", total: 93.00,  items: [{ name: "Cable Management Kit", quantity: 3, price: 31 }], estimated_delivery: "2026-06-05", order_date: "2026-05-29" },
]

export const MOCK_SESSIONS = [
  { session_id: "session_cust_004_a1b2c3d4", user_id: "cust_004", customer_id: "cust_004", name: "Order not received — cust_004",     message_count: 6,  is_active: true,  created_at: new Date(Date.now() - 12  * 60000).toISOString(), updated_at: new Date(Date.now() - 1  * 60000).toISOString() },
  { session_id: "session_cust_009_e5f6g7h8", user_id: "cust_009", customer_id: "cust_009", name: "Refund follow-up",                  message_count: 4,  is_active: true,  created_at: new Date(Date.now() - 45  * 60000).toISOString(), updated_at: new Date(Date.now() - 3  * 60000).toISOString() },
  { session_id: "session_cust_017_i9j0k1l2", user_id: "cust_017", customer_id: "cust_017", name: "Return policy query",               message_count: 3,  is_active: true,  created_at: new Date(Date.now() - 18  * 60000).toISOString(), updated_at: new Date(Date.now() - 2  * 60000).toISOString() },
  { session_id: "session_cust_022_m3n4o5p6", user_id: "cust_022", customer_id: "cust_022", name: "Delivery address change",           message_count: 2,  is_active: true,  created_at: new Date(Date.now() - 65  * 60000).toISOString(), updated_at: new Date(Date.now() - 5  * 60000).toISOString() },
  { session_id: "session_cust_031_q7r8s9t0", user_id: "cust_031", customer_id: "cust_031", name: "Invoice request",                   message_count: 2,  is_active: false, created_at: new Date(Date.now() - 3   * 3600000).toISOString(), updated_at: new Date(Date.now() - 2 * 3600000).toISOString() },
  { session_id: "session_cust_015_u1v2w3x4", user_id: "cust_015", customer_id: "cust_015", name: "Tracking issue — cust_015",         message_count: 5,  is_active: true,  created_at: new Date(Date.now() - 30  * 60000).toISOString(), updated_at: new Date(Date.now() - 4  * 60000).toISOString() },
  { session_id: "session_cust_028_y5z6a7b8", user_id: "cust_028", customer_id: "cust_028", name: "Duplicate charge dispute",          message_count: 7,  is_active: true,  created_at: new Date(Date.now() - 55  * 60000).toISOString(), updated_at: new Date(Date.now() - 6  * 60000).toISOString() },
  { session_id: "session_cust_003_c9d0e1f2", user_id: "cust_003", customer_id: "cust_003", name: "Damaged item — replacement needed", message_count: 4,  is_active: true,  created_at: new Date(Date.now() - 75  * 60000).toISOString(), updated_at: new Date(Date.now() - 8  * 60000).toISOString() },
  { session_id: "session_cust_011_g3h4i5j6", user_id: "cust_011", customer_id: "cust_011", name: "Subscription cancellation",         message_count: 3,  is_active: true,  created_at: new Date(Date.now() - 90  * 60000).toISOString(), updated_at: new Date(Date.now() - 10 * 60000).toISOString() },
  { session_id: "session_cust_019_k7l8m9n0", user_id: "cust_019", customer_id: "cust_019", name: "Wrong shipping address",            message_count: 8,  is_active: true,  created_at: new Date(Date.now() - 20  * 60000).toISOString(), updated_at: new Date(Date.now() - 2  * 60000).toISOString() },
  { session_id: "session_cust_006_o1p2q3r4", user_id: "cust_006", customer_id: "cust_006", name: "General shipping question",         message_count: 2,  is_active: false, created_at: new Date(Date.now() - 4   * 3600000).toISOString(), updated_at: new Date(Date.now() - 3 * 3600000).toISOString() },
  { session_id: "session_cust_014_s5t6u7v8", user_id: "cust_014", customer_id: "cust_014", name: "Order status check",                message_count: 1,  is_active: true,  created_at: new Date(Date.now() - 5   * 60000).toISOString(), updated_at: new Date(Date.now() - 1  * 60000).toISOString() },
  { session_id: "session_cust_025_w9x0y1z2", user_id: "cust_025", customer_id: "cust_025", name: "Promo code not working",            message_count: 3,  is_active: true,  created_at: new Date(Date.now() - 35  * 60000).toISOString(), updated_at: new Date(Date.now() - 7  * 60000).toISOString() },
  { session_id: "session_cust_033_a3b4c5d6", user_id: "cust_033", customer_id: "cust_033", name: "Product quality feedback",          message_count: 2,  is_active: false, created_at: new Date(Date.now() - 5   * 3600000).toISOString(), updated_at: new Date(Date.now() - 4 * 3600000).toISOString() },
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
  "session_cust_019_k7l8m9n0": [
    { id: "9",  role: "user",      content: "I need to change my shipping address! The order hasn't shipped yet — it's order_032.", timestamp: new Date(Date.now() - 18 * 60000).toISOString(), metadata: {} },
    { id: "10", role: "assistant", content: "I can see order_032 is still in processing. What's the new shipping address?", timestamp: new Date(Date.now() - 17 * 60000).toISOString(), metadata: { agent: "order_agent", response_time: 1.2 } },
    { id: "11", role: "user",      content: "45 Oak Street, Apt 3B, Montreal, QC H2X 1Y5", timestamp: new Date(Date.now() - 15 * 60000).toISOString(), metadata: {} },
    { id: "12", role: "assistant", content: "Done! I've updated the shipping address to 45 Oak Street, Apt 3B, Montreal. The order will ship to that address. You'll get a confirmation email shortly.", timestamp: new Date(Date.now() - 14 * 60000).toISOString(), metadata: { agent: "order_agent", response_time: 1.9 } },
    { id: "13", role: "user",      content: "Perfect, thank you so much!", timestamp: new Date(Date.now() - 12 * 60000).toISOString(), metadata: {} },
  ],
  "session_cust_028_y5z6a7b8": [
    { id: "14", role: "user",      content: "I was charged twice for my last order. This is unacceptable.", timestamp: new Date(Date.now() - 52 * 60000).toISOString(), metadata: {} },
    { id: "15", role: "assistant", content: "I'm so sorry about that. I can see a duplicate charge of $344.50 on order_036. I'll initiate the refund for the duplicate charge immediately.", timestamp: new Date(Date.now() - 50 * 60000).toISOString(), metadata: { agent: "escalation_agent", response_time: 2.8 } },
    { id: "16", role: "user",      content: "How long will the refund take?", timestamp: new Date(Date.now() - 48 * 60000).toISOString(), metadata: {} },
    { id: "17", role: "assistant", content: "The refund will appear on your card within 3–5 business days. I've also flagged your account for a priority review so this doesn't happen again.", timestamp: new Date(Date.now() - 47 * 60000).toISOString(), metadata: { agent: "escalation_agent", response_time: 1.6 } },
  ],
}

export const MOCK_REFINEMENTS = {
  orchestrator: {
    agent_name: "orchestrator",
    pending_refinements: [
      { id: "ref_001", agent_name: "orchestrator", refinement_text: "When a customer mentions both an order issue and a refund, route to escalation_agent first to assess priority before handing off to order_agent.", status: "pending", created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
      { id: "ref_002", agent_name: "orchestrator", refinement_text: "Add sentiment check before routing to FAQ agent — if frustration score > 0.7, route directly to escalation.", status: "pending", created_at: new Date(Date.now() - 4 * 3600000).toISOString() },
    ],
  },
  order_agent: {
    agent_name: "order_agent",
    pending_refinements: [
      { id: "ref_003", agent_name: "order_agent", refinement_text: "Always include estimated delivery date and last carrier scan location when providing order status.", status: "pending", created_at: new Date(Date.now() - 1 * 3600000).toISOString() },
      { id: "ref_004", agent_name: "order_agent", refinement_text: "Proactively offer replacement or refund when order is 'delivery_soon' and customer has contacted support 2+ times.", status: "pending", created_at: new Date(Date.now() - 5 * 3600000).toISOString() },
    ],
  },
  faq_agent: {
    agent_name: "faq_agent",
    pending_refinements: [
      { id: "ref_005", agent_name: "faq_agent", refinement_text: "Always mention both 30-day full refund and 60-day store credit options when discussing return policy.", status: "pending", created_at: new Date(Date.now() - 3 * 3600000).toISOString() },
      { id: "ref_006", agent_name: "faq_agent", refinement_text: "When asked about shipping times, include both standard and express options with estimated dates.", status: "pending", created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
    ],
  },
}

export const MOCK_INSIGHTS = {
  insights: [
    { id: "ins_001", agent_name: "order_agent", content: "Customers asking about delivery status are 3x more likely to escalate if no tracking number is provided in first response.", status: "active", created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
    { id: "ins_002", agent_name: "faq_agent",   content: "Return policy questions spike on Mondays — proactive KB enrichment for weekend-purchase returns recommended.", status: "active", created_at: new Date(Date.now() - 8 * 3600000).toISOString() },
    { id: "ins_003", agent_name: "escalation_agent", content: "Refund-related escalations resolve 40% faster when agent proactively mentions credit compensation.", status: "active", created_at: new Date(Date.now() - 10 * 3600000).toISOString() },
  ],
  refinements: [
    { id: "ref_001", agent_name: "orchestrator", content: "Route multi-issue messages to escalation first.", status: "pending", created_at: new Date().toISOString() },
    { id: "ref_003", agent_name: "order_agent",  content: "Include carrier scan location in status updates.", status: "pending", created_at: new Date().toISOString() },
    { id: "ref_005", agent_name: "faq_agent",    content: "Mention both refund windows in return policy answers.", status: "pending", created_at: new Date().toISOString() },
  ],
  kb_updates: [
    { id: "kb_001", content: { customer_comment: "What happens if my package is lost in transit?", reason: "missing_info" }, status: "pending", created_at: new Date(Date.now() - 2 * 3600000).toISOString() },
    { id: "kb_002", content: { customer_comment: "Can I change my delivery address after ordering?", reason: "missing_info" }, status: "pending", created_at: new Date(Date.now() - 4 * 3600000).toISOString() },
    { id: "kb_003", content: { customer_comment: "How do I track an international order?", reason: "missing_info" }, status: "pending", created_at: new Date(Date.now() - 6 * 3600000).toISOString() },
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
