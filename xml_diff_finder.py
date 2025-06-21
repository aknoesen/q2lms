#!/usr/bin/env python3
"""
XML Content Difference Finder
Find the exact 18-byte difference in the main QTI XML files
"""

import zipfile
import difflib
import re

def extract_and_compare_main_xml():
    """Extract and compare the main QTI XML files"""
    
    print("🔍 ANALYZING MAIN QTI XML DIFFERENCES")
    print("=" * 60)
    
    # Get the latest files
    import glob
    import os
    
    native_files = glob.glob("native_qti_*.zip")
    webapp_files = glob.glob("webapp_qti_*.zip")
    
    native_file = max(native_files, key=os.path.getctime)
    webapp_file = max(webapp_files, key=os.path.getctime)
    
    print(f"📦 Comparing XML content from:")
    print(f"   Native: {native_file}")
    print(f"   Webapp: {webapp_file}")
    
    # Extract the main XML files
    with zipfile.ZipFile(native_file, 'r') as native_zip:
        native_xml = native_zip.read('Native_Test.xml').decode('utf-8')
    
    with zipfile.ZipFile(webapp_file, 'r') as webapp_zip:
        webapp_xml = webapp_zip.read('Native_Test.xml').decode('utf-8')
    
    print(f"\n📊 XML File Sizes:")
    print(f"   Native:  {len(native_xml):,} characters")
    print(f"   Webapp:  {len(webapp_xml):,} characters")
    print(f"   Difference: {len(webapp_xml) - len(native_xml):+d} characters")
    
    # Find differences
    find_xml_differences(native_xml, webapp_xml)
    
    return native_xml, webapp_xml

def find_xml_differences(native_xml, webapp_xml):
    """Find specific differences between XML files"""
    
    print(f"\n🔎 SEARCHING FOR DIFFERENCES...")
    
    # Split into lines for comparison
    native_lines = native_xml.splitlines()
    webapp_lines = webapp_xml.splitlines()
    
    print(f"📄 Line counts:")
    print(f"   Native:  {len(native_lines)} lines")
    print(f"   Webapp:  {len(webapp_lines)} lines")
    
    # Generate detailed diff
    diff = list(difflib.unified_diff(
        native_lines,
        webapp_lines,
        fromfile="Native_QTI",
        tofile="Webapp_QTI",
        lineterm='',
        n=5  # Show 5 lines of context
    ))
    
    if diff:
        print(f"\n📝 FOUND DIFFERENCES:")
        print("-" * 50)
        
        difference_count = 0
        for line in diff:
            if line.startswith('@@'):
                difference_count += 1
                print(f"\n🎯 DIFFERENCE #{difference_count}:")
            print(line)
            
            # Stop after showing first few differences
            if difference_count >= 3:
                remaining = len([l for l in diff if l.startswith('@@')]) - 3
                if remaining > 0:
                    print(f"\n... ({remaining} more difference sections)")
                break
    else:
        print(f"🤔 No line-level differences found")
        print(f"   This suggests whitespace or encoding differences")
        
        # Check for character-level differences
        analyze_character_differences(native_xml, webapp_xml)

def analyze_character_differences(native_xml, webapp_xml):
    """Analyze character-by-character differences"""
    
    print(f"\n🔬 CHARACTER-LEVEL ANALYSIS:")
    
    min_len = min(len(native_xml), len(webapp_xml))
    differences = []
    
    # Find character differences
    for i in range(min_len):
        if native_xml[i] != webapp_xml[i]:
            differences.append((i, native_xml[i], webapp_xml[i]))
    
    # Handle length differences
    if len(native_xml) != len(webapp_xml):
        longer = webapp_xml if len(webapp_xml) > len(native_xml) else native_xml
        extra_chars = longer[min_len:]
        source = "Webapp" if len(webapp_xml) > len(native_xml) else "Native"
        
        print(f"📏 {source} has {len(extra_chars)} extra characters:")
        print(f"   Content: {repr(extra_chars[:100])}")
        if len(extra_chars) > 100:
            print(f"   ... (showing first 100 of {len(extra_chars)} chars)")
    
    if differences:
        print(f"\n🎯 CHARACTER DIFFERENCES FOUND:")
        for i, (pos, char1, char2) in enumerate(differences[:10]):
            # Show context around the difference
            start = max(0, pos - 20)
            end = min(len(native_xml), pos + 20)
            
            native_context = native_xml[start:end]
            webapp_context = webapp_xml[start:end]
            
            print(f"\n   Difference #{i+1} at position {pos}:")
            print(f"   Native:  ...{native_context}...")
            print(f"   Webapp:  ...{webapp_context}...")
            print(f"   Change:  '{char1}' → '{char2}'")
        
        if len(differences) > 10:
            print(f"   ... ({len(differences) - 10} more differences)")
    else:
        print(f"   No character differences in common length")

def analyze_xml_structure(native_xml, webapp_xml):
    """Analyze XML structure differences"""
    
    print(f"\n🏗️  XML STRUCTURE ANALYSIS:")
    
    # Look for common XML patterns that might differ
    patterns_to_check = [
        r'<item[^>]*>',  # Item tags
        r'response_lid[^>]*>',  # Response tags  
        r'<material>.*?</material>',  # Material content
        r'<mattext[^>]*>.*?</mattext>',  # Text content
        r'<response_label[^>]*>',  # Response labels
    ]
    
    for pattern in patterns_to_check:
        native_matches = re.findall(pattern, native_xml, re.DOTALL)
        webapp_matches = re.findall(pattern, webapp_xml, re.DOTALL)
        
        if len(native_matches) != len(webapp_matches):
            print(f"⚠️  Pattern '{pattern}' count mismatch:")
            print(f"   Native: {len(native_matches)} matches")
            print(f"   Webapp: {len(webapp_matches)} matches")

def main():
    """Main analysis function"""
    
    print("🚀 XML DIFFERENCE HUNTER")
    print("=" * 50)
    
    try:
        native_xml, webapp_xml = extract_and_compare_main_xml()
        analyze_xml_structure(native_xml, webapp_xml)
        
        print(f"\n💡 LIKELY CAUSES OF 18-BYTE DIFFERENCE:")
        print(f"1. Extra whitespace or newlines in webapp version")
        print(f"2. Additional XML attributes or formatting")
        print(f"3. Character encoding differences")
        print(f"4. Streamlit session state bleeding into XML generation")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
