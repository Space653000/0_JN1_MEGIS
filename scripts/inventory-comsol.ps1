$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$outputDir = Join-Path $repoRoot 'artifacts\g0-sim'
$outputPath = Join-Path $outputDir 'inventory.json'

$commands = @('comsol', 'comsolbatch', 'mphserver') | ForEach-Object {
    $command = Get-Command $_ -ErrorAction SilentlyContinue
    [ordered]@{
        name = $_
        found = [bool]$command
        path = if ($command) { $command.Source } else { $null }
    }
}

$standardPaths = @(
    'C:\Program Files\COMSOL',
    'C:\Program Files (x86)\COMSOL',
    'C:\COMSOL'
) | ForEach-Object {
    [ordered]@{ path = $_; exists = Test-Path -LiteralPath $_ }
}

$environmentVariables = @(
    'COMSOL',
    'COMSOL_ROOT',
    'COMSOL_HOME',
    'LMCOMSOL_LICENSE_FILE'
) | ForEach-Object {
    [ordered]@{
        name = $_
        present = [bool][Environment]::GetEnvironmentVariable($_)
    }
}

$registryKeys = @(
    'HKLM:\SOFTWARE\COMSOL',
    'HKLM:\SOFTWARE\WOW6432Node\COMSOL',
    'HKCU:\SOFTWARE\COMSOL'
) | ForEach-Object {
    [ordered]@{ path = $_; exists = Test-Path -LiteralPath $_ }
}

$installationDetected = @($commands | Where-Object found).Count -gt 0 -or
    @($standardPaths | Where-Object exists).Count -gt 0 -or
    @($registryKeys | Where-Object exists).Count -gt 0
$licenseConfigurationDetected = @($environmentVariables | Where-Object present).Count -gt 0

$inventory = [ordered]@{
    schemaVersion = '1.0.0'
    workItem = 'G0-SIM-001'
    inspectedAt = [DateTime]::UtcNow.ToString('o')
    scope = 'read_only_local_inventory'
    commands = $commands
    standardPaths = $standardPaths
    environmentVariables = $environmentVariables
    registryKeys = $registryKeys
    summary = [ordered]@{
        installationDetected = $installationDetected
        licenseConfigurationDetected = $licenseConfigurationDetected
        batchExecutableDetected = [bool]($commands | Where-Object { $_.name -eq 'comsolbatch' -and $_.found })
        decision = if ($installationDetected -and $licenseConfigurationDetected) { 'requires_manual_license_validation' } else { 'out_of_scope' }
        blocksCoreGate = $false
    }
    privacy = [ordered]@{
        environmentVariableValuesCaptured = $false
        licenseContentsCaptured = $false
    }
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$inventory | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outputPath -Encoding utf8
Write-Output "COMSOL inventory written to $outputPath"
Write-Output "Decision: $($inventory.summary.decision); blocks core gate: $($inventory.summary.blocksCoreGate)"

