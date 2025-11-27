# Script PowerShell pour créer une branche de sauvegarde avant push

Write-Host "=== Création d'une branche de sauvegarde ===" -ForegroundColor Cyan
Write-Host ""

# Obtenir le nom de la branche actuelle
$currentBranch = git branch --show-current
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupBranch = "backup-$timestamp"

Write-Host "Branche actuelle: $currentBranch" -ForegroundColor Yellow
Write-Host "Création de la branche de sauvegarde: $backupBranch" -ForegroundColor Yellow
Write-Host ""

# Créer la branche de sauvegarde
git checkout -b $backupBranch

# Commit tous les changements actuels dans la sauvegarde
git add .
git commit -m "Backup: État avant A/B Testing et QA & Compliance"

# Revenir à la branche originale
git checkout $currentBranch

Write-Host ""
Write-Host "✅ Sauvegarde créée: $backupBranch" -ForegroundColor Green
Write-Host ""
Write-Host "Pour revenir à cette sauvegarde:" -ForegroundColor Cyan
Write-Host "  git checkout $backupBranch" -ForegroundColor White
Write-Host ""
Write-Host "Vous pouvez maintenant continuer à travailler sur $currentBranch" -ForegroundColor Green

