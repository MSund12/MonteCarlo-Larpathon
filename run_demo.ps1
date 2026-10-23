$ErrorActionPreference = 'Stop'
$runtimePath = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$scriptPath = Join-Path $PSScriptRoot 'monte_carlo_demo.py'
$localDependencies = Join-Path $PSScriptRoot '.visualization-deps'
$previousPythonPath = $env:PYTHONPATH
try {
    if (Test-Path -LiteralPath $localDependencies) {
        $env:PYTHONPATH = "$localDependencies;$previousPythonPath"
    }
    if (Test-Path -LiteralPath $runtimePath) {
        & $runtimePath $scriptPath @args
    } else {
        & python $scriptPath @args
    }
    $demoExitCode = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $previousPythonPath
}
exit $demoExitCode
