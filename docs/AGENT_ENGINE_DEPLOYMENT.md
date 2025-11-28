# 🚀 Vertex AI Agent Engine Deployment Guide

## 📋 Overview

This guide walks you through deploying CustoFlow agents to **Google Cloud Vertex AI Agent Engine**, a managed service specifically designed for deploying ADK agents. This is an **optional bonus feature** worth 5 points in the capstone project.

**Note**: You've already deployed to Cloud Run + Vercel, which is production-ready. Agent Engine is an alternative managed deployment option.

---

## 🎯 What is Vertex AI Agent Engine?

**Vertex AI Agent Engine** is Google Cloud's fully managed service for deploying and scaling ADK agents. It provides:

- ✅ **Automatic scaling** - Handles traffic spikes automatically
- ✅ **Built-in monitoring** - Integrated observability and metrics
- ✅ **Version management** - Easy rollbacks and A/B testing
- ✅ **Managed infrastructure** - No need to manage servers
- ✅ **Direct ADK integration** - Optimized for Agent Development Kit

**Difference from Cloud Run:**
- **Cloud Run**: Deploys your FastAPI server (what you have now ✅)
- **Agent Engine**: Managed deployment of ADK agents themselves (this guide)

---

## 📦 Prerequisites

Before starting, ensure you have:

1. ✅ **Google Cloud Project** with billing enabled
2. ✅ **gcloud CLI** installed and configured
3. ✅ **Python 3.10+** installed
4. ✅ **ADK installed** (`pip install google-adk`)
5. ✅ **Google Cloud credentials** configured
6. ✅ **API access** to Vertex AI enabled

### Setup Google Cloud CLI

```bash
# Install gcloud CLI (if not already installed)
# Windows: Download from https://cloud.google.com/sdk/docs/install
# Mac: brew install google-cloud-sdk
# Linux: curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

## 🏗️ Project Structure for Agent Engine

Your agents need to be structured in a way that Agent Engine can deploy them. Here's the recommended structure:

```
customer-support-agent/
├── agents/
│   ├── __init__.py
│   ├── orchestrator_agent.py    # Main agent to deploy
│   ├── faq_agent.py
│   ├── order_agent.py
│   ├── sentiment_agent.py
│   └── escalation_agent.py
├── tools/
│   ├── faq_tool.py
│   ├── order_tool.py
│   └── ... (other tools)
├── config/
│   └── settings.py
├── requirements.txt
├── agent_engine_config.yaml      # New: Agent Engine config
└── deploy_agent_engine.py        # New: Deployment script
```

---

## 📝 Step 1: Create Agent Engine Configuration

Create a configuration file for Agent Engine deployment:

**`agent_engine_config.yaml`:**

```yaml
# Agent Engine Configuration for CustoFlow
agent:
  name: custoflow-orchestrator
  display_name: CustoFlow Orchestrator Agent
  description: Multi-agent customer support system orchestrator
  
  # Main agent entry point
  entry_point: agents.orchestrator_agent:orchestrator_agent
  
  # Model configuration
  model:
    provider: google
    model_name: gemini-2.5-flash-lite
    
  # Environment variables
  env:
    - name: GOOGLE_API_KEY
      value_from_secret: google-api-key
    - name: SUPABASE_URL
      value_from_secret: supabase-url
    - name: SUPABASE_KEY
      value_from_secret: supabase-key
      
  # Resource requirements
  resources:
    cpu: "2"
    memory: "4Gi"
    
  # Scaling configuration
  scaling:
    min_instances: 1
    max_instances: 10
    target_concurrent_requests: 10
```

---

## 🔧 Step 2: Prepare Deployment Script

Create a Python script to deploy your agent:

**`deploy_agent_engine.py`:**

```python
"""
Deploy CustoFlow orchestrator agent to Vertex AI Agent Engine.
"""
import os
import yaml
from google.cloud import aiplatform
from google.adk.deploy import AgentEngineDeployer

def load_config(config_path: str = "agent_engine_config.yaml"):
    """Load Agent Engine configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def deploy_agent():
    """Deploy agent to Vertex AI Agent Engine."""
    
    # Initialize Vertex AI
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    aiplatform.init(project=project_id, location=location)
    
    # Load configuration
    config = load_config()
    
    # Create deployer
    deployer = AgentEngineDeployer(
        agent_name=config['agent']['name'],
        entry_point=config['agent']['entry_point'],
        project_id=project_id,
        location=location
    )
    
    # Deploy agent
    print(f"🚀 Deploying {config['agent']['name']} to Agent Engine...")
    
    endpoint = deployer.deploy(
        display_name=config['agent']['display_name'],
        description=config['agent']['description'],
        model_config=config['agent']['model'],
        env_vars=config['agent']['env'],
        resources=config['agent']['resources'],
        scaling=config['agent']['scaling']
    )
    
    print(f"✅ Agent deployed successfully!")
    print(f"📍 Endpoint: {endpoint.resource_name}")
    print(f"🌐 Endpoint URL: {endpoint.endpoint_url}")
    
    return endpoint

if __name__ == "__main__":
    deploy_agent()
```

---

## 🔐 Step 3: Set Up Secrets

Store sensitive credentials in Google Cloud Secret Manager:

```bash
# Create secrets
echo -n "your-google-api-key" | gcloud secrets create google-api-key --data-file=-
echo -n "your-supabase-url" | gcloud secrets create supabase-url --data-file=-
echo -n "your-supabase-key" | gcloud secrets create supabase-key --data-file=-

# Grant access to the service account
gcloud secrets add-iam-policy-binding google-api-key \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## 📦 Step 4: Create Deployment Package

Create a deployment package with all dependencies:

**`Dockerfile.agent-engine`:**

```dockerfile
# Dockerfile for Agent Engine deployment
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ADK
RUN pip install google-adk

# Copy application code
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY config/ ./config/
COPY agent_engine_config.yaml .

# Set Python path
ENV PYTHONPATH=/app

# Expose port (Agent Engine will handle this)
EXPOSE 8080

# Entry point (Agent Engine will override this)
CMD ["python", "-m", "agents.orchestrator_agent"]
```

---

## 🚀 Step 5: Deploy to Agent Engine

### Option A: Using ADK CLI (Recommended)

```bash
# Install ADK CLI tools
pip install google-adk[deploy]

# Deploy agent
adk deploy agent-engine \
    --config agent_engine_config.yaml \
    --project YOUR_PROJECT_ID \
    --region us-central1 \
    --entry-point agents.orchestrator_agent:orchestrator_agent
```

### Option B: Using Python Script

```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_REGION=us-central1

# Run deployment script
python deploy_agent_engine.py
```

### Option C: Using gcloud CLI

```bash
# Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/custoflow-agent

# Deploy to Agent Engine
gcloud ai agents deploy \
    --agent-name=custoflow-orchestrator \
    --display-name="CustoFlow Orchestrator" \
    --image=gcr.io/YOUR_PROJECT_ID/custoflow-agent \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID
```

---

## 🧪 Step 6: Test the Deployment

Once deployed, test your agent:

**`test_agent_engine.py`:**

```python
"""Test deployed agent on Agent Engine."""
from google.cloud import aiplatform
from google.adk.runners import Runner

# Initialize
project_id = "YOUR_PROJECT_ID"
location = "us-central1"
endpoint_name = "custoflow-orchestrator"

aiplatform.init(project=project_id, location=location)

# Get endpoint
endpoint = aiplatform.Endpoint.list(
    filter=f'display_name="{endpoint_name}"'
)[0]

# Create runner
runner = Runner(endpoint=endpoint)

# Test query
response = runner.run(
    user_id="test_user",
    session_id="test_session",
    message="Hello, I need help with my order"
)

print(f"Response: {response}")
```

---

## 📊 Step 7: Monitor and Manage

### View Agent Status

```bash
# List deployed agents
gcloud ai agents list --region=us-central1

# Get agent details
gcloud ai agents describe custoflow-orchestrator --region=us-central1

# View logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent" --limit=50
```

### Monitor Metrics

Access metrics in Google Cloud Console:
- **Vertex AI > Agents > custoflow-orchestrator**
- View request counts, latency, errors
- Monitor scaling and resource usage

### Update Agent

```bash
# Update agent configuration
adk deploy agent-engine \
    --config agent_engine_config.yaml \
    --update \
    --version=v2
```

---

## 🔄 Step 8: Integrate with Your Frontend

Update your frontend to use Agent Engine endpoint:

**`frontend/lib/agent-engine-client.ts`:**

```typescript
import { GoogleAuth } from 'google-auth-library';

const AGENT_ENGINE_ENDPOINT = process.env.NEXT_PUBLIC_AGENT_ENGINE_ENDPOINT;

export async function callAgentEngine(
  userId: string,
  sessionId: string,
  message: string
): Promise<string> {
  const auth = new GoogleAuth({
    scopes: ['https://www.googleapis.com/auth/cloud-platform'],
  });

  const client = await auth.getClient();
  const accessToken = await client.getAccessToken();

  const response = await fetch(AGENT_ENGINE_ENDPOINT, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      message: message,
    }),
  });

  const data = await response.json();
  return data.response;
}
```

---

## 🎯 Alternative: Keep Cloud Run + Add Agent Engine

You can run both deployments in parallel:

- **Cloud Run**: Your FastAPI server (current deployment ✅)
- **Agent Engine**: Managed ADK agents (optional bonus)

This allows you to:
1. Keep your existing Cloud Run deployment
2. Add Agent Engine as an alternative endpoint
3. A/B test between the two
4. Gradually migrate if desired

---

## 📝 Update Your Writeup

Add this section to your capstone writeup:

```markdown
### Agent Engine Deployment (Bonus)

CustoFlow has been deployed to **Google Cloud Vertex AI Agent Engine**, 
demonstrating managed ADK agent deployment. The orchestrator agent is 
available as a managed service with automatic scaling, built-in monitoring, 
and version management.

**Deployment Details:**
- Agent Name: `custoflow-orchestrator`
- Region: `us-central1`
- Model: `gemini-2.5-flash-lite`
- Scaling: 1-10 instances based on traffic

**Benefits:**
- Automatic scaling for traffic spikes
- Integrated observability and metrics
- Easy version management and rollbacks
- Managed infrastructure (no server management)

**Endpoint:** [Your Agent Engine endpoint URL]
```

---

## ⚠️ Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Re-authenticate
   gcloud auth application-default login
   ```

2. **Permission Errors**
   ```bash
   # Grant necessary roles
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="user:YOUR_EMAIL" \
       --role="roles/aiplatform.admin"
   ```

3. **Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check that `PYTHONPATH` is set correctly
   - Verify all modules are included in deployment package

4. **Deployment Timeout**
   - Increase timeout in configuration
   - Check Cloud Build logs for errors
   - Verify container builds successfully

---

## 📚 Additional Resources

- [ADK Deployment Documentation](https://google.github.io/adk-docs/deploy/agent-engine/)
- [Vertex AI Agent Engine Guide](https://cloud.google.com/vertex-ai/docs/agents/overview)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)
- [ADK Examples](https://github.com/google/adk-examples)

---

## ✅ Checklist

Before submitting, ensure:

- [ ] Agent Engine configuration file created
- [ ] Secrets stored in Secret Manager
- [ ] Agent deployed successfully
- [ ] Agent tested and working
- [ ] Monitoring set up
- [ ] Endpoint URL documented
- [ ] Writeup updated with deployment details
- [ ] Frontend integration (if applicable)

---

## 🎉 Success!

Once deployed, you'll have:

- ✅ **Managed ADK agent deployment** on Vertex AI Agent Engine
- ✅ **Automatic scaling** based on traffic
- ✅ **Built-in monitoring** and observability
- ✅ **5 bonus points** for your capstone submission!

**Note**: This is optional. Your Cloud Run + Vercel deployment is already excellent and production-ready. Agent Engine is an additional bonus feature.

---

*Last Updated: November 27, 2025*

