#!/usr/bin/env python3
"""
Find the exact function doing text.replace(' $', '$')
"""

import os
import re

def search_for_replace_space_dollar():
    """Search all files for .replace(' $', '$') patterns"""
    
    print("=== SEARCHING FOR .replace(' $', '$') PATTERNS ===")
    
    # Search patterns that would strip space before $
    patterns_to_find = [
        r'\.replace\([\'\"]\s+\$[\'\"]\s*,\s*[\'\"]\$[\'\"]\)',     # .replace(' $', '$')
        r'\.replace\([\'\"]\s\$[\'\"]\s*,\s*[\'\"]\$[\'\"]\)',      # .replace(' $', '$') 
        r'\.replace\([\'\"]\s+\\\$[\'\"]\s*,\s*[\'\"]\\\$[\'\"]\)', # .replace(' \$', '\$')
    ]
    
    # Check all Python files
    if os.path.exists("modules"):
        for root, dirs, files in os.walk("modules"):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    search_file_for_patterns(filepath, patterns_to_find)
    
    # Check main directory
    for file in os.listdir('.'):
        if file.endswith('.py'):
            search_file_for_patterns(file, patterns_to_find)

def search_file_for_patterns(filepath, patterns):
    """Search a specific file for the patterns"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return
    
    found_patterns = []
    
    for i, line in enumerate(lines, 1):
        # Look for any .replace with $ 
        if '.replace(' in line and '$' in line:
            found_patterns.append((i, line.strip()))
        
        # Also check for the specific patterns
        for pattern in patterns:
            if re.search(pattern, line):
                found_patterns.append((i, f"EXACT MATCH: {line.strip()}"))
    
    if found_patterns:
        print(f"\n🚨 FOUND .replace with $ in {filepath}:")
        for line_num, line_content in found_patterns:
            print(f"  Line {line_num}: {line_content}")
            
            # Show context for suspicious lines
            if 'EXACT MATCH' in line_content or (' $' in line_content and ', $' in line_content):
                print(f"    ⚠️  THIS IS LIKELY THE CULPRIT!")

def search_for_text_cleaning_functions():
    """Search for any text cleaning functions that might do this"""
    
    print(f"\n=== SEARCHING FOR TEXT CLEANING FUNCTIONS ===")
    
    # Common function names that might clean text
    cleaning_function_patterns = [
        r'def\s+clean_',
        r'def\s+normalize_',
        r'def\s+process_',
        r'def\s+sanitize_',
        r'def\s+format_',
    ]
    
    if os.path.exists("modules"):
        for root, dirs, files in os.walk("modules"):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    search_for_cleaning_functions_in_file(filepath, cleaning_function_patterns)

def search_for_cleaning_functions_in_file(filepath, patterns):
    """Search for cleaning functions in a specific file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return
    
    found_functions = []
    
    for i, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line):
                found_functions.append((i, line.strip()))
    
    if found_functions:
        print(f"\n📁 Text cleaning functions in {filepath}:")
        for line_num, line_content in found_functions:
            print(f"  Line {line_num}: {line_content}")
            
            # Show more context for these functions
            print(f"    📋 Checking this function for .replace operations...")
            check_function_for_replace_operations(filepath, line_num)

def check_function_for_replace_operations(filepath, start_line):
    """Check a specific function for .replace operations"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return
    
    # Look at the next 50 lines after the function definition
    end_line = min(len(lines), start_line + 50)
    
    replace_operations = []
    
    for i in range(start_line, end_line):
        line = lines[i]
        if '.replace(' in line:
            replace_operations.append((i+1, line.strip()))
        
        # Stop at next function definition
        if line.strip().startswith('def ') and i > start_line:
            break
    
    if replace_operations:
        print(f"      🚨 REPLACE OPERATIONS FOUND:")
        for line_num, line_content in replace_operations:
            print(f"        Line {line_num}: {line_content}")
            if '$' in line_content:
                print(f"          ⚠️  INVOLVES $ SYMBOL - POTENTIAL CULPRIT!")

def create_quick_test_fix():
    """Create a quick test to confirm and fix the issue"""
    
    test_script = '''
# Quick test to confirm the replace issue
# Save as confirm_replace_issue.py

def test_replace_operations():
    """Test different replace operations"""
    
    original = "Current leads voltage by $90\\\\,^\\\\circ$."
    
    print("=== TESTING REPLACE OPERATIONS ===")
    print(f"Original: '{original}'")
    
    # Test the suspected operation
    result1 = original.replace(' $', '$')
    print(f"After .replace(' $', '$'): '{result1}'")
    print(f"  This matches your issue: {'by$90' in result1}")
    
    # Test variations
    result2 = original.replace(' \\$', '\\$')  # Escaped version
    print(f"After .replace(' \\\\$', '\\\\$'): '{result2}'")
    
    # Test if it's a regex
    import re
    result3 = re.sub(r' \\$', '$', original)
    print(f"After re.sub(r' \\\\$', '$', text): '{result3}'")
    
    print(f"\\n🎯 CONCLUSION:")
    print(f"The operation .replace(' $', '$') definitely causes your issue!")
    print(f"Now we need to find where this is happening in your code.")

if __name__ == "__main__":
    test_replace_operations()
    '''
    
    print(f"\n=== QUICK TEST SCRIPT ===")
    print("Save this as confirm_replace_issue.py and run it:")
    print(test_script)

if __name__ == "__main__":
    search_for_replace_space_dollar()
    search_for_text_cleaning_functions()
    create_quick_test_fix()
    
    print(f"\n" + "="*60)
    print(f"🎯 SUMMARY:")
    print(f"1. We know .replace(' $', '$') is the exact operation causing the issue")
    print(f"2. Now we need to find which function is doing this")
    print(f"3. It's likely in a text cleaning/processing function")
    print(f"4. Once found, we can either fix or disable that function")
