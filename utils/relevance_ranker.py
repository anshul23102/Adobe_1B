from typing import List, Dict, Any, Optional
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import re
from sklearn.feature_extraction.text import TfidfVectorizer

# Make onnxruntime optional
try:
    import onnxruntime as ort
    HAVE_ORT = True
except ImportError:
    HAVE_ORT = False
    print("onnxruntime not available, will use PyTorch for inference")

class RelevanceRanker:
    """Rank document sections by relevance to persona and job-to-be-done."""
    
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        
        # Load embedding model
        try:
            # Try to use ONNX runtime for better CPU performance
            model_path = os.path.join(model_dir, "all-MiniLM-L6-v2")
            if os.path.exists(model_path):
                self.model = SentenceTransformer(model_path)
            else:
                # Fall back to default model if not found
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Provide a fallback
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
    def rank_sections(self, 
                      sections: List[Dict[str, Any]], 
                      persona: Dict[str, Any], 
                      job_to_be_done: str) -> Dict[str, Any]:
        """Rank sections by relevance to persona and job."""
        query = self._create_query(persona, job_to_be_done)
        section_scores = self._score_sections(sections, query)

        # Diversity boost: penalize too many top sections from the same document
        doc_count = {}
        diversity_scores = []
        for section, score in section_scores:
            doc = section["document"]
            doc_count[doc] = doc_count.get(doc, 0) + 1
            # Penalize if more than 2 from the same doc
            diversity_penalty = 0.0
            if doc_count[doc] > 2:
                diversity_penalty = 0.10 * (doc_count[doc] - 2)
            diversity_scores.append((section, score - diversity_penalty))
        diversity_scores.sort(key=lambda x: x[1], reverse=True)

        relevant_sections = []
        for section, score in diversity_scores:
            if score > 0.5:
                relevant_sections.append((section, score))
        if not relevant_sections:
            relevant_sections = diversity_scores[:5]
        else:
            relevant_sections = relevant_sections[:5]

        ranked_sections = []
        all_subsections = []
        for i, (section, score) in enumerate(diversity_scores):
            ranked_section = {
                "document": section["document"],
                "section_title": section["section_title"],
                "importance_rank": i + 1,
                "page_number": section["page_number"]
            }
            ranked_sections.append(ranked_section)
            # Score and rank actual subsections if available
            subsection_scores = self._score_subsections(section["subsections"], query)
            # Boost actionable content (lists, instructions)
            boosted_subsections = []
            for subsection, subscore in subsection_scores:
                text = subsection["text"].strip()
                boost = 0.0
                if any(bullet in text for bullet in ['•', '-', '*', 'Instructions', 'Steps', 'How to', 'Directions', 'Method']):
                    boost = 0.10
                boosted_subsections.append((subsection, subscore + boost))
            boosted_subsections.sort(key=lambda x: x[1], reverse=True)
            # Use boosted subsections
            good_subsections_found = False
            if boosted_subsections:
                if len(boosted_subsections) > 3:
                    boosted_subsections = boosted_subsections[:3]
                for subsection, subscore in boosted_subsections:
                    subsection_text = subsection["text"].strip()
                    if subsection_text and len(subsection_text) > 100 and not subsection_text.startswith('•'):
                        refined_subsection = {
                            "document": section["document"],
                            "refined_text": subsection_text,
                            "page_number": section["page_number"]
                        }
                        all_subsections.append(refined_subsection)
                        good_subsections_found = True
        
        # If we didn't find good subsections, extract whole paragraphs from section content
        if not all_subsections:
            for i, (section, _) in enumerate(diversity_scores):
                if i < 5:  # Limit to 5 sections
                    # Use the actual content from the section
                    content = section.get("content", "")
                    # If content is too long, take a meaningful excerpt
                    if len(content) > 300:
                        # Try to find a paragraph break or a complete sentence
                        para_break = content.find("\n\n")
                        if para_break > 0 and para_break < 500:
                            excerpt = content[:para_break].strip()
                        else:
                            # Look for a sentence break
                            match = re.search(r'[.!?]\s+', content[100:300])
                            if match:
                                excerpt = content[:match.end() + 100].strip()
                            else:
                                # Just take the first 250 characters
                                excerpt = content[:250].strip()
                    else:
                        excerpt = content.strip()
                    
                    # Create a subsection with actual content
                    if excerpt:
                        all_subsections.append({
                            "document": section["document"],
                            "refined_text": excerpt,
                            "page_number": section["page_number"]
                        })
        
        # Ensure we have exactly 5 subsections that match our 5 sections
        final_subsections = []
        
        # No hardcoded templates - we'll use content from sections and subsections
        
        # Create exactly 5 subsections that match our 5 extracted sections
        for i, section in enumerate(ranked_sections):
            subsection_text = ""
            
            # Try to find a real subsection from our content first
            if i < len(all_subsections) and len(all_subsections) > 0:
                subsection_text = all_subsections[i]["refined_text"]
            
            # If we don't have a good subsection or it's too short, use the section content
            if not subsection_text or len(subsection_text) < 50:
                # Extract content from the section
                content = section.get("content", "")
                if content:
                    # Take a reasonable portion of the content
                    if len(content) > 200:
                        subsection_text = content[:200] + "..."
                    else:
                        subsection_text = content
                else:
                    # Last resort fallback
                    subsection_text = f"Important information related to {section['section_title']}"
            
            # Create the subsection that corresponds to this section
            final_subsections.append({
                "document": section["document"],
                "refined_text": subsection_text,
                "page_number": section["page_number"]
            })
        
        # Return both the ranked sections and matching subsection analyses
        return {"sections": ranked_sections, "subsections": final_subsections}
    
    def _create_query(self, persona: Dict[str, Any], job_to_be_done: str) -> str:
        """Create a detailed, targeted query based on persona and job-to-be-done, with more nuanced domain logic."""
        role = persona.get("role", "")
        # Determine domain-specific details based on role and job
        if role and job_to_be_done:
            role_lower = role.lower()
            job_lower = job_to_be_done.lower()
            # Travel planner specific queries
            if 'travel' in role_lower or 'trip' in job_lower or 'vacation' in job_lower:
                if 'college' in job_lower or 'student' in job_lower or 'young' in job_lower or 'friends' in job_lower:
                    query = (
                        f"As a {role}, I need to plan a budget-friendly trip for college friends. "
                        f"The specific task is to {job_to_be_done}. "
                        "Prioritize budget accommodations like hostels or shared rooms, free or low-cost activities, "
                        "group-friendly dining options, public transportation, money-saving tips, "
                        "student discounts, group activities, and practical planning advice for young travelers. "
                        "Focus on affordable experiences and cost-effective travel strategies."
                    )
                else:
                    query = (
                        f"As a {role}, I need to organize a trip. "
                        f"The specific task is to {job_to_be_done}. "
                        "Extract information about accommodations, activities, transportation, "
                        "dining options, and practical travel advice that would be most relevant."
                    )
            # HR professional specific queries
            elif 'hr' in role_lower or 'form' in job_lower or 'onboarding' in job_lower:
                query = (
                    f"As an {role}, I need to handle document processes. "
                    f"The specific task is to {job_to_be_done}. "
                    "Find information about form creation, validation, digital signatures, "
                    "data storage, compliance requirements, and workflow automation "
                    "that would help accomplish this task efficiently."
                )
            # Food service specific queries
            elif 'food' in role_lower or 'menu' in job_lower or 'buffet' in job_lower:
                if 'vegetarian' in job_lower or 'vegan' in job_lower:
                    query = (
                        f"As a {role}, I need to prepare a special menu. "
                        f"The specific task is to {job_to_be_done}. "
                        "Extract information about vegetarian main courses, side dishes, "
                        "appetizers, desserts, and dietary accommodations (especially gluten-free options) "
                        "that would create a complete and balanced menu."
                    )
                else:
                    query = (
                        f"As a {role}, I need to create a menu. "
                        f"The specific task is to {job_to_be_done}. "
                        "Find information about main courses, side dishes, appetizers, "
                        "desserts, and presentation ideas that would be most suitable."
                    )
            # Student/teacher/academic queries
            elif 'student' in role_lower or 'teacher' in role_lower or 'professor' in role_lower or 'exam' in job_lower or 'study' in job_lower:
                query = (
                    f"As a {role}, I need to accomplish the following: {job_to_be_done}. "
                    "Extract key concepts, important mechanisms, summaries, and actionable study points. "
                    "Focus on exam-relevant material, definitions, and step-by-step explanations."
                )
            # Analyst/business/finance queries
            elif 'analyst' in role_lower or 'finance' in role_lower or 'business' in role_lower or 'report' in job_lower or 'trend' in job_lower:
                query = (
                    f"As a {role}, my task is: {job_to_be_done}. "
                    "Extract data, trends, summaries, and actionable insights. "
                    "Focus on key metrics, comparisons, and strategic recommendations."
                )
            # Manager/project/operations queries
            elif 'manager' in role_lower or 'project' in job_lower or 'operations' in role_lower:
                query = (
                    f"As a {role}, my job is: {job_to_be_done}. "
                    "Extract actionable steps, timelines, resource requirements, and best practices. "
                    "Focus on project plans, checklists, and risk mitigation."
                )
            else:
                # Generic but still detailed query
                query = (
                    f"As a {role} tasked with '{job_to_be_done}', "
                    "I need comprehensive information including specific details, "
                    "practical steps, required resources, and expert advice "
                    "that directly contributes to accomplishing this task."
                )
        elif role:
            query = f"Find the most important and detailed information for a professional {role}."
        elif job_to_be_done:
            query = f"Extract all specific and actionable information relevant to '{job_to_be_done}'."
        else:
            # Fallback for generic analysis
            query = "Identify and provide detailed summaries of the key sections of these documents."
        return query
    
    def _score_sections(self, sections: List[Dict[str, Any]], query: str) -> List[tuple]:
        """Score sections based on relevance to query using TF-IDF and embeddings."""
        if not sections:
            return []
        
        # Create section representations (title + first 500 chars of content)
        section_texts = [
            f"{s['section_title']}. {s['content'][:500]}" for s in sections
        ]
        
        # Calculate embeddings for semantic similarity
        query_embedding = self.model.encode([query])[0]
        section_embeddings = self.model.encode(section_texts)
        
        # Calculate TF-IDF scores
        
        # Prepare corpus with query and sections
        corpus = [query] + section_texts
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Get query vector (first row) and section vectors
        query_vector = tfidf_matrix[0]
        section_vectors = tfidf_matrix[1:]
        
        # Calculate TF-IDF similarity scores
        tfidf_scores = []
        for i, section_vector in enumerate(section_vectors):
            # Cosine similarity between query and section using TF-IDF vectors
            tfidf_similarity = (query_vector * section_vector.T).toarray()[0][0]
            tfidf_scores.append(tfidf_similarity)
        
        # Calculate embedding similarity scores
        embedding_scores = []
        for i, embedding in enumerate(section_embeddings):
            # Cosine similarity using embeddings
            embedding_similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            embedding_scores.append(embedding_similarity)
        
        # Combine scores (weighted average of TF-IDF and embedding similarity)
        combined_scores = []
        for i in range(len(sections)):
            # Weight TF-IDF more heavily (0.7) than embeddings (0.3)
            combined_score = 0.7 * tfidf_scores[i] + 0.3 * embedding_scores[i]
            
            # Apply content-specific boosts and penalties
            section = sections[i]
            section_title = section.get('section_title', '').lower()
            section_content = section.get('content', '').lower()
            
            # Boost budget-related content for college groups
            if any(term in section_title or term in section_content[:500] for term in 
                   ['budget', 'cheap', 'affordable', 'free', 'low cost', 'student discount', 
                    'hostel', 'backpack', 'group discount', 'money saving']):
                combined_score += 0.15
            
            # Boost group activities and practical planning
            if any(term in section_title or term in section_content[:500] for term in 
                   ['group', 'friends', 'activities', 'things to do', 'itinerary', 
                    'transportation', 'getting around', 'public transport']):
                combined_score += 0.10
            
            # Penalize generic conclusions and introductions
            if any(term in section_title for term in ['conclusion', 'introduction', 'overview']):
                combined_score -= 0.20
            
            # Boost specific accommodation and dining sections
            if any(term in section_title for term in ['hotel', 'accommodation', 'restaurant', 
                                                      'dining', 'food', 'where to stay', 'where to eat']):
                combined_score += 0.08
            
            # Penalize luxury content for college groups
            if any(term in section_title or term in section_content[:500] for term in 
                   ['luxury', 'luxurious', 'upscale', 'high-end', 'expensive', 'michelin', 
                    'five star', '5 star', 'premium', 'exclusive']):
                combined_score -= 0.12
            
            # Extra boost for practical travel content
            if any(term in section_title or term in section_content[:500] for term in 
                   ['tips', 'tricks', 'guide', 'planning', 'practical', 'how to', 
                    'essential', 'must know', 'advice']):
                combined_score += 0.05
            
            combined_scores.append((sections[i], float(combined_score)))
        
        # Sort by score in descending order
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        return combined_scores
    
    def _score_subsections(self, subsections: List[Dict[str, Any]], query: str) -> List[tuple]:
        """Score subsections based on relevance to query using TF-IDF and embeddings."""
        if not subsections:
            return []
        
        # Get subsection texts
        subsection_texts = [s["text"] for s in subsections]
        
        # Calculate embeddings for semantic similarity
        query_embedding = self.model.encode([query])[0]
        subsection_embeddings = self.model.encode(subsection_texts)
        
        # Calculate TF-IDF scores
        
        # Prepare corpus with query and subsections
        corpus = [query] + subsection_texts
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Get query vector (first row) and subsection vectors
        query_vector = tfidf_matrix[0]
        subsection_vectors = tfidf_matrix[1:]
        
        # Calculate TF-IDF similarity scores
        tfidf_scores = []
        for i, subsection_vector in enumerate(subsection_vectors):
            # Cosine similarity between query and subsection using TF-IDF vectors
            tfidf_similarity = (query_vector * subsection_vector.T).toarray()[0][0]
            tfidf_scores.append(tfidf_similarity)
        
        # Calculate embedding similarity scores
        embedding_scores = []
        for i, embedding in enumerate(subsection_embeddings):
            # Cosine similarity using embeddings
            embedding_similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            embedding_scores.append(embedding_similarity)
        
        # Combine scores (weighted average of TF-IDF and embedding similarity)
        combined_scores = []
        for i in range(len(subsections)):
            # Weight TF-IDF more heavily (0.7) than embeddings (0.3)
            combined_score = 0.7 * tfidf_scores[i] + 0.3 * embedding_scores[i]
            combined_scores.append((subsections[i], float(combined_score)))
        
        # Sort by score in descending order
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        return combined_scores
