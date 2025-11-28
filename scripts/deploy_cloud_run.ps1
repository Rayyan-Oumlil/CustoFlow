# Script de deploiement automatique sur Google Cloud Run (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Deploiement CustoFlow sur Google Cloud Run" -ForegroundColor Green
Write-Host ""

# Configuration
$SERVICE_NAME = "custoflow-api"
$REGION = "us-central1"
$MEMORY = "1Gi"
$CPU = "1"
$TIMEOUT = "300"
$MAX_INSTANCES = "10"
$MIN_INSTANCES = "0"

# Verifier que gcloud est installe
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "ERREUR: gcloud CLI n'est pas installe" -ForegroundColor Red
    Write-Host "Installez-le depuis: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Verifier l'authentification
Write-Host "Verification de l'authentification..." -ForegroundColor Cyan
$activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $activeAccount) {
    Write-Host "ATTENTION: Vous n'etes pas authentifie. Lancement de gcloud auth login..." -ForegroundColor Yellow
    gcloud auth login
}

# Obtenir le projet actuel
$PROJECT_ID = gcloud config get-value project 2>$null
if (-not $PROJECT_ID) {
    Write-Host "ERREUR: Aucun projet selectionne" -ForegroundColor Red
    Write-Host "Selectionnez un projet avec: gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK Projet: $PROJECT_ID" -ForegroundColor Green
Write-Host ""

# Activer les APIs necessaires
Write-Host "Activation des APIs necessaires..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
Write-Host "OK APIs activees" -ForegroundColor Green
Write-Host ""

# Verifier les variables d'environnement
Write-Host "Verification des variables d'environnement..." -ForegroundColor Cyan
$envFile = ".env.gcloud"
$envVars = @()

if (Test-Path $envFile) {
    Write-Host "OK Fichier .env.gcloud trouve" -ForegroundColor Green
    
    # Lire et parser le fichier .env
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        # Ignorer les commentaires et lignes vides
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match "^([^=]+)=(.*)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Ignorer les valeurs placeholder
                if ($value -and $value -ne "your_google_api_key_here" -and $value -ne "your_supabase_url_here" -and $value -ne "your_supabase_key_here") {
                    # Echapper les valeurs qui contiennent des virgules ou des espaces
                    if ($value -match "[, ]") {
                        $value = "`"$value`""
                    }
                    $envVars += "$key=$value"
                }
            }
        }
    }
    
    if ($envVars.Count -eq 0) {
        Write-Host "ATTENTION: Aucune variable d'environnement valide trouvee dans .env.gcloud" -ForegroundColor Yellow
        Write-Host "Assurez-vous d'avoir rempli les valeurs" -ForegroundColor Yellow
    } else {
        Write-Host "OK $($envVars.Count) variable(s) d'environnement trouvee(s)" -ForegroundColor Green
    }
} else {
    Write-Host "ATTENTION: Fichier .env.gcloud non trouve" -ForegroundColor Yellow
    Write-Host "Les variables d'environnement doivent etre definies manuellement" -ForegroundColor Yellow
}
Write-Host ""

# Deployer
Write-Host "Deploiement du service..." -ForegroundColor Cyan
$deployCommand = "gcloud run deploy $SERVICE_NAME --source . --platform managed --region $REGION --allow-unauthenticated --memory $MEMORY --cpu $CPU --timeout $TIMEOUT --max-instances $MAX_INSTANCES --min-instances $MIN_INSTANCES"

if ($envVars.Count -gt 0) {
    $envVarsString = $envVars -join ","
    $deployCommand += " --set-env-vars `"$envVarsString`""
}

Invoke-Expression $deployCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK Deploiement reussi!" -ForegroundColor Green
    Write-Host ""
    
    # Obtenir l'URL
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
    Write-Host "URL du service: $SERVICE_URL" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Testez avec:" -ForegroundColor Yellow
    Write-Host "   curl $SERVICE_URL/health" -ForegroundColor White
    Write-Host ""
    Write-Host "Voir les logs:" -ForegroundColor Yellow
    Write-Host "   gcloud run services logs read $SERVICE_NAME --region $REGION --follow" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "ERREUR: Erreur lors du deploiement" -ForegroundColor Red
    exit 1
}
