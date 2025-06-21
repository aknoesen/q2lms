#!/usr/bin/env python3
"""
Data Processor Module
Handles filtering, cleaning, and synchronizing question data for export
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class QuestionDataProcessor:
    """Processes and validates question data for export"""
    
    def __init__(self):
        self.safe_field_mappings = {
            'Title': 'title',
            'Points': 'points', 
            'Topic': 'topic',
            'Subtopic': 'subtopic',
            'Difficulty': 'difficulty',
            'Tolerance': 'tolerance',
            'Type': 'type',
            'Correct_Answer': 'correct_answer'
        }
        
        self.choice_columns = ['Choice_A', 'Choice_B', 'Choice_C', 'Choice_D', 'Choice_E']
        self.numeric_fields = ['points', 'tolerance']
    
    def fix_dataframe_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fix DataFrame column types to preserve integers where appropriate
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with corrected data types
        """
        if df is None or df.empty:
            return df
        
        df_copy = df.copy()
        
        # Integer columns that should be preserved as integers
        int_columns = ['Points', 'Question_Number', 'ID']
        
        for col in int_columns:
            if col in df_copy.columns:
                try:
                    # Convert float to int if all values are whole numbers
                    if df_copy[col].dtype in ['float64', 'float32']:
                        # Check if all non-null values are whole numbers
                        non_null_mask = df_copy[col].notna()
                        if non_null_mask.any():
                            whole_numbers = (df_copy[col][non_null_mask] % 1 == 0).all()
                            if whole_numbers:
                                df_copy[col] = df_copy[col].astype('Int64')  # Nullable integer
                except Exception as e:
                    logger.warning(f"Could not convert column {col} to integer: {e}")
        
        return df_copy
    
    def filter_questions_from_dataframe(self, 
                                       df: pd.DataFrame, 
                                       original_questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filter and synchronize questions based on DataFrame content
        
        Args:
            df: Filtered DataFrame containing questions to export
            original_questions: Original question data with LaTeX preserved
            
        Returns:
            Tuple of (filtered_questions, processing_stats)
        """
        if df is None or df.empty:
            return [], {"error": "No questions in DataFrame"}
        
        if not original_questions:
            return [], {"error": "No original questions provided"}
        
        stats = {
            "dataframe_rows": len(df),
            "original_questions": len(original_questions),
            "matched_questions": 0,
            "unmatched_questions": 0,
            "matching_method": None,
            "warnings": []
        }
        
        # Determine matching strategy
        use_index_matching = self._should_use_index_matching(df, stats)
        
        if use_index_matching:
            filtered_questions = self._match_by_index(df, original_questions, stats)
        else:
            filtered_questions = self._match_by_id(df, original_questions, stats)
        
        # Apply DataFrame changes to matched questions
        for i, question in enumerate(filtered_questions):
            if i < len(df):
                filtered_questions[i] = self._sync_dataframe_to_question(
                    question, df.iloc[i]
                )
        
        stats["matched_questions"] = len(filtered_questions)
        
        return filtered_questions, stats
    
    def _should_use_index_matching(self, df: pd.DataFrame, stats: Dict[str, Any]) -> bool:
        """Determine if we should use index-based vs ID-based matching"""
        
        if 'ID' not in df.columns:
            stats["matching_method"] = "index (no ID column)"
            stats["warnings"].append("No ID column found, using index-based matching")
            return True
        
        df_ids = df['ID'].tolist()
        non_empty_ids = [id for id in df_ids if id and str(id).strip()]
        
        # Use index matching if most IDs are empty
        if len(non_empty_ids) < len(df) * 0.5:
            stats["matching_method"] = "index (sparse IDs)"
            stats["warnings"].append("Most DataFrame IDs are empty, using index-based matching")
            return True
        
        stats["matching_method"] = "ID-based"
        return False
    
    def _match_by_index(self, 
                       df: pd.DataFrame, 
                       original_questions: List[Dict[str, Any]], 
                       stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match questions by DataFrame index position"""
        
        filtered_questions = []
        max_index = min(len(df), len(original_questions))
        
        for i in range(max_index):
            question = original_questions[i].copy()
            filtered_questions.append(question)
        
        if len(df) > len(original_questions):
            stats["warnings"].append(
                f"DataFrame has {len(df)} rows but only {len(original_questions)} original questions"
            )
        
        return filtered_questions
    
    def _match_by_id(self, 
                    df: pd.DataFrame, 
                    original_questions: List[Dict[str, Any]], 
                    stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match questions by ID field"""
        
        df_ids = set(str(id).strip() for id in df['ID'].tolist() if id and str(id).strip())
        filtered_questions = []
        
        for i, question in enumerate(original_questions):
            question_id = str(question.get('id', f"Q_{i+1:05d}")).strip()
            
            # Check various ID formats
            id_matches = [
                question_id in df_ids,
                f"Q_{i+1:05d}" in df_ids,
                str(i+1) in df_ids
            ]
            
            if any(id_matches):
                filtered_questions.append(question.copy())
            else:
                stats["unmatched_questions"] += 1
        
        return filtered_questions
    
    def _sync_dataframe_to_question(self, 
                                   original_question: Dict[str, Any], 
                                   df_row: pd.Series) -> Dict[str, Any]:
        """
        Synchronize DataFrame row changes back to question JSON
        
        Args:
            original_question: Original question data
            df_row: DataFrame row with potential changes
            
        Returns:
            Updated question with DataFrame changes applied
        """
        updated_question = original_question.copy()
        
        # Apply safe field mappings
        for df_col, json_key in self.safe_field_mappings.items():
            if df_col in df_row and pd.notna(df_row[df_col]):
                value = df_row[df_col]
                
                if json_key in self.numeric_fields:
                    try:
                        updated_question[json_key] = float(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert {json_key} to float: {value}")
                elif json_key == 'type':
                    # Normalize question type
                    updated_question[json_key] = str(value).lower().replace(' ', '_')
                else:
                    updated_question[json_key] = str(value)
        
        # Handle choices array
        choices = self._extract_choices_from_row(df_row)
        if choices:
            updated_question['choices'] = choices
        
        # Handle question text carefully (preserve LaTeX)
        if 'Question_Text' in df_row and pd.notna(df_row['Question_Text']):
            df_text = str(df_row['Question_Text']).strip()
            original_text = original_question.get('question_text', '').strip()
            
            # Only update if text actually changed
            if df_text and df_text != original_text:
                updated_question['question_text'] = df_text
        
        return updated_question
    
    def _extract_choices_from_row(self, df_row: pd.Series) -> List[str]:
        """Extract choices from DataFrame row"""
        choices = []
        
        for choice_col in self.choice_columns:
            if choice_col in df_row and pd.notna(df_row[choice_col]):
                choice_text = str(df_row[choice_col]).strip()
                if choice_text:
                    choices.append(choice_text)
        
        return choices
    
    def fix_numeric_formatting(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure numeric values are formatted as integers when appropriate
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Questions with fixed numeric formatting
        """
        fixed_questions = []
        
        for question in questions:
            fixed_question = question.copy()
            
            # Fix numeric fields
            for field in self.numeric_fields:
                if field in fixed_question:
                    value = fixed_question[field]
                    if isinstance(value, float) and value.is_integer():
                        fixed_question[field] = int(value)
            
            fixed_questions.append(fixed_question)
        
        return fixed_questions
    
    def validate_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate question data for export
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Validation results with errors and warnings
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "question_count": len(questions),
            "questions_with_issues": []
        }
        
        required_fields = ['question_text', 'type']
        
        for i, question in enumerate(questions):
            question_issues = []
            
            # Check required fields
            for field in required_fields:
                if field not in question or not question[field]:
                    question_issues.append(f"Missing required field: {field}")
            
            # Validate question type
            question_type = question.get('type', '').lower()
            valid_types = ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank']
            if question_type not in valid_types:
                question_issues.append(f"Invalid question type: {question_type}")
            
            # Check choices for multiple choice
            if question_type == 'multiple_choice':
                choices = question.get('choices', [])
                if not choices or len(choices) < 2:
                    question_issues.append("Multiple choice questions need at least 2 choices")
            
            # Check numerical answer
            if question_type == 'numerical':
                if 'correct_answer' not in question:
                    question_issues.append("Numerical questions need a correct_answer")
                else:
                    try:
                        float(question['correct_answer'])
                    except (ValueError, TypeError):
                        question_issues.append("Numerical correct_answer must be a number")
            
            if question_issues:
                validation_results["questions_with_issues"].append({
                    "question_index": i,
                    "question_title": question.get('title', f'Question {i+1}'),
                    "issues": question_issues
                })
                
                # Determine if these are errors or warnings
                critical_issues = [issue for issue in question_issues 
                                 if 'Missing required field' in issue or 'Invalid question type' in issue]
                if critical_issues:
                    validation_results["errors"].extend(critical_issues)
                    validation_results["valid"] = False
                else:
                    validation_results["warnings"].extend(question_issues)
        
        return validation_results


class ExportDataManager:
    """High-level manager for export data processing"""
    
    def __init__(self):
        self.processor = QuestionDataProcessor()
    
    def prepare_questions_for_export(self, 
                                   df: pd.DataFrame, 
                                   original_questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Prepare questions for export with full processing pipeline
        
        Args:
            df: Filtered DataFrame 
            original_questions: Original question data
            
        Returns:
            Tuple of (processed_questions, processing_report)
        """
        report = {
            "success": False,
            "processing_stats": {},
            "validation_results": {},
            "final_question_count": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Fix DataFrame data types
            df = self.processor.fix_dataframe_dtypes(df)
            
            # Filter and sync questions
            filtered_questions, stats = self.processor.filter_questions_from_dataframe(
                df, original_questions
            )
            report["processing_stats"] = stats
            
            if not filtered_questions:
                report["errors"].append("No questions matched for export")
                return [], report
            
            # Fix numeric formatting
            filtered_questions = self.processor.fix_numeric_formatting(filtered_questions)
            
            # Validate questions
            validation = self.processor.validate_questions(filtered_questions)
            report["validation_results"] = validation
            
            if not validation["valid"]:
                report["errors"].extend(validation["errors"])
                return filtered_questions, report
            
            report["warnings"].extend(validation.get("warnings", []))
            report["warnings"].extend(stats.get("warnings", []))
            
            report["success"] = True
            report["final_question_count"] = len(filtered_questions)
            
            return filtered_questions, report
            
        except Exception as e:
            report["errors"].append(f"Data processing error: {str(e)}")
            logger.exception("Error in prepare_questions_for_export")
            return [], report
