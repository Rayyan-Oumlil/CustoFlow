# Diagram Images

This directory contains generated PNG diagram images for CustoFlow documentation.

## Generate Diagrams

To generate the diagrams, run:

```bash
python scripts/generate_diagrams.py
```

This will create:
- `architecture.png` - Main system architecture
- `data_flow.png` - Request data flow diagram
- `agent_coordination.png` - Multi-agent coordination flow
- `memory_architecture.png` - Memory system architecture

## Requirements

1. Install Python package:
```bash
pip install graphviz
```

2. Install Graphviz system package:
   - **Windows**: `choco install graphviz` or download from [graphviz.org](https://graphviz.org/download/)
   - **Mac**: `brew install graphviz`
   - **Linux**: `sudo apt-get install graphviz`

## Alternative: Mermaid Diagrams

The README also includes Mermaid diagrams that render automatically on GitHub without any installation needed!

