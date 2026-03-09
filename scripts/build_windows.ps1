param(
    [string]$Python = "python",
    [switch]$Clean,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$specPath = Join-Path $repoRoot "packaging\windows\contextpacker.spec"
$issPath = Join-Path $repoRoot "packaging\windows\contextpacker.iss"
$distRoot = Join-Path $repoRoot "dist"
$bundleDir = Join-Path $distRoot "ContextPacker"
$releaseDir = Join-Path $repoRoot "release"

function Get-AppVersion {
    $version = & $Python -c "import pathlib, sys; sys.path.insert(0, str(pathlib.Path('src').resolve())); import contextpacker; print(contextpacker.__version__)"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to determine the ContextPacker version."
    }
    return $version
}

function Get-IsccPath {
    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    return $null
}

Push-Location $repoRoot
try {
    if ($Clean) {
        Remove-Item $distRoot -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item (Join-Path $repoRoot "build") -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item $releaseDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    & $Python -m pip install -e ".[build]"
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed."
    }

    & $Python -m PyInstaller --noconfirm --clean $specPath
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $version = (Get-AppVersion).Trim()
    Write-Host "Built bundle:" $bundleDir

    if ($SkipInstaller) {
        return
    }

    $iscc = Get-IsccPath
    if (-not $iscc) {
        throw "Inno Setup 6 was not found. Install it or rerun with -SkipInstaller."
    }

    New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
    & $iscc "/DRepoRoot=$repoRoot" "/DDistDir=$bundleDir" "/DAppVersion=$version" $issPath
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup packaging failed."
    }

    Write-Host "Built installer:" (Join-Path $releaseDir "ContextPacker-$version-Setup.exe")
}
finally {
    Pop-Location
}
