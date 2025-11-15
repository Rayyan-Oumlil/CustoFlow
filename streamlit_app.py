"""
CustoFlow - Streamlit Dashboard
Interface web visuelle pour visualiser le système multi-agents en action.
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

# Configuration de la page
st.set_page_config(
    page_title="CustoFlow Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Styles CSS personnalisés
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

# Initialisation de la session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{int(time.time())}"


def check_api_health() -> bool:
    """Vérifier si l'API est disponible."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def send_chat_message(message: str) -> Dict:
    """Envoyer un message à l'API."""
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
    """Récupérer les métriques de l'API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def get_analytics() -> Dict:
    """Récupérer les analytics de l'API."""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def detect_agent_from_response(response_text: str) -> str:
    """Détecter quel agent a répondu basé sur le contenu."""
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
    """Obtenir la couleur pour un agent."""
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

# Vérifier la santé de l'API
api_healthy = check_api_health()
if not api_healthy:
    st.error("⚠️ L'API n'est pas disponible. Assurez-vous que le serveur FastAPI est démarré (python -m api.server)")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
    
    st.header("📊 Métriques Rapides")
    metrics = get_metrics()
    if metrics:
        st.metric("Messages Reçus", metrics.get("messages_received", 0))
        st.metric("Messages Envoyés", metrics.get("messages_sent", 0))
        st.metric("Sessions", metrics.get("sessions_started", 0))
        st.metric("Erreurs", metrics.get("errors", 0))
    
    if st.button("🔄 Rafraîchir Métriques"):
        st.rerun()
    
    if st.button("🗑️ Effacer Conversation"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Analytics", "🔄 Routing", "📈 Metrics"])

# Tab 1: Chat Interface
with tab1:
    st.header("💬 Chat avec CustoFlow")
    st.markdown("Posez vos questions et voyez comment le système route automatiquement vers le bon agent.")
    
    # Afficher l'historique des messages
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
                    # Badge de l'agent
                    agent_color = get_agent_color(agent)
                    st.markdown(f'<span style="background-color: {agent_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600;">{agent}</span>', unsafe_allow_html=True)
                    st.write(content)
                    if "response_time" in message:
                        st.caption(f"⏱️ Temps de réponse: {message['response_time']:.2f}s")
    
    # Input pour nouveau message
    if prompt := st.chat_input("Tapez votre message..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Afficher le message utilisateur
        with st.chat_message("user"):
            st.write(prompt)
        
        # Obtenir la réponse
        with st.chat_message("assistant"):
            with st.spinner("🤖 CustoFlow réfléchit..."):
                start_time = time.time()
                response_data = send_chat_message(prompt)
                response_time = time.time() - start_time
                
                if "error" in response_data:
                    st.error(f"Erreur: {response_data['error']}")
                else:
                    response_text = response_data.get("response", "")
                    agent = detect_agent_from_response(response_text)
                    agent_color = get_agent_color(agent)
                    
                    # Badge de l'agent
                    st.markdown(f'<span style="background-color: {agent_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600;">{agent}</span>', unsafe_allow_html=True)
                    
                    # Réponse
                    st.write(response_text)
                    st.caption(f"⏱️ Temps de réponse: {response_time:.2f}s")
                    
                    # Ajouter à l'historique
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "agent": agent,
                        "response_time": response_time
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
            st.metric("Total Appels Agents", total_calls)
        
        # Graphique de performance des agents
        if agent_perf:
            st.subheader("📈 Performance des Agents")
            agent_names = list(agent_perf.keys())
            agent_calls = [agent_perf[agent].get("calls", 0) for agent in agent_names]
            
            fig = px.bar(
                x=agent_names,
                y=agent_calls,
                title="Nombre d'appels par Agent",
                labels={"x": "Agent", "y": "Nombre d'appels"},
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
                title="Distribution des Patterns de Requêtes"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent interactions
        recent = analytics_data.get("recent_interactions", [])
        if recent:
            st.subheader("📝 Interactions Récentes")
            recent_df = pd.DataFrame(recent)
            st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("Aucune donnée analytics disponible. Commencez à utiliser le chat pour générer des données.")

# Tab 3: Routing Visualization
with tab3:
    st.header("🔄 Visualisation du Routing")
    st.markdown("Voyez comment l'orchestrator route les requêtes vers les agents spécialisés.")
    
    # Diagramme de routing
    st.subheader("Architecture de Routing")
    
    # Créer un graphique de flow
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
    
    # Ajouter les nodes
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
    
    # Ajouter les edges
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
        title="Flow de Routing CustoFlow",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistiques de routing depuis les messages
    if st.session_state.messages:
        st.subheader("📊 Statistiques de Routing (Session Actuelle)")
        agent_counts = {}
        for msg in st.session_state.messages:
            if msg.get("role") == "assistant":
                agent = msg.get("agent", "Orchestrator")
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        if agent_counts:
            fig = px.pie(
                values=list(agent_counts.values()),
                names=list(agent_counts.keys()),
                title="Distribution des Agents Utilisés",
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
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📨 Messages Reçus", metrics_data.get("messages_received", 0))
        with col2:
            st.metric("📤 Messages Envoyés", metrics_data.get("messages_sent", 0))
        with col3:
            st.metric("🚀 Sessions", metrics_data.get("sessions_started", 0))
        with col4:
            st.metric("❌ Erreurs", metrics_data.get("errors", 0))
        
        # Graphique de métriques
        st.subheader("📊 Évolution des Métriques")
        
        # Créer des données simulées pour la démo (dans un vrai cas, on utiliserait l'historique)
        dates = pd.date_range(end=datetime.now(), periods=7, freq="D")
        messages_received = [metrics_data.get("messages_received", 0) // 7] * 7
        messages_sent = [metrics_data.get("messages_sent", 0) // 7] * 7
        
        metrics_df = pd.DataFrame({
            "Date": dates,
            "Messages Reçus": messages_received,
            "Messages Envoyés": messages_sent
        })
        
        fig = px.line(
            metrics_df,
            x="Date",
            y=["Messages Reçus", "Messages Envoyés"],
            title="Évolution des Messages",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance des agents
        if analytics_data and analytics_data.get("agent_performance"):
            st.subheader("🤖 Performance des Agents")
            agent_perf = analytics_data["agent_performance"]
            
            perf_data = []
            for agent, stats in agent_perf.items():
                perf_data.append({
                    "Agent": agent.replace("_", " ").title(),
                    "Appels": stats.get("calls", 0),
                    "Erreurs": stats.get("errors", 0),
                    "Taux de Succès": ((stats.get("calls", 0) - stats.get("errors", 0)) / max(stats.get("calls", 1), 1)) * 100
                })
            
            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True)
            
            # Graphique en barres
            fig = px.bar(
                perf_df,
                x="Agent",
                y="Taux de Succès",
                title="Taux de Succès par Agent (%)",
                color="Agent",
                color_discrete_map={
                    "Faq Agent": "#2196F3",
                    "Order Agent": "#FF9800",
                    "Sentiment Agent": "#9C27B0",
                    "Escalation Agent": "#F44336",
                    "Orchestrator": "#4CAF50"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune métrique disponible. Commencez à utiliser le chat pour générer des métriques.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #757575;">
    <p>🤖 CustoFlow - Multi-Agent Customer Support System</p>
    <p>Built with Google's Agent Development Kit (ADK) and powered by Gemini</p>
</div>
""", unsafe_allow_html=True)

