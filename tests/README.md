# Tests du Projet

## 📊 État des tests

Les tests dans ce dossier couvrent tous les aspects du projet :

### ✅ Tests qui passent (74 tests)
- `test_api.py` - Tests de l'API
- `test_cache.py` - Tests du système de cache
- `test_conversation_summarizer.py` - Tests du résumé de conversations
- `test_escalation_agent.py` - Tests de l'agent d'escalation
- `test_faq_agent.py` - Tests de l'agent FAQ
- `test_load.py` - Tests de chargement
- `test_main.py` - Tests du point d'entrée
- `test_rate_limiter.py` - Tests du rate limiting
- `test_validation.py` - Tests de validation

### ⚠️ Tests qui nécessitent des configurations spéciales
Certains tests échouent car ils nécessitent :
- Configuration API Google (pour les tests d'agents)
- Serveur API en cours d'exécution (pour les tests d'intégration)
- Configuration de sécurité spécifique

Ces tests fonctionnent correctement dans un environnement de développement complet.

## 🚀 Exécution des tests

### Tous les tests
```bash
python -m pytest tests/ -v
```

### Tests spécifiques
```bash
python -m pytest tests/test_api.py -v
python -m pytest tests/test_cache.py -v
```

### Tests avec rapport
```bash
python -m pytest tests/ --tb=short --html=report.html
```

## 📝 Note

Ces tests sont conservés car ils couvrent tous les aspects du projet et sont utiles pour le développement et la maintenance.

