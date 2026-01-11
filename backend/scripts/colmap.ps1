# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$sourceFile = Join-Path $scriptDir "smth.txt"
$targetFile = Join-Path $scriptDir "congrats.txt"

if (Test-Path $sourceFile) {
    Rename-Item -Path $sourceFile -NewName "congrats.txt" -Force
    Write-Output "File renamed successfully."
} else {
    Write-Error "smth.txt not found."
    exit 1
}
