#!/usr/bin/env python3
"""
Find the process_single_database function that's stripping spaces
"""

import os
import re

def find_process_single_database():
    """Find where process_single_database is implemented"""
    
    print("=== SEARCHING FOR process_single_database FUNCTION ===")
    
    # Search for the function definition
    files_to_check = [
        "modules/database_processor.py",
        "modules/upload_handler.py",
        "modules/file_processor_module.py",
    ]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f"\n🔍 Checking {filepath}...")
            find_function_in_file(filepath, "process_single_database")

def find_function_in_file(filepath, function_name):
    """Find a specific function in a file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    # Look for function definition
    function_found = False
    in_function = False
    function_lines = []
    
    for i, line in enumerate(lines, 1):
        # Check for function definition
        if re.search(rf'def\s+{function_name}\s*\(', line):
            function_found = True
            in_function = True
            function_lines = [(i, line)]
            print(f"📍 Found {function_name} at line {i}")
            continue
        
        # If we're in the function, collect lines until next function or end
        if in_function:
            # Check if this is a new function (not indented)
            if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' in line:
                in_function = False
            else:
                function_lines.append((i, line))
        
        # Limit to reasonable size
        if len(function_lines) > 100:
            break
    
    if function_found:
        print(f"📋 Function content preview (first 30 lines):")
        
        for line_num, line_content in function_lines[:30]:
            # Highlight lines that might process LaTeX
            marker = ""
            if 'auto_latex' in line_content.lower():
                marker = " ← AUTO_LATEX"
            elif any(keyword in line_content.lower() for keyword in ['latex', 'clean', 'process', 'strip']):
                marker = " ← SUSPICIOUS"
            
            print(f"  {line_num:3d}: {line_content}{marker}")
        
        if len(function_lines) > 30:
            print(f"  ... ({len(function_lines) - 30} more lines)")
        
        # Look for auto_latex usage specifically
        auto_latex_lines = [
            (num, line) for num, line in function_lines 
            if 'auto_latex' in line.lower()
        ]
        
        if auto_latex_lines:
            print(f"\n🎯 Found auto_latex usage:")
            for line_num, line_content in auto_latex_lines:
                print(f"  Line {line_num}: {line_content.strip()}")
    
    else:
        print(f"❌ {function_name} not found in {filepath}")

def search_for_latex_processing_calls():
    """Search for calls to LaTeX processing functions"""
    
    print(f"\n=== SEARCHING FOR LATEX PROCESSING CALLS ===")
    
    # Search for function calls that might process LaTeX
    search_patterns = [
        r'if\s+.*auto_latex',
        r'clean_latex',
        r'process_latex',
        r'normalize_latex',
        r'\.sub\([^)]*\$',  # regex with $
        r'\.replace\([^)]*\$',  # replace with $
    ]
    
    # Check key files
    key_files = [
        "modules/database_processor.py",
        "modules/upload_handler.py", 
        "modules/utils.py",
    ]
    
    for filepath in key_files:
        if os.path.exists(filepath):
            print(f"\n🔍 Searching {filepath}...")
            search_patterns_in_file(filepath, search_patterns)

def search_patterns_in_file(filepath, patterns):
    """Search for specific patterns in a file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    found_any = False
    
    for i, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                if not found_any:
                    found_any = True
                
                print(f"  Line {i}: {line.strip()}")
                
                # Show context for suspicious lines
                if any(keyword in pattern for keyword in ['auto_latex', 'clean', 'process']):
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    print(f"    Context:")
                    for j in range(start, end):
                        marker = "    →" if j == i-1 else "     "
                        print(f"    {marker} {j+1}: {lines[j]}")
                    print()
    
    if not found_any:
        print(f"  ✅ No suspicious patterns found")

if __name__ == "__main__":
    find_process_single_database()
    search_for_latex_processing_calls()
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("1. Examine the process_single_database function")
    print("2. Look for 'if auto_latex:' conditions")
    print("3. Find the actual LaTeX cleaning code")
    print("4. Either fix the cleaning logic or disable it")
