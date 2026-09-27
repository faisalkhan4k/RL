param([switch]$WithModel, [switch]$WithPolicies, [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $projectRoot '../..')).Path
$pythonExe = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create the repository .venv and install this app first. See README.md.' }
if ($WithModel -or $WithPolicies) {
    $strategyPath = Join-Path $projectRoot 'artifacts/hrl/strategy.zip'
    $voicePath = Join-Path $projectRoot 'artifacts/hrl/voice.zip'
    if (-not (Test-Path -LiteralPath $strategyPath) -or -not (Test-Path -LiteralPath $voicePath)) { throw 'Train the policies first: python -m sales_agent.hrl.train' }
    $env:SALES_STRATEGY_POLICY = $strategyPath
    $env:SALES_VOICE_POLICY = $voicePath
}
$serverArgs = @('-m','uvicorn','sales_agent.app:create_app','--factory','--host','127.0.0.1','--port',"$Port",'--workers','1','--no-access-log')
$environmentFile = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $environmentFile) { $serverArgs += @('--env-file',$environmentFile) }
& $pythonExe @serverArgs
