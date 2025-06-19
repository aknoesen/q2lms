#!/usr/bin/env python3
"""
Database Processor Module for Question Database Manager
Handles database loading, processing, validation, and transformations
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

def find_correct_letter(correct_text: str, choices: List[str]) -> str:
    """Convert correct answer text to letter (A, B, C, D)"""
    if not correct_text:
        return 'A'
    
    correct_clean = str(correct_text).strip().lower()
    
    # Check if it's already a letter
    if correct_clean.upper() in ['A', 'B', 'C', 'D']:
        return correct_clean.upper()
    
    # Match against choices
    for i, choice in enumerate(choices):
        if choice and str(choice).strip().lower() == correct_clean:
            return ['A', 'B', 'C', 'D'][i]
    
    print(f"⚠️ Could not match '{correct_text}' to choices: {choices}")
    return 'A'  # Fallback

def load_database_from_json(json_content: str) -> Tuple[Optional[pd.DataFrame], Dict, List, List]:
    """Load and process JSON database content with automatic LaTeX processing"""
    try:
        data = json.loads(json_content)
        
        # Handle both formats: {"questions": [...]} or direct [...]
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
            metadata = data.get('metadata', {})
        elif isinstance(data, list):
            questions = data
            metadata = {}
        else:
            st.error("❌ Unexpected JSON structure")
            return None, None, None, None
        
        # LaTeX Processing Step (currently using raw approach)
        cleanup_reports = []
        processed_questions = questions  # Default to original questions
        
        # Use questions directly (no Unicode conversion for now)
        processed_questions = questions
        cleanup_reports = []
        
        # Use processed questions for DataFrame conversion
        questions = processed_questions
        
        # Convert to DataFrame using same logic as database_transformer.py
        rows = []
        for i, q in enumerate(questions):
            # Generate question ID
            question_id = f"Q_{i+1:05d}"
            
            # Extract basic fields with defaults and handle None values
            question_type = q.get('type', 'multiple_choice')
            title = q.get('title', f"Question {i+1}")
            question_text = q.get('question_text', '')
            
            # Handle correct_answer properly for multiple choice
            original_correct_answer = q.get('correct_answer', '')
            choices = q.get('choices', [])

            # Clean up choices and handle None values
            if choices is None:
                choices = []
            elif not isinstance(choices, list):
                choices = []

            # Ensure we have 4 choices
            while len(choices) < 4:
                choices.append('')

            choice_a = str(choices[0]) if choices[0] else ''
            choice_b = str(choices[1]) if choices[1] else ''
            choice_c = str(choices[2]) if choices[2] else ''
            choice_d = str(choices[3]) if choices[3] else ''

            # Convert correct answer text to letter for multiple choice
            if question_type == 'multiple_choice':
                correct_answer = find_correct_letter(original_correct_answer, [choice_a, choice_b, choice_c, choice_d])
            else:
                correct_answer = str(original_correct_answer) if original_correct_answer else ''
                
            points = q.get('points', 1)
            tolerance = q.get('tolerance', 0.05)
            topic = q.get('topic', 'General')
            subtopic = q.get('subtopic', '')
            difficulty = q.get('difficulty', 'Easy')
            
            # Handle image file (could be list, string, or None)
            image_file = q.get('image_file', [])
            if image_file is None:
                image_file = ''
            elif isinstance(image_file, list):
                image_file = image_file[0] if image_file else ''
            elif not isinstance(image_file, str):
                image_file = str(image_file) if image_file else ''
            
            # Extract feedback fields (handle None values)
            feedback_correct = q.get('feedback_correct', '') or ''
            feedback_incorrect = q.get('feedback_incorrect', '') or ''
            general_feedback = feedback_correct  # Use correct feedback as default
            
            # Handle None values for tolerance and points
            if tolerance is None:
                tolerance = 0.05
            if points is None:
                points = 1
            
            # Create row
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
                'Feedback': general_feedback,
                'Correct_Feedback': feedback_correct,
                'Incorrect_Feedback': feedback_incorrect,
                'Image_File': image_file,
                'Topic': topic,
                'Subtopic': subtopic,
                'Difficulty': difficulty
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Return processed data including cleanup reports
        return df, metadata, processed_questions, cleanup_reports
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON: {e}")
        return None, None, None, None
    except Exception as e:
        st.error(f"❌ Error processing database: {e}")
        return None, None, None, None

def assign_new_question_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Assign new sequential IDs while preserving originals"""
    df = df.copy()
    df['Original_ID'] = df['ID']  # Preserve original IDs
    df['ID'] = [f"Q_{i+1:05d}" for i in range(len(df))]  # New sequential IDs
    return df

def validate_question_database(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate question database for completeness and consistency"""
    errors = []
    warnings = []
    
    required_fields = ['ID', 'Type', 'Question_Text', 'Correct_Answer']
    
    for idx, row in df.iterrows():
        # Check required fields
        for field in required_fields:
            if pd.isna(row[field]) or str(row[field]).strip() == '':
                errors.append(f"Question {row['ID']}: Missing {field}")
        
        # Check question type specific requirements
        if row['Type'] == 'multiple_choice':
            choices = [row.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
            if sum(1 for c in choices if c.strip()) < 2:
                warnings.append(f"Question {row['ID']}: Fewer than 2 choices for multiple choice")
        
        # Check points are numeric and positive
        try:
            points = float(row.get('Points', 0))
            if points <= 0:
                warnings.append(f"Question {row['ID']}: Points should be positive")
        except (ValueError, TypeError):
            errors.append(f"Question {row['ID']}: Points must be numeric")
    
    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0
    }

def validate_single_question(question_row) -> Dict[str, Any]:
    """Validate a single question row"""
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ['Title', 'Type', 'Question_Text', 'Correct_Answer']
    
    for field in required_fields:
        # Use a more robust check that doesn't require pandas
        value = question_row.get(field, '')
        if value is None or str(value).strip() == '' or str(value).lower() == 'nan':
            errors.append(f"Missing {field}")
    
    # Check question type specific requirements
    if question_row['Type'] == 'multiple_choice':
        choices = [question_row.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
        if sum(1 for c in choices if str(c).strip()) < 2:
            warnings.append("Fewer than 2 choices for multiple choice")
        
        if question_row['Correct_Answer'] not in ['A', 'B', 'C', 'D']:
            errors.append("Correct answer must be A, B, C, or D for multiple choice")
    
    # Check points are positive
    try:
        points = float(question_row.get('Points', 0))
        if points <= 0:
            warnings.append("Points should be positive")
    except (ValueError, TypeError):
        errors.append("Points must be numeric")
    
    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0
    }

def process_single_database(content: str, options: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Process a single database with enhanced options"""
    
    with st.spinner("🔄 Processing database..."):
        # Use existing load_database_from_json function with enhancements
        df, metadata, original_questions, cleanup_reports = load_database_from_json(content)
        
        if df is not None:
            # Apply additional processing based on options
            if options.get('assign_new_ids', False):
                df = assign_new_question_ids(df)
            
            if options.get('validate_questions', True):
                validation_results = validate_question_database(df)
                if validation_results['errors']:
                    st.warning(f"⚠️ Found {len(validation_results['errors'])} validation issues")
                    with st.expander("View Validation Issues"):
                        for error in validation_results['errors']:
                            st.write(f"• {error}")
            
            # Store enhanced data in session state
            st.session_state['df'] = df
            st.session_state['metadata'] = metadata
            st.session_state['original_questions'] = original_questions
            st.session_state['cleanup_reports'] = cleanup_reports
            st.session_state['filename'] = options['filename']
            st.session_state['processing_options'] = options
            
            st.success(f"✅ Database processed successfully! {len(df)} questions ready.")
            
            return df
        
        return None

def process_append_operation(content: str, options: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Process appending new questions to existing database"""
    
    st.markdown("### ➕ Appending to Existing Database")
    
    # Load the new questions
    df_new, metadata_new, questions_new, cleanup_reports_new = load_database_from_json(content)
    
    if df_new is None:
        st.error("❌ Could not load new questions")
        return None
    
    # Get current database
    df_current = options['current_df']
    
    st.write(f"📊 Current database: {len(df_current)} questions")
    st.write(f"📄 Adding from {options['filename']}: {len(df_new)} questions")
    
    # Handle duplicate detection (simplified)
    duplicate_handling = options['handle_duplicates']
    
    if duplicate_handling == "Skip duplicates":
        # Simple duplicate detection based on question text
        existing_texts = set(df_current['Question_Text'].str.strip().str.lower())
        new_texts = df_new['Question_Text'].str.strip().str.lower()
        
        duplicates_mask = new_texts.isin(existing_texts)
        df_to_add = df_new[~duplicates_mask]
        
        if duplicates_mask.sum() > 0:
            st.warning(f"⚠️ Skipped {duplicates_mask.sum()} duplicate questions")
        
        st.info(f"📊 Adding {len(df_to_add)} unique questions")
    
    else:
        df_to_add = df_new
        st.info(f"📊 Adding all {len(df_to_add)} questions")
    
    if len(df_to_add) > 0:
        # Combine databases
        if options['renumber_ids']:
            # Renumber all IDs sequentially
            combined_df = pd.concat([df_current, df_to_add], ignore_index=True)
            combined_df['ID'] = [f"Q_{i+1:05d}" for i in range(len(combined_df))]
        else:
            # Keep existing IDs, assign new ones for added questions
            max_id = len(df_current)
            df_to_add = df_to_add.copy()
            df_to_add['ID'] = [f"Q_{max_id + i + 1:05d}" for i in range(len(df_to_add))]
            combined_df = pd.concat([df_current, df_to_add], ignore_index=True)
        
        # Update session state
        st.session_state['df'] = combined_df
        st.session_state['filename'] = f"appended_{options['filename']}"
        
        st.success(f"✅ Successfully appended {len(df_to_add)} questions!")
        st.info(f"📊 Total database size: {len(combined_df)} questions")
        
        return combined_df
    
    else:
        st.warning("⚠️ No questions to append")
        return None

def save_question_changes(question_index: int, changes: Dict[str, Any]) -> bool:
    """Save changes to both DataFrame and original_questions"""
    
    try:
        # Get current data
        df = st.session_state['df'].copy()
        original_questions = st.session_state['original_questions'].copy()
        
        # Update DataFrame
        df.loc[question_index, 'Title'] = changes['title']
        df.loc[question_index, 'Type'] = changes['question_type']
        df.loc[question_index, 'Difficulty'] = changes['difficulty']
        df.loc[question_index, 'Points'] = changes['points']
        df.loc[question_index, 'Topic'] = changes['topic']
        df.loc[question_index, 'Subtopic'] = changes['subtopic']
        df.loc[question_index, 'Question_Text'] = changes['question_text']
        df.loc[question_index, 'Choice_A'] = changes['choice_a']
        df.loc[question_index, 'Choice_B'] = changes['choice_b']
        df.loc[question_index, 'Choice_C'] = changes['choice_c']
        df.loc[question_index, 'Choice_D'] = changes['choice_d']
        df.loc[question_index, 'Correct_Answer'] = changes['correct_answer']
        df.loc[question_index, 'Tolerance'] = changes['tolerance']
        df.loc[question_index, 'Correct_Feedback'] = changes['correct_feedback']
        df.loc[question_index, 'Incorrect_Feedback'] = changes['incorrect_feedback']
        df.loc[question_index, 'Feedback'] = changes['correct_feedback']
        
        # Update original_questions (for QTI export compatibility)
        if question_index < len(original_questions):
            q = original_questions[question_index]
            q['title'] = changes['title']
            q['type'] = changes['question_type']
            q['difficulty'] = changes['difficulty']
            q['points'] = changes['points']
            q['topic'] = changes['topic']
            q['subtopic'] = changes['subtopic']
            q['question_text'] = changes['question_text']
            q['correct_answer'] = changes['correct_answer']
            q['tolerance'] = changes['tolerance']
            q['feedback_correct'] = changes['correct_feedback']
            q['feedback_incorrect'] = changes['incorrect_feedback']
            
            # Update choices for multiple choice
            if changes['question_type'] == 'multiple_choice':
                q['choices'] = [
                    changes['choice_a'],
                    changes['choice_b'],
                    changes['choice_c'],
                    changes['choice_d']
                ]
        
        # Update session state
        st.session_state['df'] = df
        st.session_state['original_questions'] = original_questions
        
        # Validate the changes
        validation_results = validate_single_question(df.iloc[question_index])
        
        if validation_results['is_valid']:
            st.success("✅ Question updated successfully!")
        else:
            st.warning("⚠️ Question saved but has validation issues:")
            for error in validation_results['errors']:
                st.write(f"• {error}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error saving changes: {str(e)}")
        return False

def delete_question(question_index: int) -> bool:
    """Delete a question from both DataFrame and original_questions"""
    try:
        # Get current data
        df = st.session_state['df']
        original_questions = st.session_state['original_questions']
        
        # Check if index is valid
        if question_index >= len(df) or question_index >= len(original_questions):
            st.error("❌ Invalid question index")
            return False
        
        # Remove from DataFrame
        df_updated = df.drop(df.index[question_index]).reset_index(drop=True)
        
        # Remove from original_questions
        original_questions_updated = original_questions.copy()
        original_questions_updated.pop(question_index)
        
        # Regenerate question IDs to maintain sequence
        df_updated['ID'] = [f"Q_{i+1:05d}" for i in range(len(df_updated))]
        
        # Update session state
        st.session_state['df'] = df_updated
        st.session_state['original_questions'] = original_questions_updated
        
        # Clear any edit session states for this question to avoid conflicts
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.endswith(f"_{question_index}"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error deleting question: {str(e)}")
        return False
        