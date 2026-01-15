# Price Discrepancy Email Processor (CLI)

## 🚀 Quick Start & Documentation

**Gotowy do wdrożenia?** Zobacz przewodniki krok po kroku:

📘 **[Azure AD Setup Guide](docs/AZURE_AD_SETUP.md)** - Konfiguracja Microsoft Graph API
🔧 **[OCR Tools Setup Guide](docs/OCR_TOOLS_SETUP.md)** - Instalacja Tesseract i Poppler
📚 **[Pełna dokumentacja](docs/README.md)** - Architektura, usage, troubleshooting

**Szybki test:**
```bash
# Instalacja zależności
pip install -r requirements.txt

# Testy jednostkowe (39 testów, coverage 44%)
python3 -m pytest tests/ -v

# Dry-run (nie oznacza emaili, nie uploaduje)
python3 -m src.main --auto --dry-run
```

---

## 1. Cel projektu

Celem projektu jest stworzenie **stabilnego, deterministycznego narzędzia CLI**, które automatycznie przetwarza **nieprzeczytane e-maile Outlook** dotyczące rozbieżności cenowych zgłaszanych przez sklepy, ekstraktuje z nich dane w sposób audytowalny i generuje:

- jeden **skonsolidowany plik Excel** na każde uruchomienie,
- jeden **plik logu** na każde uruchomienie,

a następnie zapisuje oba pliki do **wskazanego folderu SharePoint**.

Rozwiązanie działa:
- na **Windows 11**,
- lokalnie, 24/7,
- bez automatyzacji UI (bez sterowania przeglądarką),
- z wykorzystaniem **Microsoft Graph API**, **lokalnego OCR (Tesseract)**,
- oraz **Claude (Anthropic API)** wyłącznie jako **opcjonalnej warstwy fallback**.

---

## 2. Kluczowe założenia (nienaruszalne)

- ❌ Brak zgadywania
- ❌ Brak inferencji
- ❌ Brak rekonstrukcji brakujących danych
- ❌ Brak łączenia danych pomiędzy e-mailami
- ✅ Przetwarzanie wyłącznie danych jawnie obecnych
- ✅ Determinizm i audytowalność

Każde odstępstwo od reguł musi skutkować:
- pominięciem e-maila,
- pozostawieniem go jako **UNREAD**,
- zapisaniem informacji w logu.

---

## 3. Zakres przetwarzanych e-maili

Podczas jednego uruchomienia system:

- przetwarza **wyłącznie e-maile oznaczone jako UNREAD**,
- których **data otrzymania (Outlook receivedDateTime)** mieści się w:
  - jednej dacie **lub**
  - zadanym zakresie dat,
- strefa czasowa: **Słowenia**,
- zakres: **inclusive start / inclusive end**.

W trybie automatycznym (harmonogram):
- system zawsze przetwarza **poprzednie 24 godziny** (rolling window).

---

## 4. Krytyczna reguła biznesowa (Hard Stop)

Każdy e-mail MUSI zawierać **co najmniej jedną** z poniższych dat:

- **Delivery Date**  
LUB
- **Order Creation Date**

Daty mogą pochodzić z:
- OCR (screenshots / obrazy),
- załączników,
- treści e-maila.

### Jeśli żadna z tych dat nie występuje:
- przetwarzanie e-maila jest **natychmiast przerywane**,
- e-mail pozostaje **UNREAD**,
- brak zapisu do Excela,
- logowany jest **BUSINESS ERROR**.

### Jeśli przynajmniej jedna data występuje:
- traktowana jest jako **data na poziomie całego e-maila**,
- obowiązuje **wszystkie EAN-y** w tym e-mailu.

---

## 5. Priorytet źródeł danych (bezwzględny)

Przy ekstrakcji **każdego pola** obowiązuje ścisły priorytet:

1. **OCR ze screenshotów / obrazów**
2. **Załączniki (Excel, PDF)**
3. **Treść e-maila**

Jeśli dane występują w wielu źródłach:
- zawsze wybierane jest źródło o **wyższym priorytecie**,
- konflikt jest opisany w kolumnie **Comments**,
- jeśli użyto OCR – musi to być jawnie zaznaczone.

---

## 6. OCR (lokalne)

OCR wykonywany jest **lokalnie**, bez usług chmurowych.

- Silnik: **Tesseract OCR**
- Obsługiwane:
  - obrazy inline w treści e-maila,
  - załączniki JPG / PNG,
  - obrazy osadzone w PDF (po renderowaniu stron do PNG).
- Języki OCR:
  - `eng`
  - `slv`
  - opcjonalnie `pol`

Claude **nie może** być używany jako silnik OCR.

---

## 7. Obsługa przypadków (EAN)

- Jeden e-mail może zawierać **wiele EAN-ów**.
- Dla każdego EAN tworzony jest **osobny wiersz** w Excelu.
- Wszystkie wiersze z jednego e-maila dzielą:
  - Delivery / Order Date,
  - Email Sender Address,
  - Email Link / Reference.

---

## 8. Plik Excel – wynik

### Generowanie
- Dokładnie **jeden plik Excel na jedno uruchomienie**.
- Nazewnictwo:
  - `Price_Discrepancies_YYYY-MM-DD.xlsx`
  - `Price_Discrepancies_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
- Jeśli plik o tej nazwie już istnieje:
  - dodawany jest sufiks `_v2`, `_v3`, itd.

### Kolumny (kolejność obowiązkowa)

1. Unit (Store)
2. EAN Code
3. Document Creation Date (jeśli dostępna)
4. Delivery Date (jeśli dostępna)
5. Order Creation Date (jeśli dostępna)
6. Supplier Price
7. Internal (Own) Price
8. Supplier Name
9. Supplier Invoice Number (jeśli dostępny)
10. Email Sender Address
11. Email Link / Stable Reference
12. Comments

---

## 9. Logowanie

- Jeden **plik logu na każde uruchomienie** (TXT lub CSV).
- Nazwa zawiera timestamp.
- Plik zapisywany do SharePoint.

### Wpis w logu (per e-mail):
- timestamp uruchomienia,
- email nadawcy,
- temat e-maila,
- status:
  - `PROCESSED`
  - `SKIPPED_BUSINESS_ERROR`
  - `SKIPPED_TECHNICAL_ERROR`
- typ błędu (jeśli dotyczy):
  - BUSINESS
  - TECHNICAL
  - UNEXPECTED

Nie zapisujemy liczby EAN-ów.

---

## 10. Zarządzanie statusem e-maila

- E-mail przetworzony poprawnie → **MARK AS READ**
- E-mail pominięty (brak daty) → **POZOSTAJE UNREAD**
- E-mail z błędem technicznym → **POZOSTAJE UNREAD**, przetwarzanie idzie dalej

---

## 11. SharePoint

- Folder docelowy:
  - **istnieje wcześniej**,
  - jest przekazany w konfiguracji.
- Upload realizowany przez **Microsoft Graph API**.
- Do tego samego folderu trafiają:
  - Excel,
  - plik logu.

---

## 12. Claude (Anthropic API)

Claude jest **opcjonalny** i używany wyłącznie, gdy:
- deterministyczna ekstrakcja się nie powiodła,
- OCR zwróciło niejednoznaczne dane,
- wymagane jest uporządkowanie konfliktów.

Zasady:
- Claude **nie wymyśla danych**,
- **nie uzupełnia braków**,
- **nie interpretuje intencji**,
- działa wyłącznie na dostarczonym tekście (OCR / body / attachment text).

---

## 13. Konfiguracja

Wszystkie ustawienia znajdują się poza kodem (np. `.env`):

- dane dostępu do Microsoft Graph,
- identyfikacja skrzynki,
- lokalizacja folderu SharePoint,
- ścieżki do OCR / PDF tools,
- klucz Claude API (opcjonalnie),
- tryb uruchomienia.

Sekrety **nie mogą** być zapisane w kodzie.

---

## 14. Tryby uruchomienia

### Manualny
- CLI z parametrami:
  - pojedyncza data,
  - zakres dat.

### Automatyczny
- Windows Task Scheduler,
- uruchomienie raz dziennie,
- zakres: **poprzednie 24 godziny**.

---

## 15. Stos technologiczny

- Python 3.11+
- Microsoft Graph API
- Tesseract OCR
- Poppler (PDF rendering)
- openpyxl / pandas
- Anthropic Claude API (opcjonalnie)
- Windows Task Scheduler

---

## 16. Definition of Done

Projekt uznaje się za ukończony, gdy:
- wszystkie reguły są zaimplementowane dokładnie,
- brak inferencji w kodzie,
- każdy run generuje Excel + log,
- system działa stabilnie 24/7,
- błędy pojedynczych e-maili nie blokują całego procesu.

---

## 17. Instrukcja dla Claude Code

Ten dokument jest **wiążącą specyfikacją**.
Claude Code:
- nie może jej reinterpretować,
- nie może upraszczać,
- musi pytać, jeśli coś jest niejasne,
- implementuje punkt po punkcie.

---

## 18. Instalacja i Konfiguracja

### Wymagania systemowe
- Windows 11
- Python 3.11+
- Tesseract OCR
- Poppler (PDF rendering)

### Instalacja zależności

```bash
# Zainstaluj Python dependencies
pip install -r requirements.txt

# Zainstaluj Tesseract OCR
# Pobierz z: https://github.com/UB-Mannheim/tesseract/wiki
# Domyślna ścieżka: C:\Program Files\Tesseract-OCR\tesseract.exe

# Zainstaluj Poppler
# Pobierz z: https://github.com/oschwartz10612/poppler-windows/releases
# Domyślna ścieżka: C:\Program Files\poppler\bin
```

### Konfiguracja

1. Skopiuj `.env.example` do `.env`:
   ```bash
   copy .env.example .env
   ```

2. Wypełnij wartości w `.env`:
   - `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` - dane Azure AD App
   - `MAILBOX_USER_ID` - adres email skrzynki do przetwarzania
   - `SHAREPOINT_SITE_ID`, `SHAREPOINT_DRIVE_ID`, `SHAREPOINT_FOLDER_PATH` - lokalizacja SharePoint
   - `TESSERACT_PATH`, `POPPLER_PATH` - ścieżki do narzędzi OCR
   - `ANTHROPIC_API_KEY` - opcjonalnie, klucz Claude API

### Azure AD App Setup

Aplikacja wymaga następujących uprawnień Microsoft Graph (Application permissions):
- `Mail.Read` - odczyt emaili
- `Mail.ReadWrite` - oznaczanie jako przeczytane
- `Sites.ReadWrite.All` - upload do SharePoint

---

## 19. Użycie

### Tryb manualny (pojedyncza data)

```bash
# Przetwórz emaile z konkretnej daty
python -m src.main --date 2024-01-15

# Tryb dry-run (bez mark-as-read i upload)
python -m src.main --date 2024-01-15 --dry-run
```

### Tryb manualny (zakres dat)

```bash
# Przetwórz emaile z zakresu dat
python -m src.main --date-from 2024-01-15 --date-to 2024-01-20
```

### Tryb automatyczny (ostatnie 24h)

```bash
# Przetwórz emaile z ostatnich 24 godzin
python -m src.main --auto
```

### Windows Task Scheduler

1. Otwórz Task Scheduler
2. Create Basic Task:
   - Name: "Price Discrepancy Processor"
   - Trigger: Daily, 8:00 AM
   - Action: Start a program
   - Program: `C:\path\to\scripts\run_scheduled.bat`
3. Configure settings:
   - Run whether user is logged on or not
   - Run with highest privileges

---

## 20. Testy

```bash
# Uruchom wszystkie testy
pytest

# Uruchom konkretny test
pytest tests/test_validators.py

# Uruchom z coverage
pytest --cov=src tests/
```

---

## 21. Struktura projektu

```
price-discrepancy-agent/
├── src/
│   ├── main.py                    # CLI entrypoint
│   ├── config.py                  # Konfiguracja
│   ├── core/
│   │   ├── models.py              # Modele danych
│   │   ├── pipeline.py            # Główny pipeline
│   │   ├── extractors.py          # Ekstrakcja danych
│   │   ├── validators.py          # Walidatory
│   │   ├── normalize.py           # Normalizacja
│   │   └── priority.py            # Priority merge
│   ├── integrations/
│   │   ├── graph/
│   │   │   ├── auth.py            # MSAL auth
│   │   │   ├── mail.py            # Outlook operations
│   │   │   ├── queries.py         # Query builders
│   │   │   └── sharepoint.py      # SharePoint upload
│   │   ├── ocr/
│   │   │   ├── tesseract.py       # Tesseract wrapper
│   │   │   ├── pdf_render.py      # PDF to images
│   │   │   ├── image_extract.py   # Image extraction
│   │   │   └── ocr_pipeline.py    # OCR orchestration
│   │   ├── excel/
│   │   │   ├── parser.py          # XLSX parser
│   │   │   └── writer.py          # Excel writer
│   │   ├── logging/
│   │   │   └── run_log.py         # Log writer
│   │   └── anthropic/
│   │       └── client.py          # Claude fallback (optional)
│   └── utils/
│       └── text.py                # Text utilities (regex)
├── tests/                         # Unit tests
├── scripts/                       # Bat scripts
├── logs/                          # Scheduled run logs
├── .env.example                   # Example config
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```