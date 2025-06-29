#!/usr/bin/env python3
"""
Unicode Converter Integration for Q2Validate
Wraps the existing unicode_to_latex_converter.py functionality
"""

try:
    # Import your existing Unicode converter
    from .unicode_to_latex_converter import UnicodeToLaTeXConverter as OriginalConverter
    CONVERTER_AVAILABLE = True
except ImportError:
    print("Warning: unicode_to_latex_converter.py not found in modules folder")
    CONVERTER_AVAILABLE = False

from typing import Dict, List, Any, Tuple

class UnicodeDetector:
    """Detect Unicode characters that should be LaTeX"""
    
    unicode_patterns = [
        # Greek letters
        'Ω', 'ω', 'π', 'φ', 'θ', 'α', 'β', 'γ', 'δ', 'λ', 'μ', 'σ', 'τ', 'ρ', 'ε',
        'ζ', 'η', 'ι', 'κ', 'ν', 'ξ', 'υ', 'χ', 'ψ',
        
        # Mathematical operators
        '±', '∓', '×', '·', '÷', '≠', '≤', '≥', '≪', '≫', '≈', '≡', '∝', '∞', '∅',
        '∈', '∉', '⊂', '⊃', '⊆', '⊇', '∪', '∩', '∀', '∃', '∇', '∂', '∫', '∮', 
        '∑', '∏', '√', '∠', '°',
        
        # Arrows
        '→', '←', '↔', '⇒', '⇐', '⇔', '↑', '↓',
        
        # Superscripts
        '⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '⁺', '⁻', 'ⁿ',
        
        # Subscripts  
        '₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉', '₊', '₋', 'ₙ'
    ]
    
    @classmethod
    def detect_unicode_in_text(cls, text: str) -> List[str]:
        """Detect Unicode characters in text"""
        if not isinstance(text, str):
            return []
        
        found = []
        for char in cls.unicode_patterns:
            if char in text:
                found.append(char)
        
        return list(set(found))  # Remove duplicates
    
    @classmethod
    def scan_question(cls, question: Dict[str, Any]) -> Dict[str, List[str]]:
        """Scan entire question for Unicode characters"""
        unicode_found = {}
        
        # Text fields to check
        text_fields = [
            'title', 'question_text', 'correct_answer', 
            'feedback_correct', 'feedback_incorrect'
        ]
        
        for field in text_fields:
            if field in question and question[field]:
                found = cls.detect_unicode_in_text(str(question[field]))
                if found:
                    unicode_found[field] = found
        
        # Check choices for multiple choice questions
        if 'choices' in question and question['choices']:
            for i, choice in enumerate(question['choices']):
                if choice:
                    found = cls.detect_unicode_in_text(str(choice))
                    if found:
                        unicode_found[f'choice_{i}'] = found
        
        return unicode_found
    
    @classmethod
    def has_unicode_issues(cls, question: Dict[str, Any]) -> bool:
        """Quick check if question has any Unicode issues"""
        unicode_issues = cls.scan_question(question)
        return len(unicode_issues) > 0


class UnicodeConverter:
    """Unicode to LaTeX converter for Q2Validate"""
    
    def __init__(self):
        """Initialize converter"""
        if CONVERTER_AVAILABLE:
            self.converter = OriginalConverter()
        else:
            self.converter = None
        
        self.detector = UnicodeDetector()
    
    def is_available(self) -> bool:
        """Check if full converter is available"""
        return CONVERTER_AVAILABLE and self.converter is not None
    
    def convert_question(self, question: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Convert Unicode in question to LaTeX
        Returns: (converted_question, conversion_report)
        """
        if not self.is_available():
            return question, {"error": "Converter not available"}
        
        # Detect issues before conversion
        original_issues = self.detector.scan_question(question)
        
        # Convert using your existing converter
        converted_question = self.converter.convert_question(question)
        
        # Detect remaining issues after conversion
        remaining_issues = self.detector.scan_question(converted_question)
        
        # Create conversion report
        conversion_report = {
            "original_unicode_count": len(original_issues),
            "remaining_unicode_count": len(remaining_issues),
            "fields_converted": list(original_issues.keys()),
            "remaining_issues": remaining_issues,
            "conversion_successful": len(remaining_issues) == 0
        }
        
        return converted_question, conversion_report
    
    def detect_issues(self, question: Dict[str, Any]) -> Dict[str, List[str]]:
        """Detect Unicode issues in question"""
        return self.detector.scan_question(question)
    
    def batch_convert(self, questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Convert multiple questions
        Returns: (converted_questions, batch_report)
        """
        if not self.is_available():
            return questions, {"error": "Converter not available"}
        
        converted_questions = []
        total_converted = 0
        total_issues = 0
        
        for question in questions:
            converted_q, report = self.convert_question(question)
            converted_questions.append(converted_q)
            
            if report.get("original_unicode_count", 0) > 0:
                total_converted += 1
            total_issues += report.get("remaining_unicode_count", 0)
        
        batch_report = {
            "total_questions": len(questions),
            "questions_with_unicode": total_converted,
            "questions_converted": total_converted,
            "remaining_issues": total_issues,
            "conversion_rate": (total_converted / len(questions)) * 100 if questions else 0,
            "success_rate": ((total_converted - total_issues) / total_converted) * 100 if total_converted > 0 else 100
        }
        
        return converted_questions, batch_report


# Fallback converter for when the original isn't available
class FallbackUnicodeConverter:
    """Basic Unicode detection when full converter unavailable"""
    
    def __init__(self):
        self.detector = UnicodeDetector()
    
    def detect_issues(self, question: Dict[str, Any]) -> Dict[str, List[str]]:
        """Detect Unicode issues"""
        return self.detector.scan_question(question)
    
    def convert_question(self, question: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Fallback - just detect, don't convert"""
        issues = self.detect_issues(question)
        
        report = {
            "original_unicode_count": len(issues),
            "remaining_unicode_count": len(issues),
            "fields_with_issues": list(issues.keys()),
            "conversion_successful": False,
            "error": "Full converter not available - detection only"
        }
        
        return question, report


# Factory function to get appropriate converter
def get_unicode_converter():
    """Get the best available Unicode converter"""
    if CONVERTER_AVAILABLE:
        return UnicodeConverter()
    else:
        return FallbackUnicodeConverter()
