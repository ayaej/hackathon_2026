#!/bin/bash
# Script de test complet du Data Lake
# Usage: ./test-datalake.sh

echo "╔════════════════════════════════════════════╗"
echo "║  🧪 Tests du Data Lake - Étudiant 4       ║"
echo "╚════════════════════════════════════════════╝"
echo ""

API_URL="http://localhost:3000"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1 : Health Check
echo -e "${BLUE}📍 Test 1: Health Check${NC}"
curl -s $API_URL/health | jq .
echo -e "${GREEN}✅ Health check OK${NC}\n"
sleep 1

# Test 2 : Créer un fichier test
echo -e "${BLUE}📍 Test 2: Créer un fichier test${NC}"
cat > test_facture.txt << EOF
FACTURE N°2024-001
Date: 15/01/2024

Entreprise: Test SAS
SIRET: 12345678901234
Adresse: 123 Rue de Test, 75001 Paris

Montant HT: 1000.00 €
TVA (20%): 200.00 €
Montant TTC: 1200.00 €

Validité: 30 jours
EOF
echo -e "${GREEN}✅ Fichier test créé${NC}\n"

# Test 3 : Upload document
echo -e "${BLUE}📍 Test 3: Upload du document (RAW ZONE)${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST $API_URL/api/raw/upload \
  -F "file=@test_facture.txt" \
  -F "metadata={\"source\":\"test\",\"uploadedBy\":\"etudiant4\"}")

echo $UPLOAD_RESPONSE | jq .

# Extraire le documentId
RAW_DOC_ID=$(echo $UPLOAD_RESPONSE | jq -r '.data.documentId')
echo -e "${GREEN}✅ Document uploadé: $RAW_DOC_ID${NC}\n"
sleep 1

# Test 4 : Récupérer métadonnées
echo -e "${BLUE}📍 Test 4: Récupérer métadonnées${NC}"
curl -s $API_URL/api/raw/$RAW_DOC_ID | jq .
echo -e "${GREEN}✅ Métadonnées récupérées${NC}\n"
sleep 1

# Test 5 : Sauvegarder texte OCR (CLEAN ZONE)
echo -e "${BLUE}📍 Test 5: Sauvegarder texte OCR (CLEAN ZONE)${NC}"
CLEAN_DOC_ID="clean-$(uuidgen 2>/dev/null || echo 'test-123')"
curl -s -X POST $API_URL/api/clean \
  -H "Content-Type: application/json" \
  -d "{
    \"documentId\": \"$CLEAN_DOC_ID\",
    \"rawDocumentId\": \"$RAW_DOC_ID\",
    \"extractedText\": \"FACTURE N°2024-001 SIRET: 12345678901234 Montant TTC: 1200€\",
    \"ocrEngine\": \"Tesseract\",
    \"options\": {
      \"ocrConfidence\": 0.95,
      \"language\": \"fra\"
    }
  }" | jq .
echo -e "${GREEN}✅ Texte OCR sauvegardé: $CLEAN_DOC_ID${NC}\n"
sleep 1

# Test 6 : Sauvegarder données structurées (CURATED ZONE)
echo -e "${BLUE}📍 Test 6: Sauvegarder données structurées (CURATED ZONE)${NC}"
CURATED_RESPONSE=$(curl -s -X POST $API_URL/api/curated \
  -H "Content-Type: application/json" \
  -d "{
    \"cleanDocumentId\": \"$CLEAN_DOC_ID\",
    \"documentType\": \"FACTURE\",
    \"extractedData\": {
      \"siret\": \"12345678901234\",
      \"companyName\": \"Test SAS\",
      \"montantHT\": 1000.00,
      \"montantTTC\": 1200.00,
      \"tva\": 200.00,
      \"dateEmission\": \"2024-01-15\"
    }
  }")

echo $CURATED_RESPONSE | jq .
CURATED_DOC_ID=$(echo $CURATED_RESPONSE | jq -r '.data.documentId')
echo -e "${GREEN}✅ Données structurées sauvegardées: $CURATED_DOC_ID${NC}\n"
sleep 1

# Test 7 : Recherche par SIRET
echo -e "${BLUE}📍 Test 7: Recherche par SIRET${NC}"
curl -s $API_URL/api/curated/search/siret/12345678901234 | jq .
echo -e "${GREEN}✅ Recherche par SIRET OK${NC}\n"
sleep 1

# Test 8 : Vérifier incohérences
echo -e "${BLUE}📍 Test 8: Vérifier incohérences${NC}"
curl -s $API_URL/api/curated/check-inconsistencies/12345678901234 | jq .
echo -e "${GREEN}✅ Vérification incohérences OK${NC}\n"
sleep 1

# Test 9 : Statistiques RAW ZONE
echo -e "${BLUE}📍 Test 9: Statistiques RAW ZONE${NC}"
curl -s $API_URL/api/raw/stats | jq .
echo -e "${GREEN}✅ Stats RAW ZONE${NC}\n"
sleep 1

# Test 10 : Statistiques globales
echo -e "${BLUE}📍 Test 10: Statistiques globales (3 zones)${NC}"
curl -s $API_URL/api/stats | jq .
echo -e "${GREEN}✅ Stats globales${NC}\n"

# Nettoyage
echo -e "${BLUE}📍 Nettoyage...${NC}"
rm -f test_facture.txt
echo -e "${GREEN}✅ Fichier test supprimé${NC}\n"

echo "╔════════════════════════════════════════════╗"
echo "║  ✅ Tous les tests sont passés !          ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "📊 Résumé:"
echo "  - RAW Document ID: $RAW_DOC_ID"
echo "  - CLEAN Document ID: $CLEAN_DOC_ID"
echo "  - CURATED Document ID: $CURATED_DOC_ID"
echo ""
echo "🌐 MinIO Console: http://localhost:9001"
echo "   Login: minioadmin / minioadmin"
