#!/usr/bin/env python3
"""
Script to extract questions from all PDFs in the data folder
"""
import os
from question_extractor import QuestionExtractor
from database import Database
import config

def main():
    print("=" * 60)
    print("CAT Exam Question Extraction Script")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing components...")
    extractor = QuestionExtractor()
    db = Database()
    
    # Check data folder
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory '{data_dir}' not found!")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ No PDF files found in '{data_dir}' directory!")
        return
    
    print(f"\n2. Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"   - {pdf}")
    
    # Process each PDF
    total_questions = 0
    total_errors = 0
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(data_dir, pdf_file)
        print(f"\n{'=' * 60}")
        print(f"Processing {idx}/{len(pdf_files)}: {pdf_file}")
        print(f"{'=' * 60}")
        
        try:
            # Extract questions
            questions, errors = extractor.extract_questions_from_pdf(pdf_path)
            
            # Show errors if any
            if errors:
                print(f"\n⚠️  Warnings/Errors ({len(errors)}):")
                for err in errors[:10]:  # Show first 10
                    print(f"   - {err}")
                if len(errors) > 10:
                    print(f"   ... and {len(errors) - 10} more")
                total_errors += len(errors)
            
            if not questions:
                print(f"\n⚠️  No questions extracted from {pdf_file}")
                print("   This might mean:")
                print("   - PDF doesn't contain questions in recognizable format")
                print("   - Text extraction failed (scanned PDF?)")
                print("   - Questions are in images/tables that need OCR")
                continue
            
            print(f"\n✓ Extracted {len(questions)} questions from {pdf_file}")
            
            # Add questions to database
            added_count = 0
            failed_count = 0
            
            for q_idx, q in enumerate(questions, 1):
                try:
                    difficulty = extractor.score_difficulty(q)
                    db.add_question(
                        topic_name=q.get('topic', 'General'),
                        question_text=q['question_text'],
                        options=q.get('options', []),
                        correct_answer=q.get('correct_answer', 'A'),
                        explanation=q.get('explanation', ''),
                        difficulty_score=difficulty,
                        estimated_time_sec=120,
                        source_document=q.get('source_document', pdf_file),
                        source_page=q.get('source_page', 0)
                    )
                    added_count += 1
                    if q_idx % 10 == 0:
                        print(f"   Added {q_idx}/{len(questions)} questions...")
                except Exception as e:
                    failed_count += 1
                    print(f"   ✗ Error adding question {q_idx}: {str(e)[:100]}")
                    continue
            
            print(f"\n✓ Successfully added {added_count} questions to database")
            if failed_count > 0:
                print(f"⚠️  Failed to add {failed_count} questions")
            
            total_questions += added_count
            
        except Exception as e:
            print(f"\n❌ Error processing {pdf_file}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print(f"\n{'=' * 60}")
    print("EXTRACTION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"Total questions extracted: {total_questions}")
    print(f"Total errors/warnings: {total_errors}")
    print(f"\n✓ Question bank now contains {len(db.get_all_questions())} questions")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    # Check if API key is set
    if not config.Config.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in .env file!")
        print("Please set your OpenAI API key in the .env file first.")
        exit(1)
    
    main()

