#!/usr/bin/env python3
"""
File Processor Module for Question Database Manager
Handles file validation, parsing, and format detection
Phase 3A Implementation
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class QuestionFormat(Enum):
    """Supported question database formats"""
    PHASE_FOUR = "Phase Four"
    PHASE_THREE = "Phase Three"
    LEGACY = "Legacy"
    UNKNOWN = "Unknown"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    level: ValidationLevel
    message: str
    location: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Result of validation process"""
    is_valid: bool
    issues: List[ValidationIssue]
    format_detected: QuestionFormat
    question_count: int
    metadata: Dict[str, Any]
    
    def has_critical_errors(self) -> bool:
        return any(issue.level == ValidationLevel.CRITICAL for issue in self.issues)
    
    def has_errors(self) -> bool:
        return any(issue.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL] 
                  for issue in self.issues)
    
    def get_error_summary(self) -> str:
        errors = [issue.message for issue in self.issues 
                 if issue.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]]
        return "; ".join(errors) if errors else ""


@dataclass
class ProcessingResult:
    """Complete file processing result"""
    validation_result: ValidationResult
    questions: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    file_info: Dict[str, Any]
    processing_time: float


class BaseValidator:
    """Base class for validators"""
    
    def __init__(self, name: str):
        self.name = name
    
    def validate(self, data: Any) -> List[ValidationIssue]:
        """Override in subclasses"""
        raise NotImplementedError


class JSONSyntaxValidator(BaseValidator):
    """Validates JSON syntax"""
    
    def __init__(self):
        super().__init__("JSON Syntax")
    
    def validate(self, content: str) -> List[ValidationIssue]:
        issues = []
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Invalid JSON syntax: {str(e)}",
                location=f"Line {e.lineno}, Column {e.colno}",
                suggestion="Check JSON syntax using a JSON validator"
            ))
        return issues


class QuestionStructureValidator(BaseValidator):
    """Validates question structure and required fields"""
    
    def __init__(self):
        super().__init__("Question Structure")
        self.required_fields = {
            'type', 'title', 'question_text', 'correct_answer', 'points'
        }
        self.optional_fields = {
            'choices', 'tolerance', 'feedback_correct', 'feedback_incorrect',
            'image_file', 'topic', 'subtopic', 'difficulty'
        }
    
    def validate(self, questions: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        
        if not questions:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message="No questions found in database",
                suggestion="Ensure the file contains a 'questions' array with at least one question"
            ))
            return issues
        
        for i, question in enumerate(questions):
            # Check required fields
            missing_fields = self.required_fields - set(question.keys())
            if missing_fields:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Missing required fields: {', '.join(missing_fields)}",
                    location=f"Question {i+1}",
                    suggestion=f"Add the following fields: {', '.join(missing_fields)}"
                ))
            
            # Validate question type
            if 'type' in question:
                valid_types = {'multiple_choice', 'numerical', 'true_false', 'fill_in_blank'}
                if question['type'] not in valid_types:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Unknown question type: {question['type']}",
                        location=f"Question {i+1}",
                        suggestion=f"Use one of: {', '.join(valid_types)}"
                    ))
            
            # Validate choices for multiple choice
            if question.get('type') == 'multiple_choice':
                if not question.get('choices') or len(question.get('choices', [])) < 2:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message="Multiple choice questions need at least 2 choices",
                        location=f"Question {i+1}",
                        suggestion="Add more choice options to the 'choices' array"
                    ))
            
            # Validate numerical questions
            if question.get('type') == 'numerical':
                if 'tolerance' not in question:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message="Numerical question missing tolerance field",
                        location=f"Question {i+1}",
                        suggestion="Add 'tolerance' field for numerical answer acceptance range"
                    ))
        
        return issues


class LaTeXValidator(BaseValidator):
    """Validates LaTeX syntax in questions"""
    
    def __init__(self):
        super().__init__("LaTeX Syntax")
        # Common LaTeX patterns to check
        self.latex_pattern = re.compile(r'\$([^$]+)\$')
        self.common_errors = {
            r'\\\\': 'Double backslashes should be single in JSON strings',
            r'\$\$': 'Use single $ for inline math, not $$',
            r'\\text\{[^}]*\$': 'LaTeX commands should not contain $ inside \\text{}',
        }
    
    def validate(self, questions: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        
        for i, question in enumerate(questions):
            # Check LaTeX in text fields
            text_fields = ['question_text', 'feedback_correct', 'feedback_incorrect']
            for field in text_fields:
                if field in question and isinstance(question[field], str):
                    field_issues = self._validate_latex_field(question[field], f"Question {i+1}, {field}")
                    issues.extend(field_issues)
            
            # Check LaTeX in choices
            if 'choices' in question and isinstance(question['choices'], list):
                for j, choice in enumerate(question['choices']):
                    if isinstance(choice, str):
                        choice_issues = self._validate_latex_field(choice, f"Question {i+1}, Choice {j+1}")
                        issues.extend(choice_issues)
        
        return issues
    
    def _validate_latex_field(self, text: str, location: str) -> List[ValidationIssue]:
        issues = []
        
        # Find all LaTeX expressions
        latex_matches = self.latex_pattern.findall(text)
        
        for latex_expr in latex_matches:
            # Check for common errors
            for error_pattern, error_msg in self.common_errors.items():
                if re.search(error_pattern, latex_expr):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"LaTeX issue: {error_msg}",
                        location=location,
                        suggestion="Check LaTeX syntax and escaping"
                    ))
            
            # Check for unmatched braces
            if latex_expr.count('{') != latex_expr.count('}'):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="Unmatched braces in LaTeX expression",
                    location=location,
                    suggestion="Ensure all { have matching } in LaTeX"
                ))
        
        # Check for unmatched $ symbols
        dollar_count = text.count('$')
        if dollar_count % 2 != 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message="Unmatched $ symbols in LaTeX",
                location=location,
                suggestion="Ensure all $ symbols are paired"
            ))
        
        return issues


class MetadataValidator(BaseValidator):
    """Validates metadata structure"""
    
    def __init__(self):
        super().__init__("Metadata")
        self.recommended_fields = {
            'generated_by', 'generation_date', 'format_version', 
            'total_questions', 'subject'
        }
    
    def validate(self, metadata: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        
        if not metadata:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="No metadata found",
                suggestion="Consider adding metadata for better organization"
            ))
            return issues
        
        # Check for recommended fields
        missing_recommended = self.recommended_fields - set(metadata.keys())
        if missing_recommended:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message=f"Missing recommended metadata fields: {', '.join(missing_recommended)}",
                suggestion="Add metadata for better database organization"
            ))
        
        # Validate specific fields
        if 'total_questions' in metadata:
            if not isinstance(metadata['total_questions'], int) or metadata['total_questions'] < 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="Invalid total_questions value in metadata",
                    suggestion="total_questions should be a non-negative integer"
                ))
        
        return issues


class FormatDetector:
    """Detects question database format version"""
    
    def detect_format(self, data: Dict[str, Any], questions: List[Dict[str, Any]]) -> QuestionFormat:
        """Detect format based on structure and fields"""
        
        # Check metadata for explicit format version
        metadata = data.get('metadata', {})
        format_version = metadata.get('format_version', '').lower()
        
        if 'phase four' in format_version or 'phase 4' in format_version:
            return QuestionFormat.PHASE_FOUR
        elif 'phase three' in format_version or 'phase 3' in format_version:
            return QuestionFormat.PHASE_THREE
        
        # Analyze questions to detect format
        if not questions:
            return QuestionFormat.UNKNOWN
        
        sample_question = questions[0]
        
        # Phase Four indicators
        if 'subtopic' in sample_question:
            return QuestionFormat.PHASE_FOUR
        
        # Phase Three indicators
        if 'topic' in sample_question and 'difficulty' in sample_question:
            return QuestionFormat.PHASE_THREE
        
        # Legacy format
        if 'question' in sample_question or 'answer' in sample_question:
            return QuestionFormat.LEGACY
        
        return QuestionFormat.UNKNOWN


class FileProcessor:
    """Main file processor class"""
    
    def __init__(self):
        self.validators = [
            JSONSyntaxValidator(),
            QuestionStructureValidator(),
            LaTeXValidator(),
            MetadataValidator()
        ]
        self.format_detector = FormatDetector()
    
    def process_file(self, uploaded_file, options: Dict[str, Any] = None) -> ProcessingResult:
        """
        Main file processing pipeline
        
        Args:
            uploaded_file: Streamlit uploaded file object
            options: Processing options (validate_latex, etc.)
        
        Returns:
            ProcessingResult with validation results and extracted data
        """
        import time
        start_time = time.time()
        
        if options is None:
            options = {}
        
        # Read file content
        try:
            content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return ProcessingResult(
                validation_result=ValidationResult(
                    is_valid=False,
                    issues=[ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message="File encoding error - not a valid text file",
                        suggestion="Ensure file is saved as UTF-8 text"
                    )],
                    format_detected=QuestionFormat.UNKNOWN,
                    question_count=0,
                    metadata={}
                ),
                questions=[],
                metadata={},
                file_info={},
                processing_time=time.time() - start_time
            )
        
        # File info
        file_info = {
            'name': uploaded_file.name,
            'size_bytes': len(content),
            'size_mb': len(content) / (1024 * 1024)
        }
        
        # Start validation process
        all_issues = []
        
        # 1. JSON Syntax Validation
        json_validator = JSONSyntaxValidator()
        json_issues = json_validator.validate(content)
        all_issues.extend(json_issues)
        
        # If JSON is invalid, stop here
        if any(issue.level == ValidationLevel.CRITICAL for issue in json_issues):
            return ProcessingResult(
                validation_result=ValidationResult(
                    is_valid=False,
                    issues=all_issues,
                    format_detected=QuestionFormat.UNKNOWN,
                    question_count=0,
                    metadata={}
                ),
                questions=[],
                metadata={},
                file_info=file_info,
                processing_time=time.time() - start_time
            )
        
        # Parse JSON
        try:
            data = json.loads(content)
        except Exception as e:
            all_issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"JSON parsing failed: {str(e)}",
                suggestion="Check JSON syntax"
            ))
            return ProcessingResult(
                validation_result=ValidationResult(
                    is_valid=False,
                    issues=all_issues,
                    format_detected=QuestionFormat.UNKNOWN,
                    question_count=0,
                    metadata={}
                ),
                questions=[],
                metadata={},
                file_info=file_info,
                processing_time=time.time() - start_time
            )
        
        # Extract questions and metadata
        questions, metadata = self._extract_questions_and_metadata(data)
        
        # Detect format
        format_detected = self.format_detector.detect_format(data, questions)
        
        # 2. Question Structure Validation
        structure_validator = QuestionStructureValidator()
        structure_issues = structure_validator.validate(questions)
        all_issues.extend(structure_issues)
        
        # 3. LaTeX Validation (if enabled)
        if options.get('validate_latex', True):
            latex_validator = LaTeXValidator()
            latex_issues = latex_validator.validate(questions)
            all_issues.extend(latex_issues)
        
        # 4. Metadata Validation
        metadata_validator = MetadataValidator()
        metadata_issues = metadata_validator.validate(metadata)
        all_issues.extend(metadata_issues)
        
        # Determine if validation passed
        is_valid = not any(issue.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL] 
                          for issue in all_issues)
        
        validation_result = ValidationResult(
            is_valid=is_valid,
            issues=all_issues,
            format_detected=format_detected,
            question_count=len(questions),
            metadata=metadata
        )
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            validation_result=validation_result,
            questions=questions,
            metadata=metadata,
            file_info=file_info,
            processing_time=processing_time
        )
    
    def _extract_questions_and_metadata(self, data: Dict[str, Any]) -> Tuple[List[Dict], Dict[str, Any]]:
        """Extract questions and metadata from parsed JSON"""
        
        if isinstance(data, dict) and 'questions' in data:
            # Structured format with questions array
            questions = data['questions']
            metadata = data.get('metadata', {})
        elif isinstance(data, list):
            # Simple list format
            questions = data
            metadata = {}
        else:
            # Unknown format
            questions = []
            metadata = {}
        
        return questions, metadata
    
    def get_processing_summary(self, result: ProcessingResult) -> Dict[str, Any]:
        """Generate a summary of processing results"""
        
        issues_by_level = {}
        for level in ValidationLevel:
            count = sum(1 for issue in result.validation_result.issues 
                       if issue.level == level)
            if count > 0:
                issues_by_level[level.value] = count
        
        return {
            'file_name': result.file_info.get('name', 'Unknown'),
            'file_size_mb': round(result.file_info.get('size_mb', 0), 2),
            'format_detected': result.validation_result.format_detected.value,
            'question_count': result.validation_result.question_count,
            'is_valid': result.validation_result.is_valid,
            'has_errors': result.validation_result.has_errors(),
            'issues_by_level': issues_by_level,
            'processing_time_ms': round(result.processing_time * 1000, 1),
            'metadata_fields': list(result.metadata.keys()) if result.metadata else []
        }


# Utility functions for integration
def validate_uploaded_file(uploaded_file, options: Dict[str, Any] = None) -> ProcessingResult:
    """Convenience function for single file validation"""
    processor = FileProcessor()
    return processor.process_file(uploaded_file, options)


def batch_validate_files(uploaded_files: List, options: Dict[str, Any] = None) -> List[ProcessingResult]:
    """Validate multiple files and return results"""
    processor = FileProcessor()
    results = []
    
    for uploaded_file in uploaded_files:
        result = processor.process_file(uploaded_file, options)
        results.append(result)
    
    return results