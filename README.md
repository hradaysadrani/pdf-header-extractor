# Challenge 1A: Document Outline Extractor 📄

Extract document structure (title and H1, H2, H3 headings) from PDF files with blazing speed and comprehensive multilingual support.

## 🎯 What This Does

This solution automatically analyzes PDF documents and extracts:
- **Document Title** - The main title of the document
- **Headings Hierarchy** - H1, H2, H3 headings with page numbers (0-based indexing)
- **Comprehensive Multilingual Support** - Works with 3 languages and scripts

### 🌍 Supported Languages:
- **English** - Chapter, Section patterns
- **Hindi** - अध्याय, भाग, प्रकरण patterns
- **Japanese** - 第N章, 第N節 patterns
- **Chinese** - 第N章, 第N节 patterns

### 🌍 Languages which will be supported in future:
- **Marathi** - अध्याय, भाग, विभाग patterns
- **Tamil** - அத்தியாயம், பகுதி, பிரிவு patterns
- **Gujarati** - અધ્યાય, ભાગ, વિભાગ patterns
- **French** - Chapitre, Partie, Section patterns  
- **Spanish** - Capítulo, Parte, Sección patterns
- And many more to come..

## 🚀 Quick Start (For Complete Beginners)

### Step 1: Install Docker
If you don't have Docker installed:

**On Windows:**
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Open Command Prompt or PowerShell

**On Mac:**
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install the application
3. Open Terminal

**On Linux:**
```bash
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
```

### Step 2: Prepare Your Files
1. Create a folder called `input` in this directory
2. Put your PDF files inside the `input` folder
3. Create an empty folder called `output`

Your folder structure should look like:
```
pdf-header-extractor/
├── input/           ← Put your PDF files here
│   ├── document1.pdf
│   └── document2.pdf
├── output/          ← Results will appear here
├── process_pdfs.py
├── Dockerfile
└── README.md
```

### Step 3: Build the Solution
Open your terminal/command prompt in this folder and run:

```bash
docker build --platform linux/amd64 -t outline-extractor .
```

### Step 4: Run the Extraction
```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  outline-extractor
```

**For Windows PowerShell, use:**
```powershell
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none outline-extractor
```

### Step 5: Check Results
Look in your `output` folder - you'll find JSON files with the extracted structure!

## 📊 Example Output

For a PDF about "Understanding AI", you'll get:
```json
{
    "title": "Understanding Artificial Intelligence",
    "outline": [
        {"level": "H1", "text": "Introduction", "page": 0},
        {"level": "H2", "text": "What is AI?", "page": 1},
        {"level": "H3", "text": "History of AI", "page": 2},
        {"level": "H1", "text": "Machine Learning", "page": 3}
    ]
}
```

## 🌍 Multilingual Support

The system automatically detects and processes documents in multiple languages:

**Hindi Documents:**
```json
{
    "title": "कृत्रिम बुद्धिमत्ता की समझ",
    "outline": [
        {"level": "H1", "text": "अध्याय 1: परिचय", "page": 0},
        {"level": "H2", "text": "भाग 1.1: AI का इतिहास", "page": 1},
        {"level": "H3", "text": "प्रकरण 1.1.1: शुरुआत", "page": 2}
    ]
}
```

**Japanese Documents:**
```json
{
    "title": "人工知能の理解",
    "outline": [
        {"level": "H1", "text": "第1章: 序論", "page": 0},
        {"level": "H2", "text": "第1節: AIの歴史", "page": 1},
        {"level": "H3", "text": "1.1.1 始まり", "page": 2}
    ]
}
```

**Chinese Documents:**
```json
{
    "title": "理解人工智能",
    "outline": [
        {"level": "H1", "text": "第1章: 引言", "page": 0},
        {"level": "H2", "text": "第1节: AI历史", "page": 1},
        {"level": "H3", "text": "1.1.1 起源", "page": 2}
    ]
}
```

## 🔧 How It Works (Technical Details)

### 1. Text Extraction (`extract_text_with_formatting`)
- Uses PyMuPDF to extract text with font information
- Preserves font size, weight (bold), and position data
- Tracks original text order for proper sorting

### 2. Font Analysis (`calculate_font_baseline`)
- Identifies the most common font size (body text)
- Uses this as baseline to detect larger headings
- Robust against documents with mixed font sizes

### 3. Multilingual Heading Detection (`is_likely_heading`)
- **Font-based detection**: Larger and bold text
- **Pattern recognition**: Numbers, title case, special markers
- **Multilingual patterns**: 
  - Hindi: अध्याय, भाग, प्रकरण patterns
  - Japanese: 第N章, 第N節 patterns  
  - Chinese: 第N章, 第N节 patterns
- **Scoring system**: Combines multiple features for accuracy

### 4. Title Extraction (`extract_document_title`)
- Finds largest text on first page
- Validates against common non-title patterns
- Cleans extracted text while preserving Unicode

### 5. Output Generation
- Sorts headings by page number and position
- Removes duplicates intelligently
- Outputs clean JSON with proper Unicode encoding

## 📏 Performance Specifications

- **Processing Time**: ≤10 seconds for 50-page PDFs
- **Container Size**: ~100MB (lightweight)
- **Model Requirements**: No ML models (rule-based)
- **Memory Usage**: Minimal - processes page by page
- **Offline**: No internet required

## 🐛 Troubleshooting

### "Docker command not found"
Install Docker Desktop from the official website.

### "Permission denied"
On Linux, try:
```bash
sudo docker build --platform linux/amd64 -t outline-extractor .
```

### "No output files generated"
Check that:
1. PDF files are in the `input` folder
2. PDFs are not password-protected or corrupted
3. Run with `-v` for verbose output:
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output outline-extractor
```

### "Empty outline array"
This can happen if:
- Document has no clear heading structure
- All text is the same font size
- PDF is image-based (scanned document)

## 📁 File Structure

```
pdf-header-extractor/
├── process_pdfs.py     # Main extraction script
├── outline_extractor.py     # This script is under testing. It has some upcoming features but presently, not as accurate as main sript
├── Dockerfile          # Container configuration
├── README.md           # This file
├── input/              # Put PDF files here
└── output/             # Results appear here
```

The multi-feature detection algorithm combines font analysis, pattern recognition, and position information for maximum accuracy across diverse document types. 

## Future Upgrades

In future, we will add following features:
- More language support
- 99%+ accuracy
- And many more in pipeline..