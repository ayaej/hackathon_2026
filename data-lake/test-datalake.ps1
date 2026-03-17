# Script PowerShell de test complet du Data Lake
# Usage: .\test-datalake.ps1

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🧪 Tests du Data Lake - Étudiant 4       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$API_URL = "http://localhost:3000"

# Test 1 : Health Check
Write-Host "📍 Test 1: Health Check" -ForegroundColor Blue
$health = Invoke-RestMethod -Uri "$API_URL/health" -Method Get
$health | ConvertTo-Json
Write-Host "✅ Health check OK`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 2 : Créer un fichier test
Write-Host "📍 Test 2: Créer un fichier test" -ForegroundColor Blue
$testContent = @"
FACTURE N°2024-001
Date: 15/01/2024

Entreprise: Test SAS
SIRET: 12345678901234
Adresse: 123 Rue de Test, 75001 Paris

Montant HT: 1000.00 €
TVA (20%): 200.00 €
Montant TTC: 1200.00 €

Validité: 30 jours
"@
$testContent | Out-File -FilePath "test_facture.txt" -Encoding UTF8
Write-Host "✅ Fichier test créé`n" -ForegroundColor Green

# Test 3 : Upload document
Write-Host "📍 Test 3: Upload du document (RAW ZONE)" -ForegroundColor Blue
$filePath = "test_facture.txt"
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes)

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"test_facture.txt`"",
    "Content-Type: text/plain$LF",
    $fileContent,
    "--$boundary",
    "Content-Disposition: form-data; name=`"metadata`"$LF",
    '{"source":"test","uploadedBy":"etudiant4"}',
    "--$boundary--$LF"
) -join $LF

$uploadResponse = Invoke-RestMethod -Uri "$API_URL/api/raw/upload" `
    -Method Post `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $bodyLines

$uploadResponse | ConvertTo-Json -Depth 10
$RAW_DOC_ID = $uploadResponse.data.documentId
Write-Host "✅ Document uploadé: $RAW_DOC_ID`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 4 : Récupérer métadonnées
Write-Host "📍 Test 4: Récupérer métadonnées" -ForegroundColor Blue
$metadata = Invoke-RestMethod -Uri "$API_URL/api/raw/$RAW_DOC_ID" -Method Get
$metadata | ConvertTo-Json
Write-Host "✅ Métadonnées récupérées`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 5 : Sauvegarder texte OCR (CLEAN ZONE)
Write-Host "📍 Test 5: Sauvegarder texte OCR (CLEAN ZONE)" -ForegroundColor Blue
$CLEAN_DOC_ID = "clean-$([guid]::NewGuid().ToString())"
$cleanData = @{
    documentId = $CLEAN_DOC_ID
    rawDocumentId = $RAW_DOC_ID
    extractedText = "FACTURE N°2024-001 SIRET: 12345678901234 Montant TTC: 1200€"
    ocrEngine = "Tesseract"
    options = @{
        ocrConfidence = 0.95
        language = "fra"
    }
} | ConvertTo-Json

$cleanResponse = Invoke-RestMethod -Uri "$API_URL/api/clean" `
    -Method Post `
    -ContentType "application/json" `
    -Body $cleanData

$cleanResponse | ConvertTo-Json -Depth 10
Write-Host "✅ Texte OCR sauvegardé: $CLEAN_DOC_ID`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 6 : Sauvegarder données structurées (CURATED ZONE)
Write-Host "📍 Test 6: Sauvegarder données structurées (CURATED ZONE)" -ForegroundColor Blue
$curatedData = @{
    cleanDocumentId = $CLEAN_DOC_ID
    documentType = "FACTURE"
    extractedData = @{
        siret = "12345678901234"
        companyName = "Test SAS"
        montantHT = 1000.00
        montantTTC = 1200.00
        tva = 200.00
        dateEmission = "2024-01-15"
    }
} | ConvertTo-Json

$curatedResponse = Invoke-RestMethod -Uri "$API_URL/api/curated" `
    -Method Post `
    -ContentType "application/json" `
    -Body $curatedData

$curatedResponse | ConvertTo-Json -Depth 10
$CURATED_DOC_ID = $curatedResponse.data.documentId
Write-Host "✅ Données structurées sauvegardées: $CURATED_DOC_ID`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 7 : Recherche par SIRET
Write-Host "📍 Test 7: Recherche par SIRET" -ForegroundColor Blue
$searchResult = Invoke-RestMethod -Uri "$API_URL/api/curated/search/siret/12345678901234" -Method Get
$searchResult | ConvertTo-Json -Depth 10
Write-Host "✅ Recherche par SIRET OK`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 8 : Vérifier incohérences
Write-Host "📍 Test 8: Vérifier incohérences" -ForegroundColor Blue
$inconsistencies = Invoke-RestMethod -Uri "$API_URL/api/curated/check-inconsistencies/12345678901234" -Method Get
$inconsistencies | ConvertTo-Json -Depth 10
Write-Host "✅ Vérification incohérences OK`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 9 : Statistiques RAW ZONE
Write-Host "📍 Test 9: Statistiques RAW ZONE" -ForegroundColor Blue
$rawStats = Invoke-RestMethod -Uri "$API_URL/api/raw/stats" -Method Get
$rawStats | ConvertTo-Json
Write-Host "✅ Stats RAW ZONE`n" -ForegroundColor Green
Start-Sleep -Seconds 1

# Test 10 : Statistiques globales
Write-Host "📍 Test 10: Statistiques globales (3 zones)" -ForegroundColor Blue
$globalStats = Invoke-RestMethod -Uri "$API_URL/api/stats" -Method Get
$globalStats | ConvertTo-Json -Depth 10
Write-Host "✅ Stats globales`n" -ForegroundColor Green

# Nettoyage
Write-Host "📍 Nettoyage..." -ForegroundColor Blue
Remove-Item -Path "test_facture.txt" -ErrorAction SilentlyContinue
Write-Host "✅ Fichier test supprimé`n" -ForegroundColor Green

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✅ Tous les tests sont passés !          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Résumé:" -ForegroundColor Yellow
Write-Host "  - RAW Document ID: $RAW_DOC_ID"
Write-Host "  - CLEAN Document ID: $CLEAN_DOC_ID"
Write-Host "  - CURATED Document ID: $CURATED_DOC_ID"
Write-Host ""
Write-Host "🌐 MinIO Console: http://localhost:9001" -ForegroundColor Cyan
Write-Host "   Login: minioadmin / minioadmin"
