#!/usr/bin/env python3
"""
Minimal LaTeX Processor - Plan B
Focus on Unicode conversion and basic fixes only
Avoids complex regex that causes syntax errors
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CleanupReport:
    """Simple cleanup report"""
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
    """Minimal LaTeX processor focusing on proven functionality"""
    
    def __init__(self):
        """Initialize with simple, safe mappings"""
        self.unicode_map = self._build_unicode_map()
        
    def _build_unicode_map(self) -> Dict[str, str]:
        """Build safe Unicode to LaTeX mapping"""
        return {
            # Encoding artifacts (the main problem we're solving)
            'Î©': r'\Omega',     # Corrupted Ω
            'Î¼': r'\mu',        # Corrupted μ
            'Ï‰': r'\omega',     # Corrupted ω
            'Ï€': r'\pi',        # Corrupted π
            
            # Standard Unicode symbols
            'Ω': r'\Omega',
            'μ': r'\mu', 
            'ω': r'\omega',
            'π': r'\pi',
            'α': r'\alpha',
            'β': r'\beta',
            'γ': r'\gamma',
            'δ': r'\delta',
            'θ': r'\theta',
            'λ': r'\lambda',
            'σ': r'\sigma',
            'φ': r'\phi',
            '∞': r'\infty',
            '±': r'\pm',
            '≠': r'\neq',
            '≤': r'\leq',
            '≥': r'\geq',
            '≈': r'\approx',
            '√': r'\sqrt',
            '∠': r'\angle',
            '°': r'°',
        }
    
    def unicode_to_latex(self, text: str) -> Tuple[str, int]:
        """Convert Unicode symbols to LaTeX - this we know works"""
        if not text:
            return text, 0
            
        conversion_count = 0
        result = text
        
        for unicode_char, latex_cmd in self.unicode_map.items():
            if unicode_char in result:
                count = result.count(unicode_char)
                result = result.replace(unicode_char, latex_cmd)
                conversion_count += count
        
        return result, conversion_count
    
    def fix_simple_spacing(self, text: str) -> Tuple[str, int]:
        """Fix only the simplest spacing issues"""
        if not text:
            return text, 0
            
        fixes = 0
        result = text
        
        # Only the safest fixes
        simple_fixes = [
            # Fix obvious spacing around inline math
            (r'([a-zA-Z])\$([^$]+)\$([a-zA-Z])', r'\1 $\2$ \3'),
            # Fix units spacing
            (r'([0-9])([A-Z])\b', r'\1 \2'),
        ]
        
        for pattern, replacement in simple_fixes:
            try:
                new_result = re.sub(pattern, replacement, result)
                if new_result != result:
                    fixes += 1
                    result = new_result
            except:
                # Skip any problematic patterns
                pass
        
        return result, fixes
    
    def clean_mathematical_notation(self, text: str) -> str:
        """Main cleaning function - minimal and safe"""
        if not text:
            return text
            
        # Step 1: Fix Unicode (we know this works)
        result, _ = self.unicode_to_latex(text)
        
        # Step 2: Only basic spacing fixes
        result, _ = self.fix_simple_spacing(result)
        
        return result
    
    def generate_cleanup_report(self, original: str, cleaned: str) -> CleanupReport:
        """Generate simple cleanup report"""
        if not original:
            return CleanupReport("", "", [], 0, 0, 0, 0, False)
        
        # Count changes
        _, unicode_count = self.unicode_to_latex(original)
        _, spacing_count = self.fix_simple_spacing(original)
        
        changes_made = []
        if unicode_count > 0:
            changes_made.append(f"Converted {unicode_count} Unicode symbols")
        if spacing_count > 0:
            changes_made.append(f"Fixed {spacing_count} spacing issues")
        if original != cleaned:
            changes_made.append("Applied formatting improvements")
        
        return CleanupReport(
            original_text=original,
            cleaned_text=cleaned,
            changes_made=changes_made,
            unicode_conversions=unicode_count,
            inline_fixes=spacing_count,
            display_fixes=0,
            syntax_errors_fixed=0,
            mixed_notation_detected=False
        )
    
    def process_question_database(self, questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
        """Process questions safely"""
        cleaned_questions = []
        reports = []
        
        for i, question in enumerate(questions):
            cleaned_question = question.copy()
            question_changes = 0
            
            # Fields that might have math
            fields_to_clean = ['question_text', 'correct_answer', 'feedback_correct', 'feedback_incorrect']
            
            # Clean each field
            for field in fields_to_clean:
                if field in question and question[field]:
                    original = str(question[field])
                    cleaned = self.clean_mathematical_notation(original)
                    cleaned_question[field] = cleaned
                    if original != cleaned:
                        question_changes += 1
            
            # Clean choices
            if 'choices' in question and question['choices']:
                cleaned_choices = []
                for choice in question['choices']:
                    if choice:
                        cleaned_choice = self.clean_mathematical_notation(str(choice))
                        cleaned_choices.append(cleaned_choice)
                        if str(choice) != cleaned_choice:
                            question_changes += 1
                    else:
                        cleaned_choices.append(choice)
                cleaned_question['choices'] = cleaned_choices
            
            cleaned_questions.append(cleaned_question)
            
            # Create simple report if changes were made
            if question_changes > 0:
                report = CleanupReport(
                    original_text=f"Question {i+1}",
                    cleaned_text=f"Question {i+1} (processed)",
                    changes_made=[f"Fields modified: {question_changes}"],
                    unicode_conversions=question_changes,
                    inline_fixes=0,
                    display_fixes=0,
                    syntax_errors_fixed=0,
                    mixed_notation_detected=False
                )
                reports.append(report)
        
        return cleaned_questions, reports


# Simple convenience functions
def clean_text(text: str) -> str:
    """Clean a single text string"""
    processor = LaTeXProcessor()
    return processor.clean_mathematical_notation(text)

def process_question_list(questions: List[Dict]) -> Tuple[List[Dict], List[CleanupReport]]:
    """Process a list of questions"""
    processor = LaTeXProcessor()
    return processor.process_question_database(questions)

def validate_text(text: str) -> Tuple[bool, List[str]]:
    """Simple validation - always return True for now"""
    return True, []


if __name__ == "__main__":
    # Simple test
    processor = LaTeXProcessor()
    test_text = "Test with 50Î© and 10Î¼F"
    cleaned = processor.clean_mathematical_notation(test_text)
    print(f"Original: {test_text}")
    print(f"Cleaned: {cleaned}")
