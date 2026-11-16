# Build on Windows; -Install also copies the result off WSL to a native Windows directory.
param([switch]$Install)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$entry = Join-Path $root 'launcher.pyw'
$data = Join-Path $root 'src\wordflash\data\verses.json'
if (-not (Test-Path $python)) { throw 'Create the Windows venv and install .[dev,build] first.' }
if ((Get-FileHash $data -Algorithm SHA256).Hash.ToLowerInvariant() -ne '7f989fee93fdc321ae5d0c8f51c841267956aea221d80bc04f1473ead5bddcec') {
    throw 'The verse corpus differs from the pinned original.'
}
Push-Location $root
try {
    & $python -m PyInstaller --noconfirm --clean --onedir --windowed --name WordFlashPython --collect-data wordflash --distpath (Join-Path $root 'dist') --workpath (Join-Path $root 'build') --specpath $root $entry
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
    Write-Host (Join-Path $root 'dist\WordFlashPython\WordFlashPython.exe')
    if ($Install) {
        $destination = Join-Path $env:LOCALAPPDATA 'Programs\WordFlashPython'
        if (Test-Path $destination) { throw "Install destination already exists: $destination. Stop the running app and choose how to replace it." }
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $root 'dist\WordFlashPython') -Destination $destination -Recurse
        Write-Host "Installed to $(Join-Path $destination 'WordFlashPython.exe')"
    }
}
finally {
    Pop-Location
}
