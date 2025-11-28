# 🚀 CustoFlow Deployment Guide

## Deployment Overview

CustoFlow can be deployed in multiple ways depending on your needs. This guide covers deployment options and answers common questions about post-deployment modifications.

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] Python 3.10+ installed
- [ ] Google AI Studio API key
- [ ] Supabase account and credentials (optional but recommended)
- [ ] Environment variables configured
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Semantic search index initialized (`python -m tools.init_semantic_search`)
- [ ] Tests passing (`python tests/run_all_tests.py`)

---

## 🎯 Deployment Options

### Option 1: Local Development (Current Setup)

**Best for**: Development, testing, demos

```bash
# Terminal 1: Start backend
python -m api.server

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev
```

**Access**: 
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Pros**:
- ✅ Quick setup
- ✅ Easy debugging
- ✅ No deployment costs
- ✅ Full control

**Cons**:
- ❌ Not accessible from internet
- ❌ Requires your machine to be running
- ❌ Not suitable for production

---

### Option 2: Cloud Deployment (Recommended for Capstone)

#### 2A. Backend: Railway / Render / Fly.io

**Railway** (Recommended - Easy setup):
1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Connect your repository
4. Add environment variables:
   - `GOOGLE_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
5. Railway auto-detects Python and installs dependencies
6. Set start command: `python -m api.server`
7. Deploy!

**Render**:
1. Create account at [render.com](https://render.com)
2. New Web Service → Connect GitHub
3. Select repository
4. Build command: `pip install -r requirements.txt`
5. Start command: `python -m api.server`
6. Add environment variables
7. Deploy!

**Fly.io**:
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Launch: `fly launch`
4. Add secrets: `fly secrets set GOOGLE_API_KEY=xxx SUPABASE_URL=xxx`
5. Deploy: `fly deploy`

#### 2B. Frontend: Vercel / Netlify

**Vercel** (Recommended - Best for Next.js):
1. Create account at [vercel.com](https://vercel.com)
2. Import Project → Connect GitHub
3. Select `frontend` folder
4. Framework Preset: Next.js
5. Environment Variables:
   - `NEXT_PUBLIC_API_URL`: Your backend URL (e.g., `https://your-app.railway.app`)
6. Deploy!

**Netlify**:
1. Create account at [netlify.com](https://netlify.com)
2. Add new site → Import from Git
3. Build command: `cd frontend && npm install && npm run build`
4. Publish directory: `frontend/.next`
5. Add environment variables
6. Deploy!

---

### Option 3: Docker Deployment

**Best for**: Production, containerization

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "api.server"]
```

Deploy to:
- **Docker Hub** + Any container hosting
- **Google Cloud Run**
- **AWS ECS/Fargate**
- **Azure Container Instances**

---

### Option 4: Google Cloud Agent Engine (Bonus Points)

**Best for**: Capstone bonus points (5 points)

**Note**: This is optional but demonstrates Agent Engine deployment concept.

1. Research Agent Engine deployment process
2. Create deployment configuration
3. Deploy agents to Agent Engine
4. Document deployment in writeup

**Status**: Currently not implemented, but FastAPI deployment already demonstrates deployment concept.

---

## 🔄 Can You Add Things After Deployment?

### ✅ YES - You Can Add Features After Deployment!

**For Capstone Submission**:
- ✅ **Code changes**: You can update code and redeploy anytime
- ✅ **New features**: Add features, tools, agents after initial deployment
- ✅ **Bug fixes**: Fix issues and redeploy
- ✅ **Documentation**: Update README, docs anytime
- ✅ **GitHub commits**: Keep committing after submission

**Important Notes**:
- ⚠️ **Kaggle submission**: Once submitted, the writeup and links are locked
- ⚠️ **GitHub link**: Make sure your GitHub repo is public before submission
- ⚠️ **Video link**: Can update YouTube link if needed (but try to have it ready)
- ✅ **Code improvements**: You can improve code after submission (judges may check later)

### What You CAN'T Change After Submission:
- ❌ Writeup text on Kaggle (locked after submission)
- ❌ Track selection (Enterprise Agents)
- ❌ Submission date/time

### What You CAN Change After Submission:
- ✅ GitHub repository (code, commits, issues)
- ✅ YouTube video (can update link if needed)
- ✅ Documentation (README, ARCHITECTURE.md)
- ✅ Deployed application (backend, frontend)
- ✅ Features and improvements

---

## 📝 Deployment for Capstone Submission

### Minimum Requirements:
1. ✅ **GitHub Repository**: Public repository with all code
2. ✅ **Working Code**: Code should run locally
3. ⚠️ **Deployed Application**: Optional but recommended (shows production-readiness)

### Recommended Setup:
1. **Backend**: Deploy to Railway/Render (free tier available)
2. **Frontend**: Deploy to Vercel (free tier, perfect for Next.js)
3. **Database**: Use Supabase (free tier available)
4. **Documentation**: Update README with deployment links

### Deployment Links to Add:
- Backend API URL: `https://your-app.railway.app`
- Frontend URL: `https://your-app.vercel.app`
- API Docs: `https://your-app.railway.app/docs`

---

## 🛠️ Post-Deployment Checklist

After deploying:

- [ ] Test all endpoints work
- [ ] Verify frontend connects to backend
- [ ] Check environment variables are set
- [ ] Test semantic search works
- [ ] Verify Supabase connection
- [ ] Test chat functionality
- [ ] Check analytics dashboard
- [ ] Update README with deployment URLs
- [ ] Add deployment links to writeup
- [ ] Test from different devices/browsers

---

## 🔧 Environment Variables

### Backend (.env or Railway/Render secrets):
```bash
GOOGLE_API_KEY=your_google_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
MODEL_NAME=gemini-2.5-flash-lite

# Optional: For Google Cloud Speech-to-Text and Text-to-Speech
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
# OR use file path:
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Frontend (Vercel/Netlify environment variables):
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 📊 Deployment Comparison

| Option | Difficulty | Cost | Best For |
|--------|-----------|------|----------|
| Local | ⭐ Easy | Free | Development |
| Railway + Vercel | ⭐⭐ Medium | Free tier | Capstone submission |
| Docker | ⭐⭐⭐ Hard | Varies | Production |
| Agent Engine | ⭐⭐⭐⭐ Very Hard | Varies | Bonus points |

---

## 🎯 Recommendations for Capstone

### Quick Deployment (1-2 hours):
1. **Backend**: Railway (easiest, auto-detects Python)
2. **Frontend**: Vercel (perfect for Next.js, auto-deploys from GitHub)
3. **Database**: Supabase (already using it)

### Steps:
1. Push code to GitHub (make sure it's public)
2. Deploy backend to Railway (connect GitHub repo)
3. Deploy frontend to Vercel (connect GitHub repo, select `frontend` folder)
4. Update environment variables
5. Test everything works
6. Add links to writeup

### After Deployment:
- ✅ You can keep improving code
- ✅ You can add new features
- ✅ You can fix bugs
- ✅ You can update documentation
- ✅ Everything is version controlled in GitHub

---

## 🚨 Important Notes

1. **Free Tiers**: Railway, Vercel, Supabase all have free tiers sufficient for capstone
2. **API Keys**: Never commit API keys to GitHub (use environment variables)
3. **CORS**: Make sure backend allows frontend domain in CORS settings
4. **Time Limits**: Free tiers may have usage limits (usually fine for demos)
5. **GitHub**: Make repository public before submission deadline

---

## 📚 Resources

- [Railway Documentation](https://docs.railway.app)
- [Vercel Documentation](https://vercel.com/docs)
- [Render Documentation](https://render.com/docs)
- [Supabase Documentation](https://supabase.com/docs)

---

## ✅ Final Checklist Before Submission

- [ ] Code pushed to public GitHub repository
- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] All features working in deployed version
- [ ] Environment variables configured
- [ ] Deployment links added to writeup
- [ ] README updated with deployment instructions
- [ ] Tests passing locally
- [ ] No API keys in code
- [ ] Documentation complete

---

*Last Updated: November 27, 2025*

