#!/usr/bin/env python3
"""
Examine the load_database_from_json function for LaTeX processing
"""

import os
import re

def examine_load_database_function():
    """Find and examine the load_database_from_json function"""
    
    print("=== EXAMINING load_database_from_json FUNCTION ===")
    
    filepath = "modules/database_processor.py"
    
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"❌ Could not read {filepath}: {e}")
        return
    
    # Find the load_database_from_json function
    function_found = False
    in_function = False
    function_lines = []
    
    for i, line in enumerate(lines, 1):
        # Check for function definition
        if re.search(r'def\s+load_database_from_json\s*\(', line):
            function_found = True
            in_function = True
            function_lines = [(i, line)]
            print(f"📍 Found load_database_from_json at line {i}")
            continue
        
        # If we're in the function, collect lines until next function or end
        if in_function:
            # Check if this is a new function (not indented)
            if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' in line:
                in_function = False
            else:
                function_lines.append((i, line))
        
        # Limit to reasonable size
        if len(function_lines) > 150:
            break
    
    if function_found:
        print(f"📋 Function content (showing all lines):")
        
        # Look for auto_latex, clean, process, or regex patterns
        suspicious_keywords = ['auto_latex', 'clean', 'process', 'latex', 'strip', '\.sub', '\.replace']
        
        for line_num, line_content in function_lines:
            # Highlight suspicious lines
            marker = ""
            if any(keyword in line_content.lower() for keyword in suspicious_keywords):
                marker = " ← SUSPICIOUS"
            
            print(f"  {line_num:3d}: {line_content}{marker}")
        
        # Specifically look for auto_latex usage
        auto_latex_lines = [
            (num, line) for num, line in function_lines 
            if 'auto_latex' in line.lower()
        ]
        
        if auto_latex_lines:
            print(f"\n🎯 AUTO_LATEX USAGE FOUND:")
            for line_num, line_content in auto_latex_lines:
                print(f"  Line {line_num}: {line_content.strip()}")
        else:
            print(f"\n❌ No auto_latex usage found in load_database_from_json")
            print(f"   Checking if it's passed to other functions...")
            
            # Look for function calls that might receive auto_latex
            function_calls = [
                (num, line) for num, line in function_lines 
                if '(' in line and any(keyword in line.lower() for keyword in ['clean', 'process', 'latex'])
            ]
            
            if function_calls:
                print(f"\n🔍 SUSPICIOUS FUNCTION CALLS:")
                for line_num, line_content in function_calls:
                    print(f"  Line {line_num}: {line_content.strip()}")
    
    else:
        print(f"❌ load_database_from_json not found in {filepath}")

def search_all_files_for_auto_latex():
    """Search all Python files for auto_latex usage"""
    
    print(f"\n=== SEARCHING ALL FILES FOR auto_latex USAGE ===")
    
    # Search modules directory
    if os.path.exists("modules"):
        for root, dirs, files in os.walk("modules"):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    search_file_for_auto_latex(filepath)

def search_file_for_auto_latex(filepath):
    """Search a specific file for auto_latex usage"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return
    
    # Look for auto_latex usage
    auto_latex_lines = []
    
    for i, line in enumerate(lines, 1):
        if 'auto_latex' in line.lower():
            auto_latex_lines.append((i, line.strip()))
    
    if auto_latex_lines:
        print(f"\n📁 {filepath}:")
        for line_num, line_content in auto_latex_lines:
            print(f"  Line {line_num}: {line_content}")
            
            # Show context for conditional usage
            if 'if' in line_content.lower() and 'auto_latex' in line_content.lower():
                print(f"    ⚠️  CONDITIONAL USAGE - this is likely where processing happens!")

def look_for_space_stripping_specifically():
    """Look specifically for patterns that would strip spaces before $"""
    
    print(f"\n=== LOOKING FOR SPACE STRIPPING PATTERNS ===")
    
    # Patterns that would cause "by $90" to become "by$90"
    dangerous_patterns = [
        r'\.replace\([\'"][^\'"]* \$[\'"],\s*[\'"]?\$',  # .replace(" $", "$")
        r'\.sub\([^)]*\\s[^)]*\\\$[^)]*\$',             # .sub(r'\s+\$', '$', text)
        r'\.sub\([^)]*\\\$[^)]*\\s',                    # .sub(r'\$\s+', '$', text)
    ]
    
    # Check modules directory
    if os.path.exists("modules"):
        for root, dirs, files in os.walk("modules"):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    check_file_for_dangerous_patterns(filepath, dangerous_patterns)

def check_file_for_dangerous_patterns(filepath, patterns):
    """Check a file for dangerous space-stripping patterns"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return
    
    found_patterns = []
    
    for i, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line):
                found_patterns.append((i, line.strip()))
    
    if found_patterns:
        print(f"\n🚨 DANGEROUS PATTERNS in {filepath}:")
        for line_num, line_content in found_patterns:
            print(f"  Line {line_num}: {line_content}")
            print(f"    ⚠️  THIS COULD BE STRIPPING SPACES BEFORE $")

if __name__ == "__main__":
    examine_load_database_function()
    search_all_files_for_auto_latex()
    look_for_space_stripping_specifically()
    
    print("\n" + "="*60)
    print("🎯 SUMMARY:")
    print("1. Found process_single_database function")
    print("2. It calls load_database_from_json")
    print("3. Looking for where auto_latex is actually used")
    print("4. Searching for space-stripping patterns")
