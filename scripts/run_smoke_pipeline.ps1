$ErrorActionPreference = 'Stop'

$python = $env:PYTHON_EXE
if (-not $python) {
    $python = 'python'
}

if (-not (Test-Path (Join-Path (Get-Location) '.env'))) {
    Write-Host '[WARN] .env not found. Create it and fill DEEPSEEK_API_KEY first.'
    exit 1
}

$env:MIN_POSTS_RELIABLE = '1'
$env:MIN_CLUSTER_POSTS = '1'
$env:MIN_MONTHLY_CLUSTER_POSTS = '1'
$env:DEEPSEEK_BATCH_SIZE = '10'
$env:DEEPSEEK_MAX_TOKENS = '4000'
$env:SAVE_MATPLOTLIB_PLOTS = '0'

function Invoke-Step {
    param(
        [string]$Label,
        [string[]]$CommandArgs
    )
    Write-Host "== $Label =="
    & $python @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Step failed: $Label"
        exit $LASTEXITCODE
    }
}

Write-Host '== Smoke pipeline: Step 02 -> 08 =='
Invoke-Step 'Step 02' @('scripts/02_label_emotions.py', '--mode', 'smoke')
Invoke-Step 'Step 03' @('scripts/03_validate_emotions.py', '--max-samples', '300')
Invoke-Step 'Step 04' @('scripts/04_aggregate_emotions.py')
Invoke-Step 'Step 05' @('scripts/05_detect_anomalies.py')
Invoke-Step 'Step 06' @('scripts/06_cluster_provinces.py')
Invoke-Step 'Step 07' @('scripts/07_cluster_evolution.py')
Invoke-Step 'Step 08' @('scripts/08_prepare_frontend_assets.py')

Write-Host 'Smoke pipeline completed.'
