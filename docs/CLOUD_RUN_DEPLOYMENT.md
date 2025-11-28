# 🚀 Déploiement sur Google Cloud Run

## Pourquoi Cloud Run?

- ✅ **Serverless**: Payez seulement quand utilisé (0 instance quand inactif)
- ✅ **Auto-scaling**: 0 à N instances automatiquement
- ✅ **Utilise vos crédits Google Cloud**: Parfait si vous avez des crédits gratuits
- ✅ **Très scalable**: Gère des milliers de requêtes
- ✅ **HTTPS automatique**: SSL/TLS inclus
- ✅ **Gratuit**: 2M requêtes/mois (gratuit tier)

---

## 📋 Prérequis

1. **Compte Google Cloud** avec crédits activés
2. **Google Cloud SDK (gcloud)** installé
3. **Projet Google Cloud** créé
4. **Billing activé** (nécessaire même avec crédits gratuits)

---

## 🛠️ Installation de gcloud CLI

### Windows (PowerShell):
```powershell
# Téléchargez et installez depuis:
# https://cloud.google.com/sdk/docs/install

# Ou avec Chocolatey:
choco install gcloudsdk
```

### Mac:
```bash
brew install --cask google-cloud-sdk
```

### Linux:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

---

## 🚀 Déploiement Étape par Étape

### Étape 1: Authentification

```bash
# Se connecter à Google Cloud
gcloud auth login

# Sélectionner votre projet (ou créer un nouveau)
gcloud config set project YOUR_PROJECT_ID

# Activer les APIs nécessaires
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Étape 2: Créer un fichier .env.gcloud (optionnel)

Créez un fichier `.env.gcloud` avec vos variables (ne le commitez pas!):

```bash
GOOGLE_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
MODEL_NAME=gemini-2.5-flash-lite
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
```

### Étape 3: Déployer sur Cloud Run

```bash
# Depuis la racine du projet
gcloud run deploy custoflow-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "GOOGLE_API_KEY=your_key,SUPABASE_URL=your_url,SUPABASE_KEY=your_key"
```

**Ou avec un fichier .env:**

```bash
# Créer un fichier .env.gcloud avec vos variables
# Puis:
gcloud run deploy custoflow-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --env-vars-file .env.gcloud
```

### Étape 4: Vérifier le déploiement

```bash
# Obtenir l'URL du service
gcloud run services describe custoflow-api --region us-central1 --format 'value(status.url)'

# Tester
curl https://YOUR-SERVICE-URL.run.app/health
```

---

## 🔧 Configuration Avancée

### Variables d'environnement

```bash
# Ajouter des variables
gcloud run services update custoflow-api \
  --region us-central1 \
  --update-env-vars "NEW_VAR=value"

# Ou depuis un fichier
gcloud run services update custoflow-api \
  --region us-central1 \
  --env-vars-file .env.gcloud
```

### Secrets (Recommandé pour les clés sensibles)

```bash
# Créer un secret
echo -n "your-secret-value" | gcloud secrets create google-api-key --data-file=-

# Donner accès au service
gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Utiliser le secret dans Cloud Run
gcloud run services update custoflow-api \
  --region us-central1 \
  --update-secrets "GOOGLE_API_KEY=google-api-key:latest"
```

### Scaling

```bash
# Configurer le scaling
gcloud run services update custoflow-api \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 2 \
  --memory 2Gi
```

### Timeout

```bash
# Augmenter le timeout (max 3600s pour Cloud Run)
gcloud run services update custoflow-api \
  --region us-central1 \
  --timeout 300
```

---

## 📊 Monitoring et Logs

### Voir les logs

```bash
# Logs en temps réel
gcloud run services logs read custoflow-api --region us-central1 --follow

# Logs dans la console
# https://console.cloud.google.com/run
```

### Monitoring

```bash
# Voir les métriques
gcloud run services describe custoflow-api --region us-central1
```

---

## 💰 Coûts et Crédits

### Gratuit Tier:
- ✅ **2M requêtes/mois** gratuites
- ✅ **360,000 GB-secondes CPU** gratuites
- ✅ **180,000 GB-secondes mémoire** gratuites

### Après le gratuit tier:
- 💰 **$0.40 par million de requêtes**
- 💰 **$0.00002400 par GB-seconde CPU**
- 💰 **$0.00000250 par GB-seconde mémoire**

**Avec vos crédits Google Cloud, vous pouvez déployer gratuitement!**

---

## 🔄 Mise à Jour

```bash
# Redéployer après des changements
gcloud run deploy custoflow-api \
  --source . \
  --platform managed \
  --region us-central1
```

---

## 🐛 Dépannage

### Erreur: "Permission denied"
```bash
# Vérifier les permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

### Erreur: "Build failed"
```bash
# Vérifier les logs de build
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

### Erreur: "Service unavailable"
```bash
# Vérifier les logs du service
gcloud run services logs read custoflow-api --region us-central1 --limit=50
```

### Erreur: "Timeout"
```bash
# Augmenter le timeout
gcloud run services update custoflow-api \
  --region us-central1 \
  --timeout 300
```

---

## 📝 Commandes Utiles

```bash
# Lister les services
gcloud run services list

# Décrire un service
gcloud run services describe custoflow-api --region us-central1

# Supprimer un service
gcloud run services delete custoflow-api --region us-central1

# Voir les révisions
gcloud run revisions list --service custoflow-api --region us-central1

# Rollback à une révision précédente
gcloud run services update-traffic custoflow-api \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

---

## 🎯 Configuration Recommandée pour CustoFlow

```bash
gcloud run deploy custoflow-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "GOOGLE_API_KEY=$GOOGLE_API_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_KEY=$SUPABASE_KEY,MODEL_NAME=gemini-2.5-flash-lite"
```

---

## ✅ Checklist de Déploiement

- [ ] gcloud CLI installé
- [ ] Authentifié (`gcloud auth login`)
- [ ] Projet créé et sélectionné
- [ ] Billing activé
- [ ] APIs activées (Cloud Run, Cloud Build)
- [ ] Dockerfile créé
- [ ] Variables d'environnement configurées
- [ ] Service déployé
- [ ] URL obtenue et testée
- [ ] `/health` endpoint fonctionne
- [ ] Logs vérifiés

---

## 🔗 Liens Utiles

- **Console Cloud Run**: https://console.cloud.google.com/run
- **Documentation**: https://cloud.google.com/run/docs
- **Pricing**: https://cloud.google.com/run/pricing
- **Quotas**: https://console.cloud.google.com/iam-admin/quotas

---

*Dernière mise à jour: Novembre 2025*

