#!/usr/bin/env python3
"""
Search for the function that's stripping spaces before $
"""

import os
import re

def search_for_space_stripping_patterns():
    """Search all Python files for patterns that strip spaces"""
    
    # Patterns that would cause the issue
    suspicious_patterns = [
        r'\.sub\([^)]*\\s[^)]*\\\$',           # re.sub with \s and \$
        r'\.replace\([^)]*\s[^)]*\$',          # .replace with space and $
        r'\.sub\([^)]*\$[^)]*\\1\\2',          # re.sub pattern like (\w)\s+(\$) -> \1\2
        r'clean.*latex',                       # Any function with "clean" and "latex"
        r'normalize.*text',                    # Text normalization functions
        r'strip.*space',                       # Space stripping functions
    ]
    
    print("=== SEARCHING FOR SPACE-STRIPPING FUNCTIONS ===")
    
    # Search in modules directory
    modules_dir = "modules"
    if os.path.exists(modules_dir):
        print(f"Searching in {modules_dir}/...")
        search_directory(modules_dir, suspicious_patterns)
    
    # Search in main directory
    print(f"Searching in main directory...")
    search_files([f for f in os.listdir(".") if f.endswith(".py")], suspicious_patterns)

def search_directory(directory, patterns):
    """Search all Python files in a directory"""
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                search_file(filepath, patterns)

def search_files(files, patterns):
    """Search specific files"""
    
    for file in files:
        if os.path.exists(file):
            search_file(file, patterns)

def search_file(filepath, patterns):
    """Search a single file for suspicious patterns"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    file_found_issues = False
    
    for i, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                if not file_found_issues:
                    print(f"\n🚨 SUSPICIOUS PATTERN in {filepath}:")
                    file_found_issues = True
                
                print(f"  Line {i}: {line.strip()}")
                
                # Show context around the suspicious line
                start = max(0, i-3)
                end = min(len(lines), i+2)
                print(f"    Context:")
                for j in range(start, end):
                    marker = "  →" if j == i-1 else "   "
                    print(f"    {marker} {j+1}: {lines[j]}")
                print()

def search_for_specific_functions():
    """Search for specific function names that might be doing this"""
    
    print("\n=== SEARCHING FOR SPECIFIC FUNCTION NAMES ===")
    
    function_names = [
        'clean_text',
        'normalize_text', 
        'process_text',
        'sanitize_text',
        'format_text',
        'clean_latex',
        'process_latex',
        'normalize_latex',
        'strip_spaces',
        'remove_spaces',
    ]
    
    search_patterns = [rf'\bdef\s+{name}\b' for name in function_names]
    search_patterns.extend([rf'\b{name}\s*\(' for name in function_names])
    
    # Search modules
    if os.path.exists("modules"):
        search_directory("modules", search_patterns)
    
    # Search main files
    search_files([f for f in os.listdir(".") if f.endswith(".py")], search_patterns)

def check_utils_file_specifically():
    """Check utils.py specifically for the issue"""
    
    print("\n=== DETAILED CHECK OF utils.py ===")
    
    utils_path = "modules/utils.py"
    if not os.path.exists(utils_path):
        utils_path = "utils.py"
    
    if os.path.exists(utils_path):
        print(f"Checking {utils_path}...")
        
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Look for any regex operations
        regex_lines = []
        for i, line in enumerate(lines, 1):
            if 're.sub' in line or '.replace(' in line:
                regex_lines.append((i, line.strip()))
        
        if regex_lines:
            print(f"Found {len(regex_lines)} regex/replace operations:")
            for line_num, line in regex_lines:
                print(f"  Line {line_num}: {line}")
                
                # Test this specific line against our test case
                if '$' in line and ('\\s' in line or 'space' in line.lower()):
                    print(f"    ⚠️  SUSPICIOUS: Contains $ and space patterns")
        else:
            print("No regex operations found in utils.py")
    else:
        print(f"❌ {utils_path} not found")

if __name__ == "__main__":
    search_for_space_stripping_patterns()
    search_for_specific_functions()
    check_utils_file_specifically()
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("1. Check any files flagged above")
    print("2. Look for function calls in question_editor.py")
    print("3. Check if there's a global text processor")
    print("4. Search for 'render_latex_in_text' usage")
