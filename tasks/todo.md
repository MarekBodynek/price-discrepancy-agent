# Analiza jakości testów - Price Discrepancy Agent

## Stan obecny testów (2026-01-14)

### Statystyki testów
- **Liczba testów**: 22 (w 4 plikach testowych)
- **Coverage całościowy**: ~23% (935/1207 linii niepokrytych)
- **Coverage core modules**: ~89% (models, priority, validators, normalizers)
- **Status testów**: Wszystkie 22 testy PASSED

### Pliki testowe
1. `tests/test_validators.py` - 7 testów
2. `tests/test_priority.py` - 4 testy
3. `tests/test_normalizers.py` - 6 testów
4. `tests/test_text_utils.py` - 5 testów

---

## 1. Ocena obecnych testów jednostkowych

### ✅ Co jest dobrze przetestowane

#### 1.1 Validators (67% coverage, kluczowe funkcje 100%)
- ✅ Mandatory Date Gate (Hard Stop Rule) - KOMPLETNY
  - Test z Delivery Date
  - Test z Order Creation Date
  - Test z obiema datami
  - Test bez żadnej daty (ValidationError)
- ✅ Walidacja EAN (różne długości, nieprawidłowe formaty)
- ✅ Walidacja cen (dodatnie, zerowe, ujemne)
- ✅ Walidacja zakresów dat (2000-2100)

**Brakuje**: `validate_extracted_data()` - agregująca walidacja (linijki 110-135)

#### 1.2 Priority Merge (97% coverage)
- ✅ Priorytet OCR > Attachments > Body
- ✅ Łączenie EAN-ów ze wszystkich źródeł
- ✅ Merge dict fields (ceny per EAN z różnych źródeł)
- ✅ Konflikt detection i logging
- ✅ Pusta lista ekstrakcji

**Brakuje**: Linijki 47, 111 (edge cases w merge_field)

#### 1.3 Normalizers (98% coverage)
- ✅ EAN normalization (usuwanie spacji, prefiksów)
- ✅ Price normalization (zaokrąglanie do 2 miejsc)
- ✅ Text normalization (whitespace, None handling)
- ✅ Supplier name (title case)
- ✅ Store (uppercase)
- ✅ Invoice number (uppercase)

**Brakuje**: Linijka 53 (edge case w normalize_price)

#### 1.4 Text Utils (82% coverage)
- ✅ Ekstrakcja EAN (różne formaty)
- ✅ Ekstrakcja cen (z walutami)
- ✅ Ekstrakcja numerów faktur
- ✅ Ekstrakcja dat (YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY)
- ✅ find_date_by_keyword (delivery, order)

**Brakuje**:
- Linijki 69-70 (ValueError handling w extract_prices)
- Linijki 111-114 (format daty DD MMM YYYY)
- Linijki 119-120 (ValueError handling w extract_dates)
- Linijki 135-136 (extract_stores)
- Linijki 149-150 (extract_suppliers)

---

## 2. Identyfikacja brakujących test cases

### 🔴 KRYTYCZNE BRAKI (0% coverage)

#### 2.1 Pipeline Orchestration (`src/core/pipeline.py` - 0% coverage)
**To jest SERCE systemu - wymaga priorytetowych testów!**

Brakujące test cases:
- ❌ `process_single_email()` - główna funkcja przetwarzania
  - Test happy path (wszystkie źródła mają dane)
  - Test z OCR tylko
  - Test z attachments tylko
  - Test z body tylko
  - Test z BUSINESS_ERROR (brak dat) → UNREAD, SKIP
  - Test z TECHNICAL_ERROR (exception w extractor) → UNREAD, CONTINUE
  - Test dry-run mode (marked_as_read = False)

- ❌ `generate_case_rows()` - generowanie wierszy Excel
  - Test z wieloma EAN-ami
  - Test bez EAN-ów (UNKNOWN)
  - Test z konfliktami (sprawdzenie Comments)
  - Test z OCR usage note
  - Test mapowania EAN → store, prices

- ❌ `run_pipeline()` - główna pętla
  - Test continue-on-error (błąd jednego emaila nie blokuje innych)
  - Test mark-as-read po sukcesie
  - Test UNREAD po błędzie biznesowym
  - Test UNREAD po błędzie technicznym
  - Test generowania Excel + log
  - Test SharePoint upload (mock)
  - Test dry-run (brak upload, brak mark-as-read)

#### 2.2 Extractors (`src/core/extractors.py` - 0% coverage)
**Kluczowe dla priorytetów OCR > Attachments > Body**

Brakujące test cases:
- ❌ `extract_from_ocr()` - ekstrakcja z obrazów
  - Test z prawidłowym OCR tekstem
  - Test bez obrazów (return None)
  - Test ekstrakcji dat (delivery, order, document)
  - Test ekstrakcji cen i przypisania do EAN
  - Test ekstrakcji store i supplier

- ❌ `extract_from_attachments()` - ekstrakcja z załączników
  - Test z Excel attachment
  - Test z PDF attachment
  - Test z obrazem (skip - handled by OCR)
  - Test z wieloma załącznikami
  - Test z błędem parsowania (exception handling)

- ❌ `extract_from_body()` - ekstrakcja z treści emaila
  - Test z HTML body (stripping tagów)
  - Test z text body
  - Test z pustym body (return None)
  - Test ekstrakcji wszystkich pól

#### 2.3 Config (`src/config.py` - 0% coverage)
Brakujące test cases:
- ❌ Walidacja .env (brak wymaganych wartości → błąd)
- ❌ Walidacja ścieżek (Tesseract, Poppler)
- ❌ Walidacja Azure credentials
- ❌ Default values

---

### 🟡 ŚREDNI PRIORYTET (0% coverage)

#### 2.4 Integracje Graph API
**Microsoft Graph - mail operations**
- ❌ `GraphMailClient.list_unread_messages()` - filtrowanie po dacie + unread
- ❌ `GraphMailClient.get_email_item()` - fetch full email
- ❌ `GraphMailClient.mark_as_read()` - oznaczanie jako przeczytane
- ❌ Query builder (date range, Slovenia TZ)

**SharePoint upload**
- ❌ `GraphSharePointClient.upload_file()` - upload z collision handling
- ❌ Suffix naming (_v2, _v3)

**Auth**
- ❌ `GraphAuthClient` - MSAL token acquisition

#### 2.5 OCR Pipeline
- ❌ `OCRPipeline.get_combined_ocr_text()` - łączenie OCR z wielu źródeł
- ❌ `TesseractOCR.run_ocr()` - wrapper Tesseract
- ❌ `PDFRenderer.render_to_images()` - PDF → PNG
- ❌ `ImageExtractor` - ekstrakcja inline + attachments

#### 2.6 Excel Operations
- ❌ `ExcelParser.extract_text_from_xlsx()` - parsing XLSX
- ❌ `ExcelWriter.write_report()` - generowanie pliku Excel
- ❌ Walidacja kolejności kolumn (1-12 zgodnie z README)
- ❌ Generowanie filename (date range, suffixes)

#### 2.7 Logging
- ❌ `RunLogWriter.write_log()` - generowanie logu per run
- ❌ Format logu (timestamp, status, error_type)
- ❌ Generowanie filename

---

### 🟢 NISKI PRIORYTET (opcjonalne)

#### 2.8 Claude Fallback (`src/integrations/anthropic/` - 0% coverage)
- Obecnie nie używany domyślnie
- Można pominąć w pierwszej iteracji testów

#### 2.9 Main CLI (`src/main.py` - 0% coverage)
- Argumenty CLI (--date, --date-from, --date-to, --auto, --dry-run)
- Parsing argumentów
- Error handling

---

## 3. Sprawdzenie pokrycia wymagań z README.md

### ✅ Zweryfikowane wymagania (przez obecne testy)

1. **Hard Stop Rule (Mandatory Date Gate)** ✅
   - Test z Delivery Date ✅
   - Test z Order Creation Date ✅
   - Test bez żadnej daty → SKIP ✅
   - ValidationError ✅

2. **Priority Merge (OCR > Attachments > Body)** ✅
   - OCR wins ✅
   - Attachment fallback ✅
   - Body fallback ✅
   - Conflict detection ✅

3. **Data Normalization** ✅
   - EAN ✅
   - Prices (2 decimal places) ✅
   - Dates (ISO) ✅
   - Text (whitespace) ✅

4. **Data Validation** ✅
   - EAN format (8 or 13 digits) ✅
   - Price > 0 ✅
   - Date range (2000-2100) ✅

### ❌ NIEzweryfikowane wymagania (brak testów)

1. **Continue-on-error** ❌
   - Błąd jednego emaila nie blokuje innych
   - TECHNICAL_ERROR → SKIP, UNREAD, CONTINUE
   - Brak testów pipeline'u

2. **Email Status Management** ❌
   - Mark-as-read po PROCESSED
   - Leave UNREAD po BUSINESS_ERROR
   - Leave UNREAD po TECHNICAL_ERROR
   - Brak testów mail operations

3. **Excel Generation** ❌
   - Kolumny 1-12 w poprawnej kolejności
   - Jeden wiersz per EAN
   - Comments (conflicts, OCR usage)
   - Brak testów ExcelWriter

4. **Log Generation** ❌
   - Per-run log file
   - Status logging (PROCESSED / SKIPPED_*)
   - Error type logging
   - Brak testów RunLogWriter

5. **SharePoint Upload** ❌
   - Upload Excel + log
   - Collision handling (_v2, _v3)
   - Brak testów SharePoint client

6. **OCR Priority** ❌
   - OCR z inline images
   - OCR z attachments (JPG, PNG)
   - OCR z PDF images
   - Brak testów OCR pipeline

7. **Dry-run Mode** ❌
   - No mark-as-read
   - No SharePoint upload
   - Brak testów pipeline w dry-run

---

## 4. Propozycja dodatkowych testów dla zwiększenia pokrycia

### 🎯 Faza 1: Testy krytycznych ścieżek (priorytet WYSOKI)

#### 4.1 Pipeline Integration Tests
```python
# tests/test_pipeline_integration.py

def test_process_single_email_happy_path():
    """Test przetwarzania emaila z wszystkimi danymi."""
    # Mock email z OCR, attachments, body
    # Verify: PROCESSED, cases extracted, marked_as_read=True

def test_process_single_email_business_error_no_dates():
    """Test Hard Stop Rule - brak Delivery i Order Date."""
    # Mock email bez dat
    # Verify: SKIPPED_BUSINESS_ERROR, marked_as_read=False

def test_process_single_email_technical_error():
    """Test błędu technicznego (exception w extractor)."""
    # Mock extractor raising exception
    # Verify: SKIPPED_TECHNICAL_ERROR, marked_as_read=False

def test_process_single_email_dry_run():
    """Test dry-run mode."""
    # Mock email
    # Verify: marked_as_read=False (nawet po sukcesie)

def test_generate_case_rows_multiple_eans():
    """Test generowania wielu wierszy (per EAN)."""
    # Verify: jeden wiersz per EAN

def test_generate_case_rows_conflicts_in_comments():
    """Test zapisu konfliktów w Comments."""
    # Verify: konflikty w kolumnie Comments

def test_run_pipeline_continue_on_error():
    """Test continue-on-error: błąd jednego emaila nie blokuje innych."""
    # Mock 3 emails: success, business error, success
    # Verify: 2 PROCESSED, 1 SKIPPED_BUSINESS_ERROR
```

#### 4.2 Extractors Unit Tests
```python
# tests/test_extractors.py

def test_extract_from_ocr_with_images():
    """Test ekstrakcji z OCR."""
    # Mock OCR text
    # Verify: ExtractedData z DataSource.OCR

def test_extract_from_ocr_no_images():
    """Test bez obrazów."""
    # Verify: return None

def test_extract_from_attachments_excel():
    """Test ekstrakcji z Excel attachment."""
    # Mock Excel bytes
    # Verify: ExtractedData z DataSource.ATTACHMENT

def test_extract_from_attachments_skip_images():
    """Test pomijania obrazów (OCR handled separately)."""
    # Mock image attachment
    # Verify: empty list

def test_extract_from_body_html():
    """Test ekstrakcji z HTML body (strip tags)."""
    # Mock HTML
    # Verify: ExtractedData z DataSource.BODY

def test_extract_from_body_empty():
    """Test z pustym body."""
    # Verify: return None
```

#### 4.3 Config Validation Tests
```python
# tests/test_config.py

def test_config_missing_required_env():
    """Test błędu gdy brakuje wymaganych zmiennych .env."""
    # Verify: ValidationError

def test_config_invalid_paths():
    """Test błędu gdy ścieżki nie istnieją."""
    # Verify: ValidationError

def test_config_defaults():
    """Test domyślnych wartości."""
    # Verify: default values applied
```

---

### 🎯 Faza 2: Testy integracyjne (priorytet ŚREDNI)

#### 4.4 Excel Writer Tests
```python
# tests/test_excel_writer.py

def test_write_report_column_order():
    """Test poprawnej kolejności kolumn (1-12)."""
    # Verify: kolumny zgodne z README

def test_write_report_multiple_eans():
    """Test wielu wierszy (per EAN)."""
    # Verify: jeden wiersz per EAN

def test_generate_filename_single_date():
    """Test filename dla pojedynczej daty."""
    # Verify: Price_Discrepancies_YYYY-MM-DD.xlsx

def test_generate_filename_date_range():
    """Test filename dla zakresu dat."""
    # Verify: Price_Discrepancies_YYYY-MM-DD_to_YYYY-MM-DD.xlsx
```

#### 4.5 Mail Client Tests (z mockami)
```python
# tests/test_mail_client.py

def test_list_unread_messages_date_filter():
    """Test filtrowania po dacie i UNREAD."""
    # Mock Graph API
    # Verify: query z date range + isRead=false

def test_mark_as_read():
    """Test oznaczania jako przeczytane."""
    # Mock Graph API PATCH
    # Verify: isRead=true

def test_get_email_item_with_attachments():
    """Test pobierania pełnego emaila z załącznikami."""
    # Mock Graph API
    # Verify: EmailItem z attachments
```

#### 4.6 SharePoint Upload Tests (z mockami)
```python
# tests/test_sharepoint_client.py

def test_upload_file_collision_handling():
    """Test collision handling (_v2, _v3)."""
    # Mock existing file
    # Verify: filename z suffiksem

def test_upload_file_success():
    """Test poprawnego uploadu."""
    # Mock Graph API
    # Verify: file uploaded
```

---

### 🎯 Faza 3: Testy edge cases (priorytet NISKI)

#### 4.7 Text Utils - dodatkowe testy
```python
# tests/test_text_utils_extended.py

def test_extract_prices_comma_vs_dot():
    """Test cen z przecinkiem i kropką."""
    # "10,50" i "10.50"

def test_extract_dates_dd_mmm_yyyy():
    """Test formatu DD MMM YYYY."""
    # "15 Jan 2024"

def test_extract_stores():
    """Test ekstrakcji store identifiers."""
    # "Store: ABC-123"

def test_extract_suppliers():
    """Test ekstrakcji nazw dostawców."""
    # "Supplier: Acme Corp"
```

#### 4.8 Validators - dodatkowe testy
```python
# tests/test_validators_extended.py

def test_validate_extracted_data_invalid_ean():
    """Test agregującej walidacji - nieprawidłowy EAN."""
    # Verify: warning w liście

def test_validate_extracted_data_date_out_of_range():
    """Test agregującej walidacji - data poza zakresem."""
    # Verify: warning w liście

def test_validate_extracted_data_invalid_price():
    """Test agregującej walidacji - nieprawidłowa cena."""
    # Verify: warning w liście
```

---

## 5. Podsumowanie i rekomendacje

### 📊 Obecny stan
- **Core logic (models, validators, priority, normalizers)**: ~89% coverage ✅
- **Pipeline orchestration**: 0% coverage ❌ KRYTYCZNE
- **Extractors**: 0% coverage ❌ KRYTYCZNE
- **Integrations**: 0% coverage ❌ WYSOKIE RYZYKO

### 🎯 Czy obecne testy wystarczają?

**NIE** - obecne testy pokrywają tylko ~23% kodu i nie weryfikują:
1. **Głównego pipeline'u** (process_single_email, run_pipeline)
2. **Continue-on-error** (kluczowe wymaganie)
3. **Email status management** (mark-as-read vs UNREAD)
4. **Generowania Excel + log** (output files)
5. **SharePoint upload** (delivery)
6. **OCR priority** (OCR > Attachments > Body w praktyce)

### 🚨 Krytyczne braki testowe

1. **NAJWYŻSZY PRIORYTET**: Pipeline integration tests
   - `process_single_email()` - serce systemu
   - `run_pipeline()` - continue-on-error
   - Error handling (BUSINESS vs TECHNICAL)

2. **WYSOKI PRIORYTET**: Extractors unit tests
   - OCR extraction
   - Attachment extraction
   - Body extraction
   - Priority verification

3. **ŚREDNI PRIORYTET**: Integration tests
   - Excel Writer (kolumny, format)
   - Mail Client (mock Graph API)
   - SharePoint Client (mock upload)

### ✅ Rekomendacje

#### Faza 1 (KRYTYCZNA - do implementacji natychmiast)
1. Dodać testy pipeline integration (8-10 testów)
2. Dodać testy extractors (6-8 testów)
3. Dodać testy config validation (3-4 testy)

**Target coverage po Fazie 1**: ~50-60%

#### Faza 2 (ŚREDNI PRIORYTET - przed wdrożeniem produkcyjnym)
1. Dodać testy Excel Writer
2. Dodać testy Mail Client (z mockami)
3. Dodać testy SharePoint Client (z mockami)
4. Dodać testy OCR Pipeline (z mockami)

**Target coverage po Fazie 2**: ~70-80%

#### Faza 3 (NISKI PRIORYTET - continuous improvement)
1. Dodać edge cases dla text utils
2. Dodać testy dla Claude fallback (jeśli używany)
3. Dodać E2E tests na fixtures

**Target coverage po Fazie 3**: >85%

### 📝 Plan działania

```markdown
## TODO: Zwiększenie pokrycia testami

### Faza 1: Testy krytycznych ścieżek (3-5 dni)
- [ ] 1.1 Utworzyć `tests/test_pipeline_integration.py`
  - [ ] test_process_single_email_happy_path
  - [ ] test_process_single_email_business_error_no_dates
  - [ ] test_process_single_email_technical_error
  - [ ] test_process_single_email_dry_run
  - [ ] test_generate_case_rows_multiple_eans
  - [ ] test_generate_case_rows_conflicts_in_comments
  - [ ] test_run_pipeline_continue_on_error

- [ ] 1.2 Utworzyć `tests/test_extractors.py`
  - [ ] test_extract_from_ocr_with_images
  - [ ] test_extract_from_ocr_no_images
  - [ ] test_extract_from_attachments_excel
  - [ ] test_extract_from_attachments_skip_images
  - [ ] test_extract_from_body_html
  - [ ] test_extract_from_body_empty

- [ ] 1.3 Utworzyć `tests/test_config.py`
  - [ ] test_config_missing_required_env
  - [ ] test_config_invalid_paths
  - [ ] test_config_defaults

### Faza 2: Testy integracyjne (5-7 dni)
- [ ] 2.1 Utworzyć `tests/test_excel_writer.py`
- [ ] 2.2 Utworzyć `tests/test_mail_client.py`
- [ ] 2.3 Utworzyć `tests/test_sharepoint_client.py`
- [ ] 2.4 Utworzyć `tests/test_ocr_pipeline.py`

### Faza 3: Edge cases i E2E (opcjonalne)
- [ ] 3.1 Rozszerzyć `tests/test_text_utils.py`
- [ ] 3.2 Rozszerzyć `tests/test_validators.py`
- [ ] 3.3 Utworzyć `tests/test_e2e_fixtures.py`
```

---

## Wnioski końcowe

**Obecne testy (22 testy, 23% coverage) NIE wystarczają** do weryfikacji kluczowych wymagań z README.md.

**Brakuje testów dla**:
- Pipeline orchestration (0% coverage) - **KRYTYCZNE**
- Extractors (0% coverage) - **KRYTYCZNE**
- Continue-on-error behavior - **NIE PRZETESTOWANE**
- Email status management - **NIE PRZETESTOWANE**
- Excel/Log generation - **NIE PRZETESTOWANE**

**Minimalny zakres testów przed wdrożeniem**:
- Faza 1 (pipeline + extractors) - **WYMAGANE**
- Faza 2 (integration tests) - **WYMAGANE**

**Target coverage**: minimum 70% przed wdrożeniem produkcyjnym.
