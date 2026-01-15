# Dokumentacja - Price Discrepancy Agent

Witaj w dokumentacji projektu Price Discrepancy Agent!

## 📚 Przewodniki konfiguracji

### 1. [Azure AD Setup](AZURE_AD_SETUP.md)
Szczegółowy przewodnik konfiguracji Azure AD App Registration:
- Rejestracja aplikacji w Azure Portal
- Konfiguracja uprawnień Microsoft Graph API
- Uzyskanie Client ID, Tenant ID, Client Secret
- Znalezienie SharePoint Site ID i Drive ID
- Troubleshooting i bezpieczeństwo

**Przeczytaj to NAJPIERW przed wdrożeniem!**

### 2. [OCR Tools Setup](OCR_TOOLS_SETUP.md)
Instrukcje instalacji narzędzi OCR:
- Tesseract OCR (rozpoznawanie tekstu)
- Poppler (konwersja PDF do obrazów)
- Dla Windows 11, macOS i Linux
- Konfiguracja języków (eng, slv, pol)
- Testy i troubleshooting

## 🚀 Quick Start

### Krok po kroku wdrożenie:

#### 1. Klonuj repozytorium i zainstaluj zależności
```bash
git clone https://github.com/MarekBodynek/price-discrepancy-agent.git
cd price-discrepancy-agent
pip install -r requirements.txt
```

#### 2. Zainstaluj narzędzia OCR
Postępuj zgodnie z [OCR_TOOLS_SETUP.md](OCR_TOOLS_SETUP.md)

#### 3. Skonfiguruj Azure AD
Postępuj zgodnie z [AZURE_AD_SETUP.md](AZURE_AD_SETUP.md)

#### 4. Skopiuj i wypełnij .env
```bash
cp .env.example .env
# Edytuj .env i wypełnij wszystkie wymagane wartości
```

#### 5. Przetestuj konfigurację
```bash
# Test importu i składni
python3 -c "from src.config import load_config; print('✅ Config OK')"

# Uruchom testy jednostkowe
python3 -m pytest tests/ -v

# Test połączenia z Azure AD
python3 -c "from src.config import load_config; from src.integrations.graph.auth import GraphAuthClient; config = load_config(); auth = GraphAuthClient(config); token = auth.get_token(); print('✅ Azure AD OK')"
```

#### 6. Pierwszy run w trybie dry-run
```bash
# Przetworzy emaile z dzisiaj, ale NIE oznaczy jako przeczytane i NIE uploaduje do SharePoint
python3 -m src.main --auto --dry-run
```

#### 7. Produkcyjny run
```bash
# Po weryfikacji wyników, uruchom bez --dry-run
python3 -m src.main --auto
```

## 📖 Dokumentacja techniczna

### Architektura
Projekt składa się z następujących komponentów:

```
src/
├── cli/              # CLI interface (główny entrypoint)
├── config.py         # Konfiguracja z .env
├── core/             # Logika biznesowa
│   ├── models.py     # Modele danych (EmailItem, ExtractedData, CaseRow)
│   ├── extractors.py # Ekstrakcja danych z emaili/załączników
│   ├── validators.py # Walidacja (Hard Stop Rule: mandatory date gate)
│   ├── normalize.py  # Normalizacja danych
│   ├── priority.py   # Priority merge (OCR > attachments > body)
│   └── pipeline.py   # Orchestration całego procesu
├── integrations/     # Integracje zewnętrzne
│   ├── graph/        # Microsoft Graph API (Outlook, SharePoint)
│   ├── ocr/          # OCR (Tesseract, Poppler)
│   ├── anthropic/    # Claude API (fallback dla niejednoznacznych przypadków)
│   ├── excel/        # Excel parser i writer
│   └── logging/      # Log writer
└── utils/            # Narzędzia pomocnicze (regex, text processing)
```

### Kluczowe funkcje

#### Hard Stop Rule (Mandatory Date Gate)
Email MUSI zawierać **Delivery Date LUB Order Creation Date**.
- Jeśli nie: email jest **SKIPPED** i pozostaje **UNREAD**
- Logika: `src/core/validators.py:validate_mandatory_date_gate()`
- Testy: `tests/test_validators.py`, `tests/test_pipeline.py`

#### Priority Merge
Dane z różnych źródeł są mergowane według priorytetu:
1. **OCR** (najwyższy priorytet)
2. **Attachments** (Excel, PDF)
3. **Email Body** (najniższy priorytet)

Konflikty są wykrywane i logowane.
- Logika: `src/core/priority.py`
- Testy: `tests/test_priority.py`

#### Continue-on-Error Pattern
- **BUSINESS_ERROR**: Email nie spełnia wymagań biznesowych → SKIPPED, pozostaje UNREAD
- **TECHNICAL_ERROR**: Błąd techniczny (OCR failed, etc.) → SKIPPED, pozostaje UNREAD, inne emaile są dalej przetwarzane
- Logika: `src/core/pipeline.py:process_single_email()`
- Testy: `tests/test_pipeline.py`

#### Dry-Run Mode
```bash
python3 -m src.main --auto --dry-run
```
- Przetwarza emaile normalnie
- **NIE** oznacza emaili jako przeczytane
- **NIE** uploaduje do SharePoint
- Generuje Excel i log lokalnie
- Idealne do testowania

### CLI Usage

```bash
# Przetwórz emaile z konkretnej daty
python3 -m src.main --date 2024-01-15

# Przetwórz emaile z zakresu dat
python3 -m src.main --date-from 2024-01-10 --date-to 2024-01-15

# Przetwórz emaile z ostatnich 24h (automatyczny zakres)
python3 -m src.main --auto

# Dry-run (nie oznacza jako przeczytane, nie uploaduje)
python3 -m src.main --auto --dry-run

# Pomoc
python3 -m src.main --help
```

### Pliki wyjściowe

Po uruchomieniu aplikacja generuje:

1. **Excel Report**: `Price_Discrepancies_YYYY-MM-DD.xlsx` (lub `_YYYY-MM-DD_to_YYYY-MM-DD.xlsx` dla zakresów)
   - 12 kolumn zgodnie ze specyfikacją
   - Jeden wiersz na EAN
   - Wszystkie daty, ceny, dane dostawcy

2. **Run Log**: `Run_Log_YYYYMMDD_HHMMSS.txt`
   - Podsumowanie przebiegu
   - Statystyki (processed, skipped, errors)
   - Szczegóły błędów
   - Lista przetworzonych emaili

Oba pliki są uploadowane do SharePoint (chyba że --dry-run).

## 🧪 Testy

### Uruchomienie testów
```bash
# Wszystkie testy
python3 -m pytest tests/ -v

# Konkretny moduł
python3 -m pytest tests/test_pipeline.py -v

# Z coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage (aktualny: 44%)
- Core components: 78% średnio
- Models: 100%
- Normalizers: 98%
- Priority merge: 97%
- Config: 92%
- Text utils: 88%

Zobacz [TEST_REPORT.md](../TEST_REPORT.md) dla pełnych wyników.

## 🔧 Troubleshooting

### Najczęstsze problemy i rozwiązania:

#### "Azure AD: Insufficient privileges"
→ Zobacz [AZURE_AD_SETUP.md](AZURE_AD_SETUP.md) sekcja Troubleshooting

#### "Tesseract not found"
→ Zobacz [OCR_TOOLS_SETUP.md](OCR_TOOLS_SETUP.md) sekcja Troubleshooting

#### "ConfigError: Missing required configuration"
→ Sprawdź plik `.env`, wszystkie wymagane pola muszą być wypełnione

#### Emaile nie są przetwarzane
1. Sprawdź filtr dat (--date, --date-from/--date-to, --auto)
2. Sprawdź timezone (domyślnie Europe/Ljubljana)
3. Sprawdź, czy emaile są UNREAD
4. Sprawdź logi w `Run_Log_*.txt`

#### Hard Stop Rule: "MANDATORY DATE GATE"
- Email nie zawiera Delivery Date ANI Order Creation Date
- To jest **zamierzone zachowanie** - email pozostaje UNREAD
- Sprawdź treść emaila i załączniki

## 📊 Monitoring

### Metryki do śledzenia:
- Liczba przetworzonych emaili
- Liczba BUSINESS vs TECHNICAL errors
- Success rate SharePoint upload
- OCR success rate (% emaili z danymi z OCR)
- Claude API usage (jeśli używany)

### Logi:
- Każdy run generuje `Run_Log_*.txt` z pełnym podsumowaniem
- Logi zawierają timestampy, statusy, błędy
- Przechowuj logi w SharePoint dla audytu

## 🔐 Bezpieczeństwo

### Best Practices:
1. **NIGDY** nie commituj `.env` do Git
2. Rotuj Client Secret regularnie (przed wygaśnięciem)
3. Używaj minimum wymaganych uprawnień
4. Regularnie przeglądaj logi logowania w Azure AD
5. Traktuj Client Secret jak hasło (nie udostępniaj, nie zapisuj w plaintext)

### Backup:
- Regularnie backupuj pliki Excel i logi z SharePoint
- Zachowaj kopie `.env` w bezpiecznym miejscu (np. Azure Key Vault)

## 📞 Support

### Problemy?
1. Sprawdź [Troubleshooting](#-troubleshooting) powyżej
2. Sprawdź [AZURE_AD_SETUP.md](AZURE_AD_SETUP.md) lub [OCR_TOOLS_SETUP.md](OCR_TOOLS_SETUP.md)
3. Przeczytaj logi `Run_Log_*.txt`
4. Sprawdź testy jednostkowe: `pytest tests/ -v`
5. Zgłoś issue na GitHub (jeśli projekt jest publiczny)

## 🚀 Roadmap

### Planowane funkcje (opcjonalnie):
- [ ] Dashboard z metrykami (Streamlit/Dash)
- [ ] Email notifications przy błędach
- [ ] Scheduled runs (cron/Task Scheduler)
- [ ] Multi-mailbox support
- [ ] Advanced conflict resolution UI
- [ ] ML-based price prediction

## 📝 Licencja

[Tutaj dodaj informacje o licencji projektu]

---

**Pytania?** Przeczytaj przewodniki w [docs/](.) lub skontaktuj się z zespołem developerskim.
