"""
Generate visual diagrams for CustoFlow documentation.

This script creates PNG images of architecture diagrams using graphviz.
"""
from graphviz import Digraph
import os

# Create output directory
os.makedirs("docs/images", exist_ok=True)


def create_architecture_diagram():
    """Create main architecture diagram."""
    dot = Digraph(comment='CustoFlow Architecture', format='png')
    dot.attr(rankdir='TB', size='12,8')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    dot.attr('edge', fontname='Arial')
    
    # Customer
    dot.node('customer', 'Customer Query', fillcolor='#E3F2FD', fontsize='14')
    
    # Orchestrator
    dot.node('orchestrator', 'CustoFlow\nOrchestrator', fillcolor='#4CAF50', 
             fontcolor='white', fontsize='16', shape='ellipse')
    
    # Agents
    dot.node('faq', 'FAQ Agent\n📚', fillcolor='#2196F3', fontcolor='white', fontsize='12')
    dot.node('order', 'Order Agent\n📦', fillcolor='#FF9800', fontcolor='white', fontsize='12')
    dot.node('sentiment', 'Sentiment Agent\n😊', fillcolor='#9C27B0', fontcolor='white', fontsize='12')
    dot.node('escalation', 'Escalation Agent\n🎫', fillcolor='#F44336', fontcolor='white', fontsize='12')
    
    # Tools
    dot.node('faq_tool', 'FAQ Tool\n🔍', fillcolor='#64B5F6', fontsize='10')
    dot.node('order_tool', 'Order Tool\n📋', fillcolor='#FFB74D', fontsize='10')
    dot.node('ticket_tool', 'Ticket Tool\n🎫', fillcolor='#E57373', fontsize='10')
    
    # Connections
    dot.edge('customer', 'orchestrator', label='Query', style='bold')
    dot.edge('orchestrator', 'faq', label='FAQ Query')
    dot.edge('orchestrator', 'order', label='Order Query')
    dot.edge('orchestrator', 'sentiment', label='Sentiment Analysis')
    dot.edge('orchestrator', 'escalation', label='Escalation')
    dot.edge('faq', 'faq_tool', label='Search')
    dot.edge('order', 'order_tool', label='Lookup')
    dot.edge('escalation', 'ticket_tool', label='Create')
    
    # Render
    dot.render('docs/images/architecture', cleanup=True)
    print("✅ Created architecture diagram: docs/images/architecture.png")


def create_data_flow_diagram():
    """Create data flow diagram."""
    dot = Digraph(comment='CustoFlow Data Flow', format='png')
    dot.attr(rankdir='LR', size='14,8')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    dot.attr('edge', fontname='Arial')
    
    # Flow steps
    steps = [
        ('request', 'User Request', '#E3F2FD'),
        ('validate', 'Validation\n🔒', '#FFC107'),
        ('rate_limit', 'Rate Limiting\n⏱️', '#FF9800'),
        ('cache', 'Cache Check\n💾', '#4CAF50'),
        ('orchestrator', 'Orchestrator\n🎯', '#2196F3'),
        ('agent', 'Agent\n🤖', '#9C27B0'),
        ('tool', 'Tool\n🛠️', '#F44336'),
        ('response', 'Response\n✅', '#4CAF50'),
    ]
    
    for i, (id, label, color) in enumerate(steps):
        dot.node(id, label, fillcolor=color, fontcolor='white' if i > 0 else 'black', fontsize='12')
        if i < len(steps) - 1:
            dot.edge(steps[i][0], steps[i+1][0], style='bold')
    
    # Cache hit path
    dot.node('cache_hit', 'Return\nCached', fillcolor='#81C784', fontcolor='white', fontsize='10', style='dashed')
    dot.edge('cache', 'cache_hit', label='Hit', style='dashed', color='green')
    dot.edge('cache_hit', 'response', style='dashed', color='green')
    
    dot.render('docs/images/data_flow', cleanup=True)
    print("✅ Created data flow diagram: docs/images/data_flow.png")


def create_agent_coordination_diagram():
    """Create agent coordination diagram."""
    dot = Digraph(comment='Agent Coordination', format='png')
    dot.attr(rankdir='TB', size='12,10')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    dot.attr('edge', fontname='Arial')
    
    # User query
    dot.node('query', 'Customer Query:\n"I\'m frustrated with\norder 12345!"', 
             fillcolor='#E3F2FD', fontsize='12')
    
    # Orchestrator analysis
    dot.node('analysis', 'Orchestrator Analysis:\n• Sentiment: Negative 😠\n• Type: Order 📦\n• Urgency: High ⚠️', 
             fillcolor='#4CAF50', fontcolor='white', fontsize='11')
    
    # Agents
    dot.node('sentiment', 'Sentiment Agent\n😊\nDetects emotion', 
             fillcolor='#9C27B0', fontcolor='white', fontsize='10')
    dot.node('order', 'Order Agent\n📦\nLooks up order', 
             fillcolor='#FF9800', fontcolor='white', fontsize='10')
    dot.node('escalation', 'Escalation Agent\n🎫\nCreates ticket', 
             fillcolor='#F44336', fontcolor='white', fontsize='10')
    
    # Response
    dot.node('response', 'Combined Response:\n"I understand your\nfrustration. Order 12345\nis shipped. Ticket\ncreated: TICKET-ABC123"', 
             fillcolor='#81C784', fontcolor='white', fontsize='11')
    
    # Connections
    dot.edge('query', 'analysis', style='bold')
    dot.edge('analysis', 'sentiment', label='Analyze')
    dot.edge('analysis', 'order', label='Lookup')
    dot.edge('analysis', 'escalation', label='Escalate')
    dot.edge('sentiment', 'response', style='dashed')
    dot.edge('order', 'response', style='dashed')
    dot.edge('escalation', 'response', style='dashed')
    
    dot.render('docs/images/agent_coordination', cleanup=True)
    print("✅ Created agent coordination diagram: docs/images/agent_coordination.png")


def create_memory_architecture_diagram():
    """Create memory architecture diagram."""
    dot = Digraph(comment='Memory Architecture', format='png')
    dot.attr(rankdir='TB', size='12,10')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    dot.attr('edge', fontname='Arial')
    
    # Session Memory
    dot.node('session', 'Session Memory\n💭\nInMemorySessionService\n• Current context\n• Event history\n• Auto compaction', 
             fillcolor='#2196F3', fontcolor='white', fontsize='11')
    
    # Conversation History
    dot.node('history', 'Conversation History\n📝\nPersistent storage\n• User messages\n• Agent responses\n• Metadata', 
             fillcolor='#FF9800', fontcolor='white', fontsize='11')
    
    # Long-term Memory
    dot.node('longterm', 'Long-Term Memory\n🧠\nMemoryManager\n• Preferences\n• Past issues\n• Patterns', 
             fillcolor='#4CAF50', fontcolor='white', fontsize='11')
    
    # Flow
    dot.edge('session', 'history', label='After session', style='bold')
    dot.edge('history', 'longterm', label='Ingestion', style='bold')
    
    dot.render('docs/images/memory_architecture', cleanup=True)
    print("✅ Created memory architecture diagram: docs/images/memory_architecture.png")


if __name__ == "__main__":
    print("Generating CustoFlow diagrams...\n")
    
    try:
        create_architecture_diagram()
        create_data_flow_diagram()
        create_agent_coordination_diagram()
        create_memory_architecture_diagram()
        
        print("\nAll diagrams generated successfully!")
        print("Location: docs/images/")
        
    except ImportError:
        print("Error: graphviz not installed")
        print("Install with: pip install graphviz")
        print("Also install Graphviz system package:")
        print("   - Windows: choco install graphviz")
        print("   - Mac: brew install graphviz")
        print("   - Linux: sudo apt-get install graphviz")
    except Exception as e:
        print(f"Error: {e}")

