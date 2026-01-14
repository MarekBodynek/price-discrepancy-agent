# Plan implementacji - Price Discrepancy Email Processor

## Faza 1: Podstawowa struktura
- [ ] Utworzenie struktury katalogów
- [ ] Plik .env.example z placeholderami
- [ ] Plik .gitignore
- [ ] requirements.txt
- [ ] src/main.py - CLI entrypoint z argument parsing
- [ ] src/config.py - ładowanie konfiguracji z .env

## Faza 2: Microsoft Graph API
- [ ] src/graph/auth.py - MSAL client credentials flow
- [ ] src/graph/messages.py - pobieranie UNREAD e-maili w zakresie dat
- [ ] src/graph/attachments.py - pobieranie załączników i inline images
- [ ] src/graph/mark_read.py - oznaczanie e-maili jako READ
- [ ] Testy dla modułu graph

## Faza 3: SharePoint upload
- [ ] src/sharepoint/upload.py - upload plików przez Graph API
- [ ] Obsługa kolizji nazw (_v2, _v3, etc.)
- [ ] Testy dla modułu sharepoint

## Faza 4: OCR Pipeline
- [ ] src/ocr/tesseract.py - wrapper dla Tesseract OCR
- [ ] src/ocr/pdf_renderer.py - renderowanie PDF do obrazów (Poppler)
- [ ] src/ocr/pipeline.py - przetwarzanie obrazów i PDF
- [ ] Testy dla modułu ocr

## Faza 5: Ekstrakcja danych
- [ ] src/extraction/xlsx_parser.py - deterministyczne parsowanie Excel
- [ ] src/extraction/body_parser.py - parsowanie treści e-maila
- [ ] src/extraction/validators.py - walidacja dat, EAN, cen
- [ ] src/extraction/normalizers.py - normalizacja danych
- [ ] src/extraction/merger.py - łączenie danych z priorytetem źródeł
- [ ] Testy dla modułu extraction

## Faza 6: Raportowanie
- [ ] src/report/excel_writer.py - generowanie Excel z wynikami
- [ ] src/report/log_writer.py - generowanie pliku logu
- [ ] Testy dla modułu report

## Faza 7: Integracja
- [ ] src/pipeline.py - główny pipeline przetwarzania
- [ ] Tryb dry-run
- [ ] Obsługa błędów (BUSINESS vs TECHNICAL)
- [ ] Testy integracyjne

## Faza 8: Finalizacja
- [ ] Testy end-to-end z fixtures
- [ ] Dokumentacja użytkowania
- [ ] Review kodu

---

## Review
(uzupełnić po zakończeniu)
