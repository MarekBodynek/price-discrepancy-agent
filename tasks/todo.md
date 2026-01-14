# Plan implementacji - Price Discrepancy Email Processor

## EPIC 0: Repo i uruchamialność
- [ ] 0.1 Struktura folderów (już istnieje)
- [ ] 0.2 `requirements.txt` + `.env.example` + `.gitignore` (już istnieje)
- [ ] 0.3 `src/main.py` - argumenty CLI, wczytanie configu, stub pipeline
- [ ] 0.4 `scripts/run_manual.bat` i `scripts/run_scheduled.bat`

## EPIC 1: Konfiguracja i modele danych
- [ ] 1.1 `src/config.py` - loader `.env` + walidacja (brak wartości = twardy błąd)
- [ ] 1.2 `src/core/models.py` - EmailItem, CaseRow, EmailProcessResult, RunResult
- [ ] 1.3 `src/integrations/logging/formats.py` - enumy statusów i typów błędów

## EPIC 2: Microsoft Graph - mail
- [ ] 2.1 `src/integrations/graph/auth.py` - MSAL client credentials flow
- [ ] 2.2 `src/integrations/graph/queries.py` - builder filtrów (unread, date range, Slovenia TZ)
- [ ] 2.3 `src/integrations/graph/mail.py` - list messages, fetch body, attachments, inline images
- [ ] 2.4 `src/integrations/graph/mail.py` - mark message as read

## EPIC 3: SharePoint upload
- [ ] 3.1 `src/integrations/graph/sharepoint.py` - upload file
- [ ] 3.2 `src/integrations/graph/sharepoint.py` - suffix `_v2` jeśli plik istnieje

## EPIC 4: OCR lokalny
- [ ] 4.1 `src/integrations/ocr/pdf_render.py` - PDF → PNG (Poppler pdftoppm)
- [ ] 4.2 `src/integrations/ocr/tesseract.py` - wrapper Tesseract
- [ ] 4.3 `src/integrations/ocr/image_extract.py` - wyciąganie obrazów (inline, attachments, PDF)
- [ ] 4.4 `src/integrations/ocr/ocr_pipeline.py` - OCR_TEXT_BLOB + metadane

## EPIC 5: XLSX parsing
- [ ] 5.1 `src/integrations/excel/parser.py` - deterministyczne parsowanie XLSX

## EPIC 6: Ekstrakcja danych
- [ ] 6.1 `src/utils/text.py` - regexy (EAN, ceny, daty, invoice number)
- [ ] 6.2 `src/core/priority.py` - scalanie wg priorytetu (OCR > attachments > body)
- [ ] 6.3 `src/core/validators.py` - mandatory delivery/order date gate
- [ ] 6.4 `src/core/normalize.py` - normalizacja (ISO daty, EAN, ceny)
- [ ] 6.5 `src/core/pipeline.py` - orkiestracja per email

## EPIC 7: Excel writer + log writer
- [ ] 7.1 `src/integrations/excel/writer.py` - XLSX z kolumnami w kolejności
- [ ] 7.2 `src/integrations/logging/run_log.py` - log TXT/CSV per run
- [ ] 7.3 Upload Excel + log do SharePoint

## EPIC 8: Claude fallback (opcjonalny)
- [ ] 8.1 `src/integrations/anthropic/client.py` - wywołanie Claude
- [ ] 8.2 `src/integrations/anthropic/prompts.py` - prompty (never infer)
- [ ] 8.3 Integracja fallback w pipeline

## EPIC 9: Testy + stabilizacja
- [ ] 9.1 Unit tests (priorytety, normalizacja, walidacja dat, suffix naming)
- [ ] 9.2 Test dry-run na fixtures
- [ ] 9.3 Instrukcja Task Scheduler

---

## Kolumny Excel (kolejność obowiązkowa)
1. Unit (Store)
2. EAN Code
3. Document Creation Date
4. Delivery Date
5. Order Creation Date
6. Supplier Price
7. Internal (Own) Price
8. Supplier Name
9. Supplier Invoice Number
10. Email Sender Address
11. Email Link / Stable Reference
12. Comments

## Hard Stop Rule
Brak Delivery Date AND Order Creation Date → SKIP email, UNREAD, BUSINESS ERROR

## Priorytet źródeł
1. OCR (obrazy inline + załączniki + PDF images)
2. Załączniki (Excel, PDF text)
3. Body e-maila

---

## Review
(uzupełnić po zakończeniu)
