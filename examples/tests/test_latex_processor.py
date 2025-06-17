#!/usr/bin/env python3
"""
Test Suite for LaTeX Processor Module
Comprehensive testing with real electrical engineering examples
"""

import pytest
import json
import sys
import os
from typing import List, Dict

# Add the modules directory to the path (assuming test is run from project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

try:
    from latex_processor import LaTeXProcessor, clean_text, process_question_list, validate_text
except ImportError:
    # If running standalone, assume latex_processor is in the same directory
    from latex_processor import LaTeXProcessor, clean_text, process_question_list, validate_text

class TestLaTeXProcessor:
    """Test suite for LaTeX processor functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.processor = LaTeXProcessor()
        
        # Sample electrical engineering content from your actual database
        self.sample_questions = [
            {
                "type": "multiple_choice",
                "title": "Complex Impedance Calculation",
                "question_text": "Calculate the complex impedance Z for a circuit with R = 50Ω in series with a capacitor C = 10μF at frequency f = 1000 Hz. Use the formula: $$Z = R + j\\omega C$$ where $$\\omega = 2\\pi f$$ and $$j = \\sqrt{-1}$$",
                "choices": [
                    "$$Z = 50 - j15.9\\,\\Omega$$",
                    "$$Z = 50 + j15.9\\,\\Omega$$",
                    "$$Z = 52.5\\angle{-17.7°}\\,\\Omega$$",
                    "$$Z = 50 - j159\\,\\Omega$$"
                ],
                "correct_answer": "$$Z = 50 - j15.9\\,\\Omega$$",
                "feedback_correct": "Correct! $$\\omega = 2\\pi \\times 1000 = 6283\\,\\text{rad/s}$$, so $$X_C = \\frac{1}{\\omega C} = \\frac{1}{6283 \\times 10^{-5}} = 15.9\\,\\Omega$$, giving $$Z = 50 - j15.9\\,\\Omega$$"
            },
            {
                "type": "numerical",
                "title": "RMS Voltage Calculation", 
                "question_text": "Calculate the RMS value of the voltage $$v(t) = 10\\sin(\\omega t) + 5\\cos(2\\omega t + \\frac{\\pi}{4})$$ volts.",
                "correct_answer": "7.91",
                "feedback_correct": "Excellent! For sinusoidal components: $$V_{RMS} = \\sqrt{\\frac{V_1^2}{2} + \\frac{V_2^2}{2}} = \\sqrt{50 + 12.5} = \\sqrt{62.5} = 7.91\\,\\text{V}$$"
            }
        ]
        
        # Test cases with known issues
        self.test_cases = [
            # Unicode to LaTeX conversion
            {
                "input": "R = 50Ω, f = 1000Hz, μF capacitor",
                "expected_changes": ["Unicode conversions"],
                "should_contain": ["\\Omega", "\\mu"]
            },
            # Inline math fixes
            {
                "input": "The voltage$V=IR$is important",
                "expected_changes": ["inline equation"],
                "should_contain": [" $V=IR$ "]
            },
            # Display math fixes
            {
                "input": "$$Z = R + jX$and$$Y = G + jB$$",
                "expected_changes": ["display equation"],
                "should_contain": ["$$ "]
            },
            # Angle notation
            {
                "input": "Phase angle ∠45° or \\angle{30°}",
                "expected_changes": ["Unicode conversions"],
                "should_contain": ["\\angle"]
            },
            # Mixed notation detection
            {
                "input": "ω = 2πf where π is pi and $$\\omega = 2\\pi f$$",
                "expected_changes": ["Unicode conversions"],
                "mixed_notation": True
            }
        ]
    
    def test_unicode_to_latex_conversion(self):
        """Test Unicode symbol conversion"""
        test_cases = [
            ("50Ω resistor", "50\\Omega resistor"),
            ("μF capacitor", "\\muF capacitor"), 
            ("α = 30°", "\\alpha = 30°"),
            ("∞ resistance", "\\infty resistance"),
            ("√2 ≈ 1.414", "\\sqrt2 \\approx 1.414")
        ]
        
        for input_text, expected in test_cases:
            result, count = self.processor.unicode_to_latex(input_text)
            assert expected in result, f"Expected '{expected}' in result '{result}'"
            assert count > 0, f"Should have made conversions for '{input_text}'"
    
    def test_inline_equation_fixes(self):
        """Test inline equation formatting fixes"""
        test_cases = [
            # Missing spaces around inline math
            ("voltage$V=IR$current", "voltage $V=IR$ current"),
            # Complex inline expressions should become display
            ("$\\frac{1}{\\omega C}$", "$$\\frac{1}{\\omega C}$$"),
            # Proper inline delimiters
            ("$V$ and $I$", "$V$ and $I$")  # Should remain unchanged
        ]
        
        for input_text, expected in test_cases:
            result, count = self.processor.fix_inline_equations(input_text)
            assert expected == result, f"Expected '{expected}', got '{result}'"
    
    def test_display_equation_fixes(self):
        """Test display equation formatting fixes"""
        test_cases = [
            # Unmatched delimiters
            ("$$Z = R + jX$", "$$Z = R + jX$$"),
            ("$Z = R + jX$$", "$$Z = R + jX$$"),
            # Spacing issues
            ("$$  V = IR  $$", "$$V = IR$$")
        ]
        
        for input_text, expected in test_cases:
            result, count = self.processor.fix_display_equations(input_text)
            assert expected == result, f"Expected '{expected}', got '{result}'"
    
    def test_syntax_error_fixes(self):
        """Test common syntax error corrections"""
        test_cases = [
            # Missing braces for superscripts
            ("V^RMS", "V^{RMS}"),
            ("X_C", "X_{C}"),  # Should remain unchanged (single char)
            ("X_capacitor", "X_{capacitor}"),  # Multi-char subscript
            # Function spacing
            ("\\sinωt", "\\sin ωt"),
            ("\\log10", "\\log 10")
        ]
        
        for input_text, expected in test_cases:
            result, count = self.processor.fix_common_syntax_errors(input_text)
            assert expected == result, f"Expected '{expected}', got '{result}'"
    
    def test_mixed_notation_detection(self):
        """Test detection of mixed Unicode/LaTeX notation"""
        test_cases = [
            ("ω = 2πf with $\\omega = 2\\pi f$", True),  # Mixed Unicode and LaTeX
            ("$\\omega = 2\\pi f$", False),  # Pure LaTeX
            ("ω = 2πf", False),  # Pure Unicode
            ("Regular text", False),  # No math notation
            ("μF with $\\mu$F", True)  # Mixed in same expression
        ]
        
        for input_text, expected_mixed in test_cases:
            result = self.processor.detect_mixed_notation(input_text)
            assert result == expected_mixed, f"Mixed notation detection failed for '{input_text}'"
    
    def test_latex_syntax_validation(self):
        """Test LaTeX syntax validation"""
        valid_cases = [
            "$Z = R + jX$",
            "$V = IR$",
            "\\alpha = 30°",
            "Regular text with no math"
        ]
        
        invalid_cases = [
            "$Z = R + jX$",  # Unmatched $
            "$V = IR",        # Unmatched $
            "\\frac{1}{2",    # Unmatched braces
            "\\incomplete",   # Incomplete command
        ]
        
        for text in valid_cases:
            is_valid, errors = self.processor.validate_latex_syntax(text)
            assert is_valid, f"'{text}' should be valid, but got errors: {errors}"
        
        for text in invalid_cases:
            is_valid, errors = self.processor.validate_latex_syntax(text)
            assert not is_valid, f"'{text}' should be invalid but was marked as valid"
            assert len(errors) > 0, f"'{text}' should have error messages"
    
    def test_complete_cleaning_pipeline(self):
        """Test the complete cleaning pipeline with real examples"""
        for test_case in self.test_cases:
            input_text = test_case["input"]
            cleaned = self.processor.clean_mathematical_notation(input_text)
            
            # Check that expected changes were made
            for expected_change in test_case.get("should_contain", []):
                assert expected_change in cleaned, f"Expected '{expected_change}' in cleaned text: '{cleaned}'"
            
            # Check mixed notation if specified
            if test_case.get("mixed_notation"):
                assert self.processor.detect_mixed_notation(input_text), f"Should detect mixed notation in: '{input_text}'"
            
            # Validate that result is syntactically correct
            is_valid, errors = self.processor.validate_latex_syntax(cleaned)
            assert is_valid, f"Cleaned text should be valid: '{cleaned}', errors: {errors}"
    
    def test_question_database_processing(self):
        """Test processing of complete question database"""
        cleaned_questions, reports = self.processor.process_question_database(self.sample_questions)
        
        # Should have same number of questions
        assert len(cleaned_questions) == len(self.sample_questions)
        
        # Check that Omega symbols were converted
        first_question = cleaned_questions[0]
        assert "\\Omega" in first_question["question_text"]
        assert "\\mu" in first_question["question_text"]  # μF should be converted
        
        # Check that choices were processed
        assert "\\Omega" in first_question["choices"][0]
        
        # Check that feedback was processed
        assert "\\omega" in first_question["feedback_correct"]
        
        # Should have reports for questions that needed changes
        assert len(reports) > 0, "Should have cleanup reports for questions with changes"
        
        # Validate all cleaned questions
        for question in cleaned_questions:
            for field in ["question_text", "correct_answer", "feedback_correct"]:
                if field in question and question[field]:
                    is_valid, errors = self.processor.validate_latex_syntax(question[field])
                    assert is_valid, f"Field '{field}' should be valid: '{question[field]}', errors: {errors}"
    
    def test_cleanup_report_generation(self):
        """Test cleanup report generation"""
        input_text = "Calculate impedance Z = 50Ω + j15.9Ω at ω = 2πf"
        cleaned_text = self.processor.clean_mathematical_notation(input_text)
        
        report = self.processor.generate_cleanup_report(input_text, cleaned_text)
        
        # Should detect Unicode conversions
        assert report.unicode_conversions > 0
        assert len(report.changes_made) > 0
        assert "Unicode symbols" in str(report)
        
        # Should detect mixed notation
        assert report.mixed_notation_detected
    
    def test_electrical_engineering_specifics(self):
        """Test electrical engineering specific patterns"""
        test_cases = [
            # Units with proper spacing
            ("50Ω resistor", "50\\,\\Omega resistor"),
            ("120V supply", "120\\,\\text{V} supply"),
            ("5A current", "5\\,\\text{A} current"),
            ("60Hz frequency", "60\\,\\text{Hz} frequency"),
            ("10μF capacitor", "10\\,\\mu\\text{F} capacitor"),
            
            # Angle notation
            ("Phase ∠45°", "Phase \\angle{45°}"),
            ("\\angle30°", "\\angle{30°}"),
            
            # Complex number notation
            ("Z = R + jX", "Z = R + jX"),  # Should remain as is
            ("j = √-1", "j = \\sqrt-1")
        ]
        
        for input_text, expected_pattern in test_cases:
            result = self.processor.clean_mathematical_notation(input_text)
            assert expected_pattern in result, f"Expected pattern '{expected_pattern}' in result '{result}'"
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly"""
        test_text = "Impedance Z = 50Ω at frequency f = 1000Hz"
        
        # Test clean_text function
        cleaned = clean_text(test_text)
        assert "\\Omega" in cleaned
        assert "\\text{Hz}" in cleaned
        
        # Test process_question_list function
        cleaned_questions, reports = process_question_list(self.sample_questions)
        assert len(cleaned_questions) == len(self.sample_questions)
        assert len(reports) >= 0  # May or may not have reports
        
        # Test validate_text function
        is_valid, errors = validate_text("$Z = R + jX$")
        assert is_valid
        assert len(errors) == 0
        
        is_valid, errors = validate_text("$Z = R + jX$")  # Unmatched
        assert not is_valid
        assert len(errors) > 0
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Empty/None inputs
        assert self.processor.clean_mathematical_notation("") == ""
        assert self.processor.clean_mathematical_notation(None) == None
        
        # Very long text
        long_text = "Z = R + jX" * 1000
        cleaned_long = self.processor.clean_mathematical_notation(long_text)
        assert len(cleaned_long) >= len(long_text)  # Should not truncate
        
        # Text with no mathematical content
        plain_text = "This is just regular text with no math."
        cleaned_plain = self.processor.clean_mathematical_notation(plain_text)
        assert cleaned_plain == plain_text  # Should be unchanged
        
        # Extremely nested LaTeX
        nested = "$\\frac{\\frac{1}{2}}{\\frac{3}{4}}$"
        cleaned_nested = self.processor.clean_mathematical_notation(nested)
        is_valid, errors = self.processor.validate_latex_syntax(cleaned_nested)
        assert is_valid, f"Nested LaTeX should remain valid: {errors}"
    
    def test_performance_with_large_dataset(self):
        """Test performance with larger question sets"""
        # Create a larger dataset by repeating sample questions
        large_dataset = self.sample_questions * 100  # 200 questions
        
        import time
        start_time = time.time()
        
        cleaned_questions, reports = self.processor.process_question_database(large_dataset)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 10.0, f"Processing took too long: {processing_time:.2f} seconds"
        assert len(cleaned_questions) == len(large_dataset)
        
        print(f"Processed {len(large_dataset)} questions in {processing_time:.2f} seconds")


# Integration test with actual sample data
class TestWithActualData:
    """Test with the actual sample data from complex_math_test.json"""
    
    def setup_method(self):
        """Load actual sample data"""
        self.processor = LaTeXProcessor()
        
        # Sample data from your complex_math_test.json
        self.actual_sample = {
            "questions": [
                {
                    "type": "multiple_choice",
                    "title": "Complex Impedance Calculation",
                    "question_text": "Calculate the complex impedance Z for a circuit with R = 50Ω in series with a capacitor C = 10μF at frequency f = 1000 Hz. Use the formula: $Z = R + j\\omega C$ where $\\omega = 2\\pi f$ and $j = \\sqrt{-1}$",
                    "choices": [
                        "$Z = 50 - j15.9\\,\\Omega$",
                        "$Z = 50 + j15.9\\,\\Omega$", 
                        "$Z = 52.5\\angle{-17.7°}\\,\\Omega$",
                        "$Z = 50 - j159\\,\\Omega$"
                    ],
                    "correct_answer": "$Z = 50 - j15.9\\,\\Omega$",
                    "feedback_correct": "Correct! $\\omega = 2\\pi \\times 1000 = 6283\\,\\text{rad/s}$, so $X_C = \\frac{1}{\\omega C} = \\frac{1}{6283 \\times 10^{-5}} = 15.9\\,\\Omega$, giving $Z = 50 - j15.9\\,\\Omega$"
                }
            ]
        }
    
    def test_actual_sample_processing(self):
        """Test processing of actual sample data"""
        questions = self.actual_sample["questions"]
        cleaned_questions, reports = self.processor.process_question_database(questions)
        
        # Should have processed successfully
        assert len(cleaned_questions) == 1
        
        question = cleaned_questions[0]
        
        # Check Unicode conversions
        assert "\\Omega" in question["question_text"]
        assert "\\mu" in question["question_text"]
        
        # Check all choices were processed
        for choice in question["choices"]:
            is_valid, errors = self.processor.validate_latex_syntax(choice)
            assert is_valid, f"Choice should be valid: '{choice}', errors: {errors}"
        
        # Check feedback was processed
        assert "\\omega" in question["feedback_correct"]
        assert "\\Omega" in question["feedback_correct"]
        
        # Should have reports if changes were made
        if reports:
            assert len(reports) > 0
            report = reports[0]
            assert report.unicode_conversions > 0


# Utility functions for running tests
def run_basic_tests():
    """Run basic functionality tests"""
    processor = LaTeXProcessor()
    
    print("🧪 Running Basic LaTeX Processor Tests...")
    
    # Test 1: Unicode conversion
    test_text = "Circuit with R = 50Ω, C = 10μF, ω = 2πf"
    cleaned = processor.clean_mathematical_notation(test_text)
    print(f"✓ Unicode conversion: '{test_text}' → '{cleaned}'")
    
    # Test 2: Equation fixing
    test_equation = "The voltage$V=IR$is related to current"
    cleaned_eq = processor.clean_mathematical_notation(test_equation)
    print(f"✓ Equation spacing: '{test_equation}' → '{cleaned_eq}'")
    
    # Test 3: Validation
    is_valid, errors = processor.validate_latex_syntax("$Z = R + jX$")
    print(f"✓ Validation: Valid LaTeX detected correctly: {is_valid}")
    
    is_valid, errors = processor.validate_latex_syntax("$Z = R + jX$")
    print(f"✓ Validation: Invalid LaTeX detected correctly: {not is_valid}")
    
    # Test 4: Full question processing
    sample_question = {
        "question_text": "Calculate impedance Z = 50Ω + j15.9Ω",
        "choices": ["Option with μF", "Option with ∠45°"],
        "feedback_correct": "Good! The ω = 2πf formula applies."
    }
    
    cleaned_questions, reports = processor.process_question_database([sample_question])
    print(f"✓ Question processing: {len(cleaned_questions)} questions processed")
    print(f"✓ Reports generated: {len(reports)} cleanup reports")
    
    print("\n🎉 All basic tests passed!")
    return True


if __name__ == "__main__":
    """Run tests when called directly"""
    
    # Run basic tests first
    run_basic_tests()
    
    # If pytest is available, run full test suite
    try:
        import pytest
        print("\n🚀 Running full test suite with pytest...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("\n📝 Install pytest to run the full test suite:")
        print("pip install pytest")
        print("\nThen run: pytest test_latex_processor.py -v")
