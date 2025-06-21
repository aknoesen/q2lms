#!/usr/bin/env python3
"""
QTI Package Difference Analyzer
Identifies the exact 3-byte difference between native and webapp QTI packages
"""

import zipfile
import io
import difflib
import sys
import os
from datetime import datetime

def extract_and_compare_qti_packages(native_zip_path, webapp_zip_path):
    """Extract and compare the contents of two QTI packages"""
    
    print("🔬 DETAILED QTI PACKAGE ANALYSIS")
    print("=" * 60)
    
    try:
        # Extract both packages
        native_files = {}
        webapp_files = {}
        
        print("📦 Extracting native package...")
        with zipfile.ZipFile(native_zip_path, 'r') as native_zip:
            for file_info in native_zip.filelist:
                filename = file_info.filename
                content = native_zip.read(filename)
                native_files[filename] = content
                print(f"   📄 {filename}: {len(content)} bytes")
        
        print(f"\n📦 Extracting webapp package...")
        with zipfile.ZipFile(webapp_zip_path, 'r') as webapp_zip:
            for file_info in webapp_zip.filelist:
                filename = file_info.filename
                content = webapp_zip.read(filename)
                webapp_files[filename] = content
                print(f"   📄 {filename}: {len(content)} bytes")
        
        # Compare file lists
        print(f"\n🗂️  FILE COMPARISON:")
        native_files_set = set(native_files.keys())
        webapp_files_set = set(webapp_files.keys())
        
        if native_files_set == webapp_files_set:
            print(f"✅ Identical file lists ({len(native_files_set)} files)")
        else:
            print(f"⚠️  Different file lists!")
            print(f"   Only in native: {native_files_set - webapp_files_set}")
            print(f"   Only in webapp: {webapp_files_set - native_files_set}")
        
        # Compare individual files
        print(f"\n📊 INDIVIDUAL FILE COMPARISON:")
        differences_found = []
        
        for filename in sorted(native_files_set & webapp_files_set):
            native_content = native_files[filename]
            webapp_content = webapp_files[filename]
            
            if native_content == webapp_content:
                print(f"✅ {filename}: Identical ({len(native_content)} bytes)")
            else:
                size_diff = len(webapp_content) - len(native_content)
                print(f"⚠️  {filename}: DIFFERENT!")
                print(f"    Native: {len(native_content)} bytes")
                print(f"    Webapp: {len(webapp_content)} bytes")
                print(f"    Difference: {size_diff:+d} bytes")
                
                differences_found.append((filename, native_content, webapp_content))
        
        # Analyze differences in detail
        if differences_found:
            print(f"\n🔍 DETAILED DIFFERENCE ANALYSIS:")
            analyze_content_differences(differences_found)
        else:
            print(f"\n🤔 No content differences found, but packages differ in size...")
            print(f"   This might be due to compression or metadata differences")
        
        return differences_found
        
    except Exception as e:
        print(f"❌ Error analyzing packages: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def analyze_content_differences(differences):
    """Analyze the specific content differences"""
    
    for filename, native_content, webapp_content in differences:
        print(f"\n📝 ANALYZING: {filename}")
        print("-" * 50)
        
        # Try to decode as text for XML/text files
        try:
            native_text = native_content.decode('utf-8')
            webapp_text = webapp_content.decode('utf-8')
            
            print(f"📄 File type: Text/XML")
            print(f"📏 Native length: {len(native_text)} characters")
            print(f"📏 Webapp length: {len(webapp_text)} characters")
            print(f"📏 Character difference: {len(webapp_text) - len(native_text):+d}")
            
            # Find exact differences
            if len(native_text) < 2000 and len(webapp_text) < 2000:  # Only for small files
                print(f"\n🔎 LINE-BY-LINE COMPARISON:")
                native_lines = native_text.splitlines(keepends=True)
                webapp_lines = webapp_text.splitlines(keepends=True)
                
                diff = list(difflib.unified_diff(
                    native_lines, 
                    webapp_lines,
                    fromfile=f"Native/{filename}",
                    tofile=f"Webapp/{filename}",
                    lineterm='',
                    n=3
                ))
                
                if diff:
                    for line in diff[:20]:  # Show first 20 lines of diff
                        print(line.rstrip())
                    if len(diff) > 20:
                        print(f"... ({len(diff) - 20} more diff lines)")
                else:
                    print("No line differences found (might be whitespace/encoding)")
            
            # Character-by-character analysis for small differences
            if abs(len(webapp_text) - len(native_text)) <= 10:
                print(f"\n🔬 CHARACTER-LEVEL ANALYSIS:")
                find_character_differences(native_text, webapp_text)
                
        except UnicodeDecodeError:
            print(f"📄 File type: Binary")
            print(f"📏 Native size: {len(native_content)} bytes")
            print(f"📏 Webapp size: {len(webapp_content)} bytes")
            
            # Binary comparison
            if len(native_content) < 100 and len(webapp_content) < 100:
                print(f"\n🔬 BINARY COMPARISON:")
                print(f"Native:  {native_content.hex()}")
                print(f"Webapp:  {webapp_content.hex()}")

def find_character_differences(text1, text2):
    """Find exact character differences between two texts"""
    
    min_len = min(len(text1), len(text2))
    max_len = max(len(text1), len(text2))
    
    differences = []
    
    # Find character differences in common length
    for i in range(min_len):
        if text1[i] != text2[i]:
            differences.append((i, text1[i], text2[i]))
    
    # Handle length differences
    if len(text1) != len(text2):
        longer_text = text1 if len(text1) > len(text2) else text2
        shorter_name = "Native" if len(text1) < len(text2) else "Webapp"
        longer_name = "Webapp" if len(text1) < len(text2) else "Native"
        
        extra_chars = longer_text[min_len:]
        print(f"📝 {longer_name} has {len(extra_chars)} extra characters at end:")
        print(f"   '{extra_chars}' (repr: {repr(extra_chars)})")
    
    if differences:
        print(f"🎯 Found {len(differences)} character differences:")
        for i, (pos, char1, char2) in enumerate(differences[:10]):  # Show first 10
            print(f"   Position {pos}: '{char1}' → '{char2}' (repr: {repr(char1)} → {repr(char2)})")
        if len(differences) > 10:
            print(f"   ... ({len(differences) - 10} more differences)")
    else:
        print(f"🤔 No character differences in common length")

def main():
    """Main function to run the analysis"""
    
    print("🚀 QTI PACKAGE DIFFERENCE ANALYZER")
    print("=" * 70)
    print(f"📅 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Look for the latest generated files
    import glob
    
    native_files = glob.glob("native_qti_*.zip")
    webapp_files = glob.glob("webapp_qti_*.zip")
    
    if not native_files or not webapp_files:
        print("❌ Could not find QTI packages to compare")
        print("   Make sure to run comparison_test_script.py first")
        return
    
    # Use the most recent files
    native_file = max(native_files, key=os.path.getctime)
    webapp_file = max(webapp_files, key=os.path.getctime)
    
    print(f"📦 Comparing:")
    print(f"   Native: {native_file}")
    print(f"   Webapp: {webapp_file}")
    print()
    
    differences = extract_and_compare_qti_packages(native_file, webapp_file)
    
    if differences:
        print(f"\n🎯 SUMMARY:")
        print(f"Found differences in {len(differences)} file(s)")
        print(f"These differences are causing Canvas import issues")
        print(f"\n💡 RECOMMENDATION:")
        print(f"Focus on fixing the webapp processing pipeline to match native output")
    else:
        print(f"\n🤔 MYSTERY:")
        print(f"No content differences found, but package sizes differ")
        print(f"This might be ZIP compression or metadata differences")

if __name__ == "__main__":
    main()
