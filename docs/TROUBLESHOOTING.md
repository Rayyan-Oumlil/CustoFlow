# Troubleshooting Guide

Common issues and solutions for CustoFlow.

## Setup Issues

### API Key Not Found
**Error**: `ValueError: GOOGLE_API_KEY environment variable is required`

**Solution**:
1. Create a `.env` file in the project root
2. Add: `GOOGLE_API_KEY=your_api_key_here`
3. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Module Import Errors
**Error**: `ModuleNotFoundError: No module named 'utils.xxx'`

**Solution**:
1. Ensure you're in the project root directory
2. Run: `pip install -r requirements.txt`
3. Verify Python path includes project root

## Runtime Issues

### Rate Limit Exceeded
**Error**: `Rate limit exceeded. Maximum 60 requests per 60 seconds.`

**Solution**:
- Wait 60 seconds before making another request
- For testing, reset rate limiter: `rate_limiter.reset("user_id")`
- Adjust limits in `utils/rate_limiter.py` if needed

### Timeout Errors
**Error**: `The request took too long to process`

**Solution**:
- Check internet connection
- Verify API key is valid
- Try a simpler query
- Increase timeout in `api/server.py` (default: 30 seconds)

### Empty Responses
**Issue**: Agent returns empty or incomplete responses

**Solution**:
1. Check logs for errors: `observability/logs/app.log`
2. Verify FAQ data exists: `data/faq_knowledge_base.json`
3. Check API key quota/limits
4. Review agent instructions in `agents/*.py`

## Performance Issues

### Slow Response Times
**Issue**: Responses take >5 seconds

**Solution**:
1. Enable caching (already enabled by default)
2. Check cache hit rate: `faq_cache.size()`
3. Optimize FAQ queries (use specific keywords)
4. Consider using faster model: `gemini-2.0-flash-exp`

### High Memory Usage
**Issue**: Application uses too much memory

**Solution**:
1. Clear caches periodically: `faq_cache.clear()`
2. Limit conversation history: `conversation_history.get_history(user_id, limit=50)`
3. Use session cleanup for old sessions

## API Issues

### CORS Errors
**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**:
- CORS is already configured in `api/server.py`
- Verify `allow_origins=["*"]` is set
- Check browser console for specific error

### 500 Internal Server Error
**Error**: `HTTPException(status_code=500, detail=...)`

**Solution**:
1. Check server logs
2. Verify all dependencies installed
3. Ensure `.env` file exists with valid API key
4. Review error message for specific issue

## Testing Issues

### Tests Failing
**Error**: `AssertionError` in tests

**Solution**:
1. Run tests individually: `pytest tests/test_validation.py -v`
2. Check test data matches current implementation
3. Verify API key is set for integration tests
4. Review test output for specific failures

### Import Errors in Tests
**Error**: `ImportError` when running tests

**Solution**:
1. Ensure you're in project root
2. Run: `python -m pytest tests/`
3. Check `PYTHONPATH` includes project root

## Agent-Specific Issues

### FAQ Agent Not Finding Answers
**Issue**: FAQ agent returns "partial" matches

**Solution**:
1. Check FAQ data in `data/faq_knowledge_base.json`
2. Add more keywords to FAQ entries
3. Review scoring algorithm in `tools/faq_tool.py`
4. Use more specific queries

### Order Agent Not Finding Orders
**Issue**: Order lookup returns "not found"

**Solution**:
1. Verify order ID format (5-10 alphanumeric characters)
2. Check mock orders in `tools/order_tool.py`
3. Use valid test order IDs: "12345", "67890", "11111"
4. Review order validation in `utils/validation.py`

### Orchestrator Routing Incorrectly
**Issue**: Wrong agent handles query

**Solution**:
1. Review orchestrator instructions in `agents/orchestrator_agent.py`
2. Use more specific keywords in queries
3. Check agent descriptions match query intent
4. Review routing logic

## Getting Help

1. **Check Logs**: `observability/logs/app.log`
2. **Review Metrics**: `GET /metrics` endpoint
3. **Check Analytics**: `GET /analytics` endpoint
4. **GitHub Issues**: Create an issue with error details

## Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| API Key Error | Create `.env` with `GOOGLE_API_KEY=...` |
| Rate Limit | Wait 60 seconds or reset limiter |
| Timeout | Increase timeout or simplify query |
| Empty Response | Check logs and API key |
| Import Error | Run `pip install -r requirements.txt` |
| CORS Error | Already configured, check browser |
| Test Failure | Run with `-v` flag for details |

