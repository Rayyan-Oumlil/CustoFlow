# 🚀 Commandes pour lancer l'application

## Terminal 1 - Backend (FastAPI)
```bash
python -m api.server
```
Backend disponible sur: http://localhost:8000

## Terminal 2 - Frontend (Next.js)
```bash
cd frontend
npm run dev
```
**Note:** Si c'est la première fois, installe d'abord les dépendances:
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Frontend disponible sur: http://localhost:3000

## Vérifier que ça marche
1. Backend: http://localhost:8000/health
2. Frontend: http://localhost:3000

