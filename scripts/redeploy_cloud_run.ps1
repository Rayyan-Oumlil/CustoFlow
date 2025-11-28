# Script pour supprimer et recréer le service Cloud Run (solution radicale)

$ErrorActionPreference = "Stop"

Write-Host "⚠️  ATTENTION: Ce script va SUPPRIMER et RECREER le service" -ForegroundColor Red
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour annuler, ou Entree pour continuer..." -ForegroundColor Yellow
Read-Host

Write-Host "🗑️  Suppression du service existant..." -ForegroundColor Cyan
gcloud run services delete custoflow-api --region us-central1 --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Service supprime" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Creation d'un nouveau service..." -ForegroundColor Cyan
    Write-Host ""
    
    # Utiliser le script de deploiement normal
    .\scripts\deploy_cloud_run.ps1
} else {
    Write-Host "❌ Erreur lors de la suppression" -ForegroundColor Red
    Write-Host "Le service n'existe peut-etre pas, on continue avec le deploiement normal..." -ForegroundColor Yellow
    Write-Host ""
    .\scripts\deploy_cloud_run.ps1
}

