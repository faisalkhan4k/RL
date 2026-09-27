param([switch]$Force)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelsRoot = Join-Path $projectRoot 'data/models'
$modelName = 'vosk-model-small-en-us-0.15'
$modelPath = Join-Path $modelsRoot $modelName
New-Item -ItemType Directory -Force -Path $modelsRoot | Out-Null
if ($Force -or -not (Test-Path -LiteralPath (Join-Path $modelPath 'conf/model.conf'))) {
    $archive = Join-Path $env:TEMP "$modelName.zip"
    Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/$modelName.zip" -OutFile $archive
    if (Test-Path -LiteralPath $modelPath) { Remove-Item -LiteralPath $modelPath -Recurse -Force }
    Expand-Archive -LiteralPath $archive -DestinationPath $modelsRoot -Force
    Remove-Item -LiteralPath $archive -Force
    Write-Host "Installed offline recognition model at $modelPath"
} else { Write-Host "Offline recognition model is already installed at $modelPath" }

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $projectRoot '../..')).Path
$pythonExe = Join-Path $repoRoot '.venv/Scripts/python.exe'
$piperRoot = Join-Path $modelsRoot 'piper'
$piperModel = Join-Path $piperRoot 'en_US-lessac-medium.onnx'
if ($Force -or -not (Test-Path -LiteralPath $piperModel)) {
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create the repository .venv and install the app dependencies first.' }
    New-Item -ItemType Directory -Force -Path $piperRoot | Out-Null
    if ($Force) { Remove-Item -LiteralPath "$piperModel" -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath "$piperModel.json" -Force -ErrorAction SilentlyContinue }
    & $pythonExe -m piper.download_voices --data-dir $piperRoot en_US-lessac-medium
    if ($LASTEXITCODE -ne 0) { throw 'Natural speech model download failed' }
    Write-Host "Installed natural speech model at $piperModel"
} else { Write-Host "Natural speech model is already installed at $piperModel" }
