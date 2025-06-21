#!/usr/bin/env python3
"""
Canvas Adapter Module
Canvas-specific adaptations for QTI export
"""

from typing import List, Dict, Any, Optional
import logging

from .qti_generator import QTIPackageBuilder
from .latex_converter import CanvasLaTeXConverter

logger = logging.getLogger(__name__)


class CanvasQTIAdapter:
    """Canvas-specific QTI package generator"""
    
    def __init__(self):
        self.latex_converter = CanvasLaTeXConverter()
        self.package_builder = QTIPackageBuilder(self.latex_converter)
    
    def create_package(self, questions: List[Dict[str, Any]], 
                      assessment_title: str,
                      filename: str) -> Optional[bytes]:
        """
        Create Canvas-compatible QTI package
        
        Args:
            questions: List of question dictionaries
            assessment_title: Title for the assessment
            filename: Desired filename (with or without .zip)
            
        Returns:
            ZIP package data as bytes
        """
        try:
            # Ensure filename doesn't have .zip extension for internal use
            base_filename = filename.replace('.zip', '') if filename.endswith('.zip') else filename
            
            # Preprocess questions for Canvas compatibility
            canvas_questions = self._preprocess_questions_for_canvas(questions)
            
            # Create the package
            package_data = self.package_builder.create_package(
                canvas_questions, 
                assessment_title, 
                base_filename
            )
            
            if package_data:
                logger.info(f"Successfully created Canvas QTI package with {len(canvas_questions)} questions")
            
            return package_data
            
        except Exception as e:
            logger.exception("Error creating Canvas QTI package")
            return None
    
    def _preprocess_questions_for_canvas(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess questions for Canvas compatibility
        
        Args:
            questions: Original questions
            
        Returns:
            Canvas-optimized questions
        """
        canvas_questions = []
        
        for question in questions:
            canvas_question = question.copy()
            
            # Normalize question types for Canvas
            canvas_question = self._normalize_question_type(canvas_question)
            
            # Ensure Canvas-compatible point values
            canvas_question = self._normalize_points(canvas_question)
            
            # Handle Canvas-specific true/false format
            if canvas_question.get('type') == 'true_false':
                canvas_question = self._normalize_true_false(canvas_question)
            
            # Normalize choice format for multiple choice
            if canvas_question.get('type') == 'multiple_choice':
                canvas_question = self._normalize_multiple_choice(canvas_question)
            
            # Ensure numerical questions have proper format
            if canvas_question.get('type') == 'numerical':
                canvas_question = self._normalize_numerical(canvas_question)
            
            canvas_questions.append(canvas_question)
        
        return canvas_questions
    
    def _normalize_question_type(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize question type for Canvas"""
        qtype = question.get('type', 'multiple_choice').lower()
        
        # Canvas type mappings
        type_mappings = {
            'mc': 'multiple_choice',
            'multiple choice': 'multiple_choice',
            'multiplechoice': 'multiple_choice',
            'tf': 'true_false',
            'true/false': 'true_false',
            'truefalse': 'true_false',
            'num': 'numerical',
            'numeric': 'numerical',
            'fib': 'fill_in_blank',
            'fill_in_the_blank': 'fill_in_blank',
            'fillinthblank': 'fill_in_blank'
        }
        
        normalized_type = type_mappings.get(qtype, qtype)
        question['type'] = normalized_type
        
        return question
    
    def _normalize_points(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure points are in Canvas-compatible format"""
        points = question.get('points', 1)
        
        try:
            # Convert to float first
            points_float = float(points)
            
            # If it's a whole number, convert to int
            if points_float.is_integer():
                question['points'] = int(points_float)
            else:
                question['points'] = points_float
                
        except (ValueError, TypeError):
            logger.warning(f"Invalid points value: {points}, using 1")
            question['points'] = 1
        
        return question
    
    def _normalize_true_false(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize true/false questions for Canvas"""
        # Ensure choices are exactly ['True', 'False']
        question['choices'] = ['True', 'False']
        
        # Normalize correct answer
        correct = str(question.get('correct_answer', 'True')).strip().lower()
        
        if correct in ['true', 't', '1', 'yes', 'correct']:
            question['correct_answer'] = 'True'
        elif correct in ['false', 'f', '0', 'no', 'incorrect']:
            question['correct_answer'] = 'False'
        else:
            logger.warning(f"Unclear true/false answer: {correct}, using True")
            question['correct_answer'] = 'True'
        
        return question
    
    def _normalize_multiple_choice(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize multiple choice questions for Canvas"""
        choices = question.get('choices', [])
        
        if not choices:
            logger.warning("Multiple choice question has no choices")
            return question
        
        # Ensure we have string choices
        question['choices'] = [str(choice) for choice in choices]
        
        # Normalize correct answer
        correct_answer = question.get('correct_answer', '')
        
        # If correct answer is already a letter (A, B, C), convert to choice text
        if len(str(correct_answer)) == 1 and str(correct_answer).upper() in 'ABCDEFGHIJ':
            letter_index = ord(str(correct_answer).upper()) - ord('A')
            if 0 <= letter_index < len(choices):
                question['correct_answer'] = choices[letter_index]
        
        return question
    
    def _normalize_numerical(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize numerical questions for Canvas"""
        # Ensure correct answer is a number
        try:
            correct_val = float(question.get('correct_answer', 0))
            question['correct_answer'] = correct_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid numerical answer: {question.get('correct_answer')}, using 0")
            question['correct_answer'] = 0.0
        
        # Ensure tolerance is set
        if 'tolerance' not in question:
            question['tolerance'] = 0.01  # Default 1% tolerance
        else:
            try:
                tolerance = float(question['tolerance'])
                question['tolerance'] = tolerance
            except (ValueError, TypeError):
                logger.warning(f"Invalid tolerance: {question.get('tolerance')}, using 0.01")
                question['tolerance'] = 0.01
        
        return question


class CanvasImportValidator:
    """Validates questions before Canvas import"""
    
    def validate_questions_for_canvas(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate questions for Canvas compatibility
        
        Args:
            questions: List of questions to validate
            
        Returns:
            Validation report with errors and warnings
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'question_issues': []
        }
        
        for i, question in enumerate(questions):
            issues = self._validate_single_question(question, i + 1)
            
            if issues['errors']:
                report['errors'].extend(issues['errors'])
                report['valid'] = False
            
            if issues['warnings']:
                report['warnings'].extend(issues['warnings'])
            
            if issues['errors'] or issues['warnings']:
                report['question_issues'].append({
                    'question_number': i + 1,
                    'title': question.get('title', f'Question {i + 1}'),
                    'issues': issues
                })
        
        return report
    
    def _validate_single_question(self, question: Dict[str, Any], question_num: int) -> Dict[str, List[str]]:
        """Validate a single question"""
        issues = {'errors': [], 'warnings': []}
        
        # Required fields
        if not question.get('question_text'):
            issues['errors'].append("Missing question text")
        
        if not question.get('type'):
            issues['errors'].append("Missing question type")
        
        # Type-specific validation
        qtype = question.get('type', '').lower()
        
        if qtype == 'multiple_choice':
            choices = question.get('choices', [])
            if not choices:
                issues['errors'].append("Multiple choice questions must have choices")
            elif len(choices) < 2:
                issues['warnings'].append("Multiple choice questions should have at least 2 choices")
            
            if not question.get('correct_answer'):
                issues['errors'].append("Multiple choice questions must have a correct answer")
        
        elif qtype == 'numerical':
            if 'correct_answer' not in question:
                issues['errors'].append("Numerical questions must have a correct answer")
            else:
                try:
                    float(question['correct_answer'])
                except (ValueError, TypeError):
                    issues['errors'].append("Numerical correct answer must be a number")
        
        elif qtype == 'true_false':
            correct = str(question.get('correct_answer', '')).lower()
            if correct not in ['true', 'false', 't', 'f', '1', '0']:
                issues['warnings'].append("True/false answer should be 'True' or 'False'")
        
        # Points validation
        points = question.get('points', 1)
        try:
            points_val = float(points)
            if points_val <= 0:
                issues['warnings'].append("Question points should be greater than 0")
        except (ValueError, TypeError):
            issues['warnings'].append("Invalid points value")
        
        return issues


class CanvasMetadataEnhancer:
    """Adds Canvas-specific metadata to QTI packages"""
    
    def enhance_assessment_metadata(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create Canvas-specific assessment metadata
        
        Args:
            questions: List of questions
            
        Returns:
            Canvas metadata dictionary
        """
        total_points = sum(q.get('points', 1) for q in questions)
        
        # Analyze question types
        type_counts = {}
        for question in questions:
            qtype = question.get('type', 'unknown')
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        # Analyze topics if available
        topics = set()
        for question in questions:
            if question.get('topic'):
                topics.add(question['topic'])
        
        metadata = {
            'canvas_version': '2024',
            'qti_version': '1.2',
            'total_questions': len(questions),
            'total_points': total_points,
            'question_types': type_counts,
            'topics': list(topics),
            'has_latex': any(self._question_has_latex(q) for q in questions),
            'import_settings': {
                'shuffle_answers': False,
                'show_correct_answers': True,
                'one_question_at_a_time': False,
                'cant_go_back': False,
                'time_limit': None
            }
        }
        
        return metadata
    
    def _question_has_latex(self, question: Dict[str, Any]) -> bool:
        """Check if question contains LaTeX"""
        text_fields = [
            question.get('question_text', ''),
            question.get('feedback_correct', ''),
            question.get('feedback_incorrect', '')
        ]
        
        # Add choices text
        choices = question.get('choices', [])
        text_fields.extend(str(choice) for choice in choices)
        
        # Simple check for dollar signs (LaTeX delimiters)
        return any('$' in str(field) for field in text_fields)


# Convenience functions for integration
def create_canvas_qti_package(questions: List[Dict[str, Any]], 
                             title: str, 
                             filename: str) -> Optional[bytes]:
    """
    Convenience function to create Canvas QTI package
    
    Args:
        questions: List of question dictionaries
        title: Assessment title
        filename: Package filename
        
    Returns:
        QTI package data or None if failed
    """
    adapter = CanvasQTIAdapter()
    return adapter.create_package(questions, title, filename)


def validate_for_canvas(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to validate questions for Canvas
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        Validation report
    """
    validator = CanvasImportValidator()
    return validator.validate_questions_for_canvas(questions)


def get_canvas_metadata(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to get Canvas metadata
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        Canvas metadata dictionary
    """
    enhancer = CanvasMetadataEnhancer()
    return enhancer.enhance_assessment_metadata(questions)
