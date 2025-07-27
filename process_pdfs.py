#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter
import fitz  # PyMuPDF

# --- Stage 1: Text Extraction & Document Profiling ---

def extract_and_group_lines(pdf_path: str) -> (List[Dict[str, Any]], Dict):
    """
    Extracts text, groups it into lines, and builds a document profile.
    """
    doc = fitz.open(pdf_path)
    lines = {}
    
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_LIGATURES)["blocks"]
        for block in blocks:
            if block['type'] == 0:  # Text block
                for line in block.get("lines", []):
                    line_bbox = line['bbox']
                    line_key = (page_num, int(line_bbox[1]))
                    
                    if line_key not in lines:
                        lines[line_key] = {"spans": [], "bbox": line_bbox, "page": page_num}
                    
                    lines[line_key]['spans'].extend(line['spans'])

    logical_lines = []
    for key in sorted(lines.keys()):
        line_data = lines[key]
        line_spans = sorted(line_data['spans'], key=lambda s: s['bbox'][0])
        
        # Reconstruct line text by joining spans. This preserves spaces within spans
        # and avoids inserting artificial spaces, which is better for CJK (Chinese, Japanese, Korean) languages.
        full_text = "".join(s['text'] for s in line_spans).strip()
        if full_text:
            first_span = line_spans[0]
            logical_lines.append({
                "text": full_text,
                "font_size": first_span["size"],
                "font_name": first_span["font"],
                "is_bold": "bold" in first_span["font"].lower() or (first_span['flags'] & 16) != 0,
                "page": line_data["page"],
                "bbox": line_data["bbox"],
            })

    # Build Document Profile
    profile = {}
    font_sizes = [s['font_size'] for s in logical_lines if len(s['text']) > 15]
    profile['baseline_font_size'] = Counter(font_sizes).most_common(1)[0][0] if font_sizes else 10.0
    
    page_0_lines = [line for line in logical_lines if line['page'] == 0]
    profile['page_offset'] = 1 if len(page_0_lines) < 10 and doc.page_count > 1 else 0
    
    left_margins = [int(line['bbox'][0]) for line in logical_lines if len(line['text']) > 20]
    profile['left_margin'] = Counter(left_margins).most_common(1)[0][0] if left_margins else 72

    doc.close()
    return logical_lines, profile

# --- Stage 2: Title and Heading Extraction ---

def extract_title(lines: List[Dict[str, Any]]) -> str:
    """Extracts a title by finding the largest text on the first page."""
    page_0_lines = [line for line in lines if line['page'] == 0]
    if not page_0_lines: return ""
    
    max_font_size = max(line['font_size'] for line in page_0_lines)
    title_lines = [line for line in page_0_lines if abs(line['font_size'] - max_font_size) < 0.5]
    title_lines.sort(key=lambda l: (l['bbox'][1], l['bbox'][0]))
    
    return "".join(line['text'] for line in title_lines).strip()

def find_headings(lines: List[Dict[str, Any]], profile: Dict) -> List[Dict]:
    """
    Applies a precise, priority-based rule system to identify headings.
    """
    headings = []
    baseline_size = profile['baseline_font_size']
    left_margin = profile['left_margin']
    
    # Expanded regex to support full-width ASCII, Devanagari (Hindi) numerals,
    # and common CJK separators (．, 、).
    structural_patterns = [
        (re.compile(r'^([0-9０-９०-९]+)[.\．、]\s'), 'H1'),
        (re.compile(r'^([0-9０-９०-९]+\.[0-9０-９०-९]+)\s'), 'H2'),
        (re.compile(r'^([0-9０-９०-९]+\.[0-9０-９०-९]+\.[0-9０-９०-९]+)\s'), 'H3')
    ]
    
    # Added multilingual keywords for common section headers. Using a set for efficient lookup.
    special_h1s = {
        # English
        'Revision History', 'Table of Contents', 'Acknowledgements', 'References',
        # Japanese (日本語)
        '改訂履歴', '目次', '謝辞', '参考文献',
        # Chinese (简体中文)
        '修订历史', '目录', '致谢', # Note: '参考文献' (References) is the same in Japanese and Chinese
        # Hindi (हिन्दी)
        'संशोधन इतिहास', 'विषय-सूची', 'आभार', 'संदर्भ'
    }
    
    for line in lines:
        text = line['text']
        is_bold = line['is_bold']
        font_size = line['font_size']
        bbox = line['bbox']
        
        # --- Rule 0: Negative Filters ---
        if '....' in text or re.match(r'^\d\.\d+\s+\d{1,2}\s+[A-Z]{3,}', text):
            continue

        # --- Rule 1: Structural Patterns (with Positional Logic) ---
        matched_structure = False
        for pattern, level in structural_patterns:
            if pattern.match(text):
                if abs(bbox[0] - left_margin) < 15: # Allow 15pt tolerance
                    headings.append({**line, 'level': level})
                    matched_structure = True
                    break
        if matched_structure:
            continue

        # --- Rule 2: Keyword Headings ---
        # Used strip() to ensure accurate matching against the set.
        if text.strip() in special_h1s:
            if is_bold or font_size > baseline_size:
                headings.append({**line, 'level': 'H1'})
                continue
    
    return headings

# --- Stage 3: Finalization ---

def finalize_outline(headings: List[Dict], profile: Dict) -> List[Dict]:
    """Sorts, merges, deduplicates, and formats the final outline."""
    if not headings: return []

    headings.sort(key=lambda h: (h['page'], h['bbox'][1]))
    
    merged_headings = []
    i = 0
    while i < len(headings):
        current = headings[i]
        if i + 1 < len(headings):
            nxt = headings[i+1]
            h1_pattern = r'^[0-9０-９०-९]+[.\．、]\s*'
            next_line_is_not_heading = not re.match(r'^[0-9０-９०-९]+[.\．、]', nxt['text'])

            if (current['page'] == nxt['page'] and
                re.match(h1_pattern, current['text']) and next_line_is_not_heading):
                # Merge text from the continuation line, ensuring a single space separator.
                current['text'] = f"{current['text'].strip()} {nxt['text'].strip()}"
                i += 1 # Skip the next line as it has been merged
        merged_headings.append(current)
        i += 1

    final_outline = []
    seen = set()
    page_offset = profile['page_offset']
    for item in merged_headings:
        # Normalize whitespace for clean output
        clean_text = re.sub(r'\s+', ' ', item['text']).strip()
        final_page = item['page'] + 1 - page_offset
        
        key = (clean_text.lower(), final_page)
        if key not in seen:
            final_outline.append({
                'level': item['level'],
                'text': clean_text + " ",
                'page': final_page,
            })
            seen.add(key)
            
    return final_outline

# --- Main Orchestration ---

def process_single_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Orchestrates the entire pipeline."""
    try:
        lines, profile = extract_and_group_lines(str(pdf_path))
        title = extract_title(lines)
        headings = find_headings(lines, profile)
        outline = finalize_outline(headings, profile)

        return {
            "title": title.strip() + "  ",
            "outline": outline
        }
    except Exception as e:
        print(f"!! Critical Error processing {pdf_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return {"title": "", "outline": []}

def main():
    """Main function to run the extraction process."""
    CWD = Path(__file__).parent
    INPUT_DIR = CWD / "input"
    OUTPUT_DIR = CWD / "output"
    
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("--- Definitive Document Outline Extractor ---")
    
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in '{INPUT_DIR}'. Please place PDFs there to process.")
        return

    for pdf_file in pdf_files:
        print(f"\nProcessing '{pdf_file.name}'...")
        result = process_single_pdf(pdf_file)
        
        output_file = OUTPUT_DIR / f"{pdf_file.stem}.json"
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        print(f" -> Success. Outline saved to '{output_file.name}'")
        
    print("\n--- All files processed. ---")

if __name__ == "__main__":
    main()