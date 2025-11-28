#!/bin/bash
# Script de déploiement automatique sur Google Cloud Run

set -e  # Exit on error

echo "🚀 Déploiement CustoFlow sur Google Cloud Run"
echo ""

# Configuration
SERVICE_NAME="custoflow-api"
REGION="us-central1"
MEMORY="1Gi"
CPU="1"
TIMEOUT="300"
MAX_INSTANCES="10"
MIN_INSTANCES="0"

# Vérifier que gcloud est installé
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI n'est pas installé"
    echo "Installez-le depuis: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Vérifier l'authentification
echo "🔐 Vérification de l'authentification..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  Vous n'êtes pas authentifié. Lancement de gcloud auth login..."
    gcloud auth login
fi

# Obtenir le projet actuel
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Aucun projet sélectionné"
    echo "Sélectionnez un projet avec: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Projet: $PROJECT_ID"
echo ""

# Activer les APIs nécessaires
echo "🔧 Activation des APIs nécessaires..."
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
echo "✅ APIs activées"
echo ""

# Vérifier les variables d'environnement
echo "📝 Vérification des variables d'environnement..."
if [ -f .env.gcloud ]; then
    echo "✅ Fichier .env.gcloud trouvé"
    ENV_FLAG="--env-vars-file .env.gcloud"
else
    echo "⚠️  Fichier .env.gcloud non trouvé"
    echo "Les variables d'environnement doivent être définies manuellement"
    ENV_FLAG=""
fi
echo ""

# Déployer
echo "🚀 Déploiement du service..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --max-instances $MAX_INSTANCES \
  --min-instances $MIN_INSTANCES \
  $ENV_FLAG

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Déploiement réussi!"
    echo ""
    
    # Obtenir l'URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    echo "🌐 URL du service: $SERVICE_URL"
    echo ""
    echo "🧪 Testez avec:"
    echo "   curl $SERVICE_URL/health"
    echo ""
    echo "📊 Voir les logs:"
    echo "   gcloud run services logs read $SERVICE_NAME --region $REGION --follow"
else
    echo ""
    echo "❌ Erreur lors du déploiement"
    exit 1
fi

