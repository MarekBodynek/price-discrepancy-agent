# Tworzenie instalatora Windows dla Price Discrepancy Agent

Ten przewodnik pokazuje, jak stworzyć jeden instalator `.exe`, który zainstaluje całą aplikację wraz z Tesseract OCR i Poppler na Windows 11.

## Architektura instalatora

Instalator będzie zawierał:
1. ✅ Aplikację Python jako standalone executable (PyInstaller)
2. ✅ Tesseract OCR z językami (eng, slv, pol)
3. ✅ Poppler (pdftoppm)
4. ✅ Szablon konfiguracji (.env.example)
5. ✅ Dokumentację
6. ✅ Skróty w Menu Start
7. ✅ Automatyczną konfigurację ścieżek

## Narzędzia

### 1. PyInstaller
Do stworzenia standalone executable z aplikacji Python.

```bash
pip install pyinstaller
```

### 2. Inno Setup
Do stworzenia instalatora Windows (.exe).

**Pobierz:** https://jrsoftware.org/isdl.php
- Instaluj wersję Unicode (domyślna)
- Bezpłatny, open source

## Krok 1: Przygotowanie standalone executable

### A. Stwórz plik spec dla PyInstaller

Utwórz `price_agent.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),  # Cały folder src
        ('.env.example', '.'),
        ('README.md', '.'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'anthropic',
        'openpyxl',
        'msal',
        'python-dotenv',
        'bs4',
        'html2text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PriceDiscrepancyAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Opcjonalnie: dodaj ikonę
)
```

### B. Zbuduj executable

```bash
# Build standalone exe
pyinstaller price_agent.spec

# Executable będzie w: dist/PriceDiscrepancyAgent.exe
```

### C. Przetestuj executable

```bash
# Test
dist\PriceDiscrepancyAgent.exe --help
```

## Krok 2: Pobierz zależności

### A. Tesseract OCR

1. Pobierz instalator: https://github.com/UB-Mannheim/tesseract/wiki
2. Pobierz wersję **portable** (ZIP) zamiast instalatora
3. Rozpakuj do `installer_resources/tesseract/`

Struktura:
```
installer_resources/
└── tesseract/
    ├── tesseract.exe
    ├── tessdata/
    │   ├── eng.traineddata
    │   ├── slv.traineddata
    │   └── pol.traineddata
    └── ...
```

### B. Poppler

1. Pobierz: https://github.com/oschwartz10612/poppler-windows/releases
2. Pobierz ZIP (np. `Release-24.08.0-0.zip`)
3. Rozpakuj do `installer_resources/poppler/`

Struktura:
```
installer_resources/
└── poppler/
    └── Library/
        └── bin/
            ├── pdftoppm.exe
            ├── pdfinfo.exe
            └── ...
```

## Krok 3: Stwórz skrypt Inno Setup

Utwórz `installer.iss`:

```pascal
; Price Discrepancy Agent Installer
; Inno Setup Script

#define MyAppName "Price Discrepancy Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppExeName "PriceDiscrepancyAgent.exe"

[Setup]
AppId={{12345678-1234-1234-1234-123456789012}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename=PriceDiscrepancyAgent_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Tesseract OCR
Source: "installer_resources\tesseract\*"; DestDir: "{app}\tools\tesseract"; Flags: ignoreversion recursesubdirs createallsubdirs

; Poppler
Source: "installer_resources\poppler\Library\bin\*"; DestDir: "{app}\tools\poppler\bin"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration template
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Documentation
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Configuration"; Filename: "notepad.exe"; Parameters: "{app}\.env"
Name: "{group}\Documentation"; Filename: "{app}\docs"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\docs\README.md"; Description: "Otwórz dokumentację"; Flags: postinstall shellexec skipifsilent
Filename: "notepad.exe"; Parameters: "{app}\.env.example"; Description: "Skonfiguruj aplikację (skopiuj .env.example do .env)"; Flags: postinstall skipifsilent

[Code]
const
  EnvFileName = '.env';

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvExamplePath: String;
  EnvPath: String;
  ConfigContent: String;
  TesseractPath: String;
  PopplerPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    EnvExamplePath := ExpandConstant('{app}\.env.example');
    EnvPath := ExpandConstant('{app}\.env');
    TesseractPath := ExpandConstant('{app}\tools\tesseract\tesseract.exe');
    PopplerPath := ExpandConstant('{app}\tools\poppler\bin');

    // Czytaj .env.example
    if LoadStringFromFile(EnvExamplePath, ConfigContent) then
    begin
      // Zastąp ścieżki do narzędzi
      StringChangeEx(ConfigContent, 'TESSERACT_PATH=', 'TESSERACT_PATH=' + TesseractPath + #13#10 + ';OLD_', False);
      StringChangeEx(ConfigContent, 'POPPLER_PATH=', 'POPPLER_PATH=' + PopplerPath + #13#10 + ';OLD_', False);

      // Zapisz .env (jeśli nie istnieje)
      if not FileExists(EnvPath) then
        SaveStringToFile(EnvPath, ConfigContent, False);
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\output"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\.env"
```

## Krok 4: Kompilacja instalatora

### A. Otwórz Inno Setup Compiler

1. Uruchom **Inno Setup Compiler**
2. File → Open → `installer.iss`
3. Build → Compile (lub F9)

### B. Wynik

Instalator zostanie stworzony w `output/PriceDiscrepancyAgent_Setup.exe`

## Krok 5: Dystrybucja

### Plik instalatora zawiera:
- ✅ Aplikację (~50-100 MB)
- ✅ Tesseract OCR (~50 MB)
- ✅ Poppler (~20 MB)
- ✅ Dokumentację

**Całkowity rozmiar:** ~100-200 MB (w zależności od kompresji)

### Instalacja dla użytkownika:

1. Uruchom `PriceDiscrepancyAgent_Setup.exe`
2. Wybierz lokalizację instalacji (domyślnie: `C:\Program Files\Price Discrepancy Agent`)
3. Instalator automatycznie:
   - Instaluje aplikację
   - Instaluje Tesseract i Poppler
   - Tworzy plik `.env` z poprawnymi ścieżkami do narzędzi
   - Tworzy skróty w Menu Start
4. Po instalacji:
   - Edytuj `.env` (Menu Start → Configuration)
   - Wypełnij Azure AD credentials i SharePoint IDs
   - Uruchom aplikację (Menu Start → Price Discrepancy Agent)

## Krok 6: Automatyzacja budowania

Utwórz `build_installer.bat`:

```batch
@echo off
echo ========================================
echo Building Price Discrepancy Agent Installer
echo ========================================
echo.

REM 1. Build executable with PyInstaller
echo Step 1: Building standalone executable...
pyinstaller price_agent.spec
if errorlevel 1 (
    echo ERROR: PyInstaller failed!
    exit /b 1
)
echo ✓ Executable created: dist\PriceDiscrepancyAgent.exe
echo.

REM 2. Check for Tesseract
if not exist "installer_resources\tesseract\tesseract.exe" (
    echo ERROR: Tesseract not found in installer_resources\tesseract\
    echo Please download Tesseract portable and extract to installer_resources\tesseract\
    exit /b 1
)
echo ✓ Tesseract found
echo.

REM 3. Check for Poppler
if not exist "installer_resources\poppler\Library\bin\pdftoppm.exe" (
    echo ERROR: Poppler not found in installer_resources\poppler\
    echo Please download Poppler and extract to installer_resources\poppler\
    exit /b 1
)
echo ✓ Poppler found
echo.

REM 4. Build installer with Inno Setup
echo Step 2: Building Windows installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
if errorlevel 1 (
    echo ERROR: Inno Setup failed!
    exit /b 1
)
echo ✓ Installer created: output\PriceDiscrepancyAgent_Setup.exe
echo.

echo ========================================
echo Build completed successfully!
echo Installer: output\PriceDiscrepancyAgent_Setup.exe
echo ========================================
pause
```

Uruchom:
```batch
build_installer.bat
```

## Krok 7: Instalacja jako Windows Service (opcjonalnie)

Jeśli chcesz, aby aplikacja działała 24/7 jako Windows Service:

### A. Dodaj NSSM (Non-Sucking Service Manager)

1. Pobierz NSSM: https://nssm.cc/download
2. Dodaj do instalatora
3. W skrypcie Inno Setup dodaj opcję instalacji jako service

### B. Dodaj do installer.iss:

```pascal
[Tasks]
Name: "installservice"; Description: "Zainstaluj jako Windows Service (działa 24/7)"; GroupDescription: "Opcje zaawansowane:"; Flags: unchecked

[Files]
Source: "installer_resources\nssm\nssm.exe"; DestDir: "{app}\tools"; Flags: ignoreversion; Tasks: installservice

[Run]
; Install as service
Filename: "{app}\tools\nssm.exe"; Parameters: "install PriceAgent ""{app}\{#MyAppExeName}"" --auto"; Flags: runhidden; Tasks: installservice
Filename: "{app}\tools\nssm.exe"; Parameters: "set PriceAgent AppDirectory ""{app}"""; Flags: runhidden; Tasks: installservice
Filename: "{app}\tools\nssm.exe"; Parameters: "set PriceAgent DisplayName ""Price Discrepancy Agent"""; Flags: runhidden; Tasks: installservice
Filename: "{app}\tools\nssm.exe"; Parameters: "set PriceAgent Description ""Automatyczne przetwarzanie emaili z rozbieżnościami cenowymi"""; Flags: runhidden; Tasks: installservice
Filename: "{app}\tools\nssm.exe"; Parameters: "set PriceAgent Start SERVICE_AUTO_START"; Flags: runhidden; Tasks: installservice
Filename: "{app}\tools\nssm.exe"; Parameters: "start PriceAgent"; Flags: runhidden; Tasks: installservice

[UninstallRun]
Filename: "{app}\tools\nssm.exe"; Parameters: "stop PriceAgent"; Flags: runhidden; Tasks: installservice
Filename: "{app}\tools\nssm.exe"; Parameters: "remove PriceAgent confirm"; Flags: runhidden; Tasks: installservice
```

## Troubleshooting

### PyInstaller: "module not found"
- Dodaj brakujący moduł do `hiddenimports` w `.spec`
- Uruchom z `--debug=all` aby zobaczyć szczegóły

### Inno Setup: Nie można skompilować
- Sprawdź, czy wszystkie ścieżki w `[Files]` są poprawne
- Upewnij się, że pliki istnieją przed kompilacją

### Installer: "Access denied" podczas instalacji
- Instalator wymaga uprawnień administratora
- Dodaj `PrivilegesRequired=admin` w `[Setup]`

### Duży rozmiar instalatora
- Użyj `Compression=lzma2/ultra64` dla najlepszej kompresji
- Rozważ instalator online (pobiera komponenty podczas instalacji)

## Wersjonowanie

Przy każdej nowej wersji:
1. Zaktualizuj `#define MyAppVersion` w `installer.iss`
2. Zaktualizuj `AppId` (nowy GUID) jeśli breaking changes
3. Zbuduj nowy instalator
4. Przetestuj na czystym Windows 11

## Alternatywne podejścia

### 1. NSIS (Nullsoft Scriptable Install System)
- Podobny do Inno Setup
- Bardziej skomplikowany
- Więcej kontroli

### 2. WiX Toolset
- Standard Microsoft
- Integracja z Visual Studio
- Bardziej skomplikowany

### 3. Docker (dla advanced users)
- Konteneryzacja aplikacji
- Wymaga Docker Desktop na Windows
- Łatwiejsze aktualizacje

## Podsumowanie

Po wykonaniu tych kroków będziesz miał:
- ✅ Jeden plik `.exe` (~150-200 MB)
- ✅ Automatyczna instalacja wszystkich zależności
- ✅ Proste wdrożenie na wielu komputerach
- ✅ Profesjonalny installer z polskim UI
- ✅ Automatyczna konfiguracja ścieżek do narzędzi
- ✅ Opcjonalnie: Windows Service dla operacji 24/7

Użytkownicy końcowi potrzebują tylko:
1. Uruchomić installer
2. Wypełnić `.env` (Azure AD credentials)
3. Uruchomić aplikację
