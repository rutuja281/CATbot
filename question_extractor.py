import os
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json
import re
from typing import List, Dict, Tuple
import config

# Try to use pypdf if available (better PDF support)
try:
    import pypdf
    USE_PYPDF = True
except ImportError:
    USE_PYPDF = False

class QuestionExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=config.Config.CHAT_MODEL,
            temperature=0.3,  # Lower temperature for more consistent extraction
            openai_api_key=config.Config.OPENAI_API_KEY
        )
        
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting CAT exam questions from PDF documents. 
            Extract ONLY actual questions with their answer options and correct answers.
            
            CRITICAL RULES:
            1. Extract ONLY complete questions that have:
               - A question statement (ending with "?" or clearly a problem to solve)
               - Multiple choice options (A, B, C, D or numbered options)
               - A visible correct answer or answer marked in the text
            
            2. DO NOT extract:
               - Explanatory text or theory
               - Incomplete questions
               - Questions without answer options
               - General statements or tips
            
            3. For each valid question, extract:
               - question_text: The complete question/problem statement
               - options: List of ALL answer options EXACTLY as they appear (e.g., ["A) 10", "B) 20", "C) 30", "D) 40"])
               - correct_answer: The correct answer letter (A, B, C, or D) - look for "Answer:", "Correct Answer:", or marked answers
               - explanation: Solution/explanation if provided (empty string if none)
               - topic: Based on question content - Arithmetic, Algebra, Geometry, Percentages, Simple Interest, Compound Interest, Probability, Combinatorics, Number Systems, Data Interpretation, Logical Reasoning, Reading Comprehension, Vocabulary, or General
               - difficulty_estimate: 1-5 based on complexity (1=very easy, 3=medium, 5=very hard)
            
            4. Format requirements:
               - Return ONLY a valid JSON array
               - Each question must have question_text, options, and correct_answer
               - Options must be actual values, NOT placeholders like "Option A"
               - If correct answer not found, try to infer from context or skip the question
               - If no valid questions found, return empty array: []
            
            Return ONLY valid JSON array, no markdown, no explanations:"""),
            ("human", "Extract all complete questions with answer options from this text:\n\n{text}")
        ])
    
    def load_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            # Try pypdf first (better compatibility)
            try:
                reader = pypdf.PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- Page {i+1} ---\n{page_text}\n"
                return text
            except Exception as e:
                print(f"pypdf failed, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {i+1} ---\n{page_text}\n"
        except Exception as e:
            raise Exception(f"Failed to read PDF {file_path}: {str(e)}. The PDF may be corrupted or use unsupported encoding.")
        
        return text
    
    def extract_questions_from_text(self, text: str, chunk_size: int = 3000) -> Tuple[List[Dict], List[str]]:
        """Extract questions from text using LLM"""
        all_questions = []
        errors = []
        
        # Split text into chunks to avoid token limits
        # Use smaller chunks and overlap to catch questions at boundaries
        overlap = 500
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i+chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        print(f"Processing {len(chunks)} chunks...")
        
        for idx, chunk in enumerate(chunks):
            try:
                if len(chunk) < 50:  # Skip very short chunks
                    continue
                
                print(f"Processing chunk {idx+1}/{len(chunks)} ({len(chunk)} chars)...")
                
                # Extract questions using LLM
                messages = self.extraction_prompt.format_messages(text=chunk)
                response = self.llm.invoke(messages)
                
                # Parse JSON response
                content = response.content.strip()
                
                # Try to extract JSON from markdown code blocks if present
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                elif content.startswith('['):
                    # Already JSON
                    pass
                else:
                    # Try to find JSON array in the response
                    json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                    else:
                        # Try to fix common JSON issues
                        # Remove any text before first [
                        bracket_start = content.find('[')
                        if bracket_start > 0:
                            content = content[bracket_start:]
                
                # Clean up content
                content = content.strip()
                if not content.startswith('['):
                    errors.append(f"Chunk {idx+1}: Response doesn't start with '['. First 200 chars: {content[:200]}")
                    continue
                
                questions = json.loads(content)
                
                if isinstance(questions, list):
                    if len(questions) > 0:
                        print(f"  ✓ Found {len(questions)} questions in chunk {idx+1}")
                        all_questions.extend(questions)
                    else:
                        print(f"  - No questions in chunk {idx+1}")
                elif isinstance(questions, dict) and 'questions' in questions:
                    all_questions.extend(questions['questions'])
                else:
                    errors.append(f"Chunk {idx+1}: Unexpected response format")
                    
            except json.JSONDecodeError as e:
                error_msg = f"Chunk {idx+1}: JSON parse error - {str(e)}"
                errors.append(error_msg)
                print(f"  ✗ {error_msg}")
                print(f"     Response preview: {content[:300]}")
                continue
            except Exception as e:
                error_msg = f"Chunk {idx+1}: Error - {str(e)}"
                errors.append(error_msg)
                print(f"  ✗ {error_msg}")
                continue
        
        if errors:
            print(f"\n⚠️ Encountered {len(errors)} errors during extraction")
        
        return all_questions, errors
    
    def extract_questions_from_pdf(self, pdf_path: str) -> Tuple[List[Dict], List[str]]:
        """Extract questions from a PDF file"""
        print(f"Loading PDF: {pdf_path}")
        text = self.load_pdf(pdf_path)
        
        if not text or len(text.strip()) < 100:
            return [], [f"PDF appears to be empty or unreadable. Extracted {len(text)} characters."]
        
        print(f"Extracting questions from {len(text)} characters ({len(text.split())} words)...")
        questions, errors = self.extract_questions_from_text(text)
        
        # Validate and clean questions
        valid_questions = []
        for q in questions:
            # Ensure required fields exist
            if not q.get('question_text'):
                continue
            if not q.get('options'):
                q['options'] = ["A) Option A", "B) Option B", "C) Option C", "D) Option D"]
            if not q.get('correct_answer'):
                q['correct_answer'] = "A"
            if not q.get('topic'):
                q['topic'] = "General"
            if not q.get('difficulty_estimate'):
                q['difficulty_estimate'] = 3.0
            
            valid_questions.append(q)
        
        # Add source information
        filename = os.path.basename(pdf_path)
        for i, q in enumerate(valid_questions):
            q['source_document'] = filename
            # Estimate page number (rough)
            q['source_page'] = (i // 5) + 1  # Approximate
        
        print(f"✓ Extracted {len(valid_questions)} valid questions from {filename}")
        return valid_questions, errors
    
    def score_difficulty(self, question: Dict) -> float:
        """Score question difficulty based on various factors"""
        base_score = question.get('difficulty_estimate', 3.0)
        
        # Adjust based on question length
        question_len = len(question.get('question_text', ''))
        if question_len > 500:
            base_score += 0.5  # Longer questions tend to be harder
        elif question_len < 100:
            base_score -= 0.3  # Shorter questions tend to be easier
        
        # Adjust based on number of options
        options_count = len(question.get('options', []))
        if options_count > 5:
            base_score += 0.3  # More options = harder
        
        # Adjust based on topic (some topics are inherently harder)
        topic = question.get('topic', '').lower()
        if 'geometry' in topic or 'advanced' in topic:
            base_score += 0.5
        elif 'arithmetic' in topic or 'basic' in topic:
            base_score -= 0.3
        
        # Clamp between 1 and 5
        return max(1.0, min(5.0, base_score))

