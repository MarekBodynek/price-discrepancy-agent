# Price Discrepancy Agent - Automatic Installer Resources Setup
# This script downloads and prepares Tesseract OCR and Poppler for the Windows installer
# Run this on Windows with: powershell -ExecutionPolicy Bypass -File setup_installer_resources.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Price Discrepancy Agent" -ForegroundColor Cyan
Write-Host "Installer Resources Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$TesseractVersion = "5.3.3.20231005"
$TesseractUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-$TesseractVersion.exe"
$TesseractInstaller = "tesseract-installer.exe"
$TesseractInstallDir = "C:\Program Files\Tesseract-OCR"

$PopplerVersion = "24.08.0-0"
$PopplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v$PopplerVersion/Release-$PopplerVersion.zip"
$PopplerZip = "poppler.zip"

$ProjectRoot = $PSScriptRoot
$InstallerResourcesDir = Join-Path $ProjectRoot "installer_resources"
$TesseractTargetDir = Join-Path $InstallerResourcesDir "tesseract"
$PopplerTargetDir = Join-Path $InstallerResourcesDir "poppler"

# Create installer_resources directory
Write-Host "[1/8] Creating installer_resources directory..." -ForegroundColor Yellow
if (-not (Test-Path $InstallerResourcesDir)) {
    New-Item -ItemType Directory -Path $InstallerResourcesDir | Out-Null
}
Write-Host "[OK] Directory created: $InstallerResourcesDir" -ForegroundColor Green
Write-Host ""

# Download Tesseract installer
Write-Host "[2/8] Downloading Tesseract OCR v$TesseractVersion..." -ForegroundColor Yellow
Write-Host "URL: $TesseractUrl" -ForegroundColor Gray
$TesseractInstallerPath = Join-Path $env:TEMP $TesseractInstaller
try {
    Invoke-WebRequest -Uri $TesseractUrl -OutFile $TesseractInstallerPath -UseBasicParsing
    Write-Host "[OK] Downloaded: $TesseractInstallerPath" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to download Tesseract!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Install Tesseract silently
Write-Host "[3/8] Installing Tesseract OCR (silent mode)..." -ForegroundColor Yellow
Write-Host "Install location: $TesseractInstallDir" -ForegroundColor Gray
try {
    # Silent install with additional languages (eng, slv, pol)
    $installArgs = "/S /D=$TesseractInstallDir"
    Start-Process -FilePath $TesseractInstallerPath -ArgumentList $installArgs -Wait -NoNewWindow

    # Wait for installation to complete
    Start-Sleep -Seconds 3

    if (Test-Path $TesseractInstallDir) {
        Write-Host "[OK] Tesseract installed successfully" -ForegroundColor Green
    } else {
        throw "Installation directory not found"
    }
} catch {
    Write-Host "[ERROR] Failed to install Tesseract!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Copy Tesseract to installer_resources
Write-Host "[4/8] Copying Tesseract files to installer_resources..." -ForegroundColor Yellow
try {
    if (Test-Path $TesseractTargetDir) {
        Remove-Item -Path $TesseractTargetDir -Recurse -Force
    }

    Copy-Item -Path $TesseractInstallDir -Destination $TesseractTargetDir -Recurse -Force

    # Verify critical files
    $tesseractExe = Join-Path $TesseractTargetDir "tesseract.exe"
    $engData = Join-Path $TesseractTargetDir "tessdata\eng.traineddata"

    if ((Test-Path $tesseractExe) -and (Test-Path $engData)) {
        Write-Host "[OK] Tesseract files copied successfully" -ForegroundColor Green
        Write-Host "  - tesseract.exe: OK" -ForegroundColor Gray
        Write-Host "  - tessdata/eng.traineddata: OK" -ForegroundColor Gray

        # Check for Slovenian and Polish
        $slvData = Join-Path $TesseractTargetDir "tessdata\slv.traineddata"
        $polData = Join-Path $TesseractTargetDir "tessdata\pol.traineddata"

        if (Test-Path $slvData) {
            Write-Host "  - tessdata/slv.traineddata: OK" -ForegroundColor Gray
        } else {
            Write-Host "  - tessdata/slv.traineddata: MISSING (optional)" -ForegroundColor Yellow
        }

        if (Test-Path $polData) {
            Write-Host "  - tessdata/pol.traineddata: OK" -ForegroundColor Gray
        } else {
            Write-Host "  - tessdata/pol.traineddata: MISSING (optional)" -ForegroundColor Yellow
        }
    } else {
        throw "Critical files missing after copy"
    }
} catch {
    Write-Host "[ERROR] Failed to copy Tesseract files!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Uninstall Tesseract
Write-Host "[5/8] Uninstalling Tesseract from system..." -ForegroundColor Yellow
try {
    $uninstallerPath = Join-Path $TesseractInstallDir "unins000.exe"
    if (Test-Path $uninstallerPath) {
        Start-Process -FilePath $uninstallerPath -ArgumentList "/VERYSILENT" -Wait -NoNewWindow
        Start-Sleep -Seconds 2
        Write-Host "[OK] Tesseract uninstalled from system" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Uninstaller not found, skipping..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Failed to uninstall Tesseract (not critical)" -ForegroundColor Yellow
}

# Cleanup installer
if (Test-Path $TesseractInstallerPath) {
    Remove-Item -Path $TesseractInstallerPath -Force
}
Write-Host ""

# Download Poppler
Write-Host "[6/8] Downloading Poppler v$PopplerVersion..." -ForegroundColor Yellow
Write-Host "URL: $PopplerUrl" -ForegroundColor Gray
$PopplerZipPath = Join-Path $env:TEMP $PopplerZip
try {
    Invoke-WebRequest -Uri $PopplerUrl -OutFile $PopplerZipPath -UseBasicParsing
    Write-Host "[OK] Downloaded: $PopplerZipPath" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to download Poppler!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Extract Poppler
Write-Host "[7/8] Extracting Poppler to installer_resources..." -ForegroundColor Yellow
try {
    if (Test-Path $PopplerTargetDir) {
        Remove-Item -Path $PopplerTargetDir -Recurse -Force
    }

    $TempExtractDir = Join-Path $env:TEMP "poppler_extract"
    if (Test-Path $TempExtractDir) {
        Remove-Item -Path $TempExtractDir -Recurse -Force
    }

    # Extract ZIP
    Expand-Archive -Path $PopplerZipPath -DestinationPath $TempExtractDir -Force

    # Find poppler-XX.XX.X directory
    $PopplerSubDir = Get-ChildItem -Path $TempExtractDir -Directory | Select-Object -First 1

    if ($PopplerSubDir) {
        Copy-Item -Path $PopplerSubDir.FullName -Destination $PopplerTargetDir -Recurse -Force

        # Verify critical files
        $pdftoppmExe = Join-Path $PopplerTargetDir "Library\bin\pdftoppm.exe"

        if (Test-Path $pdftoppmExe) {
            Write-Host "[OK] Poppler extracted successfully" -ForegroundColor Green
            Write-Host "  - Library/bin/pdftoppm.exe: OK" -ForegroundColor Gray
        } else {
            throw "pdftoppm.exe not found after extraction"
        }
    } else {
        throw "Poppler subdirectory not found in ZIP"
    }

    # Cleanup
    Remove-Item -Path $TempExtractDir -Recurse -Force
    Remove-Item -Path $PopplerZipPath -Force

} catch {
    Write-Host "[ERROR] Failed to extract Poppler!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Final verification
Write-Host "[8/8] Final verification..." -ForegroundColor Yellow
$allOk = $true

# Check Tesseract
$tesseractExe = Join-Path $TesseractTargetDir "tesseract.exe"
if (Test-Path $tesseractExe) {
    $tesseractSize = (Get-Item $tesseractExe).Length / 1MB
    Write-Host "[OK] Tesseract: $tesseractExe ($([math]::Round($tesseractSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Tesseract executable not found!" -ForegroundColor Red
    $allOk = $false
}

# Check Poppler
$pdftoppmExe = Join-Path $PopplerTargetDir "Library\bin\pdftoppm.exe"
if (Test-Path $pdftoppmExe) {
    $popplerSize = (Get-Item $pdftoppmExe).Length / 1MB
    Write-Host "[OK] Poppler: $pdftoppmExe ($([math]::Round($popplerSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Poppler executable not found!" -ForegroundColor Red
    $allOk = $false
}

# Check tessdata languages
$tessdataDir = Join-Path $TesseractTargetDir "tessdata"
$languages = @("eng", "slv", "pol")
foreach ($lang in $languages) {
    $langFile = Join-Path $tessdataDir "$lang.traineddata"
    if (Test-Path $langFile) {
        $langSize = (Get-Item $langFile).Length / 1MB
        Write-Host "[OK] Language $lang`: $langFile ($([math]::Round($langSize, 2)) MB)" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Language $lang not found (optional)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allOk) {
    Write-Host "SUCCESS! Installer resources ready." -ForegroundColor Green
    Write-Host ""
    Write-Host "Structure:" -ForegroundColor White
    Write-Host "installer_resources/" -ForegroundColor Gray
    Write-Host "├── tesseract/" -ForegroundColor Gray
    Write-Host "│   ├── tesseract.exe" -ForegroundColor Gray
    Write-Host "│   └── tessdata/" -ForegroundColor Gray
    Write-Host "│       ├── eng.traineddata" -ForegroundColor Gray
    Write-Host "│       ├── slv.traineddata" -ForegroundColor Gray
    Write-Host "│       └── pol.traineddata" -ForegroundColor Gray
    Write-Host "└── poppler/" -ForegroundColor Gray
    Write-Host "    └── Library/bin/pdftoppm.exe" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next step: Run build_installer.bat" -ForegroundColor Yellow
} else {
    Write-Host "FAILED! Some resources are missing." -ForegroundColor Red
    Write-Host "Please check the errors above." -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
