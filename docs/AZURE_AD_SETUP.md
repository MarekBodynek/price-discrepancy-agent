# Azure AD Setup Guide - Price Discrepancy Agent

Ten przewodnik krok po kroku pomoże Ci skonfigurować Azure AD App Registration dla aplikacji.

## Wymagane uprawnienia

Aplikacja wymaga następujących uprawnień Microsoft Graph API:
- **Mail.Read** - czytanie emaili z skrzynki
- **Mail.ReadWrite** - oznaczanie emaili jako przeczytane
- **Sites.ReadWrite.All** - upload plików do SharePoint

## Krok 1: Rejestracja aplikacji w Azure Portal

1. Zaloguj się do [Azure Portal](https://portal.azure.com)
2. Przejdź do **Azure Active Directory** (lub **Microsoft Entra ID**)
3. W menu po lewej wybierz **App registrations**
4. Kliknij **+ New registration**

### Wypełnij formularz rejestracji:
- **Name**: `Price Discrepancy Agent` (lub dowolna nazwa)
- **Supported account types**:
  - Wybierz **Accounts in this organizational directory only (Single tenant)**
- **Redirect URI**:
  - Zostaw puste (aplikacja używa client credentials flow, nie wymaga redirect URI)
- Kliknij **Register**

### Po rejestracji zobaczysz stronę Overview aplikacji:
✅ **Skopiuj i zapisz:**
- **Application (client) ID** → to będzie `AZURE_CLIENT_ID`
- **Directory (tenant) ID** → to będzie `AZURE_TENANT_ID`

## Krok 2: Utworzenie Client Secret

1. W menu aplikacji wybierz **Certificates & secrets**
2. W zakładce **Client secrets** kliknij **+ New client secret**
3. Wypełnij:
   - **Description**: `Price Discrepancy Agent Secret`
   - **Expires**: Wybierz odpowiedni okres (np. 24 months)
4. Kliknij **Add**

### ⚠️ WAŻNE - Skopiuj Secret NATYCHMIAST:
- **Value** pojawi się tylko RAZ
- ✅ Skopiuj i zapisz → to będzie `AZURE_CLIENT_SECRET`
- Po odświeżeniu strony nie będziesz mógł ponownie zobaczyć wartości

## Krok 3: Konfiguracja API Permissions

1. W menu aplikacji wybierz **API permissions**
2. Kliknij **+ Add a permission**
3. Wybierz **Microsoft Graph**
4. Wybierz **Application permissions** (NIE Delegated permissions!)

### Dodaj następujące uprawnienia Application permissions:

#### Mail permissions:
5. Wyszukaj i zaznacz:
   - ✅ **Mail.Read**
   - ✅ **Mail.ReadWrite**

#### SharePoint permissions:
6. Wyszukaj i zaznacz:
   - ✅ **Sites.ReadWrite.All**

7. Kliknij **Add permissions**

### ⚠️ KRYTYCZNE - Admin Consent:
8. Po dodaniu uprawnień kliknij **✅ Grant admin consent for [Twoja organizacja]**
9. Potwierdź w oknie dialogowym
10. Poczekaj, aż status wszystkich uprawnień zmieni się na **Granted for [Twoja organizacja]** (zielona fajka)

**Bez admin consent aplikacja NIE BĘDZIE DZIAŁAĆ!**

## Krok 4: Uzyskanie SharePoint IDs

### A. SharePoint Site ID

1. Otwórz Twój SharePoint site w przeglądarce
2. Przejdź do folderu, gdzie chcesz uploadować pliki
3. Z URL wyciągnij nazwę site'a:
   ```
   https://[tenant].sharepoint.com/sites/[site-name]/...
   ```

4. Użyj Graph Explorer lub PowerShell, aby uzyskać Site ID:

**Opcja 1: Graph Explorer** (https://developer.microsoft.com/graph/graph-explorer)
```
GET https://graph.microsoft.com/v1.0/sites/[tenant].sharepoint.com:/sites/[site-name]
```

**Opcja 2: PowerShell** (z zainstalowanym Microsoft.Graph)
```powershell
Connect-MgGraph -Scopes "Sites.Read.All"
Get-MgSite -Search "[site-name]" | Select Id, DisplayName, WebUrl
```

✅ Skopiuj **Site ID** (format: `contoso.sharepoint.com,12345678-1234-1234-1234-123456789012,12345678-1234-1234-1234-123456789012`)

### B. Drive ID (Document Library)

1. Mając Site ID, użyj:

**Graph Explorer:**
```
GET https://graph.microsoft.com/v1.0/sites/[SITE_ID]/drives
```

**PowerShell:**
```powershell
Get-MgSiteDrive -SiteId "[SITE_ID]" | Select Id, Name, WebUrl
```

2. Znajdź właściwą bibliotekę dokumentów (zwykle "Documents" lub "Shared Documents")
✅ Skopiuj **Drive ID** (format: `b!12345678...`)

### C. Folder Path

3. Zdecyduj, w którym folderze chcesz zapisywać pliki Excel i logi
   - Jeśli w głównym katalogu: `/`
   - Jeśli w podfolderze: `/PriceDiscrepancies` (folder musi istnieć!)

## Krok 5: Uzyskanie Mailbox User ID

To jest User Principal Name (UPN) lub Object ID skrzynki pocztowej, którą chcesz monitorować.

**Opcja 1: UPN (preferowana)**
- Format: `username@domain.com`
- Przykład: `finance@contoso.com`

**Opcja 2: User Object ID**
1. W Azure Portal → Azure AD → Users
2. Znajdź użytkownika
3. Skopiuj **Object ID**

**Najczęściej używa się UPN (email address).**

## Krok 6: Wypełnienie pliku .env

1. W katalogu projektu skopiuj `.env.example` do `.env`:
```bash
cp .env.example .env
```

2. Otwórz `.env` i wypełnij wartości:

```env
# Azure AD Configuration
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
AZURE_CLIENT_SECRET=abC~1234567890aBcDeFgHiJkLmNoPqRsTuVwXyZ

# Email Configuration
MAILBOX_USER_ID=finance@contoso.com

# SharePoint Configuration
SHAREPOINT_SITE_ID=contoso.sharepoint.com,12345678-1234-1234-1234-123456789012,12345678-1234-1234-1234-123456789012
SHAREPOINT_DRIVE_ID=b!12345678abcdefgh...
SHAREPOINT_FOLDER_PATH=/PriceDiscrepancies

# OCR Configuration (ścieżki do zainstalowanych narzędzi)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Program Files\poppler-24.08.0\Library\bin

# Optional: Anthropic API (fallback dla niejednoznacznych przypadków)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Timezone (default: Europe/Ljubljana)
TIMEZONE=Europe/Ljubljana

# Optional: OCR Languages (default: eng,slv)
OCR_LANGUAGES=eng,slv,pol

# Optional: Log Level (default: INFO)
LOG_LEVEL=INFO
```

## Krok 7: Weryfikacja konfiguracji

### Test połączenia z Graph API:

```python
python3 -c "
from src.config import load_config
from src.integrations.graph.auth import GraphAuthClient

config = load_config()
auth = GraphAuthClient(config)
token = auth.get_token()
print('✅ Autentykacja działa! Token uzyskany.')
"
```

### Test czytania emaili:

```python
python3 -c "
from src.config import load_config
from src.integrations.graph.mail import GraphMailClient
from datetime import date

config = load_config()
mail_client = GraphMailClient(config)
messages = mail_client.list_unread_messages(date.today(), date.today())
print(f'✅ Znaleziono {len(messages)} nieprzeczytanych wiadomości.')
"
```

## Troubleshooting

### Błąd: "Insufficient privileges to complete the operation"
- ✅ Sprawdź, czy nadano **Admin Consent** dla wszystkich uprawnień
- ✅ Upewnij się, że używasz **Application permissions**, a nie Delegated
- ✅ Odczekaj 5-10 minut po nadaniu consent (cache Azure AD)

### Błąd: "The tenant for tenant guid does not exist"
- ✅ Sprawdź, czy `AZURE_TENANT_ID` jest poprawny
- ✅ Upewnij się, że aplikacja jest zarejestrowana w tym samym tenant

### Błąd: "Invalid client secret provided"
- ✅ Client Secret mógł wygasnąć - wygeneruj nowy
- ✅ Sprawdź, czy nie ma spacji na początku/końcu wartości w .env

### Błąd: "Resource not found for the segment 'users'"
- ✅ Sprawdź, czy `MAILBOX_USER_ID` jest poprawny
- ✅ Spróbuj użyć UPN zamiast Object ID (lub odwrotnie)

### Błąd: "The site could not be found"
- ✅ Sprawdź Site ID (użyj Graph Explorer do weryfikacji)
- ✅ Upewnij się, że aplikacja ma uprawnienie Sites.ReadWrite.All z admin consent

## Bezpieczeństwo

### ⚠️ NIGDY nie commituj pliku .env do Git!
- Plik `.env` jest już dodany do `.gitignore`
- Client Secret to tajny klucz - traktuj jak hasło

### Rotacja Client Secret:
- Ustaw przypomnienie o wygaśnięciu secretu
- Przed wygaśnięciem stwórz nowy secret
- Zaktualizuj .env
- Po weryfikacji usuń stary secret

### Monitoring:
- Regularnie przeglądaj logi logowania aplikacji w Azure AD
- Sprawdzaj uprawnienia aplikacji co kwartał
- Używaj minimum wymaganych uprawnień

## Następne kroki

Po skonfigurowaniu Azure AD:
1. ✅ Zainstaluj Tesseract OCR
2. ✅ Zainstaluj Poppler
3. ✅ Przetestuj aplikację w trybie dry-run
4. ✅ Uruchom na prawdziwych danych

## Przydatne linki

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/api/overview)
- [Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)
- [Azure AD App Registration](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Application vs Delegated Permissions](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent)
