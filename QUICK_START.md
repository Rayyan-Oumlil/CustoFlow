# 🚀 Quick Start Guide - CustoFlow

Guide rapide pour lancer et tester CustoFlow.

---

## 📋 Prérequis

1. **Python 3.10+** installé
2. **Dépendances installées** :
   ```bash
   pip install -r requirements.txt
   ```
3. **Fichier `.env`** avec votre clé API :
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

---

## 🚀 Lancer l'Application

### Étape 1 : Démarrer l'API Server

**Ouvrez un premier terminal** et exécutez :

```bash
python -m api.server
```

Vous devriez voir :
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ L'API est maintenant disponible sur `http://localhost:8000`

**Vérifier que l'API fonctionne** :
- Ouvrez votre navigateur : `http://localhost:8000/health`
- Vous devriez voir : `{"status": "healthy", "metrics": {...}}`

---

### Étape 2 : Démarrer le Dashboard Streamlit

**Ouvrez un deuxième terminal** (laissez le premier ouvert) et exécutez :

**Sur Windows** :
```bash
python -m streamlit run streamlit_app.py
```

**Sur Linux/Mac** :
```bash
streamlit run streamlit_app.py
```

Vous devriez voir :
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://...
```

✅ Le dashboard s'ouvrira automatiquement dans votre navigateur sur `http://localhost:8501`

---

## 🧪 Tester l'Application

### Test 1 : Via le Dashboard (Recommandé)

1. **Ouvrez le dashboard** : `http://localhost:8501`
2. **Allez dans le tab "💬 Chat"**
3. **Testez avec ces questions** :

   **FAQ Agent** (Questions générales) :
   ```
   What is your refund policy?
   How long does shipping take?
   Can I return items?
   ```

   **Order Agent** (Commandes) :
   ```
   What's the status of order 12345?
   Where is my order 67890?
   Check my order 11111
   ```

   **Sentiment Agent** (Sentiment) :
   ```
   I'm extremely frustrated with my order!
   I love your service, thank you!
   ```

   **Escalation Agent** (Tickets) :
   ```
   I need to create a ticket for a damaged product
   My order was never delivered, I need urgent help
   ```

4. **Observez** :
   - Le badge de l'agent utilisé (couleur)
   - L'indicateur de confiance (🟢🟡🔴)
   - Le temps de réponse
   - La réponse de l'agent

---

### Test 2 : Via l'API directement

**Avec curl** :
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is your refund policy?",
    "user_id": "test_user"
  }'
```

**Avec Python** :
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What is your refund policy?",
        "user_id": "test_user"
    }
)

print(response.json())
```

**Avec le navigateur** :
- Ouvrez : `http://localhost:8000/docs`
- C'est l'interface Swagger UI
- Testez l'endpoint `/chat` directement

---

### Test 3 : Via le CLI

```bash
python main.py
```

Puis entrez vos questions dans le terminal.

---

## 📊 Explorer les Tabs du Dashboard

### Tab 1 : 💬 Chat
- Posez des questions
- Voyez les agents répondre
- Observez les badges et indicateurs

### Tab 2 : 📊 Analytics
- Consultez les statistiques
- Voyez les graphiques de performance
- Analysez les patterns de requêtes

### Tab 3 : 🔄 Routing
- Visualisez le flow de routing
- Voyez la distribution des agents
- Comprenez l'architecture

### Tab 4 : 📈 Metrics
- Métriques en temps réel
- Performance des agents
- Évolution des messages

### Tab 5 : 📖 User Guide
- Guide complet d'utilisation
- Instructions détaillées
- Tips et bonnes pratiques

---

## ✅ Checklist de Test

- [ ] API démarre sans erreur
- [ ] Dashboard démarre sans erreur
- [ ] Chat fonctionne et retourne des réponses
- [ ] Les badges d'agents s'affichent correctement
- [ ] Les graphiques Analytics fonctionnent
- [ ] La visualisation Routing s'affiche
- [ ] Les métriques sont visibles
- [ ] L'export de conversation fonctionne

---

## 🐛 Dépannage

### Problème : "API is not available"

**Solution** :
1. Vérifiez que l'API server est démarré : `python -m api.server`
2. Vérifiez que le port 8000 n'est pas utilisé par un autre processus
3. Vérifiez l'URL dans `streamlit_app.py` (par défaut : `http://localhost:8000`)

### Problème : "Module not found"

**Solution** :
```bash
pip install -r requirements.txt
```

### Problème : "GOOGLE_API_KEY not found"

**Solution** :
1. Créez un fichier `.env` à la racine du projet
2. Ajoutez : `GOOGLE_API_KEY=your_api_key_here`
3. Obtenez votre clé sur : https://aistudio.google.com/app/apikey

### Problème : "Port already in use"

**Solution** :
- Pour l'API : Changez le port dans `config/settings.py` ou utilisez `uvicorn api.server:app --port 8001`
- Pour Streamlit : Utilisez `streamlit run streamlit_app.py --server.port 8502`

---

## 🎯 Tests Recommandés

### Test Basique
1. Démarrer API + Dashboard
2. Poser une question simple : "What is your refund policy?"
3. Vérifier que FAQ Agent répond

### Test Complet
1. Tester tous les types d'agents (FAQ, Order, Sentiment, Escalation)
2. Vérifier les graphiques Analytics
3. Vérifier la visualisation Routing
4. Vérifier les métriques
5. Exporter une conversation

### Test de Performance
1. Envoyer plusieurs requêtes rapidement
2. Vérifier le rate limiting (60 req/min)
3. Observer les temps de réponse
4. Vérifier les métriques de performance

---

## 📝 Commandes Utiles

```bash
# Démarrer l'API
python -m api.server

# Démarrer le Dashboard (Windows)
python -m streamlit run streamlit_app.py

# Démarrer le Dashboard (Linux/Mac)
streamlit run streamlit_app.py

# Tester l'API
curl http://localhost:8000/health

# Voir la documentation API
# Ouvrir http://localhost:8000/docs dans le navigateur

# Lancer les tests
python -m pytest tests/

# Vérifier le projet
python scripts/check_project.py

# Lancer l'évaluation
python notebooks/evaluation.py
```

---

## 🎉 C'est Prêt !

Une fois l'API et le Dashboard démarrés, vous pouvez :
- ✅ Utiliser le chat pour poser des questions
- ✅ Explorer les analytics et métriques
- ✅ Visualiser le routing
- ✅ Exporter vos conversations
- ✅ Tester tous les agents

**Bon test ! 🚀**

---

*Guide créé le : 2024-11-15*

