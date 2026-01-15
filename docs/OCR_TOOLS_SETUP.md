# Instalacja narzędzi OCR - Tesseract i Poppler

Aplikacja wymaga dwóch narzędzi do przetwarzania obrazów i PDF:
- **Tesseract OCR** - rozpoznawanie tekstu z obrazów
- **Poppler** - konwersja PDF do obrazów

## Windows 11 (system docelowy)

### 1. Instalacja Tesseract OCR

#### Pobierz instalator:
1. Przejdź do: https://github.com/UB-Mannheim/tesseract/wiki
2. Pobierz najnowszą wersję dla Windows (np. `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

#### Zainstaluj:
1. Uruchom instalator
2. **WAŻNE**: Podczas instalacji zaznacz języki:
   - ✅ **English** (eng) - domyślnie zaznaczone
   - ✅ **Slovenian** (slv) - dodaj manualnie
   - ✅ **Polish** (pol) - dodaj manualnie (jeśli potrzebne)
3. Domyślna ścieżka instalacji: `C:\Program Files\Tesseract-OCR`
4. Zakończ instalację

#### Weryfikacja:
```cmd
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

Powinieneś zobaczyć:
```
tesseract 5.3.3
 leptonica-1.83.0
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.4) : libpng 1.6.39 : libtiff 4.5.0 : zlib 1.2.13 : libwebp 1.2.4
```

#### Lista zainstalowanych języków:
```cmd
"C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
```

Powinieneś zobaczyć:
```
List of available languages (3):
eng
pol
slv
```

### 2. Instalacja Poppler (pdftoppm)

#### Pobierz Poppler:
1. Przejdź do: https://github.com/oschwartz10612/poppler-windows/releases
2. Pobierz najnowszą wersję `Release-XX.XX.X-X.zip` (np. `Release-24.08.0-0.zip`)
3. Rozpakuj ZIP do folderu, np. `C:\Program Files\poppler-24.08.0`

#### Struktura po rozpakowaniu:
```
C:\Program Files\poppler-24.08.0\
├── Library\
│   ├── bin\          ← Tu znajduje się pdftoppm.exe
│   │   ├── pdftoppm.exe
│   │   ├── pdfinfo.exe
│   │   └── ...
│   └── ...
└── ...
```

#### Weryfikacja:
```cmd
"C:\Program Files\poppler-24.08.0\Library\bin\pdftoppm.exe" -v
```

Powinieneś zobaczyć:
```
pdftoppm version 24.08.0
Copyright 2005-2024 The Poppler Developers - http://poppler.freedesktop.org
Copyright 1996-2011, 2022 Glyph & Cog, LLC
```

### 3. Konfiguracja w .env

Dodaj ścieżki do pliku `.env`:

```env
# OCR Configuration
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Program Files\poppler-24.08.0\Library\bin

# OCR Languages (domyślnie: eng,slv)
OCR_LANGUAGES=eng,slv,pol
```

**UWAGA**: `POPPLER_PATH` to folder `bin`, nie plik `pdftoppm.exe`!

## macOS (dla development)

### 1. Instalacja Tesseract OCR

```bash
# Instalacja przez Homebrew
brew install tesseract

# Instalacja dodatkowych języków
brew install tesseract-lang

# Weryfikacja
tesseract --version
tesseract --list-langs
```

Domyślna ścieżka: `/usr/local/bin/tesseract` (Intel) lub `/opt/homebrew/bin/tesseract` (Apple Silicon)

### 2. Instalacja Poppler

```bash
# Instalacja przez Homebrew
brew install poppler

# Weryfikacja
pdftoppm -v
```

Domyślna ścieżka: `/usr/local/bin` (Intel) lub `/opt/homebrew/bin` (Apple Silicon)

### 3. Konfiguracja w .env (macOS)

```env
# OCR Configuration (Apple Silicon)
TESSERACT_PATH=/opt/homebrew/bin/tesseract
POPPLER_PATH=/opt/homebrew/bin

# OCR Configuration (Intel Mac)
# TESSERACT_PATH=/usr/local/bin/tesseract
# POPPLER_PATH=/usr/local/bin

OCR_LANGUAGES=eng,slv,pol
```

## Linux (Ubuntu/Debian)

### 1. Instalacja Tesseract OCR

```bash
# Aktualizacja pakietów
sudo apt update

# Instalacja Tesseract z językami
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-slv tesseract-ocr-pol

# Weryfikacja
tesseract --version
tesseract --list-langs
```

### 2. Instalacja Poppler

```bash
# Instalacja Poppler utils
sudo apt install poppler-utils

# Weryfikacja
pdftoppm -v
```

### 3. Konfiguracja w .env (Linux)

```env
# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
POPPLER_PATH=/usr/bin

OCR_LANGUAGES=eng,slv,pol
```

## Test OCR Pipeline

Po instalacji przetestuj OCR pipeline:

### Test 1: Tesseract z obrazem
```python
python3 -c "
from src.config import load_config
from src.integrations.ocr.tesseract import TesseractOCR

config = load_config()
ocr = TesseractOCR(config)
print('✅ Tesseract OCR działa!')
print(f'Języki: {config.ocr_languages}')
"
```

### Test 2: Poppler z PDF (wymaga przykładowego PDF)
```python
python3 -c "
from src.config import load_config
from src.integrations.ocr.pdf_render import PDFRenderer

config = load_config()
renderer = PDFRenderer(config)
print('✅ Poppler (pdftoppm) działa!')
"
```

## Troubleshooting

### Windows: "tesseract.exe not found"
- ✅ Sprawdź, czy ścieżka w .env jest poprawna
- ✅ Użyj pełnej ścieżki z rozszerzeniem `.exe`
- ✅ Upewnij się, że użyłeś odwrotnych ukośników `\` (nie `/`)

### Windows: "pdftoppm.exe not found"
- ✅ `POPPLER_PATH` powinien wskazywać na folder `bin`, nie na `pdftoppm.exe`
- ✅ Sprawdź, czy plik `pdftoppm.exe` faktycznie istnieje w tym folderze

### "Language 'slv' is not available"
- ✅ Podczas instalacji Tesseract zaznacz dodatkowe języki
- ✅ Lub doinstaluj języki:
  - Windows: Pobierz pliki `.traineddata` z https://github.com/tesseract-ocr/tessdata i umieść w `C:\Program Files\Tesseract-OCR\tessdata`
  - macOS: `brew install tesseract-lang`
  - Linux: `sudo apt install tesseract-ocr-slv`

### macOS: "command not found"
- ✅ Upewnij się, że Homebrew jest zainstalowany
- ✅ Sprawdź, czy masz Apple Silicon (M1/M2) czy Intel i użyj odpowiedniej ścieżki
- ✅ Uruchom `brew doctor` aby sprawdzić instalację Homebrew

### Niskiej jakości OCR
- ✅ Zwiększ DPI w ustawieniach (domyślnie 300, możesz użyć 600)
- ✅ Sprawdź, czy obraz jest wystarczająco ostry
- ✅ Upewnij się, że używasz odpowiednich języków (eng, slv)

## Wskazówki optymalizacji

### Wydajność OCR:
- DPI 300 jest dobrym balansem (jakość vs szybkość)
- DPI 600 dla bardzo małych fontów
- DPI 150 dla szybkiego testowania

### Języki OCR:
- Im mniej języków, tym szybszy OCR
- Używaj tylko potrzebnych języków (eng, slv)
- Kolejność ma znaczenie (najpierw najczęściej występujący)

### Pamięć:
- Przetwarzanie dużych PDF może wymagać więcej RAM
- Rozważ ograniczenie liczby stron jednocześnie przetwarzanych

## Następne kroki

Po instalacji narzędzi OCR:
1. ✅ Skonfiguruj Azure AD (zobacz AZURE_AD_SETUP.md)
2. ✅ Przetestuj aplikację w trybie dry-run
3. ✅ Uruchom na prawdziwych danych
