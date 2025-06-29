# modules/export/latex_converter.py

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
        """
        if not text:
            return []
        
        expressions = []
        for match in re.finditer(self.block_pattern, text):
            expressions.append({
                'type': 'block', 'full_match': match.group(0), 'content': match.group(1),
                'start': match.start(), 'end': match.end()
            })
        for match in re.finditer(self.inline_pattern, text):
            overlaps = any(expr['start'] <= match.start() <= expr['end'] for expr in expressions if expr['type'] == 'block')
            if not overlaps:
                expressions.append({
                    'type': 'inline', 'full_match': match.group(0), 'content': match.group(1),
                    'start': match.start(), 'end': match.end()
                })
        expressions.sort(key=lambda x: x['start'])
        return expressions
    
    def has_latex(self, text: str) -> bool:
        return bool(re.search(self.combined_pattern, str(text) if text else ''))
    
    def count_latex_expressions(self, text: str) -> Dict[str, int]:
        expressions = self.find_latex_expressions(str(text) if text else '')
        counts = {'inline': 0, 'block': 0, 'total': 0}
        for expr in expressions:
            counts[expr['type']] += 1
            counts['total'] += 1
        return counts

    def _add_space_before_latex(self, text_before: str) -> str:
        if not text_before: return text_before
        last_char = text_before[-1]
        if last_char.isalnum() or last_char in ')]}':
            no_space_patterns = [r'[=(<\[\{]$', r'[+\-*/^]$', r'[,:;]$']
            for pattern in no_space_patterns:
                if re.search(pattern, text_before):
                    return text_before
            return text_before + ' '
        return text_before
    
    def _add_space_after_latex(self, latex_output: str, text_after: str) -> str:
        if not text_after: return latex_output
        first_char = text_after[0]
        if first_char.isalnum():
            return latex_output + ' '
        return latex_output

    def _safe_html_escape(self, text: str) -> str:
        if not text: return ""
        if self.has_latex(text):
            return text # CRITICAL: Do not escape LaTeX content for QTI
        escaped = html.escape(str(text), quote=False)
        escaped = escaped.replace('"', '&quot;')
        escaped = escaped.replace("'", "'") # Ensure single quotes are not double escaped
        return escaped


class CanvasLaTeXConverter(LaTeXProcessor):
    """Converts LaTeX for Canvas LMS compatibility and Streamlit display"""
    
    def __init__(self):
        super().__init__()
        # These are used for generating the delimiters
        self.canvas_inline_start = r'\(' 
        self.canvas_inline_end = r'\)'   
        self.canvas_block_start = r'\['  
        self.canvas_block_end = r'\]'    
    
    def convert_for_canvas(self, text: str) -> str:
        """
        Converts LaTeX delimiters to \\(...\\) or \\[...\\] for Canvas/QTI export.
        This method is used for QTI generation and should NOT be changed.
        """
        # print(f"DEBUG (converter): convert_for_canvas called with: '{text[:100]}...'")
        
        if not text:
            return ""
        
        expressions = self.find_latex_expressions(text)
        # print(f"DEBUG (converter): Found {len(expressions)} LaTeX expressions")
        
        if not expressions:
            return text 
        
        result_parts = []
        last_end = 0
        
        for i, expr in enumerate(expressions):
            text_before = text[last_end:expr['start']]
            if text_before:
                # Add literal spaces for Canvas format
                spaced_text_before = self._add_space_before_latex(text_before) 
                result_parts.append(spaced_text_before)
            
            # Add the converted LaTeX expression for Canvas (e.g., \(content\))
            if expr['type'] == 'block':
                latex_output = f"{self.canvas_block_start}{expr['content']}{self.canvas_block_end}"
            else: # Inline math
                latex_output = f"{self.canvas_inline_start}{expr['content']}{self.canvas_inline_end}"
            
            result_parts.append(latex_output) 
            last_end = expr['end']
        
        remaining_text = text[last_end:]
        if remaining_text:
            result_parts.append(remaining_text)
        
        final_content = ''.join(result_parts)
        # print(f"DEBUG (converter): Final content from converter: '{final_content}'")
        return final_content # Returns string with \(...\) for Canvas/QTI
    
    def convert_for_streamlit(self, text: str) -> str:
        """
        NEW METHOD: Converts LaTeX delimiters to \\(...\\) format for Streamlit display.
        Streamlit's markdown with MathJax should be able to process these.
        """
        # print(f"DEBUG (converter): convert_for_streamlit called with: '{text[:100]}...'")
        
        if not text:
            return ""
        
        expressions = self.find_latex_expressions(text)
        # print(f"DEBUG (converter): Found {len(expressions)} LaTeX expressions")
        
        if not expressions:
            return text 
        
        result_parts = []
        last_end = 0
        
        for i, expr in enumerate(expressions):
            text_before = text[last_end:expr['start']]
            if text_before:
                # Add literal spaces for the text before LaTeX
                spaced_text_before = self._add_space_before_latex(text_before)
                result_parts.append(spaced_text_before)
            
            # FIXED: Convert LaTeX to \\(...\\) format that Streamlit can handle
            if expr['type'] == 'block':
                latex_output = f"\\[{expr['content']}\\]"
            else: # Inline math
                latex_output = f"\\({expr['content']}\\)"
            
            result_parts.append(latex_output)
            last_end = expr['end']
        
        # Add any remaining text after the last LaTeX expression
        remaining_text = text[last_end:]
        if remaining_text:
            result_parts.append(remaining_text)
        
        final_content = ''.join(result_parts)
        # print(f"DEBUG (converter): Final Streamlit content: '{final_content}'")
        return final_content
    
    def convert_for_qti(self, text: str) -> str:
        """
        Converts LaTeX delimiters to \\(...\\) or \\[...\\] for QTI/Canvas export.
        This is the same as convert_for_canvas but with a clearer name.
        """
        return self.convert_for_canvas(text)


class StandardQTILaTeXConverter(LaTeXProcessor):
    """Converts LaTeX for standard QTI compatibility"""
    
    def __init__(self):
        super().__init__()
        # Use same Canvas-style delimiters
        self.canvas_inline_start = r'\(' 
        self.canvas_inline_end = r'\)'   
        self.canvas_block_start = r'\['  
        self.canvas_block_end = r'\]'
    
    def convert_for_qti(self, text: str) -> str:
        """
        Convert LaTeX for standard QTI format. This performs HTML escaping.
        """
        if not text: return ""
        expressions = self.find_latex_expressions(text)
        result_parts = []
        last_end = 0
        for expr in expressions:
            text_before = text[last_end:expr['start']]
            result_parts.append(self._safe_html_escape(text_before)) # HTML escape plain text
            
            # Convert to Canvas-style delimiters for QTI
            if expr['type'] == 'block':
                latex_part = f"{self.canvas_block_start}{expr['content']}{self.canvas_block_end}"
            else:
                latex_part = f"{self.canvas_inline_start}{expr['content']}{self.canvas_inline_end}"
            result_parts.append(latex_part) # Add LaTeX without HTML escaping
            last_end = expr['end']
            
        remaining_text = text[last_end:]
        result_parts.append(self._safe_html_escape(remaining_text)) # HTML escape remaining plain text
        
        final_qti_content = ''.join(result_parts)
        return f'<div class="question-text">{final_qti_content}</div>'


class LaTeXAnalyzer:
    """Analyzes LaTeX usage in question sets"""
    def __init__(self):
        self.processor = LaTeXProcessor()
    
    def analyze_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis = {
            'total_questions': len(questions), 'questions_with_latex': 0,
            'latex_by_field': {'question_text': 0, 'choices': 0, 'feedback': 0},
            'expression_counts': {'inline': 0, 'block': 0, 'total': 0},
            'questions_by_complexity': {'no_latex': 0, 'simple_latex': 0, 'complex_latex': 0},
            'sample_expressions': []
        }
        for question in questions:
            question_latex_count = 0
            question_expressions = []
            
            q_text = question.get('question_text', '')
            if self.processor.has_latex(q_text):
                analysis['latex_by_field']['question_text'] += 1
                counts = self.processor.count_latex_expressions(q_text)
                question_latex_count += counts['total']
                analysis['expression_counts']['inline'] += counts['inline']
                analysis['expression_counts']['block'] += counts['block']
                analysis['expression_counts']['total'] += counts['total']
                expressions = self.processor.find_latex_expressions(q_text)
                question_expressions.extend([expr['full_match'] for expr in expressions[:2]])
            
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
            
            if question_latex_count == 0: analysis['questions_by_complexity']['no_latex'] += 1
            elif question_latex_count <= 3: analysis['questions_by_complexity']['simple_latex'] += 1; analysis['questions_with_latex'] += 1
            else: analysis['questions_by_complexity']['complex_latex'] += 1; analysis['questions_with_latex'] += 1
            
            for expr in question_expressions:
                if expr not in analysis['sample_expressions'] and len(analysis['sample_expressions']) < 10:
                    analysis['sample_expressions'].append(expr)
        
        if analysis['total_questions'] > 0: analysis['latex_percentage'] = (analysis['questions_with_latex'] / analysis['total_questions']) * 100
        else: analysis['latex_percentage'] = 0
        
        return analysis


class LaTeXConverterFactory:
    """Factory for creating appropriate LaTeX converters"""
    
    @staticmethod
    def create_converter(target_system: str) -> LaTeXProcessor:
        if target_system.lower() == 'canvas':
            return CanvasLaTeXConverter()
        elif target_system.lower() in ['standard_qti', 'qti']:
            return StandardQTILaTeXConverter()
        else:
            logger.warning(f"Unknown target system: {target_system}, using Canvas converter")
            return CanvasLaTeXConverter()


# Convenience functions for backward compatibility
def convert_latex_for_canvas(text: str) -> str:
    # This legacy function will use the QTI format for exports
    converter = CanvasLaTeXConverter()
    return converter.convert_for_qti(text)


def count_latex_questions(questions: List[Dict[str, Any]]) -> int:
    analyzer = LaTeXAnalyzer()
    analysis = analyzer.analyze_questions(questions)
    return analysis['questions_with_latex']


def analyze_latex_usage(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    analyzer = LaTeXAnalyzer()
    return analyzer.analyze_questions(questions)