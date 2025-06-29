#!/usr/bin/env python3
"""
JSON Schema validation for Q2LMS questions
Validates q2prompt output against Q2LMS requirements
"""

from typing import Dict, List, Any, Tuple

class JSONSchemaValidator:
    """Validate JSON against Q2LMS question schema"""
    
    @staticmethod
    def validate_question_schema(question: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate single question against schema"""
        errors = []
        
        # Required fields validation
        required_fields = ['type', 'title', 'question_text', 'correct_answer', 'topic', 'difficulty']
        for field in required_fields:
            if field not in question:
                errors.append(f"Missing required field: '{field}'")
            elif not question[field] or (isinstance(question[field], str) and not question[field].strip()):
                errors.append(f"Empty required field: '{field}'")
        
        # Valid question types
        valid_types = ['multiple_choice', 'numerical', 'true_false', 'fill_in_multiple_blanks']
        if 'type' in question:
            if question['type'] not in valid_types:
                errors.append(f"Invalid question type: '{question['type']}'. Must be one of {valid_types}")
        
        # Type-specific validation
        if question.get('type') == 'multiple_choice':
            if 'choices' not in question:
                errors.append("Multiple choice questions must have 'choices' field")
            elif not question['choices']:
                errors.append("Multiple choice questions must have non-empty choices")
            elif not isinstance(question['choices'], list):
                errors.append("Choices must be a list")
            elif len(question['choices']) < 2:
                errors.append("Multiple choice questions must have at least 2 choices")
            elif len(question['choices']) > 4:
                errors.append("Multiple choice questions cannot have more than 4 choices")
            else:
                # Check that choices are non-empty
                empty_choices = [i for i, choice in enumerate(question['choices']) if not choice or not str(choice).strip()]
                if empty_choices:
                    errors.append(f"Empty choices found at positions: {empty_choices}")
        
        # Valid difficulty levels
        valid_difficulties = ['Easy', 'Medium', 'Hard']
        if 'difficulty' in question:
            if question['difficulty'] not in valid_difficulties:
                errors.append(f"Invalid difficulty: '{question['difficulty']}'. Must be one of {valid_difficulties}")
        
        # Points validation
        if 'points' in question:
            try:
                points = float(question['points'])
                if points <= 0:
                    errors.append("Points must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Points must be a valid number")
        
        # Tolerance validation for numerical questions
        if question.get('type') == 'numerical' and 'tolerance' in question:
            try:
                tolerance = float(question['tolerance'])
                if tolerance < 0:
                    errors.append("Tolerance must be non-negative")
            except (ValueError, TypeError):
                errors.append("Tolerance must be a valid number")
        
        # Correct answer validation for multiple choice
        if question.get('type') == 'multiple_choice':
            correct_answer = question.get('correct_answer')
            choices = question.get('choices', [])
            
            if correct_answer:
                # Check if correct_answer is a valid letter (A, B, C, D)
                if isinstance(correct_answer, str) and correct_answer.upper() in ['A', 'B', 'C', 'D']:
                    # Convert letter to index and check if choice exists
                    index = ord(correct_answer.upper()) - ord('A')
                    if index >= len(choices):
                        errors.append(f"Correct answer '{correct_answer}' references choice that doesn't exist")
                elif correct_answer not in choices:
                    # If not a letter, check if it matches any choice exactly
                    if not any(str(choice).strip() == str(correct_answer).strip() for choice in choices):
                        errors.append(f"Correct answer '{correct_answer}' does not match any choice")
        
        # String length validation
        max_lengths = {
            'title': 200,
            'question_text': 2000,
            'topic': 100,
            'subtopic': 100,
            'feedback_correct': 1000,
            'feedback_incorrect': 1000
        }
        
        for field, max_length in max_lengths.items():
            if field in question and question[field]:
                if len(str(question[field])) > max_length:
                    errors.append(f"Field '{field}' exceeds maximum length of {max_length} characters")
        
        # Check for required feedback fields (warning, not error)
        feedback_warnings = []
        if not question.get('feedback_correct'):
            feedback_warnings.append("Missing 'feedback_correct' - recommended for better learning experience")
        if not question.get('feedback_incorrect'):
            feedback_warnings.append("Missing 'feedback_incorrect' - recommended for better learning experience")
        
        # Add warnings as info (not blocking errors)
        for warning in feedback_warnings:
            # You could add these as separate warnings if needed
            pass
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_question_list(questions: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """Validate a list of questions"""
        
        if not questions:
            return False, {"error": "No questions provided"}
        
        if not isinstance(questions, list):
            return False, {"error": "Questions must be provided as a list"}
        
        results = {
            "total_questions": len(questions),
            "valid_questions": 0,
            "invalid_questions": 0,
            "question_results": []
        }
        
        overall_valid = True
        
        for i, question in enumerate(questions):
            is_valid, errors = JSONSchemaValidator.validate_question_schema(question)
            
            question_result = {
                "index": i,
                "title": question.get("title", f"Question {i+1}"),
                "valid": is_valid,
                "errors": errors
            }
            
            results["question_results"].append(question_result)
            
            if is_valid:
                results["valid_questions"] += 1
            else:
                results["invalid_questions"] += 1
                overall_valid = False
        
        results["validation_passed"] = overall_valid
        results["success_rate"] = (results["valid_questions"] / results["total_questions"]) * 100
        
        return overall_valid, results
    
    @staticmethod
    def get_question_schema() -> Dict[str, Any]:
        """Get the JSON schema definition for Q2LMS questions"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Q2LMS Question Schema",
            "description": "JSON schema for Q2LMS questions",
            "type": "object",
            "required": ["type", "title", "question_text", "correct_answer", "topic", "difficulty"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["multiple_choice", "numerical", "true_false", "fill_in_multiple_blanks"],
                    "description": "Question type"
                },
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200,
                    "description": "Question title or identifier"
                },
                "question_text": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 2000,
                    "description": "The question text (supports LaTeX)"
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 4,
                    "description": "Answer choices (required for multiple_choice)"
                },
                "correct_answer": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "number"}
                    ],
                    "description": "The correct answer"
                },
                "points": {
                    "type": "number",
                    "minimum": 0.1,
                    "default": 1,
                    "description": "Points awarded for correct answer"
                },
                "tolerance": {
                    "type": "number",
                    "minimum": 0,
                    "default": 0.05,
                    "description": "Acceptable tolerance for numerical answers"
                },
                "feedback_correct": {
                    "type": "string",
                    "maxLength": 1000,
                    "description": "Feedback for correct answers"
                },
                "feedback_incorrect": {
                    "type": "string",
                    "maxLength": 1000,
                    "description": "Feedback for incorrect answers"
                },
                "topic": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100,
                    "description": "Main topic area"
                },
                "subtopic": {
                    "type": "string",
                    "maxLength": 100,
                    "description": "Specific subtopic"
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["Easy", "Medium", "Hard"],
                    "description": "Question difficulty level"
                }
            },
            "additionalProperties": True,
            "if": {
                "properties": {"type": {"const": "multiple_choice"}}
            },
            "then": {
                "required": ["choices"]
            }
        }
