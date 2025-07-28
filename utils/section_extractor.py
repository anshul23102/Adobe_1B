from typing import List, Dict, Any, Optional
import re
import os

class SectionExtractor:
    """Extract meaningful sections from processed documents."""
    
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.font_size_threshold = 12  # Default font size threshold for headers
        self.section_patterns = [
            r'^(?:\d+\.)+\s+.+',  # Numbered sections (e.g., "1.2.3 Section Title")
            r'^[A-Z][A-Za-z\s]+:',  # Title followed by colon (e.g., "Introduction:")
            r'^[IVX]+\.\s+.+',  # Roman numeral sections (e.g., "IV. Results")
            r'^(?:Chapter|Section)\s+\d+',  # Explicit section markers
            r'^[A-Z][A-Z\s]+$'  # All caps titles
        ]
    
    def extract_sections(self, processed_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract sections from processed documents, with robust fallback for headerless docs."""
        all_sections = []
        
        for doc in processed_docs:
            doc_name = doc["document_name"]
            sections = self._identify_sections(doc)
            # Fallback: If no sections found, treat each page as a section
            if not sections:
                for page in doc["pages"]:
                    content = "\n".join([b["text"] for b in page["blocks"] if b["text"].strip()])
                    if content.strip():
                        sections.append({
                            "section_title": f"Page {page['page_number']}",
                            "page_number": page["page_number"],
                            "content": content,
                            "subsections": self._identify_subsections({"content": content, "page_number": page["page_number"], "section_title": f"Page {page['page_number']}"})
                        })
            # Merge very short sections with neighbors
            merged_sections = []
            min_section_len = 80
            i = 0
            while i < len(sections):
                sec = sections[i]
                if len(sec["content"]) < min_section_len and i > 0:
                    # Merge with previous
                    merged_sections[-1]["content"] += "\n" + sec["content"]
                    merged_sections[-1]["subsections"] = self._identify_subsections(merged_sections[-1])
                else:
                    merged_sections.append(sec)
                i += 1
            for section in merged_sections:
                section["document"] = doc_name
                all_sections.append(section)
        return all_sections
    
    def _identify_sections(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify sections within a document based on headers and content, with recipe/food PDF enhancements."""
        sections = []
        current_section = None
        for page in doc["pages"]:
            page_num = page["page_number"]
            blocks = page["blocks"]
            found_header = False
            # Try standard header detection
            for idx, block in enumerate(blocks):
                if self._is_section_header(block):
                    if current_section and current_section["content"]:
                        sections.append(current_section)
                    current_section = {
                        "section_title": block["text"].strip(),
                        "page_number": page_num,
                        "content": [],
                        "subsections": []
                    }
                    found_header = True
                elif current_section:
                    current_section["content"].append(block["text"])
            # If no header found, try recipe/food heuristics
            if not found_header and blocks:
                # Find largest font block (likely dish name)
                largest_block = max(blocks, key=lambda b: b.get("font_size", 0))
                # Prefer short lines (2-5 words) at top
                for b in blocks[:3]:
                    words = b["text"].strip().split()
                    if 2 <= len(words) <= 5 and b.get("font_size", 0) >= largest_block.get("font_size", 0) * 0.9:
                        largest_block = b
                        break
                # Prefer lines followed by 'Ingredients' or 'Instructions'
                for idx, b in enumerate(blocks[:-1]):
                    next_text = blocks[idx+1]["text"].lower()
                    if ("ingredient" in next_text or "instruction" in next_text) and 2 <= len(b["text"].split()) <= 6:
                        largest_block = b
                        break
                # Use this as section header
                if current_section and current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "section_title": largest_block["text"].strip(),
                    "page_number": page_num,
                    "content": [b["text"] for b in blocks if b != largest_block],
                    "subsections": []
                }
            # End of page: finalize section
        if current_section and current_section["content"]:
            sections.append(current_section)
        for section in sections:
            section["content"] = "\n".join(section["content"])
            section["subsections"] = self._identify_subsections(section)
        return sections
    
    def _is_section_header(self, block: Dict[str, Any]) -> bool:
        """Determine if a text block is a section header using robust checks."""
        text = block.get("text", "").strip()
        if not text:
            return False
        font_size = block.get("font_size", 10)
        is_potential_header = font_size > self.font_size_threshold
        # Numbered or roman numeral headers
        if re.match(r'^(\d+\.|[IVX]+\.)\s*[A-Z]', text):
            return True
        # All caps, short, not ending with period
        if is_potential_header and len(text.split()) < 12 and text.isupper() and not text.endswith('.'):
            return True
        # Title case, short
        if is_potential_header and len(text.split()) < 10 and text.istitle():
            return True
        # Colon-ended header
        if is_potential_header and text.endswith(":"):
            return True
        # More uppercase than lowercase, short
        if len(text) < 100:
            uppers = sum(1 for char in text if char.isupper())
            lowers = sum(1 for char in text if char.islower())
            if uppers > lowers and lowers < 5:
                return True
        return False
    
    def _identify_subsections(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break section content into meaningful, comprehensive subsections, with recipe/food PDF enhancements."""
        content = section["content"]
        # Try to extract ingredients/instructions lists for recipes
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        for idx, line in enumerate(lines):
            if line.lower().startswith("ingredients") or line.lower().startswith("instructions"):
                # Grab this line and the next 5 lines as a subsection
                para = "\n".join(lines[idx:idx+6])
                return [{
                    "id": f"{section['section_title']}_sub_1",
                    "text": para,
                    "page_number": section["page_number"]
                }]
        # Fallback to original logic
        
        # First, try to break by double newlines (paragraphs)
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        
        # If we don't have clear paragraphs, try single newlines
        if len(paragraphs) <= 1:
            paragraphs = [p for p in content.split("\n") if p.strip()]
            
            # Further process these line-break based paragraphs to group related content
            processed_paragraphs = []
            current_group = ""
            
            for para in paragraphs:
                # If it's a bullet point or numbered item
                if para.strip().startswith(('•', '-', '*', '#')) or re.match(r'^\d+\.\s', para.strip()):
                    # If we were building a paragraph, finalize it
                    if current_group:
                        processed_paragraphs.append(current_group)
                        current_group = ""
                    processed_paragraphs.append(para.strip())
                # If it's a potential header (all caps, short)
                elif para.isupper() and len(para) < 50:
                    # If we were building a paragraph, finalize it
                    if current_group:
                        processed_paragraphs.append(current_group)
                        current_group = ""
                    processed_paragraphs.append(para.strip())
                # If it seems like a continuation of content
                else:
                    if current_group:
                        current_group += " " + para.strip()
                    else:
                        current_group = para.strip()
            
            # Add any remaining group
            if current_group:
                processed_paragraphs.append(current_group)
                
            paragraphs = processed_paragraphs
        
        # For very long sections with no clear breaks, use sentence-based splitting
        if len(paragraphs) <= 1 and len(content) > 300:
            try:
                # Use regex for more accurate sentence splitting
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
                
                # Group sentences into logical chunks
                chunk_size = min(5, max(2, len(sentences) // 3))
                paragraphs = []
                
                for i in range(0, len(sentences), chunk_size):
                    chunk = " ".join(sentences[i:i+chunk_size])
                    if chunk.strip():
                        paragraphs.append(chunk.strip())
            except Exception as e:
                # Fallback if regex fails
                print(f"Error in sentence splitting: {e}")
                # Simple split by periods
                sentences = content.split(". ")
                paragraphs = []
                for i in range(0, len(sentences), 3):
                    chunk = ". ".join(sentences[i:i+3])
                    if chunk.strip() and not chunk.endswith("."):
                        chunk += "."
                    if chunk.strip():
                        paragraphs.append(chunk.strip())
        
        # Intelligently merge paragraphs that form incomplete thoughts
        merged_paragraphs = []
        i = 0
        while i < len(paragraphs):
            para = paragraphs[i].strip()
            if not para:
                i += 1
                continue
                
            # Check if this paragraph forms a complete thought
            is_complete = para.endswith(('.', '!', '?')) or para.endswith(':') or para.endswith(';')
            is_short = len(para) < 100
            
            # If it's an incomplete thought and short, try to merge with next paragraph
            if not is_complete and is_short and i < len(paragraphs) - 1:
                next_para = paragraphs[i+1].strip()
                # Only merge if next paragraph isn't a bullet point or header
                if next_para and not next_para.startswith(('•', '-', '*', '#')) and not next_para.isupper():
                    para = para + " " + next_para
                    i += 2  # Skip next paragraph in next iteration
                else:
                    i += 1
            else:
                i += 1
                
            # Add to our merged paragraphs if it's substantial
            if len(para) > 30 or (para.endswith(':') and len(para) > 10):
                merged_paragraphs.append(para)
        
        # Create subsections from our intelligently merged paragraphs
        subsections = []
        for i, para in enumerate(merged_paragraphs):
            # Create the subsection with proper metadata
            subsection = {
                "id": f"{section['section_title']}_sub_{i+1}",
                "text": para,
                "page_number": section["page_number"]
            }
            subsections.append(subsection)
        
        # If we somehow ended up with no subsections but have content,
        # create a single subsection with all content
        if not subsections and content.strip():
            subsections = [{
                "id": f"{section['section_title']}_sub_1",
                "text": content.strip(),
                "page_number": section["page_number"]
            }]
        
        return subsections
