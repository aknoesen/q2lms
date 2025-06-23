#!/usr/bin/env python3
"""
Since auto_latex isn't actually used, let's trace where spaces are really being lost
"""

def create_test_scenario():
    """Create a test to trace exactly where spaces are lost"""
    
    test_content = '''
=== TESTING SPACE LOSS SCENARIO ===

Based on our findings:
1. auto_latex option exists but is NEVER USED in processing
2. Yet spaces are being stripped from "by $90" to "by$90"
3. This means the stripping happens elsewhere

Let's test step by step:

STEP 1: Check if it happens during JSON parsing
- Raw JSON: "Current leads voltage by $90\\,^\\circ$."
- After json.loads(): Should still have the space

STEP 2: Check if it happens during DataFrame creation  
- DataFrame stores the original text
- Should preserve spaces

STEP 3: Check if it happens during render_latex_in_text()
- Input: "Current leads voltage by $90\\,^\\circ$."
- Output: Should preserve spaces (we tested this already)

STEP 4: Check if it happens during display
- After f-string formatting
- During st.markdown() rendering

STEP 5: Check browser-side processing
- CSS that might affect spacing
- JavaScript that processes text

CRITICAL INSIGHT:
If auto_latex is never used, then the space stripping is happening:
A) In your current utils.py render_latex_in_text function
B) In some other text processing function
C) In the browser/CSS
D) In a different part of the display chain

Let's test this systematically.
    '''
    
    print(test_content)

def test_hypothesis_simple_text_cleaning():
    """Test if there's simple text cleaning happening"""
    
    print("=== TESTING SIMPLE TEXT CLEANING HYPOTHESIS ===")
    
    # Test cases
    test_texts = [
        "Current leads voltage by $90\\,^\\circ$.",  # Your actual case
        "by $90",                                    # Simplified case
        "word $symbol",                             # Generic case
        "before $ after",                           # Space test
    ]
    
    print("Testing various text patterns:")
    
    for text in test_texts:
        print(f"\nInput: '{text}'")
        
        # Test common cleaning operations
        cleaned_variants = {
            "strip()": text.strip(),
            "replace(' $', '$')": text.replace(' $', '$'),
            "no double spaces": ' '.join(text.split()),
            "regex \\s+\\$": text,  # We'd need to import re
        }
        
        for method, result in cleaned_variants.items():
            if result != text:
                print(f"  {method}: '{result}' ← STRIPS SPACE!")
            else:
                print(f"  {method}: PRESERVES SPACE")

def check_if_your_utils_function_strips_spaces():
    """Check if your current utils.py function is the culprit"""
    
    print("\n=== CHECKING YOUR CURRENT utils.py FUNCTION ===")
    
    print("""
Your current utils.py contains these suspicious lines:
- Line 38: text = re.sub(r'(\\w)\\s+(\\$)', lambda m: m.group(1) + nbsp + m.group(2), text)
- Line 41: text = re.sub(r'(\\$)\\s+(\\w)', lambda m: m.group(1) + nbsp + m.group(2), text)

WAIT A MINUTE! 

Look at line 38: r'(\\w)\\s+(\\$)'
This pattern matches: WORD + SPACES + $

Your pattern is: "by $90"
- 'y' matches \\w (word character)  
- ' ' matches \\s+ (spaces)
- '$' matches \\$ (dollar sign)

So this regex SHOULD match and replace the space with NBSP!

BUT - the pattern only matches the OPENING $ sign, not the full LaTeX expression.
The pattern r'(\\w)\\s+(\\$)' matches "by $" but not "$90\\,^\\circ$"

The issue might be that your regex is TOO SPECIFIC.
    """)

def analyze_the_real_problem():
    """Analyze what's really happening"""
    
    print("\n=== ANALYZING THE REAL PROBLEM ===")
    
    print("""
BREAKTHROUGH ANALYSIS:

Your debug output showed:
- RAW CHOICE TEXT: 'Current leads voltage by $90\\,^\\circ$.'
- SPACING DEBUG: Input: 'Current leads voltage by $90\\,^\\circ$.'  
- SPACING DEBUG: Output: 'Current leads voltage by $90\\,^\\circ$.'

This means your render_latex_in_text() function is NOT CHANGING the text at all!

But you're seeing "by$90" in the display.

CONCLUSION: The issue is NOT in your LaTeX processing.
The issue is either:

1. The text in your JSON is ALREADY missing the space
2. Some other function is stripping the space AFTER render_latex_in_text()
3. The browser/CSS is removing the space during display
4. There's a display bug where spaces aren't visible but are there

NEXT STEPS:
1. Check the EXACT character codes in your JSON
2. Check if st.markdown() strips spaces
3. Check if there's CSS affecting space display
4. Test with a simple HTML display to isolate the issue
    """)

def create_simple_test_script():
    """Create a simple test to isolate the issue"""
    
    test_script = '''
# SIMPLE TEST SCRIPT - save as test_space_issue.py

def test_space_preservation():
    """Test if spaces are preserved through various operations"""
    
    # Your exact text from JSON
    original = "Current leads voltage by $90\\\\,^\\\\circ$."
    
    print("=== SPACE PRESERVATION TEST ===")
    print(f"Original: '{original}'")
    print(f"Has space after 'by': {'by ' in original}")
    print(f"Position of 'by ': {original.find('by ')}")
    print(f"Position of '$': {original.find('$')}")
    
    # Test character by character around 'by'
    by_pos = original.find('by')
    if by_pos >= 0:
        print(f"\\nCharacter analysis around 'by':")
        for i in range(by_pos, min(len(original), by_pos + 6)):
            char = original[i]
            print(f"  [{i}] '{char}' (ord: {ord(char)})")
    
    # Test simple operations
    after_strip = original.strip()
    after_format = f"• B: {original}"
    
    print(f"\\nAfter strip(): '{after_strip}'")
    print(f"After f-string: '{after_format}'")
    print(f"Still has 'by ' after f-string: {'by ' in after_format}")

if __name__ == "__main__":
    test_space_preservation()
    '''
    
    print("\n=== SIMPLE TEST SCRIPT ===")
    print("Save this as test_space_issue.py and run it:")
    print(test_script)

if __name__ == "__main__":
    create_test_scenario()
    test_hypothesis_simple_text_cleaning()
    check_if_your_utils_function_strips_spaces()
    analyze_the_real_problem()
    create_simple_test_script()
