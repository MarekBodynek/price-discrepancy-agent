# Konfiguracja Azure AD - Price Discrepancy Agent (Polski UI)

Ten przewodnik krok po kroku pomoże Ci skonfigurować Azure AD App Registration dla aplikacji w **polskiej wersji** Azure Portal.

## Wymagane uprawnienia

Aplikacja wymaga następujących uprawnień Microsoft Graph API:
- **Mail.Read** - czytanie emaili z skrzynki
- **Mail.ReadWrite** - oznaczanie emaili jako przeczytane
- **Sites.ReadWrite.All** - upload plików do SharePoint

## Krok 1: Rejestracja aplikacji w Azure Portal

1. Zaloguj się do [Azure Portal](https://portal.azure.com)
2. Przejdź do **Azure Active Directory** (lub **Microsoft Entra ID**)
3. W menu po lewej wybierz **Rejestracje aplikacji**
4. Kliknij **+ Nowa rejestracja**

### Wypełnij formularz rejestracji:
- **Nazwa**: `Price Discrepancy Agent` (lub dowolna nazwa)
- **Obsługiwane typy kont**:
  - Wybierz **Konta tylko w tym katalogu organizacji (tylko pojedyncza dzierżawa)**
- **Identyfikator URI przekierowania**:
  - Zostaw puste (aplikacja używa client credentials flow, nie wymaga redirect URI)
- Kliknij **Zarejestruj**

### Po rejestracji zobaczysz stronę Przegląd aplikacji:
✅ **Skopiuj i zapisz:**
- **Identyfikator aplikacji (klienta)** → to będzie `AZURE_CLIENT_ID`
- **Identyfikator katalogu (dzierżawy)** → to będzie `AZURE_TENANT_ID`

## Krok 2: Utworzenie wpisu tajnego klienta (Client Secret)

1. W menu aplikacji wybierz **Certyfikaty i wpisy tajne**
2. W zakładce **Wpisy tajne klienta** kliknij **+ Nowy wpis tajny klienta**
3. Wypełnij:
   - **Opis**: `Price Discrepancy Agent Secret`
   - **Wygasa**: Wybierz odpowiedni okres (np. 24 miesiące)
4. Kliknij **Dodaj**

### ⚠️ WAŻNE - Skopiuj wpis tajny NATYCHMIAST:
- **Wartość** pojawi się tylko RAZ
- ✅ Skopiuj i zapisz → to będzie `AZURE_CLIENT_SECRET`
- Po odświeżeniu strony nie będziesz mógł ponownie zobaczyć wartości

## Krok 3: Konfiguracja uprawnień interfejsu API

1. W menu aplikacji wybierz **Uprawnienia interfejsu API**
2. Kliknij **+ Dodaj uprawnienie**
3. Wybierz **Microsoft Graph**
4. Wybierz **Uprawnienia aplikacji** (NIE Uprawnienia delegowane!)

### Dodaj następujące uprawnienia aplikacji:

#### Uprawnienia Mail:
5. Wyszukaj i zaznacz:
   - ✅ **Mail.Read**
   - ✅ **Mail.ReadWrite**

#### Uprawnienia SharePoint:
6. Wyszukaj i zaznacz:
   - ✅ **Sites.ReadWrite.All**

7. Kliknij **Dodaj uprawnienia**

### ⚠️ KRYTYCZNE - Zgoda administratora:
8. Po dodaniu uprawnień kliknij **✅ Udziel zgody administratora dla [Twoja organizacja]**
9. Potwierdź w oknie dialogowym
10. Poczekaj, aż status wszystkich uprawnień zmieni się na **Udzielono dla [Twoja organizacja]** (zielona fajka)

**Bez zgody administratora aplikacja NIE BĘDZIE DZIAŁAĆ!**

## Krok 4: Uzyskanie SharePoint IDs

### A. SharePoint Site ID

1. Otwórz Twój SharePoint site w przeglądarce
2. Przejdź do folderu, gdzie chcesz uploadować pliki
3. Z URL wyciągnij nazwę site'a:
   ```
   https://[tenant].sharepoint.com/sites/[nazwa-site]/...
   ```

4. Użyj Graph Explorer lub PowerShell, aby uzyskać Site ID:

**Opcja 1: Graph Explorer** (https://developer.microsoft.com/graph/graph-explorer)
```
GET https://graph.microsoft.com/v1.0/sites/[tenant].sharepoint.com:/sites/[nazwa-site]
```

**Opcja 2: PowerShell** (z zainstalowanym Microsoft.Graph)
```powershell
Connect-MgGraph -Scopes "Sites.Read.All"
Get-MgSite -Search "[nazwa-site]" | Select Id, DisplayName, WebUrl
```

✅ Skopiuj **Site ID** (format: `contoso.sharepoint.com,12345678-1234-1234-1234-123456789012,12345678-1234-1234-1234-123456789012`)

### B. Drive ID (Biblioteka dokumentów)

1. Mając Site ID, użyj:

**Graph Explorer:**
```
GET https://graph.microsoft.com/v1.0/sites/[SITE_ID]/drives
```

**PowerShell:**
```powershell
Get-MgSiteDrive -SiteId "[SITE_ID]" | Select Id, Name, WebUrl
```

2. Znajdź właściwą bibliotekę dokumentów (zwykle "Dokumenty" lub "Documents")
✅ Skopiuj **Drive ID** (format: `b!12345678...`)

### C. Ścieżka folderu

3. Zdecyduj, w którym folderze chcesz zapisywać pliki Excel i logi
   - Jeśli w głównym katalogu: `/`
   - Jeśli w podfolderze: `/PriceDiscrepancies` (folder musi istnieć!)

## Krok 5: Uzyskanie Mailbox User ID

To jest User Principal Name (UPN) lub Object ID skrzynki pocztowej, którą chcesz monitorować.

**Opcja 1: UPN (preferowana)**
- Format: `username@domain.com`
- Przykład: `finance@contoso.com`

**Opcja 2: User Object ID**
1. W Azure Portal → Azure AD → **Użytkownicy**
2. Znajdź użytkownika
3. Skopiuj **Identyfikator obiektu**

**Najczęściej używa się UPN (adres email).**

## Krok 6: Wypełnienie pliku .env

1. W katalogu projektu skopiuj `.env.example` do `.env`:
```bash
cp .env.example .env
```

2. Otwórz `.env` i wypełnij wartości:

```env
# Konfiguracja Azure AD
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
AZURE_CLIENT_SECRET=abC~1234567890aBcDeFgHiJkLmNoPqRsTuVwXyZ

# Konfiguracja Email
MAILBOX_USER_ID=finance@contoso.com

# Konfiguracja SharePoint
SHAREPOINT_SITE_ID=contoso.sharepoint.com,12345678-1234-1234-1234-123456789012,12345678-1234-1234-1234-123456789012
SHAREPOINT_DRIVE_ID=b!12345678abcdefgh...
SHAREPOINT_FOLDER_PATH=/PriceDiscrepancies

# Konfiguracja OCR (ścieżki do zainstalowanych narzędzi)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Program Files\poppler-24.08.0\Library\bin

# Opcjonalne: Anthropic API (fallback dla niejednoznacznych przypadków)
ANTHROPIC_API_KEY=sk-ant-...

# Opcjonalne: Strefa czasowa (domyślnie: Europe/Ljubljana)
TIMEZONE=Europe/Ljubljana

# Opcjonalne: Języki OCR (domyślnie: eng,slv)
OCR_LANGUAGES=eng,slv,pol

# Opcjonalne: Poziom logowania (domyślnie: INFO)
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

## Rozwiązywanie problemów

### Błąd: "Niewystarczające uprawnienia do ukończenia operacji"
- ✅ Sprawdź, czy nadano **Zgodę administratora** dla wszystkich uprawnień
- ✅ Upewnij się, że używasz **Uprawnień aplikacji**, a nie Uprawnień delegowanych
- ✅ Odczekaj 5-10 minut po nadaniu zgody (cache Azure AD)

### Błąd: "Dzierżawa dla identyfikatora GUID dzierżawy nie istnieje"
- ✅ Sprawdź, czy `AZURE_TENANT_ID` jest poprawny
- ✅ Upewnij się, że aplikacja jest zarejestrowana w tym samym tenant

### Błąd: "Podano nieprawidłowy wpis tajny klienta"
- ✅ Wpis tajny klienta mógł wygasnąć - wygeneruj nowy
- ✅ Sprawdź, czy nie ma spacji na początku/końcu wartości w .env

### Błąd: "Nie znaleziono zasobu dla segmentu 'users'"
- ✅ Sprawdź, czy `MAILBOX_USER_ID` jest poprawny
- ✅ Spróbuj użyć UPN zamiast Object ID (lub odwrotnie)

### Błąd: "Nie można znaleźć witryny"
- ✅ Sprawdź Site ID (użyj Graph Explorer do weryfikacji)
- ✅ Upewnij się, że aplikacja ma uprawnienie Sites.ReadWrite.All ze zgodą administratora

## Bezpieczeństwo

### ⚠️ NIGDY nie commituj pliku .env do Git!
- Plik `.env` jest już dodany do `.gitignore`
- Wpis tajny klienta to tajny klucz - traktuj jak hasło

### Rotacja wpisu tajnego klienta:
- Ustaw przypomnienie o wygaśnięciu
- Przed wygaśnięciem stwórz nowy wpis tajny
- Zaktualizuj .env
- Po weryfikacji usuń stary wpis tajny

### Monitoring:
- Regularnie przeglądaj logi logowania aplikacji w Azure AD
- Sprawdzaj uprawnienia aplikacji co kwartał
- Używaj minimum wymaganych uprawnień

## Słownik terminów Polski UI ↔ Angielski

| Polski UI | Angielski UI | Notatka |
|-----------|--------------|---------|
| Azure Active Directory | Azure Active Directory | Nazwa pozostaje taka sama |
| Microsoft Entra ID | Microsoft Entra ID | Nowa nazwa AAD |
| Rejestracje aplikacji | App registrations | |
| Nowa rejestracja | New registration | |
| Identyfikator aplikacji (klienta) | Application (client) ID | AZURE_CLIENT_ID |
| Identyfikator katalogu (dzierżawy) | Directory (tenant) ID | AZURE_TENANT_ID |
| Certyfikaty i wpisy tajne | Certificates & secrets | |
| Wpisy tajne klienta | Client secrets | |
| Nowy wpis tajny klienta | New client secret | |
| Wartość | Value | AZURE_CLIENT_SECRET |
| Uprawnienia interfejsu API | API permissions | |
| Dodaj uprawnienie | Add a permission | |
| Uprawnienia aplikacji | Application permissions | NIE Delegowane! |
| Uprawnienia delegowane | Delegated permissions | |
| Udziel zgody administratora | Grant admin consent | KRYTYCZNE! |
| Udzielono dla [Org] | Granted for [Org] | Status po zgodzie |
| Użytkownicy | Users | |
| Identyfikator obiektu | Object ID | |

## Następne kroki

Po skonfigurowaniu Azure AD:
1. ✅ Zainstaluj Tesseract OCR (zobacz [OCR_TOOLS_SETUP.md](OCR_TOOLS_SETUP.md))
2. ✅ Zainstaluj Poppler
3. ✅ Przetestuj aplikację w trybie dry-run
4. ✅ Uruchom na prawdziwych danych

## Przydatne linki

- [Microsoft Graph API Documentation](https://learn.microsoft.com/pl-pl/graph/api/overview)
- [Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)
- [Azure AD App Registration](https://learn.microsoft.com/pl-pl/azure/active-directory/develop/quickstart-register-app)
- [Uprawnienia aplikacji vs delegowane](https://learn.microsoft.com/pl-pl/azure/active-directory/develop/v2-permissions-and-consent)
