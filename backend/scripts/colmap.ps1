param (
    [Parameter(Mandatory = $true)]
    [string]$caseId,
    [Parameter(Mandatory = $true)]
    [string]$uploadDir
)

# -----------------------------
# Resolve paths
# -----------------------------
$caseRoot  = Join-Path $uploadDir $caseId
$rawImages = Join-Path $caseRoot "raw_images"

# -----------------------------
# Define folder structure
# -----------------------------
$rawImages    = Join-Path $caseRoot "raw_images"

$pipelineRoot = Join-Path $caseRoot "pipeline"
$sparseFolder = Join-Path $pipelineRoot "sparse"
$denseFolder  = Join-Path $pipelineRoot "dense"
$logsFolder   = Join-Path $pipelineRoot "logs"

$outputFolder = Join-Path $caseRoot "output"
$debugFolder  = Join-Path $caseRoot "debug"

$foldersToCreate = @(
    $caseRoot
    $rawImages
    $pipelineRoot
    $sparseFolder
    $denseFolder
    $logsFolder
    $outputFolder
    $debugFolder
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

Write-Host "Case folder structure for '$caseId' ready."

# -----------------------------
# Debug: count files in raw_images
# -----------------------------
if (Test-Path $rawImages) {
    $fileCount = (Get-ChildItem -Path $rawImages -File).Count
} else {
    $fileCount = 0
}

$sizeFile = Join-Path $debugFolder "size.txt"
Set-Content -Path $sizeFile -Value $fileCount

Write-Host "Raw images count: $fileCount"
Write-Host "Written to: $sizeFile"

# -----------------------------
# (Placeholder for COLMAP pipeline)
# -----------------------------
Write-Host "Starting COLMAP pipeline..."

# Example placeholder (replace later with real commands)
Start-Sleep -Seconds 2

Write-Host "COLMAP pipeline finished successfully."