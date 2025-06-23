#!/usr/bin/env python3
"""
Standalone Unicode Character Detector
Run this script to check your JSON files for Unicode characters
"""

import json
import os
import sys

def detect_unicode_in_json(json_file_path):
    """
    Detect Unicode characters in JSON input data
    """
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"❌ File not found: {json_file_path}")
        return False
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return False
    
    print("🔍 UNICODE CHARACTER DETECTION REPORT")
    print("=" * 50)
    print(f"📁 File: {json_file_path}")
    print()
    
    unicode_findings = []
    
    def scan_text_for_unicode(text, location):
        """Scan text for non-ASCII Unicode characters"""
        if not isinstance(text, str):
            return
        
        # Find all non-ASCII characters
        non_ascii_chars = []
        for i, char in enumerate(text):
            if ord(char) > 127:  # Non-ASCII
                non_ascii_chars.append({
                    'char': char,
                    'unicode': f'U+{ord(char):04X}',
                    'position': i,
                    'name': repr(char)
                })
        
        if non_ascii_chars:
            unicode_findings.append({
                'location': location,
                'text': text,
                'unicode_chars': non_ascii_chars
            })
    
    def scan_questions(questions):
        """Recursively scan all question fields"""
        for i, question in enumerate(questions):
            question_id = question.get('id', f'question_{i}')
            
            # Scan all text fields
            text_fields = [
                'title', 'question_text', 'correct_answer',
                'feedback_correct', 'feedback_incorrect'
            ]
            
            for field in text_fields:
                if field in question:
                    scan_text_for_unicode(
                        question[field], 
                        f"Question {question_id} → {field}"
                    )
            
            # Scan choices
            if 'choices' in question:
                for j, choice in enumerate(question['choices']):
                    scan_text_for_unicode(
                        choice, 
                        f"Question {question_id} → choices[{j}]"
                    )
    
    # Scan questions
    if 'questions' in data:
        total_questions = len(data['questions'])
        print(f"📊 Total questions to scan: {total_questions}")
        scan_questions(data['questions'])
    else:
        print("⚠️  No 'questions' key found in JSON")
        return False
    
    # Report findings
    if unicode_findings:
        print(f"\n⚠️  FOUND {len(unicode_findings)} locations with Unicode characters:")
        print()
        
        for finding in unicode_findings:
            print(f"📍 Location: {finding['location']}")
            print(f"📝 Text: \"{finding['text'][:100]}{'...' if len(finding['text']) > 100 else ''}\"")
            print("🔤 Unicode characters found:")
            
            for char_info in finding['unicode_chars']:
                print(f"   • '{char_info['char']}' at position {char_info['position']} "
                      f"→ {char_info['unicode']} ({char_info['name']})")
            print("-" * 40)
    
    else:
        print("✅ NO Unicode characters found in input data!")
        print("📋 Input appears to be clean ASCII/basic text")
    
    # Check for common problematic characters
    print("\n🎯 CHECKING FOR COMMON PROBLEMATIC CHARACTERS:")
    
    problematic_chars = {
        '\u00A0': 'Non-breaking space',
        '\u2009': 'Thin space', 
        '\u202F': 'Narrow no-break space',
        '\u2014': 'Em dash',
        '\u2013': 'En dash',
        '\u201C': 'Left double quotation mark',
        '\u201D': 'Right double quotation mark',
        '\u2019': 'Right single quotation mark',
        '\u00B0': 'Degree symbol',
        '\u03A9': 'Greek capital letter omega (Ω)',
        '\u03BC': 'Greek small letter mu (μ)',
        '\u03C0': 'Greek small letter pi (π)'
    }
    
    found_problematic = False
    if 'questions' in data:
        for i, question in enumerate(data['questions']):
            question_id = question.get('id', f'question_{i}')
            for field, value in question.items():
                if isinstance(value, str):
                    for prob_char, description in problematic_chars.items():
                        if prob_char in value:
                            print(f"⚠️  Found {description} ({repr(prob_char)}) in {question_id} field '{field}'")
                            print(f"     Text: \"{value[:50]}{'...' if len(value) > 50 else ''}\"")
                            found_problematic = True
                elif isinstance(value, list):  # Handle choices
                    for j, choice in enumerate(value):
                        if isinstance(choice, str):
                            for prob_char, description in problematic_chars.items():
                                if prob_char in choice:
                                    print(f"⚠️  Found {description} ({repr(prob_char)}) in {question_id} choice[{j}]")
                                    print(f"     Text: \"{choice}\"")
                                    found_problematic = True
    
    if not found_problematic:
        print("✅ No common problematic characters found")
    
    print("\n" + "=" * 50)
    print(f"✅ Analysis complete for {json_file_path}")
    
    return len(unicode_findings) == 0  # Return True if clean

def main():
    """Main function to run the checker"""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Default to CornerCases.json
        json_file = "CornerCases.json"
        
        # Check if file exists, if not ask user
        if not os.path.exists(json_file):
            print("🔍 CornerCases.json not found in current directory")
            json_file = input("📁 Enter path to your JSON file: ").strip().strip('"')
    
    print(f"🚀 Starting Unicode detection for: {json_file}")
    print()
    
    # Run the detection
    is_clean = detect_unicode_in_json(json_file)
    
    print("\n🎯 SUMMARY:")
    if is_clean:
        print("✅ Your JSON file is clean - no Unicode characters found!")
        print("💡 The spacing issue is likely in the display logic, not the input data.")
    else:
        print("⚠️  Unicode characters found in your JSON file.")
        print("🔧 You may need to clean the input data before processing.")

if __name__ == "__main__":
    main()