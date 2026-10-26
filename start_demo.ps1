param([switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$catalogProject = $PSScriptRoot
$catalogPython = Join-Path $catalogProject '.venv\Scripts\python.exe'
$catalogRuntime = Join-Path $catalogProject 'runtime'
if (-not (Test-Path -LiteralPath $catalogPython)) { throw 'The project Python environment is missing. See local_demo/README.md.' }
New-Item -ItemType Directory -Path $catalogRuntime -Force | Out-Null

try {
    $catalogModels = Invoke-RestMethod 'http://127.0.0.1:11435/api/tags' -TimeoutSec 2
} catch {
    $catalogOllama = (Get-Command ollama -ErrorAction Stop).Source
    $env:OLLAMA_HOST = '127.0.0.1:11435'
    $env:OLLAMA_LLM_LIBRARY = 'cuda_v12'
    $env:OLLAMA_NO_CLOUD = '1'
    $env:OLLAMA_NUM_PARALLEL = '1'
    $env:OLLAMA_CONTEXT_LENGTH = '8192'
    $env:OLLAMA_KEEP_ALIVE = '30m'
    Start-Process -FilePath $catalogOllama -ArgumentList 'serve' -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $catalogRuntime 'ollama.stdout.log') `
        -RedirectStandardError (Join-Path $catalogRuntime 'ollama.stderr.log') | Out-Null
}

$env:CATALOG_OLLAMA_URL = 'http://127.0.0.1:11435'
$catalogRunning = $false
try {
    $catalogHealth = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
    $catalogRunning = $catalogHealth.status -eq 'ok' -and $catalogHealth.datasets -eq 3
} catch { }
if (-not $catalogRunning) {
    if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) {
        throw 'Port 8000 is occupied by another service.'
    }
    $catalogProcess = Start-Process -FilePath $catalogPython `
        -ArgumentList '-m uvicorn local_demo.app:app --host 127.0.0.1 --port 8000 --no-access-log' `
        -WorkingDirectory $catalogProject -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $catalogRuntime 'web.stdout.log') `
        -RedirectStandardError (Join-Path $catalogRuntime 'web.stderr.log')
    $catalogDeadline = (Get-Date).AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 300
        try { $catalogHealth = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2; $catalogRunning = $true } catch { }
    } until ($catalogRunning -or (Get-Date) -gt $catalogDeadline)
    if (-not $catalogRunning) { throw 'Website did not start. See runtime/web.stderr.log.' }
}
Write-Output 'Website: http://127.0.0.1:8000'
Write-Output 'Web API documentation: http://127.0.0.1:8000/docs'
Write-Output 'Local model endpoint: http://127.0.0.1:11435'
if ($OpenBrowser) { Start-Process 'http://127.0.0.1:8000' }

