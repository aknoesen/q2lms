#!/usr/bin/env python3
"""
Find and examine the auto-LaTeX processing function
"""

import os
import re

def find_auto_latex_processing():
    """Find where the auto-LaTeX processing is implemented"""
    
    print("=== SEARCHING FOR AUTO-LATEX PROCESSING IMPLEMENTATION ===")
    
    # Search for where auto_latex is used
    search_patterns = [
        r'if\s+auto_latex',
        r'auto_latex\s*:',
        r'process.*latex',
        r'clean.*latex',
        r'auto.*latex',
    ]
    
    # Check upload_handler.py specifically
    upload_handler_path = "modules/upload_handler.py"
    if os.path.exists(upload_handler_path):
        print(f"\n🔍 Examining {upload_handler_path}...")
        examine_file_for_auto_latex(upload_handler_path)
    
    # Check other files
    files_to_check = [
        "modules/latex_processor.py",
        "modules/utils.py", 
        "streamlit_app.py",
    ]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f"\n🔍 Examining {filepath}...")
            examine_file_for_auto_latex(filepath)

def examine_file_for_auto_latex(filepath):
    """Examine a specific file for auto-LaTeX processing"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    # Look for auto_latex usage
    found_auto_latex = False
    
    for i, line in enumerate(lines, 1):
        if 'auto_latex' in line.lower():
            if not found_auto_latex:
                print(f"📍 Found auto_latex references:")
                found_auto_latex = True
            
            print(f"  Line {i}: {line.strip()}")
            
            # Show context around auto_latex usage
            if 'if' in line and 'auto_latex' in line:
                print(f"    ⚠️  CONDITIONAL USAGE - showing context:")
                start = max(0, i-2)
                end = min(len(lines), i+10)  # Show more context after
                
                for j in range(start, end):
                    marker = "  →" if j == i-1 else "   "
                    print(f"    {marker} {j+1}: {lines[j]}")
                print()
    
    # Look for LaTeX processing functions
    latex_functions = []
    for i, line in enumerate(lines, 1):
        if re.search(r'def\s+.*latex.*\(', line, re.IGNORECASE):
            latex_functions.append((i, line.strip()))
    
    if latex_functions:
        print(f"📍 Found LaTeX processing functions:")
        for line_num, line in latex_functions:
            print(f"  Line {line_num}: {line}")

def search_for_space_removal_in_latex_processing():
    """Look for space removal specifically in LaTeX processing"""
    
    print("\n=== SEARCHING FOR SPACE REMOVAL IN LATEX PROCESSING ===")
    
    # Search for files that might contain LaTeX processing
    latex_files = []
    
    # Check modules directory
    if os.path.exists("modules"):
        for root, dirs, files in os.walk("modules"):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    if contains_latex_processing(filepath):
                        latex_files.append(filepath)
    
    # Examine each file for space removal patterns
    for filepath in latex_files:
        print(f"\n🔍 Examining {filepath} for space removal...")
        examine_for_space_removal(filepath)

def contains_latex_processing(filepath):
    """Check if a file contains LaTeX processing"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            return 'latex' in content and ('process' in content or 'clean' in content)
    except:
        return False

def examine_for_space_removal(filepath):
    """Look for space removal patterns in a file"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    # Patterns that remove spaces
    space_removal_patterns = [
        r'\.replace\([^)]*\s[^)]*\$',
        r'\.sub\([^)]*\\s[^)]*\\\$',
        r'\.strip\(\)',
        r'\.split\(\).*\.join\(',
    ]
    
    found_patterns = []
    
    for i, line in enumerate(lines, 1):
        for pattern in space_removal_patterns:
            if re.search(pattern, line):
                found_patterns.append((i, line.strip(), pattern))
    
    if found_patterns:
        print(f"  ⚠️  Found {len(found_patterns)} space removal pattern(s):")
        for line_num, line, pattern in found_patterns:
            print(f"    Line {line_num}: {line}")
            
            # Show context
            start = max(0, line_num-3)
            end = min(len(lines), line_num+2)
            print(f"      Context:")
            for j in range(start, end):
                marker = "    →" if j == line_num-1 else "     "
                print(f"      {marker} {j+1}: {lines[j]}")
            print()

if __name__ == "__main__":
    find_auto_latex_processing()
    search_for_space_removal_in_latex_processing()
    
    print("\n" + "="*60)
    print("🎯 KEY FINDINGS SUMMARY:")
    print("1. Auto-LaTeX processing is ENABLED BY DEFAULT")
    print("2. Look for conditional 'if auto_latex:' blocks")
    print("3. The space removal is happening in LaTeX processing")
    print("4. Check upload_handler.py for the implementation")
