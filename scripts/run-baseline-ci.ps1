param(
    [string]$PythonExecutable = '.\.venv\Scripts\python.exe',
    [string]$NpmCli = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$webRoot = Join-Path $repoRoot 'apps\web'

$env:TEMP = Join-Path $repoRoot '.temp'
$env:TMP = Join-Path $repoRoot '.temp'
$env:PIP_CACHE_DIR = Join-Path $repoRoot '.cache\pip'
$env:npm_config_cache = Join-Path $repoRoot '.cache\npm'
foreach ($path in @($env:TEMP, $env:PIP_CACHE_DIR, $env:npm_config_cache)) {
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}
function Invoke-Checked {
    param([string]$Name, [scriptblock]$Command)
    Write-Host "::group::$Name"
    & $Command
    $exitCode = $LASTEXITCODE
    Write-Host '::endgroup::'
    if ($exitCode -ne 0) {
        throw "$Name failed with exit code $exitCode"
    }
}

function Invoke-Npm {
    param([string[]]$Arguments)
    if ($NpmCli) {
        & node $NpmCli @Arguments
    } else {
        & npm @Arguments
    }
}

Push-Location $repoRoot
try {
    Invoke-Checked 'Control plane schema' { node scripts/verify-control-plane.mjs }
    Invoke-Checked 'Python dependency integrity' { & $PythonExecutable -m pip check }
    Invoke-Checked 'Locked CAD toolchain' { & $PythonExecutable scripts/verify_toolchain.py }
    Invoke-Checked 'Python unit tests' { & $PythonExecutable -m pytest }
    Invoke-Checked 'Artifact smoke test' { & $PythonExecutable scripts/verify_artifacts.py }
    Invoke-Checked 'Frontend lint' { Invoke-Npm @('--prefix', $webRoot, 'run', 'lint') }
    Invoke-Checked 'Frontend typecheck' { Invoke-Npm @('--prefix', $webRoot, 'run', 'typecheck') }
    Invoke-Checked 'Frontend unit tests' { Invoke-Npm @('--prefix', $webRoot, 'test', '--', '--run') }
    Invoke-Checked 'Frontend production build' { Invoke-Npm @('--prefix', $webRoot, 'run', 'build') }
    Write-Host 'Baseline CI passed.'
} finally {
    Pop-Location
}
