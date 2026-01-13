param (
    [Parameter(Mandatory = $true)]
    [string]$caseKey
)

# -----------------------------
# Resolve paths
# -----------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$casesRoot = Join-Path $scriptDir "..\data\cases"
$caseRoot  = Join-Path $casesRoot $caseKey

# -----------------------------
# Define folder structure
# -----------------------------
$encryptedImages = Join-Path $caseRoot "encrypted_images"

$pipelineRoot = Join-Path $caseRoot "pipeline"
$sparseFolder = Join-Path $pipelineRoot "sparse"
$denseFolder  = Join-Path $pipelineRoot "dense"
$logsFolder   = Join-Path $pipelineRoot "logs"

$outputFolder = Join-Path $caseRoot "output"

$foldersToCreate = @(
    $caseRoot
    $encryptedImages
    $pipelineRoot
    $sparseFolder
    $denseFolder
    $logsFolder
    $outputFolder
)

# -----------------------------
# Create folders
# -----------------------------
foreach ($folder in $foldersToCreate) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "Created: $folder"
    } else {
        Write-Host "Exists:  $folder"
    }
}

Write-Host "Case folder structure for '$caseKey' created successfully."
