# Script pour mettre a jour les variables d'environnement sans redeplyer

$ErrorActionPreference = "Stop"

Write-Host "Mise a jour des variables d'environnement Cloud Run" -ForegroundColor Green
Write-Host ""

$SERVICE_NAME = "custoflow-api"
$REGION = "us-central1"

# Demander les valeurs
Write-Host "Entrez les valeurs (appuyez sur Enter pour garder la valeur actuelle):" -ForegroundColor Yellow
Write-Host ""

$googleApiKey = Read-Host "GOOGLE_API_KEY"
$supabaseUrl = Read-Host "SUPABASE_URL"
$supabaseKey = Read-Host "SUPABASE_KEY"
$modelName = Read-Host "MODEL_NAME (defaut: gemini-2.5-flash-lite)"

if (-not $modelName) {
    $modelName = "gemini-2.5-flash-lite"
}

# Construire la commande
$envVars = @()

if ($googleApiKey) {
    $envVars += "GOOGLE_API_KEY=$googleApiKey"
}

if ($supabaseUrl) {
    $envVars += "SUPABASE_URL=$supabaseUrl"
}

if ($supabaseKey) {
    $envVars += "SUPABASE_KEY=$supabaseKey"
}

if ($modelName) {
    $envVars += "MODEL_NAME=$modelName"
}

if ($envVars.Count -eq 0) {
    Write-Host "Aucune variable a mettre a jour" -ForegroundColor Yellow
    exit 0
}

$envVarsString = $envVars -join ","

Write-Host ""
Write-Host "Mise a jour des variables..." -ForegroundColor Cyan
Write-Host "Variables: $envVarsString" -ForegroundColor White
Write-Host ""

gcloud run services update $SERVICE_NAME `
    --region $REGION `
    --update-env-vars $envVarsString

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK Variables mises a jour!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Le service va redemarrer automatiquement avec les nouvelles variables" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "ERREUR: Echec de la mise a jour" -ForegroundColor Red
    exit 1
}

