#!/bin/bash
# Script pour créer une branche de sauvegarde avant push

echo "=== Création d'une branche de sauvegarde ==="
echo ""

# Obtenir le nom de la branche actuelle
CURRENT_BRANCH=$(git branch --show-current)
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"

echo "Branche actuelle: $CURRENT_BRANCH"
echo "Création de la branche de sauvegarde: $BACKUP_BRANCH"
echo ""

# Créer la branche de sauvegarde
git checkout -b "$BACKUP_BRANCH"

# Commit tous les changements actuels dans la sauvegarde
git add .
git commit -m "Backup: État avant A/B Testing et QA & Compliance"

# Revenir à la branche originale
git checkout "$CURRENT_BRANCH"

echo ""
echo "✅ Sauvegarde créée: $BACKUP_BRANCH"
echo ""
echo "Pour revenir à cette sauvegarde:"
echo "  git checkout $BACKUP_BRANCH"
echo ""
echo "Vous pouvez maintenant continuer à travailler sur $CURRENT_BRANCH"

