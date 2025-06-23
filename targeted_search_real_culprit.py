#!/usr/bin/env python3
"""
More targeted search for the actual function stripping spaces
Focus on the real modules, not our test scripts
"""

import os
import re

def search_core_modules_only():
    """Search only the core application modules"""
    
    print("=== TARGETED SEARCH IN CORE MODULES ===")
    
    # Core modules to check (excluding our test scripts)
    core_files = [
        "modules/utils.py",
        "modules/database_processor.py", 
        "modules/question_editor.py",
        "modules/upload_handler.py",
        "modules/simple_browse.py",
        "modules/ui_components.py",
        "streamlit_app.py"
    ]
    
    for filepath in core_files:
        if os.path.exists(filepath):
            print(f"\n🔍 Searching {filepath}...")
            search_for_actual_replace_operations(filepath)

def search_for_actual_replace_operations(filepath):
    """Search for actual .replace operations (not test code)"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    suspicious_lines = []
    
    for i, line in enumerate(lines, 1):
        # Skip comments and strings  
        if line.strip().startswith('#'):
            continue
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            continue
            
        # Look for .replace operations involving $
        if '.replace(' in line and '$' in line:
            # Skip test/debug code
            if 'test' not in line.lower() and 'debug' not in line.lower():
                suspicious_lines.append((i, line.strip()))
    
    if suspicious_lines:
        print(f"  🚨 FOUND .replace operations with $:")
        for line_num, line_content in suspicious_lines:
            print(f"    Line {line_num}: {line_content}")
            
            # Check if this looks like the culprit
            if "' $'" in line_content or '" $"' in line_content:
                print(f"      ⚠️  POTENTIAL CULPRIT - contains ' $' pattern!")
                show_context_around_line(filepath, line_num)

def show_context_around_line(filepath, line_num):
    """Show context around a suspicious line"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return
    
    print(f"      📋 Context around line {line_num}:")
    start = max(0, line_num - 4)
    end = min(len(lines), line_num + 3)
    
    for i in range(start, end):
        marker = "      →" if i == line_num - 1 else "       "
        print(f"      {marker} {i+1}: {lines[i].rstrip()}")

def search_for_latex_related_functions():
    """Search for LaTeX-related functions that might be doing text processing"""
    
    print(f"\n=== SEARCHING FOR LATEX-RELATED FUNCTIONS ===")
    
    # Look for functions with LaTeX in the name
    core_files = [
        "modules/utils.py",
        "modules/database_processor.py",
        "modules/question_editor.py",
        "modules/upload_handler.py",
    ]
    
    for filepath in core_files:
        if os.path.exists(filepath):
            search_latex_functions_in_file(filepath)

def search_latex_functions_in_file(filepath):
    """Search for LaTeX functions in a specific file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return
    
    latex_functions = []
    
    for i, line in enumerate(lines, 1):
        # Look for function definitions with LaTeX in name
        if re.search(r'def\s+.*latex.*\(', line, re.IGNORECASE):
            latex_functions.append((i, line.strip()))
        # Look for functions that process text and might involve LaTeX
        elif re.search(r'def\s+.*(render|process|clean|format).*text.*\(', line, re.IGNORECASE):
            latex_functions.append((i, line.strip()))
    
    if latex_functions:
        print(f"\n📁 LaTeX/text processing functions in {filepath}:")
        for line_num, line_content in latex_functions:
            print(f"  Line {line_num}: {line_content}")
            
            # Check these functions for .replace operations
            check_function_body_for_replace(filepath, line_num)

def check_function_body_for_replace(filepath, start_line):
    """Check the body of a function for .replace operations"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return
    
    # Check the next 30 lines for .replace operations
    end_line = min(len(lines), start_line + 30)
    replace_ops = []
    
    for i in range(start_line, end_line):
        line = lines[i]
        
        # Stop at next function
        if i > start_line and line.strip().startswith('def '):
            break
            
        if '.replace(' in line and '$' in line:
            replace_ops.append((i+1, line.strip()))
    
    if replace_ops:
        print(f"    🚨 REPLACE OPERATIONS FOUND:")
        for line_num, line_content in replace_ops:
            print(f"      Line {line_num}: {line_content}")
            if "' $'" in line_content or '" $"' in line_content:
                print(f"        ⚠️  THIS IS THE CULPRIT!")

def quick_grep_alternative():
    """Alternative search using simple string matching"""
    
    print(f"\n=== ALTERNATIVE SEARCH ===")
    print("Looking for exact patterns that would cause the issue...")
    
    patterns_to_find = [
        ".replace(' $', '$')",
        '.replace(" $", "$")',
        ".replace(' \\$', '\\$')",
        '.replace(" \\$", "\\$")',
    ]
    
    core_files = [
        "modules/utils.py",
        "modules/database_processor.py", 
        "modules/question_editor.py",
        "modules/upload_handler.py",
        "modules/simple_browse.py",
        "streamlit_app.py"
    ]
    
    for filepath in core_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in patterns_to_find:
                    if pattern in content:
                        print(f"🚨 FOUND '{pattern}' in {filepath}")
                        find_line_with_pattern(filepath, pattern)
                        
            except Exception as e:
                continue

def find_line_with_pattern(filepath, pattern):
    """Find the exact line containing a pattern"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            if pattern in line:
                print(f"  Line {i}: {line.strip()}")
                print(f"  ⚠️  THIS IS THE EXACT CULPRIT LINE!")
                
                # Show context
                start = max(0, i-3)
                end = min(len(lines), i+2)
                print(f"  Context:")
                for j in range(start, end):
                    marker = "  →" if j == i-1 else "   "
                    print(f"  {marker} {j+1}: {lines[j].rstrip()}")
                
    except Exception as e:
        pass

if __name__ == "__main__":
    search_core_modules_only()
    search_for_latex_related_functions()
    quick_grep_alternative()
    
    print(f"\n" + "="*60)
    print(f"🎯 IF NO RESULTS FOUND:")
    print(f"The issue might be in:")
    print(f"1. A module we haven't checked yet")
    print(f"2. Generated/dynamic code")
    print(f"3. An imported library doing the replacement")
    print(f"4. Browser-side processing (less likely)")
