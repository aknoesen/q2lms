#!/usr/bin/env python3
"""
LaTeX Processor Module
Handles cleanup and standardization of mathematical notation from LLM outputs
Designed for electrical engineering and STEM question databases

Phase 1 Implementation - Core LaTeX Processing Foundation
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CleanupReport:
    """Report of LaTeX cleanup operations performed"""
    original_text: str
    cleaned_text: str
    changes_made: List[str]
    unicode_conversions: int
    inline_fixes: int
    display_fixes: int
    syntax_errors_fixed: int
    mixed_notation_detected: bool
    
    def __str__(self) -> str:
        return f"""LaTeX Cleanup Report:
- Unicode conversions: {self.unicode_conversions}
- Inline equation fixes: {self.inline_fixes}
- Display equation fixes: {self.display_fixes}
- Syntax errors fixed: {self.syntax_errors_fixed}
- Mixed notation detected: {'Yes' if self.mixed_notation_detected else 'No'}
- Total changes: {len(self.changes_made)}
"""

class LaTeXProcessor:
    """
    Comprehensive LaTeX processing for educational content
    Handles common LLM formatting issues and standardizes notation
    """
    
    def __init__(self):
        """Initialize the LaTeX processor with common patterns"""
        self.unicode_map = self._build_unicode_map()
        self.common_patterns = self._build_pattern_map()
        
    def _build_unicode_map(self) -> Dict[str, str]:
        """Build mapping of Unicode symbols to LaTeX equivalents"""
        return {
            # Encoding artifacts (common UTF-8 issues)
            'Î©': r'\Omega',     # Corrupted Ω
            'Î¼': r'\mu',        # Corrupted μ
            'Ï‰': r'\omega',     # Corrupted ω
            'Ï€': r'\pi',        # Corrupted π
            
            # Greek letters
            'α': r'\alpha',
            'β': r'\beta', 
            'γ': r'\gamma',
            'δ': r'\delta',
            'ε': r'\epsilon',
            'ζ': r'\zeta',
            'η': r'\eta',
            'θ': r'\theta',
            'ι': r'\iota',
            'κ': r'\kappa',
            'λ': r'\lambda',
            'μ': r'\mu',
            'ν': r'\nu',
            'ξ': r'\xi',
            'π': r'\pi',
            'ρ': r'\rho',
            'σ': r'\sigma',
            'τ': r'\tau',
            'υ': r'\upsilon',
            'φ': r'\phi',
            'χ': r'\chi',
            'ψ': r'\psi',
            'ω': r'\omega',
            
            # Capital Greek letters
            'Α': r'\Alpha',
            'Β': r'\Beta',
            'Γ': r'\Gamma',
            'Δ': r'\Delta',
            'Ε': r'\Epsilon',
            'Ζ': r'\Zeta',
            'Η': r'\Eta',
            'Θ': r'\Theta',
            'Ι': r'\Iota',
            'Κ': r'\Kappa',
            'Λ': r'\Lambda',
            'Μ': r'\Mu',
            'Ν': r'\Nu',
            'Ξ': r'\Xi',
            'Π': r'\Pi',
            'Ρ': r'\Rho',
            'Σ': r'\Sigma',
            'Τ': r'\Tau',
            'Υ': r'\Upsilon',
            'Φ': r'\Phi',
            'Χ': r'\Chi',
            'Ψ': r'\Psi',
            'Ω': r'\Omega',
            
            # Mathematical symbols
            '∞': r'\infty',
            '±': r'\pm',
            '∓': r'\mp',
            '×': r'\times',
            '÷': r'\div',
            '≠': r'\neq',
            '≤': r'\leq',
            '≥': r'\geq',
            '≈': r'\approx',
            '∝': r'\propto',
            '∂': r'\partial',
            '∇': r'\nabla',
            '∫': r'\int',
            '∑': r'\sum',
            '∏': r'\prod',
            '√': r'\sqrt',
            '∀': r'\forall',
            '∃': r'\exists',
            '∈': r'\in',
            '∉': r'\notin',
            '⊂': r'\subset',
            '⊃': r'\supset',
            '∪': r'\cup',
            '∩': r'\cap',
            '⊥': r'\perp',
            '∥': r'\parallel',
            '°': r'°',  # Degree symbol - keep as is for Canvas compatibility
            
            # Subscripts and superscripts
            '²': r'^2',
            '³': r'^3',
            '¹': r'^1',
            '₀': r'_0',
            '₁': r'_1',
            '₂': r'_2',
            '₃': r'_3',
            '₄': r'_4',
            '₅': r'_5',
            '₆': r'_6',
            '₇': r'_7',
            '₈': r'_8',
            '₉': r'_9',
            
            # Electrical engineering specific
            '∠': r'\angle',  # Angle notation
        }
    
    def _build_pattern_map(self) -> Dict[str, str]:
        """Build common LaTeX pattern fixes"""
        return {
            # Fix spacing around operators
            r'([a-zA-Z0-9])\+([a-zA-Z0-9])': r'\1 + \2',
            r'([a-zA-Z0-9])-([a-zA-Z0-9])': r'\1 - \2',
            r'([a-zA-Z0-9])\*([a-zA-Z0-9])': r'\1 \times \2',
            r'([a-zA-Z0-9])/([a-zA-Z0-9])': r'\1 / \2',
            
            # Fix electrical engineering notation
            r'([0-9]+)Ω': r'\1\\,\\Omega',
            r'([0-9]+)V': r'\1\\,\\text{V}',
            r'([0-9]+)A': r'\1\\,\\text{A}',
            r'([0-9]+)W': r'\1\\,\\text{W}',
            r'([0-9]+)Hz': r'\1\\,\\text{Hz}',
            r'([0-9]+)F': r'\1\\,\\text{F}',
            r'([0-9]+)H': r'\1\\,\\text{H}',
            
            # Fix angle notation
            r'∠([0-9.-]+)°': r'\\angle{\\1°}',
            r'\\angle([0-9.-]+)°': r'\\angle{\\1°}',
            
            # Fix common function names
            r'\\sin([^h])': r'\\sin \\1',
            r'\\cos([^h])': r'\\cos \\1', 
            r'\\tan([^h])': r'\\tan \\1',
            r'\\log([^a])': r'\\log \\1',
            r'\\ln([^a])': r'\\ln \\1',
        }
    
    def detect_mixed_notation(self, text: str) -> bool:
        """
        Detect if text contains mixed Unicode/LaTeX notation
        Returns True if mixed notation is found
        """
        if not text:
            return False
            
        # Check for Unicode symbols that should be LaTeX
        has_unicode = any(char in text for char in self.unicode_map.keys())
        
        # Check for LaTeX commands
        has_latex = bool(re.search(r'\\[a-zA-Z]+', text))
        
        # Check for $ delimiters
        has_math_delimiters = '$' in text
        
        return (has_unicode and has_latex) or (has_unicode and has_math_delimiters)
    
    def unicode_to_latex(self, text: str) -> Tuple[str, int]:
        """
        Convert Unicode mathematical symbols to LaTeX equivalents
        Returns (converted_text, conversion_count)
        """
        if not text:
            return text, 0
            
        conversion_count = 0
        result = text
        
        for unicode_char, latex_cmd in self.unicode_map.items():
            if unicode_char in result:
                result = result.replace(unicode_char, latex_cmd)
                conversion_count += text.count(unicode_char)
        
        return result, conversion_count
    
    def fix_inline_equations(self, text: str) -> Tuple[str, int]:
        """
        Fix inline equation formatting
        Handles single $ delimiters and ensures proper spacing
        Returns (fixed_text, fix_count)
        """
        if not text:
            return text, 0
            
        fix_count = 0
        result = text
        
        # Pattern to match inline math with various issues
        patterns = [
            # Fix missing spaces around inline math
            (r'([a-zA-Z])(\$[^$]+\$)([a-zA-Z])', r'\1 \2 \3'),
            
            # Fix multiple consecutive $ signs (convert to display math)
            (r'\$\$\$([^$]+)\$\$\$', r'$$\1$$'),
            
            # Fix inline math that should be display math (complex expressions)
            (r'\$([^$]*(?:\\frac|\\int|\\sum|\\prod)[^$]*)\$', r'$$\1$$'),
        ]
        
        for pattern, replacement in patterns:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fix_count += 1
                result = new_result
        
        return result, fix_count
    
    def fix_display_equations(self, text: str) -> Tuple[str, int]:
        """
        Fix display equation formatting
        Handles $$ delimiters and ensures proper structure
        Returns (fixed_text, fix_count)
        """
        if not text:
            return text, 0
            
        fix_count = 0
        result = text
        
        # Patterns for display math fixes
        patterns = [
            # Fix unmatched $$ delimiters
            (r'\$\$([^$]+)\$(?!\$)', r'$$\1$$'),
            (r'(?<!\$)\$([^$]+)\$\$', r'$$\1$$'),
            
            # Fix spacing issues in display math
            (r'\$\$\s*([^$]+?)\s*\$\$', r'$$\1$$'),
            
            # Fix broken equations like "$formula where $more$"
            (r'\$\$([^$]+?)\s+where\s*\$\$([^$]+?)\$\
        ]
        
        for pattern, replacement in patterns:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fix_count += 1
                result = new_result
        
        return result, fix_count
    
    def validate_latex_syntax(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validate LaTeX syntax and return errors found
        Returns (is_valid, error_list)
        """
        if not text:
            return True, []
            
        errors = []
        
        # Check for unmatched braces
        brace_count = text.count('{') - text.count('}')
        if brace_count != 0:
            errors.append(f"Unmatched braces: {abs(brace_count)} {'opening' if brace_count > 0 else 'closing'}")
        
        # Check for unmatched parentheses in math mode
        math_sections = re.findall(r'\$\$?[^$]+\$\$?', text)
        for section in math_sections:
            paren_count = section.count('(') - section.count(')')
            if paren_count != 0:
                errors.append(f"Unmatched parentheses in math: {section[:30]}...")
        
        # Check for incomplete LaTeX commands
        incomplete_commands = re.findall(r'\\[a-zA-Z]*(?=[^a-zA-Z]|$)', text)
        for cmd in incomplete_commands:
            if len(cmd) == 1:  # Just a backslash
                errors.append(f"Incomplete LaTeX command: {cmd}")
        
        # Check for unmatched $ delimiters
        dollar_positions = [m.start() for m in re.finditer(r'\$', text)]
        if len(dollar_positions) % 2 != 0:
            errors.append("Unmatched $ delimiters")
        
        return len(errors) == 0, errors
    
    def fix_common_syntax_errors(self, text: str) -> Tuple[str, int]:
        """
        Fix common LaTeX syntax errors
        Returns (fixed_text, error_count_fixed)
        """
        if not text:
            return text, 0
            
        fixes_applied = 0
        result = text
        
        # Fix patterns that commonly cause errors
        error_fixes = [
            # Fix incomplete fractions
            (r'\\frac([^{])', r'\\frac{\1}'),
            
            # Fix missing braces around superscripts/subscripts
            (r'\^([a-zA-Z0-9]{2,})', r'^{\1}'),
            (r'_([a-zA-Z0-9]{2,})', r'_{\1}'),
            
            # Fix double backslashes outside of arrays/matrices
            (r'\\\\(?![^$]*\$\$)', r'\\'),
            
            # Fix spacing issues with text commands
            (r'\\text\s*{([^}]+)}', r'\\text{\1}'),
            
            # Fix angle notation
            (r'\\angle\s*([0-9.-]+)', r'\\angle{\1}'),
            
            # Fix missing spaces in function names
            (r'\\(sin|cos|tan|log|ln)([a-zA-Z])', r'\\\1 \2'),
        ]
        
        for pattern, replacement in error_fixes:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fixes_applied += 1
                result = new_result
        
        return result, fixes_applied
    
    def clean_mathematical_notation(self, text: str) -> str:
        """
        Main function to clean and standardize mathematical notation
        Applies all cleaning operations in sequence
        """
        if not text:
            return text
            
        # Step 1: Convert Unicode to LaTeX
        result, _ = self.unicode_to_latex(text)
        
        # Step 2: Fix inline equations
        result, _ = self.fix_inline_equations(result)
        
        # Step 3: Fix display equations
        result, _ = self.fix_display_equations(result)
        
        # Step 4: Fix common syntax errors
        result, _ = self.fix_common_syntax_errors(result)
        
        # Step 5: Apply common pattern fixes
        for pattern, replacement in self.common_patterns.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def generate_cleanup_report(self, original: str, cleaned: str) -> CleanupReport:
        """
        Generate comprehensive cleanup report
        """
        if not original:
            return CleanupReport(
                original_text="",
                cleaned_text="",
                changes_made=[],
                unicode_conversions=0,
                inline_fixes=0,
                display_fixes=0,
                syntax_errors_fixed=0,
                mixed_notation_detected=False
            )
        
        changes_made = []
        
        # Count Unicode conversions
        _, unicode_count = self.unicode_to_latex(original)
        if unicode_count > 0:
            changes_made.append(f"Converted {unicode_count} Unicode symbols to LaTeX")
        
        # Count inline fixes
        _, inline_count = self.fix_inline_equations(original)
        if inline_count > 0:
            changes_made.append(f"Fixed {inline_count} inline equation issues")
        
        # Count display fixes
        _, display_count = self.fix_display_equations(original)
        if display_count > 0:
            changes_made.append(f"Fixed {display_count} display equation issues")
        
        # Count syntax fixes
        _, syntax_count = self.fix_common_syntax_errors(original)
        if syntax_count > 0:
            changes_made.append(f"Fixed {syntax_count} syntax errors")
        
        # Check for mixed notation
        mixed_notation = self.detect_mixed_notation(original)
        if mixed_notation:
            changes_made.append("Detected and resolved mixed notation")
        
        # Check if text actually changed
        if original != cleaned:
            changes_made.append("Applied pattern-based formatting improvements")
        
        return CleanupReport(
            original_text=original,
            cleaned_text=cleaned,
            changes_made=changes_made,
            unicode_conversions=unicode_count,
            inline_fixes=inline_count,
            display_fixes=display_count,
            syntax_errors_fixed=syntax_count,
            mixed_notation_detected=mixed_notation
        )
    
    def process_question_database(self, questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
        """
        Process entire question database and clean LaTeX notation
        Returns (cleaned_questions, cleanup_reports)
        """
        cleaned_questions = []
        reports = []
        
        for i, question in enumerate(questions):
            cleaned_question = question.copy()
            question_reports = []
            
            # Fields that may contain LaTeX
            latex_fields = [
                'question_text', 'correct_answer', 'feedback_correct', 
                'feedback_incorrect', 'title'
            ]
            
            # Process choices if they exist
            if 'choices' in question and question['choices']:
                cleaned_choices = []
                for choice in question['choices']:
                    if choice:
                        cleaned_choice = self.clean_mathematical_notation(str(choice))
                        cleaned_choices.append(cleaned_choice)
                        
                        # Generate report for this choice
                        if str(choice) != cleaned_choice:
                            report = self.generate_cleanup_report(str(choice), cleaned_choice)
                            question_reports.append(report)
                    else:
                        cleaned_choices.append(choice)
                
                cleaned_question['choices'] = cleaned_choices
            
            # Process other LaTeX fields
            for field in latex_fields:
                if field in question and question[field]:
                    original_text = str(question[field])
                    cleaned_text = self.clean_mathematical_notation(original_text)
                    cleaned_question[field] = cleaned_text
                    
                    # Generate report for this field
                    if original_text != cleaned_text:
                        report = self.generate_cleanup_report(original_text, cleaned_text)
                        question_reports.append(report)
            
            cleaned_questions.append(cleaned_question)
            
            # Combine reports for this question
            if question_reports:
                # Create summary report for the question
                total_changes = sum(len(r.changes_made) for r in question_reports)
                combined_report = CleanupReport(
                    original_text=f"Question {i+1}",
                    cleaned_text=f"Question {i+1} (processed)",
                    changes_made=[f"Total changes across all fields: {total_changes}"],
                    unicode_conversions=sum(r.unicode_conversions for r in question_reports),
                    inline_fixes=sum(r.inline_fixes for r in question_reports),
                    display_fixes=sum(r.display_fixes for r in question_reports),
                    syntax_errors_fixed=sum(r.syntax_errors_fixed for r in question_reports),
                    mixed_notation_detected=any(r.mixed_notation_detected for r in question_reports)
                )
                reports.append(combined_report)
        
        return cleaned_questions, reports


# Convenience functions for external use
def clean_text(text: str) -> str:
    """
    Convenience function to clean a single text string
    """
    processor = LaTeXProcessor()
    return processor.clean_mathematical_notation(text)

def process_question_list(questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
    """
    Convenience function to process a list of questions
    """
    processor = LaTeXProcessor()
    return processor.process_question_database(questions)

def validate_text(text: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate LaTeX syntax in text
    """
    processor = LaTeXProcessor()
    return processor.validate_latex_syntax(text)


# Example usage and testing
if __name__ == "__main__":
    # Example usage with electrical engineering question
    processor = LaTeXProcessor()
    
    # Test with sample text from your database
    sample_text = "Calculate the complex impedance Z for a circuit with R = 50Ω in series with a capacitor C = 10μF at frequency f = 1000 Hz. Use the formula: $$Z = R + j\\omega C$$ where $$\\omega = 2\\pi f$$ and $$j = \\sqrt{-1}$$"
    
    print("Original text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Clean the text
    cleaned = processor.clean_mathematical_notation(sample_text)
    print("Cleaned text:")
    print(cleaned)
    print("\n" + "="*50 + "\n")
    
    # Generate report
    report = processor.generate_cleanup_report(sample_text, cleaned)
    print("Cleanup Report:")
    print(report)
    
    # Validate result
    is_valid, errors = processor.validate_latex_syntax(cleaned)
    print(f"\nValidation: {'✅ Valid' if is_valid else '❌ Errors found'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
, r'$\1$ where $\2$'),
            (r'\$\$([^$]+?)\s+and\s*([^$]+?)\$\
        ]
        
        for pattern, replacement in patterns:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fix_count += 1
                result = new_result
        
        return result, fix_count
    
    def validate_latex_syntax(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validate LaTeX syntax and return errors found
        Returns (is_valid, error_list)
        """
        if not text:
            return True, []
            
        errors = []
        
        # Check for unmatched braces
        brace_count = text.count('{') - text.count('}')
        if brace_count != 0:
            errors.append(f"Unmatched braces: {abs(brace_count)} {'opening' if brace_count > 0 else 'closing'}")
        
        # Check for unmatched parentheses in math mode
        math_sections = re.findall(r'\$\$?[^$]+\$\$?', text)
        for section in math_sections:
            paren_count = section.count('(') - section.count(')')
            if paren_count != 0:
                errors.append(f"Unmatched parentheses in math: {section[:30]}...")
        
        # Check for incomplete LaTeX commands
        incomplete_commands = re.findall(r'\\[a-zA-Z]*(?=[^a-zA-Z]|$)', text)
        for cmd in incomplete_commands:
            if len(cmd) == 1:  # Just a backslash
                errors.append(f"Incomplete LaTeX command: {cmd}")
        
        # Check for unmatched $ delimiters
        dollar_positions = [m.start() for m in re.finditer(r'\$', text)]
        if len(dollar_positions) % 2 != 0:
            errors.append("Unmatched $ delimiters")
        
        return len(errors) == 0, errors
    
    def fix_common_syntax_errors(self, text: str) -> Tuple[str, int]:
        """
        Fix common LaTeX syntax errors
        Returns (fixed_text, error_count_fixed)
        """
        if not text:
            return text, 0
            
        fixes_applied = 0
        result = text
        
        # Fix patterns that commonly cause errors
        error_fixes = [
            # Fix incomplete fractions
            (r'\\frac([^{])', r'\\frac{\1}'),
            
            # Fix missing braces around superscripts/subscripts
            (r'\^([a-zA-Z0-9]{2,})', r'^{\1}'),
            (r'_([a-zA-Z0-9]{2,})', r'_{\1}'),
            
            # Fix double backslashes outside of arrays/matrices
            (r'\\\\(?![^$]*\$\$)', r'\\'),
            
            # Fix spacing issues with text commands
            (r'\\text\s*{([^}]+)}', r'\\text{\1}'),
            
            # Fix angle notation
            (r'\\angle\s*([0-9.-]+)', r'\\angle{\1}'),
            
            # Fix missing spaces in function names
            (r'\\(sin|cos|tan|log|ln)([a-zA-Z])', r'\\\1 \2'),
        ]
        
        for pattern, replacement in error_fixes:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fixes_applied += 1
                result = new_result
        
        return result, fixes_applied
    
    def clean_mathematical_notation(self, text: str) -> str:
        """
        Main function to clean and standardize mathematical notation
        Applies all cleaning operations in sequence
        """
        if not text:
            return text
            
        # Step 1: Convert Unicode to LaTeX
        result, _ = self.unicode_to_latex(text)
        
        # Step 2: Fix inline equations
        result, _ = self.fix_inline_equations(result)
        
        # Step 3: Fix display equations
        result, _ = self.fix_display_equations(result)
        
        # Step 4: Fix common syntax errors
        result, _ = self.fix_common_syntax_errors(result)
        
        # Step 5: Apply common pattern fixes
        for pattern, replacement in self.common_patterns.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def generate_cleanup_report(self, original: str, cleaned: str) -> CleanupReport:
        """
        Generate comprehensive cleanup report
        """
        if not original:
            return CleanupReport(
                original_text="",
                cleaned_text="",
                changes_made=[],
                unicode_conversions=0,
                inline_fixes=0,
                display_fixes=0,
                syntax_errors_fixed=0,
                mixed_notation_detected=False
            )
        
        changes_made = []
        
        # Count Unicode conversions
        _, unicode_count = self.unicode_to_latex(original)
        if unicode_count > 0:
            changes_made.append(f"Converted {unicode_count} Unicode symbols to LaTeX")
        
        # Count inline fixes
        _, inline_count = self.fix_inline_equations(original)
        if inline_count > 0:
            changes_made.append(f"Fixed {inline_count} inline equation issues")
        
        # Count display fixes
        _, display_count = self.fix_display_equations(original)
        if display_count > 0:
            changes_made.append(f"Fixed {display_count} display equation issues")
        
        # Count syntax fixes
        _, syntax_count = self.fix_common_syntax_errors(original)
        if syntax_count > 0:
            changes_made.append(f"Fixed {syntax_count} syntax errors")
        
        # Check for mixed notation
        mixed_notation = self.detect_mixed_notation(original)
        if mixed_notation:
            changes_made.append("Detected and resolved mixed notation")
        
        # Check if text actually changed
        if original != cleaned:
            changes_made.append("Applied pattern-based formatting improvements")
        
        return CleanupReport(
            original_text=original,
            cleaned_text=cleaned,
            changes_made=changes_made,
            unicode_conversions=unicode_count,
            inline_fixes=inline_count,
            display_fixes=display_count,
            syntax_errors_fixed=syntax_count,
            mixed_notation_detected=mixed_notation
        )
    
    def process_question_database(self, questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
        """
        Process entire question database and clean LaTeX notation
        Returns (cleaned_questions, cleanup_reports)
        """
        cleaned_questions = []
        reports = []
        
        for i, question in enumerate(questions):
            cleaned_question = question.copy()
            question_reports = []
            
            # Fields that may contain LaTeX
            latex_fields = [
                'question_text', 'correct_answer', 'feedback_correct', 
                'feedback_incorrect', 'title'
            ]
            
            # Process choices if they exist
            if 'choices' in question and question['choices']:
                cleaned_choices = []
                for choice in question['choices']:
                    if choice:
                        cleaned_choice = self.clean_mathematical_notation(str(choice))
                        cleaned_choices.append(cleaned_choice)
                        
                        # Generate report for this choice
                        if str(choice) != cleaned_choice:
                            report = self.generate_cleanup_report(str(choice), cleaned_choice)
                            question_reports.append(report)
                    else:
                        cleaned_choices.append(choice)
                
                cleaned_question['choices'] = cleaned_choices
            
            # Process other LaTeX fields
            for field in latex_fields:
                if field in question and question[field]:
                    original_text = str(question[field])
                    cleaned_text = self.clean_mathematical_notation(original_text)
                    cleaned_question[field] = cleaned_text
                    
                    # Generate report for this field
                    if original_text != cleaned_text:
                        report = self.generate_cleanup_report(original_text, cleaned_text)
                        question_reports.append(report)
            
            cleaned_questions.append(cleaned_question)
            
            # Combine reports for this question
            if question_reports:
                # Create summary report for the question
                total_changes = sum(len(r.changes_made) for r in question_reports)
                combined_report = CleanupReport(
                    original_text=f"Question {i+1}",
                    cleaned_text=f"Question {i+1} (processed)",
                    changes_made=[f"Total changes across all fields: {total_changes}"],
                    unicode_conversions=sum(r.unicode_conversions for r in question_reports),
                    inline_fixes=sum(r.inline_fixes for r in question_reports),
                    display_fixes=sum(r.display_fixes for r in question_reports),
                    syntax_errors_fixed=sum(r.syntax_errors_fixed for r in question_reports),
                    mixed_notation_detected=any(r.mixed_notation_detected for r in question_reports)
                )
                reports.append(combined_report)
        
        return cleaned_questions, reports


# Convenience functions for external use
def clean_text(text: str) -> str:
    """
    Convenience function to clean a single text string
    """
    processor = LaTeXProcessor()
    return processor.clean_mathematical_notation(text)

def process_question_list(questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
    """
    Convenience function to process a list of questions
    """
    processor = LaTeXProcessor()
    return processor.process_question_database(questions)

def validate_text(text: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate LaTeX syntax in text
    """
    processor = LaTeXProcessor()
    return processor.validate_latex_syntax(text)


# Example usage and testing
if __name__ == "__main__":
    # Example usage with electrical engineering question
    processor = LaTeXProcessor()
    
    # Test with sample text from your database
    sample_text = "Calculate the complex impedance Z for a circuit with R = 50Ω in series with a capacitor C = 10μF at frequency f = 1000 Hz. Use the formula: $$Z = R + j\\omega C$$ where $$\\omega = 2\\pi f$$ and $$j = \\sqrt{-1}$$"
    
    print("Original text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Clean the text
    cleaned = processor.clean_mathematical_notation(sample_text)
    print("Cleaned text:")
    print(cleaned)
    print("\n" + "="*50 + "\n")
    
    # Generate report
    report = processor.generate_cleanup_report(sample_text, cleaned)
    print("Cleanup Report:")
    print(report)
    
    # Validate result
    is_valid, errors = processor.validate_latex_syntax(cleaned)
    print(f"\nValidation: {'✅ Valid' if is_valid else '❌ Errors found'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
, r'$\1$ and $\2$'),
        ]
        
        for pattern, replacement in patterns:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fix_count += 1
                result = new_result
        
        return result, fix_count
    
    def validate_latex_syntax(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validate LaTeX syntax and return errors found
        Returns (is_valid, error_list)
        """
        if not text:
            return True, []
            
        errors = []
        
        # Check for unmatched braces
        brace_count = text.count('{') - text.count('}')
        if brace_count != 0:
            errors.append(f"Unmatched braces: {abs(brace_count)} {'opening' if brace_count > 0 else 'closing'}")
        
        # Check for unmatched parentheses in math mode
        math_sections = re.findall(r'\$\$?[^$]+\$\$?', text)
        for section in math_sections:
            paren_count = section.count('(') - section.count(')')
            if paren_count != 0:
                errors.append(f"Unmatched parentheses in math: {section[:30]}...")
        
        # Check for incomplete LaTeX commands
        incomplete_commands = re.findall(r'\\[a-zA-Z]*(?=[^a-zA-Z]|$)', text)
        for cmd in incomplete_commands:
            if len(cmd) == 1:  # Just a backslash
                errors.append(f"Incomplete LaTeX command: {cmd}")
        
        # Check for unmatched $ delimiters
        dollar_positions = [m.start() for m in re.finditer(r'\$', text)]
        if len(dollar_positions) % 2 != 0:
            errors.append("Unmatched $ delimiters")
        
        return len(errors) == 0, errors
    
    def fix_common_syntax_errors(self, text: str) -> Tuple[str, int]:
        """
        Fix common LaTeX syntax errors
        Returns (fixed_text, error_count_fixed)
        """
        if not text:
            return text, 0
            
        fixes_applied = 0
        result = text
        
        # Fix patterns that commonly cause errors
        error_fixes = [
            # Fix incomplete fractions
            (r'\\frac([^{])', r'\\frac{\1}'),
            
            # Fix missing braces around superscripts/subscripts
            (r'\^([a-zA-Z0-9]{2,})', r'^{\1}'),
            (r'_([a-zA-Z0-9]{2,})', r'_{\1}'),
            
            # Fix double backslashes outside of arrays/matrices
            (r'\\\\(?![^$]*\$\$)', r'\\'),
            
            # Fix spacing issues with text commands
            (r'\\text\s*{([^}]+)}', r'\\text{\1}'),
            
            # Fix angle notation
            (r'\\angle\s*([0-9.-]+)', r'\\angle{\1}'),
            
            # Fix missing spaces in function names
            (r'\\(sin|cos|tan|log|ln)([a-zA-Z])', r'\\\1 \2'),
        ]
        
        for pattern, replacement in error_fixes:
            new_result = re.sub(pattern, replacement, result)
            if new_result != result:
                fixes_applied += 1
                result = new_result
        
        return result, fixes_applied
    
    def clean_mathematical_notation(self, text: str) -> str:
        """
        Main function to clean and standardize mathematical notation
        Applies all cleaning operations in sequence
        """
        if not text:
            return text
            
        # Step 1: Convert Unicode to LaTeX
        result, _ = self.unicode_to_latex(text)
        
        # Step 2: Fix inline equations
        result, _ = self.fix_inline_equations(result)
        
        # Step 3: Fix display equations
        result, _ = self.fix_display_equations(result)
        
        # Step 4: Fix common syntax errors
        result, _ = self.fix_common_syntax_errors(result)
        
        # Step 5: Apply common pattern fixes
        for pattern, replacement in self.common_patterns.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def generate_cleanup_report(self, original: str, cleaned: str) -> CleanupReport:
        """
        Generate comprehensive cleanup report
        """
        if not original:
            return CleanupReport(
                original_text="",
                cleaned_text="",
                changes_made=[],
                unicode_conversions=0,
                inline_fixes=0,
                display_fixes=0,
                syntax_errors_fixed=0,
                mixed_notation_detected=False
            )
        
        changes_made = []
        
        # Count Unicode conversions
        _, unicode_count = self.unicode_to_latex(original)
        if unicode_count > 0:
            changes_made.append(f"Converted {unicode_count} Unicode symbols to LaTeX")
        
        # Count inline fixes
        _, inline_count = self.fix_inline_equations(original)
        if inline_count > 0:
            changes_made.append(f"Fixed {inline_count} inline equation issues")
        
        # Count display fixes
        _, display_count = self.fix_display_equations(original)
        if display_count > 0:
            changes_made.append(f"Fixed {display_count} display equation issues")
        
        # Count syntax fixes
        _, syntax_count = self.fix_common_syntax_errors(original)
        if syntax_count > 0:
            changes_made.append(f"Fixed {syntax_count} syntax errors")
        
        # Check for mixed notation
        mixed_notation = self.detect_mixed_notation(original)
        if mixed_notation:
            changes_made.append("Detected and resolved mixed notation")
        
        # Check if text actually changed
        if original != cleaned:
            changes_made.append("Applied pattern-based formatting improvements")
        
        return CleanupReport(
            original_text=original,
            cleaned_text=cleaned,
            changes_made=changes_made,
            unicode_conversions=unicode_count,
            inline_fixes=inline_count,
            display_fixes=display_count,
            syntax_errors_fixed=syntax_count,
            mixed_notation_detected=mixed_notation
        )
    
    def process_question_database(self, questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
        """
        Process entire question database and clean LaTeX notation
        Returns (cleaned_questions, cleanup_reports)
        """
        cleaned_questions = []
        reports = []
        
        for i, question in enumerate(questions):
            cleaned_question = question.copy()
            question_reports = []
            
            # Fields that may contain LaTeX
            latex_fields = [
                'question_text', 'correct_answer', 'feedback_correct', 
                'feedback_incorrect', 'title'
            ]
            
            # Process choices if they exist
            if 'choices' in question and question['choices']:
                cleaned_choices = []
                for choice in question['choices']:
                    if choice:
                        cleaned_choice = self.clean_mathematical_notation(str(choice))
                        cleaned_choices.append(cleaned_choice)
                        
                        # Generate report for this choice
                        if str(choice) != cleaned_choice:
                            report = self.generate_cleanup_report(str(choice), cleaned_choice)
                            question_reports.append(report)
                    else:
                        cleaned_choices.append(choice)
                
                cleaned_question['choices'] = cleaned_choices
            
            # Process other LaTeX fields
            for field in latex_fields:
                if field in question and question[field]:
                    original_text = str(question[field])
                    cleaned_text = self.clean_mathematical_notation(original_text)
                    cleaned_question[field] = cleaned_text
                    
                    # Generate report for this field
                    if original_text != cleaned_text:
                        report = self.generate_cleanup_report(original_text, cleaned_text)
                        question_reports.append(report)
            
            cleaned_questions.append(cleaned_question)
            
            # Combine reports for this question
            if question_reports:
                # Create summary report for the question
                total_changes = sum(len(r.changes_made) for r in question_reports)
                combined_report = CleanupReport(
                    original_text=f"Question {i+1}",
                    cleaned_text=f"Question {i+1} (processed)",
                    changes_made=[f"Total changes across all fields: {total_changes}"],
                    unicode_conversions=sum(r.unicode_conversions for r in question_reports),
                    inline_fixes=sum(r.inline_fixes for r in question_reports),
                    display_fixes=sum(r.display_fixes for r in question_reports),
                    syntax_errors_fixed=sum(r.syntax_errors_fixed for r in question_reports),
                    mixed_notation_detected=any(r.mixed_notation_detected for r in question_reports)
                )
                reports.append(combined_report)
        
        return cleaned_questions, reports


# Convenience functions for external use
def clean_text(text: str) -> str:
    """
    Convenience function to clean a single text string
    """
    processor = LaTeXProcessor()
    return processor.clean_mathematical_notation(text)

def process_question_list(questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
    """
    Convenience function to process a list of questions
    """
    processor = LaTeXProcessor()
    return processor.process_question_database(questions)

def validate_text(text: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate LaTeX syntax in text
    """
    processor = LaTeXProcessor()
    return processor.validate_latex_syntax(text)


# Example usage and testing
if __name__ == "__main__":
    # Example usage with electrical engineering question
    processor = LaTeXProcessor()
    
    # Test with sample text from your database
    sample_text = "Calculate the complex impedance Z for a circuit with R = 50Ω in series with a capacitor C = 10μF at frequency f = 1000 Hz. Use the formula: $$Z = R + j\\omega C$$ where $$\\omega = 2\\pi f$$ and $$j = \\sqrt{-1}$$"
    
    print("Original text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Clean the text
    cleaned = processor.clean_mathematical_notation(sample_text)
    print("Cleaned text:")
    print(cleaned)
    print("\n" + "="*50 + "\n")
    
    # Generate report
    report = processor.generate_cleanup_report(sample_text, cleaned)
    print("Cleanup Report:")
    print(report)
    
    # Validate result
    is_valid, errors = processor.validate_latex_syntax(cleaned)
    print(f"\nValidation: {'✅ Valid' if is_valid else '❌ Errors found'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
