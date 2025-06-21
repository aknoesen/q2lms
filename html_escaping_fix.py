#!/usr/bin/env python3
"""
HTML Escaping Fix for Canvas QTI Compatibility
Replace the problematic HTML entity encoding
"""

import html
import re

def canvas_safe_html_escape(text):
    """
    HTML escape that's compatible with Canvas QTI import
    Avoids problematic HTML entities that Canvas doesn't like
    """
    
    if not text:
        return ""
    
    # Convert to string first
    text = str(text)
    
    # Use Python's html.escape but with safer quote handling
    escaped = html.escape(text, quote=False)  # Don't escape quotes initially
    
    # Manually handle quotes in a Canvas-friendly way
    escaped = escaped.replace('"', '&quot;')
    escaped = escaped.replace("'", "'")  # Keep apostrophes as-is, don't convert to &#x27;
    
    return escaped

def fix_existing_html_entities(text):
    """
    Fix existing problematic HTML entities in text
    """
    
    if not text:
        return ""
    
    # Convert problematic entities back to safe characters
    fixes = {
        '&amp;#x27;': "'",  # Problematic apostrophe entity
        '&#x27;': "'",      # Another form
        '&apos;': "'",      # XML apostrophe entity
        '&rsquo;': "'",     # Right single quotation mark
        '&lsquo;': "'",     # Left single quotation mark
    }
    
    result = str(text)
    for entity, replacement in fixes.items():
        result = result.replace(entity, replacement)
    
    return result

# Updated LaTeX conversion function for the exporter
def convert_latex_for_canvas_fixed(text):
    """
    Fixed LaTeX conversion that's Canvas-compatible
    """
    
    if not text:
        return ""
    
    latex_expressions = []
    placeholder_template = "LATEX_PLACEHOLDER_{}"
    
    def replace_latex_match(match):
        expr = match.group(0)
        
        # Canvas conversion logic
        if expr.startswith('$$') and expr.endswith('$$'):
            canvas_expr = expr  # Keep block math as-is
        elif expr.startswith('$') and expr.endswith('$'):
            inner_content = expr[1:-1]
            canvas_expr = f'\\({inner_content}\\)'  # Convert inline math
        else:
            canvas_expr = expr
        
        placeholder = placeholder_template.format(len(latex_expressions))
        latex_expressions.append(canvas_expr)
        return placeholder
    
    # Process LaTeX expressions
    pattern = r'\$\$[^$]+\$\$|\$[^$]+\$'
    text_with_placeholders = re.sub(pattern, replace_latex_match, str(text))
    
    # Use Canvas-safe HTML escaping
    escaped_text = canvas_safe_html_escape(text_with_placeholders)
    
    # Restore LaTeX expressions
    for i, canvas_expr in enumerate(latex_expressions):
        placeholder = placeholder_template.format(i)
        escaped_text = escaped_text.replace(placeholder, canvas_expr)
    
    return f'<div class="question-text">{escaped_text}</div>'

# Test the fix
def test_html_escaping_fix():
    """
    Test that the fix resolves the Canvas compatibility issue
    """
    
    print("🧪 TESTING HTML ESCAPING FIX")
    print("=" * 50)
    
    # Test cases that were causing Canvas issues
    test_cases = [
        "Ohm's law",
        "What's the answer?",
        'Use "quotes" and \'apostrophes\'',
        "For a resistor with $R = 100\\,\\Omega$ and current $I = 2\\,\\text{A}$, calculate using Ohm's law $V = IR$.",
    ]
    
    print("📋 BEFORE (problematic):")
    for i, test in enumerate(test_cases):
        old_result = html.escape(test)
        print(f"   {i+1}. {old_result}")
    
    print("\n📋 AFTER (Canvas-safe):")
    for i, test in enumerate(test_cases):
        new_result = canvas_safe_html_escape(test)
        print(f"   {i+1}. {new_result}")
    
    print("\n📋 LATEX CONVERSION TEST:")
    latex_test = "For a resistor with $R = 100\\,\\Omega$ and current $I = 2\\,\\text{A}$, calculate using Ohm's law $V = IR$."
    
    print(f"Original: {latex_test}")
    print(f"Fixed:    {convert_latex_for_canvas_fixed(latex_test)}")
    
    # Check for problematic entities
    result = convert_latex_for_canvas_fixed(latex_test)
    if '&#x27;' in result or '&amp;#x27;' in result:
        print("❌ Still contains problematic entities!")
    else:
        print("✅ No problematic entities found!")

if __name__ == "__main__":
    test_html_escaping_fix()
