; Price Discrepancy Agent - Windows Installer
; Inno Setup Script (Polish UI)

#define MyAppName "Price Discrepancy Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://github.com/MarekBodynek/price-discrepancy-agent"
#define MyAppExeName "PriceDiscrepancyAgent.exe"

[Setup]
; App Info
AppId={{A5B2C3D4-E5F6-4789-A1B2-C3D4E5F67890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Install Directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=output
OutputBaseFilename=PriceDiscrepancyAgent_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576
LZMANumFastBytes=273

; UI
WizardStyle=modern
DisableWelcomePage=no
ShowLanguageDialog=auto

; Requirements
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.22000

; Misc
AllowNoIcons=yes
UninstallDisplayName={#MyAppName}

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
polish.WelcomeLabel2=Instalator zainstaluje [name/ver] na tym komputerze.%n%nAplikacja wymaga:%n• Microsoft Azure AD (Graph API)%n• Windows 11 (64-bit)%n%nInstalator zawiera:%n• Price Discrepancy Agent%n• Tesseract OCR%n• Poppler PDF Tools%n%nZaleca się zamknięcie wszystkich innych aplikacji przed kontynuowaniem.
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nRequirements:%n• Microsoft Azure AD (Graph API)%n• Windows 11 (64-bit)%n%nIncluded:%n• Price Discrepancy Agent%n• Tesseract OCR%n• Poppler PDF Tools%n%nIt is recommended that you close all other applications before continuing.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main Application
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Configuration Template
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Documentation
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

; Tests (optional, for verification)
Source: "tests\*"; DestDir: "{app}\tests"; Flags: ignoreversion recursesubdirs createallsubdirs

; Tesseract OCR (if present)
Source: "installer_resources\tesseract\*"; DestDir: "{app}\tools\tesseract"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\installer_resources\tesseract'))

; Poppler (if present)
Source: "installer_resources\poppler\Library\bin\*"; DestDir: "{app}\tools\poppler\bin"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\installer_resources\poppler\Library\bin'))

[Dirs]
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify

[Icons]
; Start Menu Icons
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Price Discrepancy Agent - Email Processor"
Name: "{group}\Konfiguracja (.env)"; Filename: "notepad.exe"; Parameters: "{app}\.env"; Comment: "Edytuj plik konfiguracji"; Languages: polish
Name: "{group}\Configuration (.env)"; Filename: "notepad.exe"; Parameters: "{app}\.env"; Comment: "Edit configuration file"; Languages: english
Name: "{group}\Dokumentacja"; Filename: "{app}\docs"; Comment: "Otwórz folder z dokumentacją"; Languages: polish
Name: "{group}\Documentation"; Filename: "{app}\docs"; Comment: "Open documentation folder"; Languages: english
Name: "{group}\Logi aplikacji"; Filename: "{app}\logs"; Comment: "Otwórz folder z logami"; Languages: polish
Name: "{group}\Application Logs"; Filename: "{app}\logs"; Comment: "Open logs folder"; Languages: english
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Comment: "Odinstaluj Price Discrepancy Agent"

; Desktop Icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Price Discrepancy Agent"

; Quick Launch Icon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Open documentation after install
Filename: "{app}\docs\README.md"; Description: "Otwórz dokumentację"; Flags: postinstall shellexec skipifsilent unchecked; Languages: polish
Filename: "{app}\docs\README.md"; Description: "Open documentation"; Flags: postinstall shellexec skipifsilent unchecked; Languages: english

; Open Azure AD setup guide
Filename: "{app}\docs\AZURE_AD_SETUP_PL.md"; Description: "Otwórz przewodnik konfiguracji Azure AD"; Flags: postinstall shellexec skipifsilent unchecked; Languages: polish
Filename: "{app}\docs\AZURE_AD_SETUP.md"; Description: "Open Azure AD setup guide"; Flags: postinstall shellexec skipifsilent unchecked; Languages: english

; Configure .env
Filename: "notepad.exe"; Parameters: "{app}\.env.example"; Description: "Skonfiguruj aplikację (.env)"; Flags: postinstall skipifsilent; Languages: polish
Filename: "notepad.exe"; Parameters: "{app}\.env.example"; Description: "Configure application (.env)"; Flags: postinstall skipifsilent; Languages: english

[Code]
var
  ConfigPage: TInputQueryWizardPage;
  TesseractFound: Boolean;
  PopplerFound: Boolean;

procedure InitializeWizard;
begin
  // Check if Tesseract and Poppler are present
  TesseractFound := DirExists(ExpandConstant('{src}\installer_resources\tesseract'));
  PopplerFound := DirExists(ExpandConstant('{src}\installer_resources\poppler\Library\bin'));

  // Create configuration info page
  ConfigPage := CreateInputQueryPage(wpWelcome,
    'Informacje o konfiguracji',
    'Przed uruchomieniem aplikacji',
    'Po instalacji należy:' + #13#10 +
    '1. Skonfigurować Azure AD App Registration' + #13#10 +
    '2. Wypełnić plik .env credentials' + #13#10 +
    '3. Przetestować połączenie' + #13#10 + #13#10 +
    'Instalator automatycznie skonfiguruje ścieżki do narzędzi OCR.');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = wpReady then
  begin
    // Show warning if Tesseract or Poppler not found
    if not TesseractFound or not PopplerFound then
    begin
      if MsgBox('UWAGA: Nie znaleziono wszystkich narzędzi OCR!' + #13#10 + #13#10 +
                'Tesseract: ' + BoolToStr(TesseractFound, 'Znaleziono', 'BRAK') + #13#10 +
                'Poppler: ' + BoolToStr(PopplerFound, 'Znaleziono', 'BRAK') + #13#10 + #13#10 +
                'Aplikacja może nie działać poprawnie bez tych narzędzi.' + #13#10 +
                'Czy kontynuować instalację?',
                mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvExamplePath: String;
  EnvPath: String;
  ConfigContent: AnsiString;
  TesseractPath: String;
  PopplerPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Paths
    EnvExamplePath := ExpandConstant('{app}\.env.example');
    EnvPath := ExpandConstant('{app}\.env');
    TesseractPath := ExpandConstant('{app}\tools\tesseract\tesseract.exe');
    PopplerPath := ExpandConstant('{app}\tools\poppler\bin');

    // Read .env.example
    if LoadStringFromFile(EnvExamplePath, ConfigContent) then
    begin
      // Replace paths (only if tools were installed)
      if TesseractFound then
      begin
        StringChangeEx(ConfigContent, 'TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe',
                       'TESSERACT_PATH=' + TesseractPath, False);
      end;

      if PopplerFound then
      begin
        StringChangeEx(ConfigContent, 'POPPLER_PATH=C:\Program Files\poppler-24.08.0\Library\bin',
                       'POPPLER_PATH=' + PopplerPath, False);
      end;

      // Save as .env (if doesn't exist)
      if not FileExists(EnvPath) then
      begin
        SaveStringToFile(EnvPath, ConfigContent, False);
        Log('Created .env file with configured tool paths');
      end;
    end;
  end;
end;

function BoolToStr(Value: Boolean; TrueStr, FalseStr: String): String;
begin
  if Value then
    Result := TrueStr
  else
    Result := FalseStr;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\output"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\.env"
