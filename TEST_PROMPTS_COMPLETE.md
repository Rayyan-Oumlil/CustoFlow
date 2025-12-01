# Complete Test Prompts for CustoFlow Agent

## 🎯 Test Checklist - All Features

### 1. FAQ Agent Tests
```
1. "What's your refund policy?"
2. "What is your shipping policy?"
3. "How long does delivery take?"
4. "What is your return policy?"
5. "Do you offer international shipping?"
6. "What payment methods do you accept?"
7. "Can I return an item after 30 days?"
8. "What's your warranty policy?"
```

### 2. Order Agent Tests
```
1. "Where's my order?"
2. "What's the status of order 10262006?"
3. "Can I cancel order 10262006?"
4. "I need help with my order"
5. "Check my order status"
6. "Track my order 10262006"
7. "When will order 10262006 arrive?"
8. "I want to cancel my order"
```

### 3. Multi-Part Questions (Orchestrator)
```
1. "What's your refund policy? Also, can I cancel order 10262006?"
2. "What's your shipping policy and where's my order?"
3. "Can I return an item? Also, check order 10262006 status"
4. "What's your refund policy? Also, I need help with my order"
```

### 4. Sentiment Analysis Tests
```
1. "I'm really frustrated right now. My order 10262006 was supposed to arrive on November 27th and I haven't received any updates. This is really unacceptable!"
2. "I'm very happy with my purchase, thank you!"
3. "I'm disappointed with the service"
4. "I'm angry about this delay"
5. "I feel sad about my order"
```

### 5. Ticket Creation & Escalation Tests
```
1. "I want to create a ticket"
2. "I need to talk to a human agent"
3. "Can you escalate this issue?"
4. "I want to speak to someone"
5. "Create a ticket for me"
```

### 6. Questions with Active Ticket (Simple Questions)
```
(After a ticket is created, test these simple questions)
1. "What's your refund policy?"
2. "Where's my order?"
3. "Can I cancel order 10262006?"
4. "What's your shipping policy?"
```

### 7. Auto-Learning Feedback Tests
```
(After agent responds, use feedback buttons)

Positive Feedback:
- Click "Thumbs Up" after a good response
- Check Analytics page for insights

Negative Feedback:
- Click "Thumbs Down" after a bad response
- Check Analytics page for refinements
- Check Agent Learning Dashboard for pending refinements
```

### 8. Order-Specific Tests (Order 10262006)
```
1. "Where's order 10262006?"
2. "What's the status of order 10262006?"
3. "Can I cancel order 10262006?"
4. "When will order 10262006 arrive?"
5. "I need help with order 10262006"
```

### 9. Complex Scenarios
```
1. "I'm frustrated. My order 10262006 was supposed to arrive on November 27th. What's your refund policy?"
2. "I need help with my order and I want to create a ticket"
3. "What's your refund policy? Also, I'm really frustrated about order 10262006"
```

### 10. Session Management Tests
```
1. Create new conversation
2. Rename conversation
3. Delete conversation (should close associated tickets)
4. Switch between conversations
```

## 📊 What to Verify

### After Each Test:
- ✅ Agent responds (doesn't stop)
- ✅ Correct agent is used (check agent badge)
- ✅ Response is helpful and complete
- ✅ Multi-part questions are fully answered
- ✅ Simple questions work even with active ticket
- ✅ No duplicate tickets created
- ✅ Feedback creates auto-learning entries
- ✅ Analytics page shows insights

### Key Features to Test:
1. ✅ FAQ Agent - answers policy questions
2. ✅ Order Agent - handles order inquiries
3. ✅ Sentiment Agent - detects emotions
4. ✅ Escalation Agent - creates tickets
5. ✅ Multi-part questions - all parts answered
6. ✅ Active ticket handling - simple questions allowed
7. ✅ Auto-learning - feedback generates insights
8. ✅ Session management - create/rename/delete
9. ✅ Ticket closure - when session deleted

## 🎬 Recommended Test Flow

### Step 1: Basic FAQ
```
"What's your refund policy?"
→ Should use FAQ agent
→ Should provide refund policy information
```

### Step 2: Order Inquiry
```
"Where's my order?"
→ Should use Order agent
→ Should show order 10262006 details
```

### Step 3: Multi-Part Question
```
"What's your refund policy? Also, can I cancel order 10262006?"
→ Should use FAQ agent + Order agent
→ Should answer both parts
```

### Step 4: Sentiment + Escalation
```
"I'm really frustrated right now. My order 10262006 was supposed to arrive on November 27th and I haven't received any updates. This is really unacceptable!"
→ Should use Sentiment agent
→ Should create ticket (TICKET-XXX)
→ Should provide empathetic response
```

### Step 5: Simple Question with Active Ticket
```
"What's your refund policy?"
→ Should work even with active ticket
→ Should use FAQ agent
→ Should NOT block the response
```

### Step 6: Feedback & Auto-Learning
```
1. Click "Thumbs Down" on a response
2. Go to Analytics page
3. Check "Feedback Insights" section
4. Go to Agent Learning Dashboard
5. Verify refinements are created
```

### Step 7: Session Deletion
```
1. Delete a session
2. Check that associated tickets are closed (not deleted)
3. Verify messages are deleted
```

## 🔍 Expected Behaviors

### ✅ Should Work:
- FAQ questions answered by FAQ agent
- Order questions answered by Order agent
- Multi-part questions answered completely
- Simple questions work with active ticket
- Feedback creates auto-learning entries
- Tickets closed (not deleted) when session deleted
- No duplicate tickets created

### ❌ Should NOT Happen:
- Agent stops responding mid-conversation
- Multi-part questions partially answered
- Simple questions blocked when ticket active
- Duplicate tickets created
- Tickets deleted when session deleted

## 📝 Test Data

### Order 10262006 Details:
- **Order ID**: 10262006
- **Customer ID**: cust_004
- **Status**: delivery_soon
- **Items**: 2x Ryzen 5 9600x
- **Total**: $300.00
- **Tracking**: TRACK0061026
- **Estimated Delivery**: 2025-11-27

### Test Customer:
- **User ID**: user_1764360688275 (or any)
- **Customer ID**: cust_004

## 🚀 Quick Test Commands

Copy-paste these in order:

```
1. "What's your refund policy?"
2. "Where's my order?"
3. "What's your refund policy? Also, can I cancel order 10262006?"
4. "I'm really frustrated right now. My order 10262006 was supposed to arrive on November 27th and I haven't received any updates. This is really unacceptable!"
5. "What's your refund policy?" (with active ticket)
6. [Click Thumbs Down]
7. [Check Analytics page]
8. [Check Agent Learning Dashboard]
```

