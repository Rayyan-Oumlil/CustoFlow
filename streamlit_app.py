"""
CustoFlow - Streamlit Dashboard
Visual web interface to interact with the multi-agent customer support system.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Page configuration
st.set_page_config(
    page_title="CustoFlow Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS styles
st.markdown("""
<style>
    /* Fix chat input at bottom of page (main area only, not sidebar) */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 20% !important;
        right: 0 !important;
        z-index: 999 !important;
        background-color: var(--background-color) !important;
        padding: 1rem !important;
        border-top: 1px solid var(--border-color) !important;
    }
    
    /* Add padding to chat container to prevent overlap */
    .stChatMessageContainer {
        padding-bottom: 100px !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .faq-agent { background-color: #2196F3; color: white; }
    .order-agent { background-color: #FF9800; color: white; }
    .sentiment-agent { background-color: #9C27B0; color: white; }
    .escalation-agent { background-color: #F44336; color: white; }
    .orchestrator { background-color: #4CAF50; color: white; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Session initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{int(time.time())}"


def check_api_health() -> bool:
    """Check if the API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def send_chat_message(message: str) -> Dict:
    """Send a message to the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": message,
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id
            },
            timeout=35
        )
        if response.status_code == 200:
            data = response.json()
            if not st.session_state.session_id:
                st.session_state.session_id = data.get("session_id")
            return data
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=5)  # Cache for 5 seconds - metrics don't need real-time updates
def get_metrics() -> Dict:
    """Get metrics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


@st.cache_data(ttl=5)  # Cache for 5 seconds - analytics don't need real-time updates
def get_analytics() -> Dict:
    """Get analytics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


@st.cache_data(ttl=10)  # Cache for 10 seconds - orders don't change frequently
def get_orders() -> Dict:
    """Get all orders from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/orders", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


@st.cache_data(ttl=10)  # Cache for 10 seconds - tickets don't change frequently
def get_tickets() -> Dict:
    """Get all tickets from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/tickets", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def create_order(order_data: Dict) -> Dict:
    """Create a new order via the API (Admin function)."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/orders",
            json=order_data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json() if response.content else {}
            return {"error": error_data.get("detail", f"API Error: {response.status_code}")}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=5)  # Cache for 5 seconds - sessions don't change that frequently
def get_user_sessions(user_id: str) -> Dict:
    """Get all sessions for a user."""
    try:
        response = requests.get(f"{API_BASE_URL}/sessions/{user_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


@st.cache_data(ttl=10)  # Cache for 10 seconds - history doesn't change frequently
def get_conversation_history(user_id: str, session_id: Optional[str] = None) -> List[Dict]:
    """Get conversation history for a user/session from the API."""
    try:
        url = f"{API_BASE_URL}/history/{user_id}"
        params = {}
        if session_id:
            params["session_id"] = session_id
        params["limit"] = 100  # Get up to 100 messages
        
        response = requests.get(url, params=params, timeout=2)
        if response.status_code == 200:
            data = response.json()
            history = data.get("history", [])
            # Convert API format to Streamlit format
            messages = []
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Extract metadata if available
                metadata = msg.get("metadata", {})
                message_dict = {
                    "role": role,
                    "content": content
                }
                # Add metadata if present
                if "agent" in metadata:
                    message_dict["agent"] = metadata["agent"]
                if "response_time" in metadata:
                    message_dict["response_time"] = metadata["response_time"]
                if "confidence" in metadata:
                    message_dict["confidence"] = metadata["confidence"]
                messages.append(message_dict)
            return messages
        return []
    except:
        return []


def create_new_session(user_id: str, name: Optional[str] = None) -> Dict:
    """Create a new session."""
    try:
        payload = {"user_id": user_id}
        if name:
            payload["name"] = name
        response = requests.post(
            f"{API_BASE_URL}/sessions/create",
            json=payload,
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def rename_session_api(session_id: str, new_name: str) -> Dict:
    """Rename a session."""
    try:
        response = requests.put(
            f"{API_BASE_URL}/sessions/{session_id}/rename",
            json={"new_name": new_name},
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def detect_agent_from_response(response_text: str, agent_from_api: Optional[str] = None) -> str:
    """Detect which agent responded based on content or API."""
    # If API returns agent, use it
    if agent_from_api:
        return agent_from_api
    
    # Otherwise, detect from content
    response_lower = response_text.lower()
    if any(word in response_lower for word in ["order", "tracking", "shipped", "delivery"]):
        return "Order Agent"
    elif any(word in response_lower for word in ["refund", "return", "policy", "shipping"]):
        return "FAQ Agent"
    elif any(word in response_lower for word in ["frustrated", "sentiment", "emotion", "urgent"]):
        return "Sentiment Agent"
    elif any(word in response_lower for word in ["ticket", "escalate", "support team"]):
        return "Escalation Agent"
    else:
        return "Orchestrator"


def get_agent_color(agent: str) -> str:
    """Get color for an agent."""
    colors = {
        "FAQ Agent": "#2196F3",
        "Order Agent": "#FF9800",
        "Sentiment Agent": "#9C27B0",
        "Escalation Agent": "#F44336",
        "Orchestrator": "#4CAF50"
    }
    return colors.get(agent, "#757575")


# Check API health (cached to avoid checking on every rerun)
@st.cache_data(ttl=30)  # Cache health check for 30 seconds
def cached_api_health_check() -> bool:
    return check_api_health()

# Header
st.markdown('<div class="main-header">💬 CustoFlow - Customer Support</div>', unsafe_allow_html=True)

# Check API health
api_healthy = cached_api_health_check()
if not api_healthy:
    st.error("⚠️ API is not available. Make sure the FastAPI server is running (python -m api.server)")
    st.stop()

# Load existing sessions on startup (after functions are defined) - Only once
if "sessions_loaded" not in st.session_state:
    st.session_state.sessions_loaded = True
    # Try to restore last session if available
    sessions_data = get_user_sessions(st.session_state.user_id)
    sessions = sessions_data.get("sessions", [])
    if sessions and not st.session_state.session_id:
        # Use the most recent session
        most_recent = sessions[0]  # Already sorted by updated_at desc
        st.session_state.session_id = most_recent.get("session_id")
    
    # Load messages for the restored session - only if we have a session and no messages
    if st.session_state.session_id and not st.session_state.messages:
        history = get_conversation_history(st.session_state.user_id, st.session_state.session_id)
        if history:
            st.session_state.messages = history
            # Mark as loaded to prevent reloading
            st.session_state.history_loaded = True

# Sidebar
with st.sidebar:
    # Logo en haut à gauche
    try:
        st.image("assets/custoflow_logo.png", use_container_width=True)
    except:
        pass  # Si le logo n'existe pas, continuer sans erreur
    
    st.markdown("---")
    
    # User ID is auto-generated and hidden from user (professional mode)
    # Only show session management for professional use
    
    st.header("💬 Conversations")
    
    # Get user sessions (cached, only refreshes every 2 seconds)
    sessions_data = get_user_sessions(st.session_state.user_id)
    sessions = sessions_data.get("sessions", [])
    
    # Initialize rename state
    if "renaming_session_id" not in st.session_state:
        st.session_state.renaming_session_id = None
    if "rename_input_key" not in st.session_state:
        st.session_state.rename_input_key = 0
    
    # List existing sessions
    if sessions:
        # Session selector - simplified for professional use
        session_options = {s.get('name', f"Conversation {i+1}"): s.get('session_id') for i, s in enumerate(sessions)}
        selected_session_display = st.selectbox(
            "Select Conversation",
            options=list(session_options.keys()),
            index=0 if st.session_state.session_id not in session_options.values() else list(session_options.values()).index(st.session_state.session_id) if st.session_state.session_id in session_options.values() else 0,
            key="session_selector"
        )
        
        selected_session_id = session_options.get(selected_session_display)
        
        # Update active session
        if selected_session_id and selected_session_id != st.session_state.session_id:
            st.session_state.session_id = selected_session_id
            st.session_state.renaming_session_id = None  # Cancel renaming when switching
            # Clear history cache for this session to force reload
            get_conversation_history.clear()
            # Load messages for the selected session
            history = get_conversation_history(st.session_state.user_id, selected_session_id)
            st.session_state.messages = history if history else []
            st.session_state.history_loaded = True
            st.rerun()
        
        # Rename functionality - show rename input if this session is being renamed
        if st.session_state.renaming_session_id == selected_session_id:
            new_name = st.text_input(
                "Rename conversation:",
                value=selected_session_display,
                key=f"rename_input_{st.session_state.rename_input_key}",
                label_visibility="visible"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Save", key="save_rename", use_container_width=True):
                    if new_name and new_name.strip():
                        result = rename_session_api(selected_session_id, new_name.strip())
                        if result.get("status") == "success":
                            st.session_state.renaming_session_id = None
                            st.session_state.rename_input_key += 1
                            st.rerun()
                        else:
                            st.error("Failed to rename conversation")
                    else:
                        st.warning("Name cannot be empty")
            with col2:
                if st.button("❌ Cancel", key="cancel_rename", use_container_width=True):
                    st.session_state.renaming_session_id = None
                    st.session_state.rename_input_key += 1
                    st.rerun()
        else:
            # Show rename button for selected session
            if st.button("✏️ Rename", key="rename_button", use_container_width=True):
                st.session_state.renaming_session_id = selected_session_id
                st.session_state.rename_input_key += 1
                st.rerun()
        
        # Create new session button
        if st.button("➕ New Conversation", use_container_width=True):
            result = create_new_session(st.session_state.user_id, None)
            if result.get("status") == "success":
                st.session_state.session_id = result.get("session_id")
                st.session_state.messages = []  # New session, no messages yet
                st.session_state.renaming_session_id = None
                # Clear cache to refresh sessions list
                get_user_sessions.clear()
                st.rerun()
    else:
        # Create first session automatically
        if st.button("➕ Start Conversation", use_container_width=True):
            result = create_new_session(st.session_state.user_id, None)
            if result.get("status") == "success":
                st.session_state.session_id = result.get("session_id")
                st.session_state.messages = []
                st.rerun()
    
    st.markdown("---")
    
    # Professional actions
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()
    
    if st.button("💾 Export Conversation"):
        if st.session_state.messages:
            export_data = {
                "session_id": st.session_state.session_id,
                "messages": st.session_state.messages,
                "exported_at": datetime.now().isoformat()
            }
            st.download_button(
                label="📥 Download",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"conversation_{int(time.time())}.json",
                mime="application/json"
            )
        else:
            st.info("No conversation to export")

# Main Content
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📦 Orders & Tickets", "📊 Statistics"])

# Tab 1: Chat Interface
with tab1:
    st.header("💬 Chat")
    st.markdown("Ask your questions and get instant answers.")
    
    # Display message history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            agent = message.get("agent", "Orchestrator")
            
            if role == "user":
                with st.chat_message("user"):
                    st.write(content)
            else:
                with st.chat_message("assistant"):
                    # Agent badge with confidence
                    agent_color = get_agent_color(agent)
                    confidence = message.get("confidence", "high")
                    confidence_emoji = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🔴"
                    
                    st.markdown(
                        f'<span style="background-color: {agent_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; margin-right: 0.5rem;">{agent}</span>'
                        f'<span style="font-size: 0.75rem; color: #757575;">{confidence_emoji} {confidence}</span>',
                        unsafe_allow_html=True
                    )
                    st.write(content)
                    
                    # Metadata
                    if "response_time" in message:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"⏱️ Time: {message['response_time']:.2f}s")
                        with col2:
                            if "confidence" in message:
                                st.caption(f"📊 Confidence: {message['confidence']}")
        
        # Add spacing before input
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Input for new message - placed after chat messages
    if prompt := st.chat_input("Type your message..."):
        # Auto-create session if none exists
        if not st.session_state.session_id:
            result = create_new_session(st.session_state.user_id, None)
            if result.get("status") == "success":
                st.session_state.session_id = result.get("session_id")
                # Reload sessions to update sidebar
                st.rerun()
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response
        with st.spinner("💬 CustoFlow is thinking..."):
            start_time = time.time()
            response_data = send_chat_message(prompt)
            response_time = time.time() - start_time
            
            if "error" in response_data:
                # Add error message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {response_data['error']}",
                    "agent": "System",
                    "response_time": response_time,
                    "confidence": "low"
                })
            else:
                response_text = response_data.get("response", "")
                agent_from_api = response_data.get("agent_used")
                response_time_api = response_data.get("response_time", response_time)
                confidence = response_data.get("confidence", "high")
                
                agent = detect_agent_from_response(response_text, agent_from_api)
                
                # Add response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "agent": agent,
                    "response_time": response_time_api,
                    "confidence": confidence
                })
        
        # Rerun to display messages from history
        st.rerun()

# Tab 2: Orders & Tickets Dashboard
with tab2:
    st.header("📦 Orders & Tickets")
    st.markdown("View all orders and support tickets.")
    
    # Orders Section
    st.subheader("📋 Orders")
    
    # Load orders data (cached, only loads when tab is viewed)
    orders_data = get_orders()
    
    # Admin: Add New Order
    with st.expander("➕ Add New Order (Admin)", expanded=False):
        st.markdown("**Create a new order manually**")
        
        col1, col2 = st.columns(2)
        with col1:
            new_order_id = st.text_input("Order ID *", key="new_order_id")
            new_customer_id = st.text_input("Customer ID *", key="new_customer_id")
            new_status = st.selectbox(
                "Status *",
                options=["processing", "shipped", "delivered", "cancelled"],
                key="new_status"
            )
            new_order_date = st.date_input("Order Date *", value=datetime.now().date(), key="new_order_date")
        
        with col2:
            new_total = st.number_input("Total Amount *", min_value=0.0, step=0.01, key="new_total")
            new_shipped_date = st.date_input("Shipped Date (optional)", value=None, key="new_shipped_date")
            new_tracking = st.text_input("Tracking Number (optional)", key="new_tracking")
            new_estimated_delivery = st.date_input("Estimated Delivery (optional)", value=None, key="new_estimated_delivery")
        
        # Items section
        st.markdown("**Items**")
        if "new_order_items" not in st.session_state:
            st.session_state.new_order_items = [{"name": "", "quantity": 1, "price": 0.0}]
        
        for i, item in enumerate(st.session_state.new_order_items):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                item_name = st.text_input(f"Item {i+1} Name", value=item["name"], key=f"item_name_{i}")
            with col2:
                item_quantity = st.number_input(f"Quantity", min_value=1, value=item["quantity"], key=f"item_quantity_{i}")
            with col3:
                item_price = st.number_input(f"Price", min_value=0.0, step=0.01, value=item["price"], key=f"item_price_{i}")
            
            st.session_state.new_order_items[i] = {
                "name": item_name,
                "quantity": item_quantity,
                "price": item_price
            }
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Another Item"):
                st.session_state.new_order_items.append({"name": "", "quantity": 1, "price": 0.0})
                st.rerun()
        with col2:
            if len(st.session_state.new_order_items) > 1:
                if st.button("➖ Remove Last Item"):
                    st.session_state.new_order_items.pop()
                    st.rerun()
        
        # Create order button
        if st.button("✅ Create Order", type="primary"):
            # Validate required fields
            if not new_order_id or not new_customer_id or not new_total or not new_order_date:
                st.error("Please fill in all required fields (marked with *)")
            elif not any(item["name"] for item in st.session_state.new_order_items):
                st.error("Please add at least one item with a name")
            else:
                # Build order data
                order_data = {
                    "order_id": new_order_id,
                    "customer_id": new_customer_id,
                    "status": new_status,
                    "items": [
                        {
                            "name": item["name"],
                            "quantity": int(item["quantity"]),
                            "price": float(item["price"])
                        }
                        for item in st.session_state.new_order_items
                        if item["name"]  # Only include items with names
                    ],
                    "total": float(new_total),
                    "order_date": new_order_date.strftime("%Y-%m-%d"),
                    "shipped_date": new_shipped_date.strftime("%Y-%m-%d") if new_shipped_date else None,
                    "tracking_number": new_tracking if new_tracking else None,
                    "estimated_delivery": new_estimated_delivery.strftime("%Y-%m-%d") if new_estimated_delivery else None
                }
                
                # Create order via API
                result = create_order(order_data)
                
                if "error" in result:
                    st.error(f"Error creating order: {result['error']}")
                else:
                    st.success(f"✅ Order {new_order_id} created successfully!")
                    # Clear cache to force refresh of orders list
                    get_orders.clear()
                    # Reset form
                    st.session_state.new_order_items = [{"name": "", "quantity": 1, "price": 0.0}]
                    st.rerun()
    
    st.markdown("---")
    
    if orders_data and orders_data.get("orders"):
        orders = orders_data["orders"]
        statuses = orders_data.get("statuses", {})
        
        # Order statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Orders", orders_data.get("count", 0))
        with col2:
            st.metric("Processing", statuses.get("processing", 0))
        with col3:
            st.metric("Shipped", statuses.get("shipped", 0))
        with col4:
            st.metric("Delivered", statuses.get("delivered", 0))
        
        # Orders table
        orders_df = pd.DataFrame([
            {
                "Order ID": order.get("order_id", "N/A"),
                "Customer ID": order.get("customer_id", "N/A"),
                "Status": order.get("status", "N/A").title(),
                "Total": f"${order.get('total', 0):.2f}",
                "Date": order.get("order_date", "N/A"),
                "Tracking": order.get("tracking_number", "N/A") if order.get("tracking_number") else "Not available",
                "Items": len(order.get("items", []))
            }
            for order in orders
        ])
        
        st.dataframe(orders_df, use_container_width=True, hide_index=True)
        
        # Order details
        st.subheader("📝 Order Details")
        selected_order_id = st.selectbox(
            "Select an order:",
            options=[order.get("order_id") for order in orders],
            key="order_selector"
        )
        
        if selected_order_id:
            selected_order = next((o for o in orders if o.get("order_id") == selected_order_id), None)
            if selected_order:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Order ID:** {selected_order.get('order_id')}")
                    st.markdown(f"**Customer ID:** {selected_order.get('customer_id')}")
                    st.markdown(f"**Status:** {selected_order.get('status', 'N/A').title()}")
                    st.markdown(f"**Total:** ${selected_order.get('total', 0):.2f}")
                    st.markdown(f"**Date:** {selected_order.get('order_date', 'N/A')}")
                
                with col2:
                    if selected_order.get("shipped_date"):
                        st.markdown(f"**Shipped Date:** {selected_order.get('shipped_date')}")
                    if selected_order.get("tracking_number"):
                        st.markdown(f"**Tracking Number:** {selected_order.get('tracking_number')}")
                    if selected_order.get("estimated_delivery"):
                        st.markdown(f"**Estimated Delivery:** {selected_order.get('estimated_delivery')}")
                
                # Items
                st.markdown("**Items:**")
                items = selected_order.get("items", [])
                if items:
                    items_df = pd.DataFrame(items)
                    st.dataframe(items_df, use_container_width=True, hide_index=True)
    else:
        st.info("No orders available in the system.")
    
    st.markdown("---")
    
    # Tickets Section
    st.subheader("🎫 Support Tickets")
    # Load tickets data (cached, only loads when tab is viewed)
    tickets_data = get_tickets()
    
    if tickets_data and tickets_data.get("tickets"):
        tickets = tickets_data["tickets"]
        ticket_statuses = tickets_data.get("statuses", {})
        priorities = tickets_data.get("priorities", {})
        
        # Ticket statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tickets", tickets_data.get("count", 0))
        with col2:
            st.metric("Open", ticket_statuses.get("open", 0))
        with col3:
            st.metric("In Progress", ticket_statuses.get("in_progress", 0))
        with col4:
            st.metric("Resolved", ticket_statuses.get("resolved", 0))
        
        # Tickets table
        tickets_df = pd.DataFrame([
            {
                "Ticket ID": ticket.get("ticket_id", "N/A"),
                "Customer ID": ticket.get("customer_id", "N/A"),
                "Status": ticket.get("status", "N/A").title(),
                "Priority": ticket.get("priority", "N/A").title(),
                "Created": ticket.get("created_at", "N/A")[:10] if ticket.get("created_at") else "N/A",
                "Assigned To": ticket.get("assigned_to", "Unassigned"),
                "Issue": ticket.get("issue", "N/A")
            }
            for ticket in tickets
        ])
        
        # Display tickets table with full Issue column
        # Use column_config to ensure Issue column shows full text
        column_config = {
            "Issue": st.column_config.TextColumn(
                "Issue",
                width="large",
                help="Full issue description"
            )
        }
        st.dataframe(
            tickets_df, 
            use_container_width=True, 
            hide_index=True,
            column_config=column_config
        )
    else:
        st.info("No tickets available. Create tickets through the chat.")

# Tab 3: Statistics Dashboard
with tab3:
    st.header("📊 Statistics")
    
    # Load metrics and analytics (cached, only loads when tab is viewed)
    metrics_data = get_metrics()
    analytics_data = get_analytics()
    
    if metrics_data:
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📨 Messages Received", metrics_data.get("messages_received", 0))
        with col2:
            st.metric("📤 Messages Sent", metrics_data.get("messages_sent", 0))
        with col3:
            st.metric("🚀 Sessions", metrics_data.get("sessions_started", 0))
        with col4:
            st.metric("❌ Errors", metrics_data.get("errors", 0))
        
        # Metrics chart
        st.subheader("📊 Messages Evolution")
        
        # Create simulated data for demo (in real case, use history)
        dates = pd.date_range(end=datetime.now(), periods=7, freq="D")
        messages_received = [metrics_data.get("messages_received", 0) // 7] * 7
        messages_sent = [metrics_data.get("messages_sent", 0) // 7] * 7
        
        metrics_df = pd.DataFrame({
            "Date": dates,
            "Messages Received": messages_received,
            "Messages Sent": messages_sent
        })
        
        fig = px.line(
            metrics_df,
            x="Date",
            y=["Messages Received", "Messages Sent"],
            title="Messages Evolution",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Agent performance
        if analytics_data and analytics_data.get("agent_performance"):
            st.subheader("🤖 Agent Performance")
            agent_perf = analytics_data["agent_performance"]
            
            perf_data = []
            for agent, stats in agent_perf.items():
                calls = stats.get("calls", 0)
                errors = stats.get("errors", 0)
                success_rate = ((calls - errors) / max(calls, 1)) * 100
                perf_data.append({
                    "Agent": agent.replace("_", " ").title(),
                    "Calls": calls,
                    "Errors": errors,
                    "Success Rate": round(success_rate, 2)
                })
            
            perf_df = pd.DataFrame(perf_data)
            
            # Bar charts with two metrics
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.bar(
                    perf_df,
                    x="Agent",
                    y="Calls",
                    title="Number of Calls per Agent",
                    color="Agent",
                    color_discrete_map={
                        "Faq Agent": "#2196F3",
                        "Order Agent": "#FF9800",
                        "Sentiment Agent": "#9C27B0",
                        "Escalation Agent": "#F44336",
                        "Orchestrator": "#4CAF50"
                    }
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.bar(
                    perf_df,
                    x="Agent",
                    y="Success Rate",
                    title="Success Rate per Agent (%)",
                    color="Agent",
                    color_discrete_map={
                        "Faq Agent": "#2196F3",
                        "Order Agent": "#FF9800",
                        "Sentiment Agent": "#9C27B0",
                        "Escalation Agent": "#F44336",
                        "Orchestrator": "#4CAF50"
                    }
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Detailed table
            st.dataframe(perf_df, use_container_width=True)
    else:
        st.info("No metrics available. Start using the chat to generate metrics.")
