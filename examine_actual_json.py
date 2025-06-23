#!/usr/bin/env python3
"""
Examine what's actually in the CornerCases.json file
"""

import json

def examine_corner_cases():
    """Look at the actual content of CornerCases.json"""
    
    try:
        with open('CornerCases.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        try:
            with open('C:\\Users\\aknoesen\\Downloads\\CornerCases.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("❌ CornerCases.json not found")
            return
    
    print("=== EXAMINING ACTUAL JSON CONTENT ===")
    
    # Look for the specific problem case
    problem_cases = []
    
    for i, question in enumerate(data.get('questions', [])):
        question_id = question.get('id', f'question_{i}')
        
        # Check all text fields for "by" followed by LaTeX
        text_fields = ['question_text', 'title'] + [f'choice_{c}' for c in 'abcd']
        
        for field in text_fields:
            if field in question:
                text = question[field]
                if isinstance(text, str) and 'by' in text and '$' in text:
                    problem_cases.append({
                        'question_id': question_id,
                        'field': field,
                        'text': text
                    })
        
        # Check choices array
        if 'choices' in question:
            for j, choice in enumerate(question['choices']):
                if isinstance(choice, str) and 'by' in choice and '$' in choice:
                    problem_cases.append({
                        'question_id': question_id,
                        'field': f'choices[{j}]',
                        'text': choice
                    })
    
    print(f"Found {len(problem_cases)} cases with 'by' and '$':")
    
    for case in problem_cases:
        print(f"\n📍 {case['question_id']} → {case['field']}")
        text = case['text']
        print(f"📝 Text: \"{text}\"")
        
        # Analyze character by character around the problematic area
        if 'by$' in text:
            pos = text.find('by$')
            start = max(0, pos - 5)
            end = min(len(text), pos + 15)
            segment = text[start:end]
            
            print(f"🔍 Problem segment: \"{segment}\"")
            print("🔤 Character analysis:")
            for i, char in enumerate(segment):
                abs_pos = start + i
                marker = " ←" if abs_pos == pos + 2 else ""  # Mark the $ character
                print(f"   [{abs_pos}] '{char}' (ord: {ord(char)}){marker}")
        
        # Check for LaTeX patterns
        import re
        latex_matches = re.findall(r'\$[^$]*\$', text)
        print(f"🔬 LaTeX patterns found: {latex_matches}")
        
        print("-" * 50)

def test_actual_problematic_text():
    """Test with the actual problematic text from JSON"""
    
    # Let's find the exact text causing issues
    try:
        with open('CornerCases.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        try:
            with open('C:\\Users\\aknoesen\\Downloads\\CornerCases.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("❌ CornerCases.json not found")
            return
    
    # Find the first question with the pattern
    for question in data.get('questions', []):
        for field in ['question_text'] + ['choices']:
            if field == 'choices' and 'choices' in question:
                for choice in question['choices']:
                    if isinstance(choice, str) and 'by' in choice and '$90' in choice:
                        print(f"\n🎯 FOUND ACTUAL PROBLEMATIC TEXT:")
                        print(f"Raw: {repr(choice)}")
                        print(f"Display: \"{choice}\"")
                        
                        # Test our current regex against this actual text
                        import re
                        latex_pattern = r'(\$\$.+?\$\$|\$.+?\$)'
                        matches = re.findall(latex_pattern, choice)
                        print(f"Current regex matches: {matches}")
                        
                        # Test enhanced patterns
                        enhanced_patterns = [
                            r'(\$\$.+?\$\$|\$.+?\$)',  # Current
                            r'(\$[^$]*\$)',           # Alternative 1
                            r'(\$[^$\s]*)',           # Alternative 2 (no closing $)
                            r'(\$\d+\\[^$]*\$)',      # LaTeX commands
                        ]
                        
                        for i, pattern in enumerate(enhanced_patterns):
                            matches = re.findall(pattern, choice)
                            print(f"Pattern {i+1} matches: {matches}")
                        
                        return choice
    
    print("❌ No problematic text found")
    return None

if __name__ == "__main__":
    examine_corner_cases()
    actual_text = test_actual_problematic_text()
