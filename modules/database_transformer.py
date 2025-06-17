#!/usr/bin/env python3
"""
Fixed Database Transformer for Question Database
Handles new JSON format with subtopic field AND null values
Properly extracts feedback fields from JSON structure
"""

import json
import csv
import sys
import os

def transform_json_to_csv(json_file, csv_file=None):
    """
    Transform JSON question database to CSV format for MATLAB
    Now properly handles feedback_correct, feedback_incorrect, subtopic fields, and null values
    """
    
    # Set default output filename
    if csv_file is None:
        base_name = os.path.splitext(json_file)[0]
        csv_file = f"{base_name}_db.csv"
    
    try:
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both formats: {"questions": [...]} or direct [...]
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
            metadata = data.get('metadata', {})
        elif isinstance(data, list):
            questions = data
            metadata = {}
        else:
            print(f"Error: Unexpected JSON structure in {json_file}")
            return False
        
        print(f"Processing {len(questions)} questions...")
        
        # Display metadata information if available
        if metadata:
            print(f"Subject: {metadata.get('subject', 'Unknown')}")
            print(f"Format Version: {metadata.get('format_version', 'Unknown')}")
            if 'topics_covered' in metadata:
                print(f"Topics: {', '.join(metadata['topics_covered'])}")
            if 'subtopics_covered' in metadata:
                print(f"Subtopics: {', '.join(metadata['subtopics_covered'])}")
        
        # Define CSV columns to match MATLAB table expectations
        # Added Subtopic column for the new field
        fieldnames = [
            'ID', 'Type', 'Title', 'Question_Text', 'Choice_A', 'Choice_B', 
            'Choice_C', 'Choice_D', 'Correct_Answer', 'Points', 'Tolerance',
            'Feedback', 'Correct_Feedback', 'Incorrect_Feedback', 'Image_File', 
            'Topic', 'Subtopic', 'Difficulty'
        ]
        
        # Write CSV file
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, q in enumerate(questions):
                # Generate question ID
                question_id = f"Q_{i+1:05d}"
                
                # Extract basic fields with defaults
                question_type = q.get('type', 'multiple_choice')
                title = q.get('title', f"Question {i+1}")
                question_text = q.get('question_text', '')
                correct_answer = q.get('correct_answer', '')
                points = q.get('points', 1)
                tolerance = q.get('tolerance', 0.05)
                topic = q.get('topic', 'General')
                subtopic = q.get('subtopic', '')  # NEW: Handle subtopic field
                difficulty = q.get('difficulty', 'Easy')
                
                # Handle image file (could be list, string, or None/null)
                image_file = q.get('image_file', [])
                if image_file is None:  # Handle null values
                    image_file = ''
                elif isinstance(image_file, list):
                    image_file = image_file[0] if image_file else ''
                elif not isinstance(image_file, str):
                    image_file = str(image_file) if image_file else ''
                
                # Extract feedback fields (handle None/null values)
                feedback_correct = q.get('feedback_correct', '') or ''
                feedback_incorrect = q.get('feedback_incorrect', '') or ''
                
                # For general feedback, use correct feedback as default
                general_feedback = feedback_correct
                
                # Handle choices for multiple choice questions (handle None/null values)
                choices = q.get('choices', [])
                if choices is None:  # Handle null values
                    choices = []
                elif not isinstance(choices, list):
                    choices = []
                
                choice_a = choices[0] if len(choices) > 0 else ''
                choice_b = choices[1] if len(choices) > 1 else ''
                choice_c = choices[2] if len(choices) > 2 else ''
                choice_d = choices[3] if len(choices) > 3 else ''
                
                # Handle tolerance and points (could be None/null)
                if tolerance is None:
                    tolerance = 0.05
                if points is None:
                    points = 1
                
                # Convert correct_answer to string to handle various types
                if correct_answer is None:
                    correct_answer = ''
                else:
                    correct_answer = str(correct_answer)
                
                # Create row for CSV
                row = {
                    'ID': question_id,
                    'Type': question_type,
                    'Title': title,
                    'Question_Text': question_text,
                    'Choice_A': choice_a,
                    'Choice_B': choice_b,
                    'Choice_C': choice_c,
                    'Choice_D': choice_d,
                    'Correct_Answer': correct_answer,
                    'Points': points,
                    'Tolerance': tolerance,
                    'Feedback': general_feedback,           # General feedback
                    'Correct_Feedback': feedback_correct,   # Specific correct feedback
                    'Incorrect_Feedback': feedback_incorrect, # Specific incorrect feedback
                    'Image_File': image_file,
                    'Topic': topic,
                    'Subtopic': subtopic,                   # NEW: Include subtopic
                    'Difficulty': difficulty
                }
                
                writer.writerow(row)
        
        print(f"Successfully transformed {len(questions)} questions")
        print(f"Output written to: {csv_file}")
        return True
        
    except FileNotFoundError:
        print(f"Error: Could not find file {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {json_file}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python database_transformer.py <input_json_file> [output_csv_file]")
        print("Example: python database_transformer.py final_cleaned_questions.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    csv_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = transform_json_to_csv(json_file, csv_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()