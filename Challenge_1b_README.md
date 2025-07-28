# Challenge 1b: Multi-Collection PDF Analysis

## Overview
Advanced PDF analysis solution that processes multiple document collections and extracts relevant content based on specific personas and use cases.

## Project Structure
```
Challenge_1b/
├── Collection 1/                    # Travel Planning
│   ├── PDFs/                       # South of France guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 2/                    # Adobe Acrobat Learning
│   ├── PDFs/                       # Acrobat tutorials
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 3/                    # Recipe Collection
│   ├── PDFs/                       # Cooking guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
└── README.md
```

## Collections

### Collection 1: Travel Planning
- Challenge ID: round_1b_002
- Persona: Travel Planner
- Task: Plan a 4-day trip for 10 college friends to South of France
- Documents: 7 travel guides

### Collection 2: Adobe Acrobat Learning
- Challenge ID: round_1b_003
- Persona: HR Professional
- Task: Create and manage fillable forms for onboarding and compliance
- Documents: 15 Acrobat guides

### Collection 3: Recipe Collection
- Challenge ID: round_1b_001
- Persona: Food Contractor
- Task: Prepare vegetarian buffet-style dinner menu for corporate gathering
- Documents: 9 cooking guides

## How to Run

From the Adobe_1B directory (where all the code is located), run:

```
python main.py --base_dir "C:\path\to\Challenge_1b"
```

This will process all collections and generate output JSON files.

To process a specific collection:

```
python main.py --base_dir "C:\path\to\Challenge_1b" --collection "Collection 1"
```

## Input/Output Format

### Input JSON Structure
```json
{
  "challenge_info": {
    "challenge_id": "round_1b_XXX",
    "test_case_name": "specific_test_case"
  },
  "documents": [{"filename": "doc.pdf", "title": "Title"}],
  "persona": {"role": "User Persona"},
  "job_to_be_done": {"task": "Use case description"}
}
```

### Output JSON Structure
```json
{
  "metadata": {
    "input_documents": ["list"],
    "persona": "User Persona",
    "job_to_be_done": "Task description"
  },
  "extracted_sections": [
    {
      "document": "source.pdf",
      "section_title": "Title",
      "importance_rank": 1,
      "page_number": 1
    }
  ],
  "subsection_analysis": [
    {
      "document": "source.pdf",
      "refined_text": "Content",
      "page_number": 1
    }
  ]
}
```

## Implementation Details

The solution uses advanced natural language processing techniques to:

1. Extract structured content from PDF documents
2. Understand the persona's role and specific needs
3. Identify the most relevant sections based on the job-to-be-done
4. Rank content by importance for the specific use case
5. Provide detailed subsection analysis for deeper understanding

All processing is optimized for CPU execution and meets the required time constraints.
