# installer poppler pour windows
# IA GENERATED - vérifié le 2024-06-17 par Matis

param(
    [string]$ZipPath = "",
    [string]$InstallDir = "",
    [switch]$SetUserEnv = $true
)

$ErrorActionPreference = "Stop"

function Ecrire-Info {
    param([string]$Message)
    Write-Host "[info] $Message"
}

function Ecrire-Succes {
    param([string]$Message)
    Write-Host "[ok] $Message" -ForegroundColor Green
}

function Ecrire-Alerte {
    param([string]$Message)
    Write-Host "[alerte] $Message" -ForegroundColor Yellow
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($ZipPath)) {
    $zipTrouve = Get-ChildItem -Path $scriptDir -Filter "*.zip" | Select-Object -First 1
    if (-not $zipTrouve) {
        throw "aucun fichier zip poppler trouve dans $scriptDir"
    }
    $ZipPath = $zipTrouve.FullName
}

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $InstallDir = Join-Path $scriptDir "poppler"
}

if (-not (Test-Path $ZipPath)) {
    throw "zip introuvable: $ZipPath"
}

Ecrire-Info "zip utilise: $ZipPath"
Ecrire-Info "dossier d'installation: $InstallDir"

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

$extractRoot = Join-Path $InstallDir "_extract_tmp"
if (Test-Path $extractRoot) {
    Remove-Item -Path $extractRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null

Ecrire-Info "decompression en cours"
Expand-Archive -Path $ZipPath -DestinationPath $extractRoot -Force

$binDir = $null
$pdfinfo = Get-ChildItem -Path $extractRoot -Recurse -Filter "pdfinfo.exe" | Select-Object -First 1
if ($pdfinfo) {
    $binDir = $pdfinfo.Directory.FullName
}

if (-not $binDir) {
    throw "pdfinfo.exe introuvable apres extraction"
}

$sourceRoot = Split-Path -Parent (Split-Path -Parent $binDir)
$targetRoot = Join-Path $InstallDir "current"

if (Test-Path $targetRoot) {
    Remove-Item -Path $targetRoot -Recurse -Force
}
Copy-Item -Path $sourceRoot -Destination $targetRoot -Recurse -Force

$finalBin = Join-Path $targetRoot "Library\bin"
if (-not (Test-Path (Join-Path $finalBin "pdfinfo.exe"))) {
    $pdfinfoFinal = Get-ChildItem -Path $targetRoot -Recurse -Filter "pdfinfo.exe" | Select-Object -First 1
    if (-not $pdfinfoFinal) {
        throw "impossible de localiser pdfinfo.exe dans l'installation finale"
    }
    $finalBin = $pdfinfoFinal.Directory.FullName
}

$env:POPPLER_PATH = $finalBin
Ecrire-Succes "variable de session definie: POPPLER_PATH=$finalBin"

if ($SetUserEnv) {
    [Environment]::SetEnvironmentVariable("POPPLER_PATH", $finalBin, "User")
    Ecrire-Succes "variable utilisateur enregistree: POPPLER_PATH"
}

$pathUser = [Environment]::GetEnvironmentVariable("Path", "User")
if ($pathUser -notlike "*$finalBin*") {
    $nouveauPath = if ([string]::IsNullOrWhiteSpace($pathUser)) { $finalBin } else { "$pathUser;$finalBin" }
    [Environment]::SetEnvironmentVariable("Path", $nouveauPath, "User")
    Ecrire-Succes "dossier ajoute au path utilisateur"
} else {
    Ecrire-Info "dossier deja present dans le path utilisateur"
}

if (Test-Path $extractRoot) {
    Remove-Item -Path $extractRoot -Recurse -Force
}

Ecrire-Succes "installation terminee"
Ecrire-Info "test recommande: python .\generatePDF.py"
