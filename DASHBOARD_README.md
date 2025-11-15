# 🎨 CustoFlow Dashboard - Guide d'Utilisation

Dashboard Streamlit pour visualiser et interagir avec le système multi-agents CustoFlow.

---

## 🚀 Démarrage Rapide

### 1. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 2. Démarrer l'API Server

Dans un premier terminal :

```bash
python -m api.server
```

L'API sera disponible sur `http://localhost:8000`

### 3. Démarrer le Dashboard

Dans un second terminal :

```bash
streamlit run streamlit_app.py
```

Le dashboard sera automatiquement ouvert dans votre navigateur sur `http://localhost:8501`

---

## 📊 Fonctionnalités du Dashboard

### 💬 Tab Chat

**Interface de conversation interactive**

- Chat interface moderne style ChatGPT
- Détection automatique de l'agent utilisé
- Badges colorés pour identifier l'agent :
  - 🔵 **FAQ Agent** (Bleu) - Questions générales
  - 🟠 **Order Agent** (Orange) - Requêtes de commandes
  - 🟣 **Sentiment Agent** (Violet) - Analyse de sentiment
  - 🔴 **Escalation Agent** (Rouge) - Création de tickets
  - 🟢 **Orchestrator** (Vert) - Routage principal
- Affichage du temps de réponse
- Historique de conversation persistante

**Utilisation** :
1. Tapez votre question dans le champ de chat
2. Voyez quel agent répond automatiquement
3. Consultez le temps de réponse

---

### 📊 Tab Analytics

**Dashboard analytics avec statistiques détaillées**

- **Métriques Globales** :
  - Total interactions
  - Total feedback
  - Total appels agents

- **Performance des Agents** :
  - Graphique en barres du nombre d'appels par agent
  - Visualisation colorée par type d'agent

- **Top Query Patterns** :
  - Pie chart des patterns de requêtes les plus fréquents
  - Identification des sujets populaires

- **Interactions Récentes** :
  - Tableau des dernières interactions
  - Détails complets (timestamp, user_id, query, etc.)

---

### 🔄 Tab Routing

**Visualisation du système de routing**

- **Architecture de Routing** :
  - Diagramme interactif du flow complet
  - Nodes pour chaque composant (User, Orchestrator, Agents)
  - Edges montrant les connexions
  - Visualisation claire du processus

- **Statistiques de Routing (Session Actuelle)** :
  - Distribution des agents utilisés dans la session
  - Pie chart montrant la répartition
  - Identification des agents les plus sollicités

---

### 📈 Tab Metrics

**Métriques détaillées et performance**

- **Métriques Principales** :
  - Messages reçus
  - Messages envoyés
  - Sessions démarrées
  - Erreurs

- **Évolution des Métriques** :
  - Line chart montrant l'évolution dans le temps
  - Comparaison messages reçus vs envoyés

- **Performance des Agents** :
  - Tableau détaillé avec appels, erreurs, taux de succès
  - Bar chart du taux de succès par agent
  - Identification des agents les plus performants

---

## 🎨 Sidebar

**Configuration et métriques rapides**

- **Configuration** :
  - User ID personnalisable
  - Identification de session

- **Métriques Rapides** :
  - Messages reçus/envoyés
  - Sessions démarrées
  - Erreurs

- **Actions** :
  - Rafraîchir les métriques
  - Effacer la conversation

---

## 🔧 Configuration

### Changer l'URL de l'API

Si votre API tourne sur un autre port ou serveur, modifiez dans `streamlit_app.py` :

```python
API_BASE_URL = "http://localhost:8000"  # Changez ici
```

### Personnaliser les Couleurs

Les couleurs des agents sont définies dans la fonction `get_agent_color()` :

```python
colors = {
    "FAQ Agent": "#2196F3",
    "Order Agent": "#FF9800",
    "Sentiment Agent": "#9C27B0",
    "Escalation Agent": "#F44336",
    "Orchestrator": "#4CAF50"
}
```

---

## 📸 Screenshots

### Interface Chat
- Chat moderne avec badges d'agents
- Historique de conversation
- Temps de réponse affiché

### Analytics Dashboard
- Graphiques interactifs
- Statistiques détaillées
- Patterns de requêtes

### Routing Visualization
- Diagramme de flow
- Statistiques de session
- Distribution des agents

### Metrics Dashboard
- Métriques en temps réel
- Graphiques d'évolution
- Performance des agents

---

## 🐛 Dépannage

### L'API n'est pas disponible

**Erreur** : "⚠️ L'API n'est pas disponible"

**Solution** :
1. Vérifiez que l'API server est démarré : `python -m api.server`
2. Vérifiez que l'API est accessible sur `http://localhost:8000`
3. Vérifiez le port dans `streamlit_app.py` si différent

### Les graphiques ne s'affichent pas

**Solution** :
1. Vérifiez que Plotly est installé : `pip install plotly`
2. Vérifiez que des données existent (utilisez le chat d'abord)

### Le chat ne répond pas

**Solution** :
1. Vérifiez que l'API est démarrée
2. Vérifiez les logs de l'API pour les erreurs
3. Vérifiez que `GOOGLE_API_KEY` est configuré dans `.env`

---

## 🚀 Déploiement

### Streamlit Cloud (Gratuit)

1. Push votre code sur GitHub
2. Allez sur [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connectez votre repository
4. Configurez les variables d'environnement (GOOGLE_API_KEY)
5. Déployez !

### Local avec Docker

```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 📝 Notes

- Le dashboard nécessite que l'API soit démarrée
- Les données analytics sont en mémoire (reset au redémarrage de l'API)
- Pour la production, utilisez une base de données pour persister les données

---

*Dashboard créé le : 2024-11-15*  
*Version : 1.0.0*

