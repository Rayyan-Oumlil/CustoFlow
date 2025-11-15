# CustoFlow Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Google AI Studio API key

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/Rayyan-Oumlil/CustoFlow.git
cd CustoFlow
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key

### 5. Create `.env` File

Create a `.env` file in the project root:

```bash
# .env
GOOGLE_API_KEY=your_api_key_here
```

**Important**: Never commit the `.env` file to Git. It's already in `.gitignore`.

### 6. Verify Installation

Run a test to verify everything works:

```bash
python tests/test_faq_agent.py
```

You should see test results indicating the agent is working.

## Troubleshooting

### Issue: `GOOGLE_API_KEY environment variable is required`

**Solution**: Make sure your `.env` file exists and contains `GOOGLE_API_KEY=your_key_here`

### Issue: `ImportError: cannot import name 'X' from 'google.adk'`

**Solution**: 
1. Make sure you installed dependencies: `pip install -r requirements.txt`
2. Update google-adk: `pip install --upgrade google-adk`

### Issue: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution**: Install missing dependency: `pip install pydantic-settings`

### Issue: API calls are slow or timing out

**Solution**: 
- Check your internet connection
- Verify your API key is valid
- Check if you've exceeded API rate limits

### Issue: Tests fail with connection errors

**Solution**:
- Verify your API key is correct
- Check your internet connection
- Ensure `.env` file is in the project root

## Running the Application

### Interactive CLI

```bash
python main.py
```

### API Server

```bash
# Option 1: Direct Python
python -m api.server

# Option 2: Using uvicorn
uvicorn api.server:app --reload
```

Then access:
- API: http://localhost:8000
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## Development Setup

For development, you may want to:

1. Install development dependencies:
```bash
pip install pytest pytest-asyncio
```

2. Run tests:
```bash
python -m pytest tests/
```

3. Run evaluation suite:
```bash
python notebooks/evaluation.py
```

## Production Considerations

For production deployment:

1. Use environment variables for all secrets
2. Replace mock data with real database/API connections
3. Add authentication and authorization
4. Implement rate limiting
5. Set up proper logging and monitoring
6. Use DatabaseSessionService instead of InMemorySessionService
7. Deploy to Cloud Run, GKE, or similar platform

See `PRODUCTION_GUIDE.md` (if exists) for detailed production setup instructions.

