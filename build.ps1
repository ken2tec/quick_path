# Build Script
$PG_NAME = "quick_path"
$VERSION = "1.4.2604"
$EXE_NAME = "$PG_NAME.$VERSION"
$ICON_PATH = "assets/ken2tec.ico"

# conda activate
$condaPath = "conda"
if (Get-Command "conda" -ErrorAction SilentlyContinue) {
    Write-Host "Activate Conda Environment to 'dev'..."
    conda deactivate
    conda activate dev
}

Write-Host "Starting build for $EXE_NAME..." -ForegroundColor Cyan

pyinstaller `
    --noconfirm --onefile `
    --name "$EXE_NAME" `
    --icon "$ICON_PATH" `
    --exclude-module pandas `
    --exclude-module numpy `
    --exclude-module matplotlib `
    --exclude-module tkinter `
    --exclude-module scipy `
    --exclude-module IPython `
    --exclude-module notebook `
    main.py

# Copy ini file
$SOURCE_INI = "main.ini"
$TARGET_DIR = "dist"
$TARGET_INI = Join-Path $TARGET_DIR "$PG_NAME.ini"

if (Test-Path $SOURCE_INI) {
    if (-not (Test-Path $TARGET_DIR)) {
        New-Item -ItemType Directory -Path $TARGET_DIR | Out-Null
    }
    Copy-Item -Path $SOURCE_INI -Destination $TARGET_INI -Force
    Write-Host "[Success] Copied from $SOURCE_INI to $TARGET_DI." -ForegroundColor Green
} else {
    Write-Host "[Warning] Not found $SOURCE_INI." -ForegroundColor Yellow
}

Write-Host "--- Build Process Completed ---" -ForegroundColor Cyan
pause
