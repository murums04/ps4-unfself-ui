param(
    [string]$PythonPath = '',
    [string]$IsccPath = '',
    [string]$WorkDirectory = '.work/build',
    [string]$OutputDirectory = 'packages'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not $PythonPath) { $PythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (-not $IsccPath) {
    $candidates = @(
        (Join-Path $projectRoot '.tools/InnoSetup/ISCC.exe'),
        'C:/Program Files (x86)/Inno Setup 7/ISCC.exe',
        'C:/Program Files (x86)/Inno Setup 6/ISCC.exe',
        'C:/Program Files/Inno Setup 7/ISCC.exe'
    )
    $IsccPath = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $IsccPath -or -not (Test-Path -LiteralPath $IsccPath)) { throw 'Pass -IsccPath with the full path to ISCC.exe.' }
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Create .venv and install requirements-build.txt first.' }
New-Item -ItemType Directory -Path $WorkDirectory -Force | Out-Null
& $PythonPath -m pytest -q --basetemp (Join-Path $WorkDirectory 'pytest')
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $PythonPath scripts/prepare_assets.py
if ($LASTEXITCODE -ne 0) { throw 'Asset preparation failed.' }
$originalBuildPath = $env:PATH
$originalCachePath = $env:PYINSTALLER_CONFIG_DIR
try {
    # Unrelated tools on PATH can shadow Windows system DLLs during collection.
    $env:PATH = (Split-Path -Parent $PythonPath) + ';' + $env:SystemRoot + '/System32;' + $env:SystemRoot
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $WorkDirectory 'pyinstaller-cache'
    & $PythonPath -m PyInstaller --noconfirm --clean --distpath (Join-Path $WorkDirectory 'dist') --workpath (Join-Path $WorkDirectory 'pyinstaller') packaging/app.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
}
finally {
    $env:PATH = $originalBuildPath
    $env:PYINSTALLER_CONFIG_DIR = $originalCachePath
}
& $PythonPath scripts/package_release.py --iscc $IsccPath --payload (Join-Path $WorkDirectory 'dist/ps4-unfself-ui') --output-dir $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
Write-Output 'BUILD_SUCCEEDED'

