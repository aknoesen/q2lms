#!/usr/bin/env python3
"""
LaTeX Converter Module
Handles LaTeX notation conversion for different target systems
"""

import re
import html
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LaTeXProcessor:
    """Base class for LaTeX processing operations"""
    
    def __init__(self):
        # Common LaTeX patterns
        self.inline_pattern = r'\$([^$]+)\$'
        self.block_pattern = r'\$\$([^$]+)\$\$'
        self.combined_pattern = r'\$\$[^$]+\$\$|\$[^$]+\$'
    
    def find_latex_expressions(self, text: str) -> List[Dict[str, Any]]:
        """
        Find all LaTeX expressions in text
        
        Args:
            text: Text to search
            
        Returns:
            List of dictionaries with expression info
        """
        if not text:
            return []
        
        expressions = []
        
        # Find block math first ($$...$$)
        for match in re.finditer(self.block_pattern, text):
            expressions.append({
                'type': 'block',
                'full_match': match.group(0),
                'content': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
        
        # Find inline math ($...$), but skip if already part of block math
        for match in re.finditer(self.inline_pattern, text):
            # Check if this match overlaps with any block math
            overlaps = any(
                expr['start'] <= match.start() <= expr['end'] 
                for expr in expressions if expr['type'] == 'block'
            )
            
            if not overlaps:
                expressions.append({
                    'type': 'inline',
                    'full_match': match.group(0),
                    'content': match.group(1),
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Sort by position for proper replacement
        expressions.sort(key=lambda x: x['start'])
        return expressions
    
    def has_latex(self, text: str) -> bool:
        """Check if text contains LaTeX expressions"""
        return bool(re.search(self.combined_pattern, str(text) if text else ''))
    
    def count_latex_expressions(self, text: str) -> Dict[str, int]:
        """Count LaTeX expressions by type"""
        expressions = self.find_latex_expressions(str(text) if text else '')
        
        counts = {'inline': 0, 'block': 0, 'total': 0}
        for expr in expressions:
            counts[expr['type']] += 1
            counts['total'] += 1
        
        return counts


class CanvasLaTeXConverter(LaTeXProcessor):
    """Converts LaTeX for Canvas LMS compatibility"""
    
    def __init__(self):
        super().__init__()
        # Canvas uses MathJax 2.7.7 and expects specific delimiters
        self.canvas_inline_start = r'\('
        self.canvas_inline_end = r'\)'
        self.canvas_block_start = r'\['
        self.canvas_block_end = r'\]'
    
    def convert_for_canvas(self, text: str) -> str:
        """
        Convert LaTeX delimiters for Canvas compatibility
        
        Args:
            text: Text with LaTeX expressions
            
        Returns:
            Text with Canvas-compatible LaTeX delimiters
        """
        if not text:
            return ""
        
        # Store LaTeX expressions temporarily
        expressions = self.find_latex_expressions(text)
        if not expressions:
            return self._safe_html_escape(text)
        
        # Replace expressions with placeholders
        placeholder_template = "LATEX_PLACEHOLDER_{}"
        converted_expressions = []
        text_with_placeholders = text
        
        # Process in reverse order to maintain positions
        for i, expr in enumerate(reversed(expressions)):
            placeholder = placeholder_template.format(len(expressions) - 1 - i)
            
            # Convert based on type
            if expr['type'] == 'block':
                # Block math: $content$ -> \[content\]
                converted_expr = f"{self.canvas_block_start}{expr['content']}{self.canvas_block_end}"
            else:
                # Inline math: $content$ -> \(content\)
                converted_expr = f"{self.canvas_inline_start}{expr['content']}{self.canvas_inline_end}"
            
            converted_expressions.insert(0, converted_expr)
            
            # Replace in text
            start, end = expr['start'], expr['end']
            text_with_placeholders = (
                text_with_placeholders[:start] + 
                placeholder + 
                text_with_placeholders[end:]
            )
        
        # HTML escape the text (but not LaTeX)
        escaped_text = self._safe_html_escape(text_with_placeholders)
        
        # Restore LaTeX expressions
        for i, converted_expr in enumerate(converted_expressions):
            placeholder = placeholder_template.format(i)
            escaped_text = escaped_text.replace(placeholder, converted_expr)
        
        return f'<div class="question-text">{escaped_text}</div>'
    
    def _safe_html_escape(self, text: str) -> str:
        """
        HTML escape that's compatible with Canvas QTI import
        Avoids problematic HTML entities that Canvas doesn't handle well
        """
        if not text:
            return ""
        
        # Use Python's html.escape but handle quotes carefully
        escaped = html.escape(str(text), quote=False)
        
        # Handle quotes in Canvas-friendly way
        escaped = escaped.replace('"', '&quot;')
        escaped = escaped.replace("'", "'")  # Keep apostrophes as-is
        
        return escaped


class StandardQTILaTeXConverter(LaTeXProcessor):
    """Converts LaTeX for standard QTI compatibility"""
    
    def __init__(self):
        super().__init__()
    
    def convert_for_qti(self, text: str) -> str:
        """
        Convert LaTeX for standard QTI format
        
        Args:
            text: Text with LaTeX expressions
            
        Returns:
            Text formatted for standard QTI
        """
        if not text:
            return ""
        
        # For standard QTI, we might want to preserve original $ delimiters
        # or convert to MathML (more complex)
        escaped_text = html.escape(str(text))
        return f'<div class="question-text">{escaped_text}</div>'


class LaTeXAnalyzer:
    """Analyzes LaTeX usage in question sets"""
    
    def __init__(self):
        self.processor = LaTeXProcessor()
    
    def analyze_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze LaTeX usage across a set of questions
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Analysis results
        """
        analysis = {
            'total_questions': len(questions),
            'questions_with_latex': 0,
            'latex_by_field': {
                'question_text': 0,
                'choices': 0,
                'feedback': 0
            },
            'expression_counts': {
                'inline': 0,
                'block': 0,
                'total': 0
            },
            'questions_by_complexity': {
                'no_latex': 0,
                'simple_latex': 0,  # 1-3 expressions
                'complex_latex': 0  # 4+ expressions
            },
            'sample_expressions': []
        }
        
        for question in questions:
            question_latex_count = 0
            question_expressions = []
            
            # Check question text
            q_text = question.get('question_text', '')
            if self.processor.has_latex(q_text):
                analysis['latex_by_field']['question_text'] += 1
                counts = self.processor.count_latex_expressions(q_text)
                question_latex_count += counts['total']
                analysis['expression_counts']['inline'] += counts['inline']
                analysis['expression_counts']['block'] += counts['block']
                analysis['expression_counts']['total'] += counts['total']
                
                # Collect sample expressions
                expressions = self.processor.find_latex_expressions(q_text)
                question_expressions.extend([expr['full_match'] for expr in expressions[:2]])
            
            # Check choices
            choices = question.get('choices', [])
            for choice in choices:
                if self.processor.has_latex(str(choice)):
                    analysis['latex_by_field']['choices'] += 1
                    counts = self.processor.count_latex_expressions(str(choice))
                    question_latex_count += counts['total']
                    analysis['expression_counts']['inline'] += counts['inline']
                    analysis['expression_counts']['block'] += counts['block']
                    analysis['expression_counts']['total'] += counts['total']
                    
                    expressions = self.processor.find_latex_expressions(str(choice))
                    question_expressions.extend([expr['full_match'] for expr in expressions[:1]])
            
            # Check feedback
            feedback_fields = ['feedback_correct', 'feedback_incorrect', 'correct_feedback', 'incorrect_feedback']
            for field in feedback_fields:
                feedback = question.get(field, '')
                if self.processor.has_latex(feedback):
                    analysis['latex_by_field']['feedback'] += 1
                    counts = self.processor.count_latex_expressions(feedback)
                    question_latex_count += counts['total']
                    analysis['expression_counts']['inline'] += counts['inline']
                    analysis['expression_counts']['block'] += counts['block']
                    analysis['expression_counts']['total'] += counts['total']
            
            # Categorize question complexity
            if question_latex_count == 0:
                analysis['questions_by_complexity']['no_latex'] += 1
            elif question_latex_count <= 3:
                analysis['questions_by_complexity']['simple_latex'] += 1
                analysis['questions_with_latex'] += 1
            else:
                analysis['questions_by_complexity']['complex_latex'] += 1
                analysis['questions_with_latex'] += 1
            
            # Store sample expressions (up to 10 unique ones)
            for expr in question_expressions:
                if expr not in analysis['sample_expressions'] and len(analysis['sample_expressions']) < 10:
                    analysis['sample_expressions'].append(expr)
        
        # Calculate percentages
        if analysis['total_questions'] > 0:
            analysis['latex_percentage'] = (analysis['questions_with_latex'] / analysis['total_questions']) * 100
        else:
            analysis['latex_percentage'] = 0
        
        return analysis


class LaTeXConverterFactory:
    """Factory for creating appropriate LaTeX converters"""
    
    @staticmethod
    def create_converter(target_system: str) -> LaTeXProcessor:
        """
        Create appropriate converter for target system
        
        Args:
            target_system: Target system ('canvas', 'standard_qti', etc.)
            
        Returns:
            Appropriate converter instance
        """
        if target_system.lower() == 'canvas':
            return CanvasLaTeXConverter()
        elif target_system.lower() in ['standard_qti', 'qti']:
            return StandardQTILaTeXConverter()
        else:
            logger.warning(f"Unknown target system: {target_system}, using Canvas converter")
            return CanvasLaTeXConverter()


# Convenience functions for backward compatibility
def convert_latex_for_canvas(text: str) -> str:
    """Legacy function for backward compatibility"""
    converter = CanvasLaTeXConverter()
    return converter.convert_for_canvas(text)


def count_latex_questions(questions: List[Dict[str, Any]]) -> int:
    """Count questions containing LaTeX notation"""
    analyzer = LaTeXAnalyzer()
    analysis = analyzer.analyze_questions(questions)
    return analysis['questions_with_latex']


def analyze_latex_usage(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze LaTeX usage in question set"""
    analyzer = LaTeXAnalyzer()
    return analyzer.analyze_questions(questions)