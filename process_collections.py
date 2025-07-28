import os
import json
import fitz  # PyMuPDF
from datetime import datetime

def extract_text_from_pdf(pdf_path, max_pages=3):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(min(max_pages, len(doc))):
        page = doc.load_page(page_num)
        text += page.get_text()
    doc.close()
    return text

def process_collection(collection_dir):
    input_path = os.path.join(collection_dir, 'challenge1b_input.json')
    output_path = os.path.join(collection_dir, 'challenge1b_output.json')
    pdfs_dir = os.path.join(collection_dir, 'PDFs')

    with open(input_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    persona = config.get('persona', {}).get('role', '')
    job = config.get('job_to_be_done', {}).get('task', '')
    documents = config.get('documents', [])
    input_documents = [doc['filename'] for doc in documents]

    extracted_sections = []
    subsection_analysis = []

    for idx, doc in enumerate(documents):
        pdf_file = os.path.join(pdfs_dir, doc['filename'])
        title = doc.get('title', os.path.splitext(doc['filename'])[0])
        text = extract_text_from_pdf(pdf_file)
        # Use first non-empty line as section title
        section_title = next((line.strip() for line in text.splitlines() if line.strip()), title)
        # Use first 200 chars as refined text
        refined_text = text.strip().replace('\n', ' ')[:200]
        extracted_sections.append({
            "document": doc['filename'],
            "section_title": section_title,
            "importance_rank": idx + 1,
            "page_number": 1
        })
        subsection_analysis.append({
            "document": doc['filename'],
            "refined_text": refined_text,
            "page_number": 1
        })
        if len(extracted_sections) >= 5:
            break

    output = {
        "metadata": {
            "input_documents": input_documents,
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Output saved to {output_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for collection in ["Collection 1", "Collection 2", "Collection 3"]:
        collection_dir = os.path.join(base_dir, collection)
        if os.path.exists(collection_dir):
            print(f"Processing {collection}...")
            process_collection(collection_dir)

if __name__ == "__main__":
    main() 