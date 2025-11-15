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


def get_metrics() -> Dict:
    """Get metrics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def get_analytics() -> Dict:
    """Get analytics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=2)
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


# Header
st.markdown('<div class="main-header">🤖 CustoFlow - Multi-Agent Customer Support Dashboard</div>', unsafe_allow_html=True)

# Check API health
api_healthy = check_api_health()
if not api_healthy:
    st.error("⚠️ API is not available. Make sure the FastAPI server is running (python -m api.server)")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
    
    st.header("📊 Quick Metrics")
    metrics = get_metrics()
    if metrics:
        st.metric("Messages Received", metrics.get("messages_received", 0))
        st.metric("Messages Sent", metrics.get("messages_sent", 0))
        st.metric("Sessions", metrics.get("sessions_started", 0))
        st.metric("Errors", metrics.get("errors", 0))
    
    if st.button("🔄 Refresh Metrics"):
        st.rerun()
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()
    
    st.markdown("---")
    st.header("📥 Export")
    if st.button("💾 Export Conversation"):
        if st.session_state.messages:
            export_data = {
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "messages": st.session_state.messages,
                "exported_at": datetime.now().isoformat()
            }
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"conversation_{st.session_state.user_id}_{int(time.time())}.json",
                mime="application/json"
            )
        else:
            st.info("No conversation to export")

# Main Content
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📊 Analytics", "🔄 Routing", "📈 Metrics", "📖 User Guide"])

# Tab 1: Chat Interface
with tab1:
    st.header("💬 Chat with CustoFlow")
    st.markdown("Ask your questions and see how the system automatically routes to the right agent.")
    
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
    
    # Input for new message
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("🤖 CustoFlow is thinking..."):
                start_time = time.time()
                response_data = send_chat_message(prompt)
                response_time = time.time() - start_time
                
                if "error" in response_data:
                    st.error(f"Error: {response_data['error']}")
                else:
                    response_text = response_data.get("response", "")
                    agent_from_api = response_data.get("agent_used")
                    response_time_api = response_data.get("response_time", response_time)
                    confidence = response_data.get("confidence", "high")
                    
                    agent = detect_agent_from_response(response_text, agent_from_api)
                    agent_color = get_agent_color(agent)
                    
                    # Agent badge with confidence
                    confidence_emoji = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🔴"
                    st.markdown(
                        f'<span style="background-color: {agent_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; margin-right: 0.5rem;">{agent}</span>'
                        f'<span style="font-size: 0.75rem; color: #757575;">{confidence_emoji} {confidence}</span>',
                        unsafe_allow_html=True
                    )
                    
                    # Response
                    st.write(response_text)
                    
                    # Metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"⏱️ Response time: {response_time_api:.2f}s")
                    with col2:
                        st.caption(f"📊 Confidence: {confidence}")
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "agent": agent,
                        "response_time": response_time_api,
                        "confidence": confidence
                    })

# Tab 2: Analytics Dashboard
with tab2:
    st.header("📊 Analytics Dashboard")
    
    analytics_data = get_analytics()
    
    if analytics_data:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Interactions", analytics_data.get("total_interactions", 0))
        with col2:
            st.metric("Total Feedback", analytics_data.get("total_feedback", 0))
        with col3:
            agent_perf = analytics_data.get("agent_performance", {})
            total_calls = sum(agent.get("calls", 0) for agent in agent_perf.values())
            st.metric("Total Agent Calls", total_calls)
        
        # Agent performance chart
        if agent_perf:
            st.subheader("📈 Agent Performance")
            agent_names = list(agent_perf.keys())
            agent_calls = [agent_perf[agent].get("calls", 0) for agent in agent_names]
            
            fig = px.bar(
                x=agent_names,
                y=agent_calls,
                title="Number of Calls per Agent",
                labels={"x": "Agent", "y": "Number of Calls"},
                color=agent_names,
                color_discrete_map={
                    "faq_agent": "#2196F3",
                    "order_agent": "#FF9800",
                    "sentiment_agent": "#9C27B0",
                    "escalation_agent": "#F44336",
                    "orchestrator": "#4CAF50"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top query patterns
        top_patterns = analytics_data.get("top_query_patterns", {})
        if top_patterns:
            st.subheader("🔍 Top Query Patterns")
            patterns_df = pd.DataFrame(
                list(top_patterns.items()),
                columns=["Pattern", "Count"]
            )
            fig = px.pie(
                patterns_df,
                values="Count",
                names="Pattern",
                title="Query Patterns Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent interactions
        recent = analytics_data.get("recent_interactions", [])
        if recent:
            st.subheader("📝 Recent Interactions")
            recent_df = pd.DataFrame(recent)
            st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No analytics data available. Start using the chat to generate data.")

# Tab 3: Routing Visualization
with tab3:
    st.header("🔄 Routing Visualization")
    st.markdown("See how the orchestrator routes queries to specialized agents.")
    
    # Routing diagram
    st.subheader("Routing Architecture")
    
    # Create flow chart
    fig = go.Figure()
    
    # Nodes
    nodes = {
        "User Query": (0, 0),
        "Orchestrator": (0, -1),
        "FAQ Agent": (-1, -2),
        "Order Agent": (0, -2),
        "Sentiment Agent": (1, -2),
        "Escalation Agent": (0, -3)
    }
    
    # Edges
    edges = [
        ("User Query", "Orchestrator"),
        ("Orchestrator", "FAQ Agent"),
        ("Orchestrator", "Order Agent"),
        ("Orchestrator", "Sentiment Agent"),
        ("Orchestrator", "Escalation Agent")
    ]
    
    # Add nodes
    for node, (x, y) in nodes.items():
        color = get_agent_color(node) if "Agent" in node else "#757575"
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode="markers+text",
            marker=dict(size=30, color=color),
            text=node,
            textposition="middle center",
            name=node,
            showlegend=False
        ))
    
    # Add edges
    for start, end in edges:
        x0, y0 = nodes[start]
        x1, y1 = nodes[end]
        fig.add_trace(go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(color="#BDBDBD", width=2),
            showlegend=False,
            hoverinfo="skip"
        ))
    
    fig.update_layout(
        title="CustoFlow Routing Flow",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Routing statistics from messages
    if st.session_state.messages:
        st.subheader("📊 Routing Statistics (Current Session)")
        agent_counts = {}
        for msg in st.session_state.messages:
            if msg.get("role") == "assistant":
                agent = msg.get("agent", "Orchestrator")
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        if agent_counts:
            fig = px.pie(
                values=list(agent_counts.values()),
                names=list(agent_counts.keys()),
                title="Distribution of Agents Used",
                color_discrete_map={
                    "FAQ Agent": "#2196F3",
                    "Order Agent": "#FF9800",
                    "Sentiment Agent": "#9C27B0",
                    "Escalation Agent": "#F44336",
                    "Orchestrator": "#4CAF50"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

# Tab 4: Metrics Dashboard
with tab4:
    st.header("📈 Metrics Dashboard")
    
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
        st.subheader("📊 Metrics Evolution")
        
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

# Tab 5: User Guide
with tab5:
    st.header("📖 User Guide")
    
    st.markdown("""
    ## Welcome to CustoFlow Dashboard
    
    This dashboard provides a visual interface to interact with the CustoFlow multi-agent customer support system.
    """)
    
    st.markdown("---")
    
    st.subheader("🚀 Getting Started")
    
    st.markdown("""
    ### Prerequisites
    1. **Start the API Server**: 
       ```bash
       python -m api.server
       ```
       The API will be available at `http://localhost:8000`
    
    2. **Start the Dashboard**:
       ```bash
       streamlit run streamlit_app.py
       ```
       The dashboard will open automatically in your browser at `http://localhost:8501`
    
    3. **Verify API Connection**:
       - The dashboard will show an error if the API is not available
       - Make sure the API server is running before using the dashboard
    """)
    
    st.markdown("---")
    
    st.subheader("💬 Chat Tab")
    
    st.markdown("""
    The **Chat** tab is where you interact with the customer support system.
    
    **How to Use**:
    1. Type your question in the chat input at the bottom
    2. Press Enter or click send
    3. The system will automatically route your query to the appropriate agent
    4. You'll see which agent responded with a colored badge
    
    **Agent Badges**:
    - 🔵 **FAQ Agent** (Blue) - Handles general questions, refunds, shipping policies
    - 🟠 **Order Agent** (Orange) - Handles order status, tracking, delivery questions
    - 🟣 **Sentiment Agent** (Violet) - Analyzes customer sentiment and emotions
    - 🔴 **Escalation Agent** (Red) - Creates tickets for complex issues
    - 🟢 **Orchestrator** (Green) - Main routing agent
    
    **Confidence Indicators**:
    - 🟢 **High** - Response time < 2 seconds
    - 🟡 **Medium** - Response time 2-5 seconds
    - 🔴 **Low** - Response time > 5 seconds
    
    **Example Questions**:
    - "What is your refund policy?" → FAQ Agent
    - "Where is my order 12345?" → Order Agent
    - "I'm frustrated with my order!" → Sentiment Agent
    - "I need to create a ticket" → Escalation Agent
    """)
    
    st.markdown("---")
    
    st.subheader("📊 Analytics Tab")
    
    st.markdown("""
    The **Analytics** tab shows detailed statistics about system usage.
    
    **Features**:
    - **Total Interactions**: Number of conversations
    - **Total Feedback**: User feedback received
    - **Total Agent Calls**: Total number of agent invocations
    - **Agent Performance Chart**: Bar chart showing calls per agent
    - **Top Query Patterns**: Pie chart of most common query patterns
    - **Recent Interactions**: Table of recent conversations
    
    **Use Cases**:
    - Monitor system usage
    - Identify popular query types
    - Track agent performance
    - Analyze user behavior
    """)
    
    st.markdown("---")
    
    st.subheader("🔄 Routing Tab")
    
    st.markdown("""
    The **Routing** tab visualizes how queries are routed through the system.
    
    **Features**:
    - **Routing Architecture Diagram**: Interactive flow chart showing the routing process
    - **Routing Statistics**: Pie chart showing agent distribution for current session
    
    **Understanding the Flow**:
    1. User Query → Orchestrator analyzes the query
    2. Orchestrator → Routes to appropriate specialized agent
    3. Agent → Processes query and returns response
    4. Response → Sent back to user
    
    **Agent Routing Logic**:
    - **FAQ Agent**: General questions, policies, product info
    - **Order Agent**: Order-related queries (status, tracking)
    - **Sentiment Agent**: Emotional queries, frustration detection
    - **Escalation Agent**: Complex issues requiring human intervention
    """)
    
    st.markdown("---")
    
    st.subheader("📈 Metrics Tab")
    
    st.markdown("""
    The **Metrics** tab displays real-time performance metrics.
    
    **Key Metrics**:
    - **Messages Received**: Total incoming messages
    - **Messages Sent**: Total outgoing responses
    - **Sessions**: Number of active sessions
    - **Errors**: Number of errors encountered
    
    **Charts**:
    - **Messages Evolution**: Line chart showing message trends over time
    - **Agent Performance**: Bar charts showing calls and success rates per agent
    - **Performance Table**: Detailed breakdown of agent statistics
    
    **Use Cases**:
    - Monitor system health
    - Track performance trends
    - Identify bottlenecks
    - Optimize agent routing
    """)
    
    st.markdown("---")
    
    st.subheader("⚙️ Sidebar Features")
    
    st.markdown("""
    The sidebar provides configuration and quick actions:
    
    **Configuration**:
    - **User ID**: Customize your user identifier
    - Automatically generated if not set
    
    **Quick Metrics**:
    - Real-time metrics at a glance
    - Refresh button to update metrics
    
    **Actions**:
    - **Refresh Metrics**: Update all metrics
    - **Clear Conversation**: Reset chat history
    - **Export Conversation**: Download conversation as JSON
    
    **Export Feature**:
    - Click "Export Conversation" button
    - Download button will appear
    - JSON file includes:
      - User ID and Session ID
      - All messages with metadata
      - Agent used for each response
      - Response times and confidence levels
    """)
    
    st.markdown("---")
    
    st.subheader("🎯 Tips & Best Practices")
    
    st.markdown("""
    **For Best Results**:
    1. **Be Specific**: Clear questions get better routing
    2. **Use Keywords**: Mention order numbers, ticket IDs when relevant
    3. **Check Agent Badges**: Understand which agent handled your query
    4. **Monitor Metrics**: Use Analytics tab to see system performance
    5. **Export Data**: Save important conversations for analysis
    
    **Troubleshooting**:
    - **API Not Available**: Make sure API server is running
    - **No Response**: Check API logs for errors
    - **Slow Response**: Check Metrics tab for performance issues
    - **Wrong Agent**: Review Routing tab to understand routing logic
    
    **Keyboard Shortcuts**:
    - **Enter**: Send message
    - **Ctrl/Cmd + R**: Refresh page
    - **Tab**: Navigate between tabs
    """)
    
    st.markdown("---")
    
    st.subheader("📚 Additional Resources")
    
    st.markdown("""
    - **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
    - **Project README**: See `README.md` for full documentation
    - **Dashboard README**: See `DASHBOARD_README.md` for detailed guide
    - **GitHub Repository**: [CustoFlow](https://github.com/Rayyan-Oumlil/CustoFlow)
    
    **Support**:
    - Check the Troubleshooting guide in documentation
    - Review API logs for error details
    - Verify API server is running and accessible
    """)
    
    st.markdown("---")
    
    st.info("💡 **Pro Tip**: Start with simple questions to see how the routing works, then explore more complex scenarios!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #757575;">
    <p>🤖 CustoFlow - Multi-Agent Customer Support System</p>
    <p>Built with Google's Agent Development Kit (ADK) and powered by Gemini</p>
</div>
""", unsafe_allow_html=True)
