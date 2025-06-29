#!/usr/bin/env python3
"""
Unicode to LaTeX Database Converter
Converts existing question databases from Unicode symbols to LaTeX notation
One-time conversion tool to preserve 369 questions while transitioning to LaTeX-native system
"""

import json
import re
import os
from typing import Dict, List, Any

class UnicodeToLaTeXConverter:
    """Convert Unicode mathematical symbols to proper LaTeX notation"""
    
    def __init__(self):
        """Initialize conversion mappings"""
        self.unicode_to_latex = {
            # Greek letters
            'Ω': r'\Omega',
            'ω': r'\omega', 
            'π': r'\pi',
            'φ': r'\phi',
            'θ': r'\theta',
            'α': r'\alpha',
            'β': r'\beta',
            'γ': r'\gamma',
            'δ': r'\delta',
            'λ': r'\lambda',
            'μ': r'\mu',
            'σ': r'\sigma',
            'τ': r'\tau',
            'ρ': r'\rho',
            'ε': r'\varepsilon',
            'ζ': r'\zeta',
            'η': r'\eta',
            'ι': r'\iota',
            'κ': r'\kappa',
            'ν': r'\nu',
            'ξ': r'\xi',
            'ο': r'o',  # omicron is just 'o'
            'υ': r'\upsilon',
            'χ': r'\chi',
            'ψ': r'\psi',
            
            # Mathematical operators
            '±': r'\pm',
            '∓': r'\mp',
            '×': r'\times',
            '·': r'\cdot',
            '÷': r'\div',
            '≠': r'\neq',
            '≤': r'\leq',
            '≥': r'\geq',
            '≪': r'\ll',
            '≫': r'\gg',
            '≈': r'\approx',
            '≡': r'\equiv',
            '∝': r'\propto',
            '∞': r'\infty',
            '∅': r'\emptyset',
            '∈': r'\in',
            '∉': r'\notin',
            '⊂': r'\subset',
            '⊃': r'\supset',
            '⊆': r'\subseteq',
            '⊇': r'\supseteq',
            '∪': r'\cup',
            '∩': r'\cap',
            '∀': r'\forall',
            '∃': r'\exists',
            '∇': r'\nabla',
            '∂': r'\partial',
            '∫': r'\int',
            '∮': r'\oint',
            '∑': r'\sum',
            '∏': r'\prod',
            '√': r'\sqrt',
            '∠': r'\angle',
            '°': r'^\circ',  # Degree symbol
            
            # Arrows
            '→': r'\rightarrow',
            '←': r'\leftarrow',
            '↔': r'\leftrightarrow',
            '⇒': r'\Rightarrow',
            '⇐': r'\Leftarrow',
            '⇔': r'\Leftrightarrow',
            '↑': r'\uparrow',
            '↓': r'\downarrow',
            
            # Superscripts
            '⁰': r'^0', '¹': r'^1', '²': r'^2', '³': r'^3', '⁴': r'^4',
            '⁵': r'^5', '⁶': r'^6', '⁷': r'^7', '⁸': r'^8', '⁹': r'^9',
            '⁺': r'^+', '⁻': r'^-', 'ⁿ': r'^n',
            
            # Subscripts  
            '₀': r'_0', '₁': r'_1', '₂': r'_2', '₃': r'_3', '₄': r'_4',
            '₅': r'_5', '₆': r'_6', '₇': r'_7', '₈': r'_8', '₉': r'_9',
            '₊': r'_+', '₋': r'_-', 'ₙ': r'_n',
        }
        
        # Common units that should be in text mode
        self.units = [
            'V', 'A', 'W', 'Hz', 'F', 'H', 'C', 'K', 'J', 'N', 'Pa', 'bar',
            'V', 'mV', 'kV', 'MV', 'μV', 'nV', 'pV',
            'A', 'mA', 'μA', 'nA', 'pA', 'kA', 'MA',
            'W', 'mW', 'μW', 'nW', 'kW', 'MW', 'GW',
            'Hz', 'kHz', 'MHz', 'GHz', 'THz',
            'F', 'mF', 'μF', 'nF', 'pF',
            'H', 'mH', 'μH', 'nH',
            's', 'ms', 'μs', 'ns', 'ps',
            'm', 'mm', 'cm', 'μm', 'nm', 'km',
            'g', 'kg', 'mg', 'μg', 'ng',
            'mol', 'mmol', 'μmol', 'nmol',
            'rad', 'mrad', 'μrad'
        ]
    
    def convert_text_to_latex(self, text: str) -> str:
        """Convert Unicode mathematical text to LaTeX with proper math mode"""
        if not text or not isinstance(text, str):
            return text
        
        # Skip if already has LaTeX math mode
        if '$' in text and '\\' in text:
            return text  # Assume already converted
        
        result = text
        
        # Step 1: Convert Unicode symbols to LaTeX commands
        for unicode_char, latex_cmd in self.unicode_to_latex.items():
            if unicode_char in result:
                result = result.replace(unicode_char, latex_cmd)
        
        # Step 2: Handle special patterns and add proper math mode
        result = self._add_math_mode(result)
        
        # Step 3: Handle units properly
        result = self._format_units(result)
        
        # Step 4: Clean up and optimize
        result = self._cleanup_latex(result)
        
        return result
    
    def _add_math_mode(self, text: str) -> str:
        """Add math mode around mathematical expressions"""
        result = text
        
        # Pattern 1: Numbers followed by LaTeX commands (e.g., "10\Omega" → "10 $\Omega$")
        result = re.sub(r'(\d+(?:\.\d+)?)\s*(\\[a-zA-Z]+)', r'\1 $\2$', result)
        
        # Pattern 2: Standalone LaTeX commands (e.g., "\pi" → "$\pi$")
        result = re.sub(r'(?<!\$)\\([a-zA-Z]+)(?!\$)', r'$\\\1$', result)
        
        # Pattern 3: Variables with subscripts/superscripts (e.g., "V_2" → "$V_2$", "I^2" → "$I^2$")
        result = re.sub(r'([a-zA-Z])([_^])([a-zA-Z0-9]+)', r'$\1\2{\3}$', result)
        
        # Pattern 4: Mathematical expressions (e.g., "I = V/R" → "$I = V/R$")
        # Look for patterns like: letter = expression
        result = re.sub(r'([A-Z][a-z]?)\s*=\s*([^,.\s]+(?:\s*[+\-*/]\s*[^,.\s]+)*)', r'$\1 = \2$', result)
        
        # Pattern 5: Fractions (e.g., "V/R" → "$V/R$" if not already in math mode)
        result = re.sub(r'(?<!\$)([A-Z][a-z]?)/([A-Z][a-z]?)(?!\$)', r'$\1/\2$', result)
        
        return result
    
    def _format_units(self, text: str) -> str:
        """Format units properly with \text{} in math mode"""
        result = text
        
        # Pattern: number + unit (e.g., "5V" → "5 $\text{V}$", but handle if already in math mode)
        for unit in self.units:
            # Only convert if not already in math mode
            pattern = r'(\d+(?:\.\d+)?)\s*' + re.escape(unit) + r'(?!\$|\\text)'
            replacement = r'\1 $\\text{' + unit + r'}$'
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def _cleanup_latex(self, text: str) -> str:
        """Clean up LaTeX formatting"""
        result = text
        
        # Merge adjacent math expressions: "$A$ $\cdot$ $B$" → "$A \cdot B$"
        while True:
            new_result = re.sub(r'\$([^$]*)\$\s*\$([^$]*)\$', r'$\1 \2$', result)
            if new_result == result:
                break
            result = new_result
        
        # Clean up spacing in math mode
        result = re.sub(r'\$\s*([^$]*?)\s*\$', lambda m: f'${m.group(1).strip()}$', result)
        
        # Ensure proper spacing around math mode
        result = re.sub(r'([a-zA-Z])\$', r'\1 $', result)  # Space before $
        result = re.sub(r'\$([a-zA-Z])', r'$ \1', result)  # Space after $
        
        # Clean up multiple spaces
        result = re.sub(r'\s{2,}', ' ', result)
        
        # Handle degree symbols specially (often used for temperature and angles)
        # result = re.sub(r'\$\\circ\$C', r'$^\circ$C', result)  # Temperature
        # result = re.sub(r'\$\\circ\$F', r'$^\circ$F', result)  # Temperature
        
        return result.strip()
    
    def convert_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single question from Unicode to LaTeX"""
        converted = question.copy()
        
        # Fields that need conversion
        text_fields = ['question_text', 'correct_answer', 'feedback_correct', 'feedback_incorrect', 'title']
        
        for field in text_fields:
            if field in converted and converted[field]:
                original = converted[field]
                converted[field] = self.convert_text_to_latex(str(original))
        
        # Convert choices if present
        if 'choices' in converted and converted['choices']:
            converted['choices'] = [
                self.convert_text_to_latex(str(choice)) if choice else choice
                for choice in converted['choices']
            ]
        
        return converted
    
    def convert_database(self, input_file: str, output_file: str = None) -> Dict[str, Any]:
        """Convert entire question database from Unicode to LaTeX"""
        
        # Read input file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {input_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in input file: {e}")
        
        # Handle different data structures
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
            metadata = data.get('metadata', {})
        elif isinstance(data, list):
            questions = data
            metadata = {}
        else:
            raise ValueError("Unexpected JSON structure")
        
        # Convert each question
        converted_questions = []
        conversion_stats = {
            'total_questions': len(questions),
            'questions_modified': 0,
            'fields_modified': 0
        }
        
        for i, question in enumerate(questions):
            original_question = json.dumps(question, sort_keys=True)
            converted_question = self.convert_question(question)
            converted_json = json.dumps(converted_question, sort_keys=True)
            
            if original_question != converted_json:
                conversion_stats['questions_modified'] += 1
                
                # Count field changes
                for field in ['question_text', 'correct_answer', 'feedback_correct', 'feedback_incorrect', 'title']:
                    if field in question and field in converted_question:
                        if str(question[field]) != str(converted_question[field]):
                            conversion_stats['fields_modified'] += 1
                
                # Check choices
                if 'choices' in question and 'choices' in converted_question:
                    original_choices = [str(c) for c in question['choices']]
                    converted_choices = [str(c) for c in converted_question['choices']]
                    if original_choices != converted_choices:
                        conversion_stats['fields_modified'] += 1
            
            converted_questions.append(converted_question)
        
        # Update metadata
        updated_metadata = metadata.copy()
        updated_metadata.update({
            'converted_to_latex': True,
            'conversion_date': '2024-12-18',  # Today's date
            'conversion_stats': conversion_stats,
            'format_version': 'Phase Four LaTeX-Native',
            'mathematical_notation': 'LaTeX math mode'
        })
        
        # Create output structure
        output_data = {
            'questions': converted_questions,
            'metadata': updated_metadata
        }
        
        # Save output file
        if output_file is None:
            # Create output filename
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_latex_converted{ext}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Print conversion summary
        print(f"\n🎉 Conversion Complete!")
        print(f"📁 Input:  {input_file}")
        print(f"📁 Output: {output_file}")
        print(f"📊 Stats:")
        print(f"   • Total questions: {conversion_stats['total_questions']}")
        print(f"   • Questions modified: {conversion_stats['questions_modified']}")
        print(f"   • Fields modified: {conversion_stats['fields_modified']}")
        print(f"   • Conversion rate: {conversion_stats['questions_modified']/conversion_stats['total_questions']*100:.1f}%")
        
        return output_data

def main():
    """Command line interface for the converter"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python unicode_to_latex_converter.py <input_file.json> [output_file.json]")
        print("\nExample: python unicode_to_latex_converter.py my_questions.json my_questions_latex.json")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = UnicodeToLaTeXConverter()
    
    try:
        result = converter.convert_database(input_file, output_file)
        print("\n✅ Conversion successful! Your questions are now LaTeX-native.")
        print("🚀 You can now use the LaTeX-native system without Unicode conversion.")
        
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())


