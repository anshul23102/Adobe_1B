# Persona-Driven Document Intelligence

A solution for Adobe India Hackathon 2025 Round 1B that extracts and prioritizes document sections based on specific personas and their job-to-be-done.

## Features

- Processes multiple PDF documents simultaneously (3-10 documents)
- Extracts and prioritizes content based on specific persona and job requirements
- Identifies both high-level sections and detailed subsections
- Works with any domain (research papers, books, financial reports, etc.)
- CPU-only operation with fast processing time (<60 seconds)
- Small model footprint (<1GB)

## Requirements

- Python 3.8+ (3.9 or 3.11 recommended)
- Required Python packages (listed in requirements.txt)

## Quickstart

### Option 1: Using Scripts (Recommended)

For Windows:
```
run_all.bat
```

For Linux/Mac:
```
chmod +x run_all.sh
./run_all.sh
```

### Option 2: Python Direct Execution

Process all collections:
```
python main.py --base_dir .
```

Process a single collection:
```
python main.py --base_dir . --collection "Collection 1"
```

### Option 3: Simplified Scripts

For Windows:
```
run_simple.bat
```

For Linux/Mac:
```
chmod +x run_simple.sh
./run_simple.sh
```

## Docker Usage

You can run the project in a containerized environment using Docker:

1. Build the Docker image:
   ```sh
   docker build -t pdfprocessor .
   ```
2. Run the container (outputs will be saved in your local folders):
   ```sh
   docker run --rm -v "$PWD:/app" pdfprocessor
   ```
   On Windows (PowerShell):
   ```sh
   docker run --rm -v ${PWD}:/app pdfprocessor
   ```

This will process all collections and generate/update `challenge1b_output.json` files in each collection folder.

## Local Execution

To run locally (without Docker):

1. Install Python 3.8+ and pip.
2. Install dependencies:
   ```sh
   pip install pymupdf
   ```
3. Run the script:
   ```sh
   python process_collections.py
   ```

Outputs will be saved in the respective collection folders.

## Project Structure

```
project/
├── main.py              # Main application code
├── requirements.txt     # Python dependencies
├── approach_explanation.md # Methodology description
├── run_all.sh           # Linux/Mac execution script
├── run_all.bat          # Windows execution script
├── run_simple.sh        # Simplified Linux/Mac script
├── run_simple.bat       # Simplified Windows script
├── utils/               # Utility modules
│   ├── document_processor.py # Document processing logic
│   ├── section_extractor.py # Section extraction logic
│   └── relevance_ranker.py # Relevance ranking logic
├── Collection 1/        # Test collection
│   ├── PDFs/           # PDF documents
│   └── challenge1b_input.json  # Input configuration
├── Collection 2/        # Test collection
└── Collection 3/        # Test collection
```

## Input Format

The system expects a JSON input file with the following structure:

```json
{
  "documents": [
    {"filename": "document1.pdf"},
    {"filename": "document2.pdf"},
    ...
  ],
  "persona": {
    "role": "Role description"
  },
  "job_to_be_done": {
    "task": "Task description"
  }
}
```

## Output Format

The system produces a JSON output with the following structure:

```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf", ...],
    "persona": "Role description",
    "job_to_be_done": "Task description",
    "processing_timestamp": "ISO-8601 timestamp"
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "section_title": "Section Title",
      "importance_rank": 1,
      "page_number": 5
    },
    ...
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "Detailed content...",
      "page_number": 5
    },
    ...
  ]
}
```

## Scoring Criteria

The system aims to achieve high scores in:

1. **Section Relevance (60 points)**: How well selected sections match persona + job requirements with proper stack ranking
2. **Sub-Section Relevance (40 points)**: Quality of granular subsection extraction and ranking

## Performance Constraints

- Runs on CPU only (no GPU required)
- Model size ≤ 1GB
- Processing time ≤ 60 seconds for document collection (3-5 documents)
- No internet access required during execution

## Methodology

For a detailed explanation of the methodology, please refer to [approach_explanation.md](approach_explanation.md).
