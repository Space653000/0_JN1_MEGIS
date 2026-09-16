$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$freeCadRoot = Join-Path $repoRoot 'tools\freecad\FreeCAD_1.1.3-Windows-x86_64-py311'
$freeCadCmd = Join-Path $freeCadRoot 'bin\freecadcmd.exe'
$spikeScript = Join-Path $repoRoot 'spikes\g0_freecad\techdraw_spike.py'
$userConfig = Join-Path $repoRoot '.cache\freecad\user.cfg'
$systemConfig = Join-Path $repoRoot '.cache\freecad\system.cfg'
$verification = Join-Path $repoRoot 'artifacts\g0-freecad\verification.json'

foreach ($requiredPath in @($freeCadCmd, $spikeScript)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required FreeCAD spike input is missing: $requiredPath"
    }
}

$env:TEMP = Join-Path $repoRoot '.temp'
$env:TMP = Join-Path $repoRoot '.temp'
$escapedScript = $spikeScript.Replace("'", "''")
$pythonCommand = "_megis_result = __import__('runpy').run_path(r'$escapedScript', run_name='__main__')"

$pythonCommand | & $freeCadCmd -c --user-cfg $userConfig --system-cfg $systemConfig
if ($LASTEXITCODE -ne 0) {
    throw "FreeCADCmd exited with code $LASTEXITCODE"
}
if (-not (Test-Path -LiteralPath $verification -PathType Leaf)) {
    throw "FreeCAD spike did not produce verification evidence: $verification"
}
