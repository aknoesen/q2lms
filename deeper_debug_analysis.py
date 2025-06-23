#!/usr/bin/env python3
"""
Deeper analysis to verify what's actually stripping the spaces
Let's test step by step to isolate the real culprit
"""

import re

def test_each_processing_step():
    """Test each step in the processing chain individually"""
    
    # Your actual JSON content
    original_text = "Current leads voltage by $90\\,^\\circ$."
    
    print("=== STEP-BY-STEP PROCESSING ANALYSIS ===")
    print(f"Step 0 - Original JSON: '{original_text}'")
    print(f"  - Length: {len(original_text)}")
    print(f"  - Has space after 'by': {'by ' in original_text}")
    print(f"  - Position of 'by ': {original_text.find('by ')}")
    print(f"  - Position of '$': {original_text.find('$')}")
    
    # Step 1: What does render_latex_in_text actually do?
    print(f"\nStep 1 - After render_latex_in_text (simulated):")
    step1_result = original_text  # Assuming it doesn't change anything based on debug
    print(f"  Result: '{step1_result}'")
    print(f"  Changed: {original_text != step1_result}")
    
    # Step 2: What happens during f-string formatting?
    choice_letter = "B"
    step2_result = f"• {choice_letter}: {step1_result}"
    print(f"\nStep 2 - After f-string formatting:")
    print(f"  Result: '{step2_result}'")
    print(f"  Has space after 'by': {'by ' in step2_result}")
    
    # Step 3: What if there are hidden characters?
    print(f"\nStep 3 - Character-by-character analysis around 'by':")
    by_pos = step2_result.find('by')
    if by_pos >= 0:
        for i in range(max(0, by_pos-2), min(len(step2_result), by_pos+8)):
            char = step2_result[i]
            marker = " ←" if i == by_pos + 2 else ""
            print(f"    [{i}] '{char}' (ord: {ord(char)}){marker}")
    
    # Step 4: Test different display methods
    print(f"\nStep 4 - Testing different display methods:")
    test_methods = [
        ("Direct print", lambda x: x),
        ("repr()", lambda x: repr(x)),
        ("HTML escape", lambda x: x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')),
    ]
    
    for method_name, method_func in test_methods:
        result = method_func(step2_result)
        print(f"  {method_name}: {result}")
        if method_name == "repr()":
            print(f"    - Shows exact characters including spaces")

def test_potential_culprits():
    """Test what might be stripping spaces"""
    
    test_text = "Current leads voltage by $90\\,^\\circ$."
    
    print("\n=== TESTING POTENTIAL SPACE-STRIPPING CULPRITS ===")
    
    # Test 1: String methods that might strip spaces
    potential_strippers = [
        ("str.strip()", lambda x: x.strip()),
        ("str.replace(' ', '')", lambda x: x.replace(' ', '')),
        ("re.sub(r'\\s+', ' ', text)", lambda x: re.sub(r'\s+', ' ', x)),
        ("' '.join(text.split())", lambda x: ' '.join(x.split())),
    ]
    
    for name, func in potential_strippers:
        result = func(test_text)
        changed = result != test_text
        print(f"  {name}: {'STRIPS SPACE' if changed else 'preserves space'}")
        if changed:
            print(f"    Before: '{test_text}'")
            print(f"    After:  '{result}'")
    
    # Test 2: Common text processing patterns
    print(f"\n=== COMMON TEXT PROCESSING PATTERNS ===")
    
    processing_patterns = [
        ("Remove multiple spaces", lambda x: re.sub(r'\s+', ' ', x)),
        ("Remove spaces around punctuation", lambda x: re.sub(r'\s*([^\w\s])\s*', r'\1', x)),
        ("Remove spaces before $", lambda x: re.sub(r'\s+\$', '$', x)),
        ("Clean LaTeX spacing", lambda x: re.sub(r'(\w)\s+(\$)', r'\1\2', x)),
    ]
    
    for name, func in processing_patterns:
        result = func(test_text)
        changed = result != test_text
        print(f"  {name}: {'MATCHES ISSUE' if changed and 'by$' in result else 'not the culprit'}")
        if changed:
            print(f"    Result: '{result}'")

def test_browser_rendering_simulation():
    """Simulate what browsers might do to the text"""
    
    test_text = "Current leads voltage by $90\\,^\\circ$."
    
    print(f"\n=== BROWSER RENDERING SIMULATION ===")
    
    # Test HTML whitespace normalization
    print(f"Original: '{test_text}'")
    
    # HTML normally collapses multiple spaces, but not single spaces
    # Test if there are hidden characters
    
    # Check for different types of spaces
    space_types = [
        ('\u0020', 'Regular space'),
        ('\u00A0', 'Non-breaking space'),
        ('\u2009', 'Thin space'),
        ('\u202F', 'Narrow no-break space'),
        ('\t', 'Tab'),
        ('\n', 'Newline'),
    ]
    
    print(f"Space analysis:")
    for space_char, name in space_types:
        if space_char in test_text:
            print(f"  Contains {name}: Yes")
        else:
            print(f"  Contains {name}: No")
    
    # Test what happens with different space types
    test_variants = [
        ("Regular space", "Current leads voltage by $90\\,^\\circ$."),
        ("No space", "Current leads voltage by$90\\,^\\circ$."),
        ("NBSP", "Current leads voltage by\u00A0$90\\,^\\circ$."),
        ("Double space", "Current leads voltage by  $90\\,^\\circ$."),
    ]
    
    print(f"\nVariant comparison:")
    for name, variant in test_variants:
        has_space_after_by = len(variant.split('by')) > 1 and variant.split('by')[1].startswith(' ')
        print(f"  {name}: space after 'by' = {has_space_after_by}")

def check_actual_vs_expected():
    """Compare what we expect vs what might actually be happening"""
    
    print(f"\n=== ACTUAL VS EXPECTED ANALYSIS ===")
    
    # What your JSON actually contains
    json_content = "Current leads voltage by $90\\,^\\circ$."
    
    # What you see in the display (based on your report)
    display_content = "Current leads voltage by$90\\,^\\circ$."  # No space
    
    print(f"JSON content:    '{json_content}'")
    print(f"Display content: '{display_content}'")
    print(f"Difference:      Space after 'by' is missing in display")
    
    # Find the exact difference
    json_chars = list(json_content)
    display_chars = list(display_content)
    
    print(f"\nCharacter-by-character comparison:")
    max_len = max(len(json_chars), len(display_chars))
    
    for i in range(max_len):
        j_char = json_chars[i] if i < len(json_chars) else "EOF"
        d_char = display_chars[i] if i < len(display_chars) else "EOF"
        
        if j_char != d_char:
            print(f"  [{i}] JSON: '{j_char}' vs Display: '{d_char}' ← DIFFERENCE")
        else:
            print(f"  [{i}] Both: '{j_char}'")
        
        if i > 30:  # Limit output
            break

if __name__ == "__main__":
    test_each_processing_step()
    test_potential_culprits()
    test_browser_rendering_simulation()
    check_actual_vs_expected()
