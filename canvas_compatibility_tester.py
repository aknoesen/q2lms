#!/usr/bin/env python3
"""
Canvas Compatibility Diagnostic Tool
Identify exactly what Canvas doesn't like about our QTI generation
"""

import json
import sys
import os
from datetime import datetime

# Add your modules path
sys.path.append('modules')

def load_controlled_test_json():
    """Load the controlled test JSON that's causing Canvas errors"""
    
    with open('controlled_test_json.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_minimal_test_qti():
    """Generate the absolute minimal QTI that Canvas should accept"""
    
    print("🧪 GENERATING MINIMAL CANVAS-COMPATIBLE QTI")
    print("=" * 60)
    
    # Start with just ONE simple question
    minimal_question = {
        "id": "Q_00001",
        "type": "multiple_choice", 
        "title": "Simple Test",
        "question_text": "What is 2 + 2?",
        "choices": ["3", "4", "5", "6"],
        "correct_answer": "4",
        "points": 1,
        "tolerance": 0.05,
        "feedback_correct": "Correct!",
        "feedback_incorrect": "Try again.",
        "image_file": [],
        "topic": "Math",
        "subtopic": "Addition",
        "difficulty": "Easy"
    }
    
    try:
        from exporter import CanvasLaTeXQTIGenerator
        
        generator = CanvasLaTeXQTIGenerator()
        qti_package = generator.create_qti_package([minimal_question], "Minimal_Test")
        
        if qti_package:
            output_filename = f"minimal_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with open(output_filename, 'wb') as f:
                f.write(qti_package)
            
            print(f"✅ Minimal QTI created: {output_filename}")
            print(f"📊 Package size: {len(qti_package):,} bytes")
            print(f"📋 Contains: 1 simple multiple choice question")
            return output_filename, qti_package
        else:
            print("❌ Failed to create minimal QTI")
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating minimal QTI: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None

def generate_latex_test_qti():
    """Generate QTI with LaTeX to test math rendering"""
    
    print("\n🧪 GENERATING LATEX TEST QTI")
    print("=" * 60)
    
    # Test question with LaTeX
    latex_question = {
        "id": "Q_00001",
        "type": "multiple_choice",
        "title": "LaTeX Test",
        "question_text": "What is the result of $2 + 2$?",
        "choices": ["$3$", "$4$", "$5$", "$6$"],
        "correct_answer": "$4$",
        "points": 1,
        "tolerance": 0.05,
        "feedback_correct": "Correct! $2 + 2 = 4$",
        "feedback_incorrect": "Remember: $2 + 2 = 4$",
        "image_file": [],
        "topic": "Math",
        "subtopic": "Addition",
        "difficulty": "Easy"
    }
    
    try:
        from exporter import CanvasLaTeXQTIGenerator
        
        generator = CanvasLaTeXQTIGenerator()
        qti_package = generator.create_qti_package([latex_question], "LaTeX_Test")
        
        if qti_package:
            output_filename = f"latex_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with open(output_filename, 'wb') as f:
                f.write(qti_package)
            
            print(f"✅ LaTeX QTI created: {output_filename}")
            print(f"📊 Package size: {len(qti_package):,} bytes")
            print(f"📋 Contains: 1 question with simple LaTeX")
            return output_filename, qti_package
        else:
            print("❌ Failed to create LaTeX QTI")
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating LaTeX QTI: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None

def generate_controlled_test_qti():
    """Generate QTI from the exact controlled test that's failing"""
    
    print("\n🧪 GENERATING CONTROLLED TEST QTI")
    print("=" * 60)
    
    try:
        test_data = load_controlled_test_json()
        questions = test_data["questions"]
        
        print(f"📋 Loaded {len(questions)} questions from controlled test")
        
        from exporter import CanvasLaTeXQTIGenerator
        
        generator = CanvasLaTeXQTIGenerator()
        qti_package = generator.create_qti_package(questions, "Controlled_Test")
        
        if qti_package:
            output_filename = f"controlled_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with open(output_filename, 'wb') as f:
                f.write(qti_package)
            
            print(f"✅ Controlled test QTI created: {output_filename}")
            print(f"📊 Package size: {len(qti_package):,} bytes")
            print(f"📋 Contains: {len(questions)} questions with complex LaTeX")
            return output_filename, qti_package
        else:
            print("❌ Failed to create controlled test QTI")
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating controlled test QTI: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None

def analyze_qti_xml_structure(qti_file):
    """Analyze the XML structure for Canvas compatibility issues"""
    
    print(f"\n🔍 ANALYZING QTI XML STRUCTURE: {qti_file}")
    print("=" * 60)
    
    import zipfile
    import xml.etree.ElementTree as ET
    
    try:
        with zipfile.ZipFile(qti_file, 'r') as zipf:
            # Find the main XML file
            xml_files = [f for f in zipf.namelist() if f.endswith('.xml') and not f.startswith('ims')]
            
            if not xml_files:
                print("❌ No main QTI XML file found")
                return
            
            main_xml = xml_files[0]
            print(f"📄 Analyzing: {main_xml}")
            
            xml_content = zipf.read(main_xml).decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            print(f"📊 XML Structure Analysis:")
            print(f"   Root element: {root.tag}")
            print(f"   Namespace: {root.get('xmlns', 'None')}")
            
            # Find assessments
            assessments = root.findall('.//assessment')
            print(f"   Assessments found: {len(assessments)}")
            
            # Find items (questions)
            items = root.findall('.//item')
            print(f"   Questions found: {len(items)}")
            
            # Check for common Canvas issues
            canvas_issues = []
            
            # Check for missing required attributes
            for item in items:
                if not item.get('ident'):
                    canvas_issues.append("Missing 'ident' attribute on item")
                if not item.get('title'):
                    canvas_issues.append("Missing 'title' attribute on item")
            
            # Check for response types
            response_types = []
            for response in root.findall('.//response_lid'):
                response_types.append('multiple_choice')
            for response in root.findall('.//response_num'):
                response_types.append('numerical')
            for response in root.findall('.//response_str'):
                response_types.append('fill_in_blank')
            
            print(f"   Response types: {set(response_types)}")
            
            # Check for LaTeX content
            latex_count = 0
            for mattext in root.findall('.//mattext'):
                if mattext.text and ('$' in mattext.text or '\\(' in mattext.text):
                    latex_count += 1
            
            print(f"   LaTeX elements: {latex_count}")
            
            # Report issues
            if canvas_issues:
                print(f"\n⚠️  POTENTIAL CANVAS ISSUES FOUND:")
                for issue in set(canvas_issues):
                    print(f"   - {issue}")
            else:
                print(f"\n✅ No obvious Canvas compatibility issues found")
            
            # Show sample XML snippet
            print(f"\n📝 SAMPLE XML (first 500 chars):")
            print(xml_content[:500])
            print("...")
            
    except Exception as e:
        print(f"❌ Error analyzing XML: {e}")
        import traceback
        print(traceback.format_exc())

def run_canvas_diagnostics():
    """Run complete Canvas compatibility diagnostics"""
    
    print("🚀 CANVAS COMPATIBILITY DIAGNOSTICS")
    print("=" * 80)
    print(f"📅 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Minimal QTI
    minimal_file, minimal_package = generate_minimal_test_qti()
    if minimal_file:
        analyze_qti_xml_structure(minimal_file)
    
    # Test 2: LaTeX QTI
    latex_file, latex_package = generate_latex_test_qti()
    if latex_file:
        analyze_qti_xml_structure(latex_file)
    
    # Test 3: Controlled test QTI
    controlled_file, controlled_package = generate_controlled_test_qti()
    if controlled_file:
        analyze_qti_xml_structure(controlled_file)
    
    # Summary and recommendations
    print(f"\n🎯 CANVAS TESTING STRATEGY:")
    print(f"1. Import {minimal_file if minimal_file else 'minimal_test_*.zip'} first")
    print(f"   - This tests basic QTI compatibility")
    print(f"   - Should import with NO errors")
    print()
    print(f"2. Import {latex_file if latex_file else 'latex_test_*.zip'} second")
    print(f"   - This tests LaTeX math rendering")
    print(f"   - May show LaTeX-related warnings")
    print()
    print(f"3. Import {controlled_file if controlled_file else 'controlled_test_*.zip'} third")
    print(f"   - This tests complex LaTeX (your failing case)")
    print(f"   - Will show the exact error you're experiencing")
    print()
    print(f"📋 DIAGNOSIS STEPS:")
    print(f"A. If minimal test FAILS → Basic QTI structure issue")
    print(f"B. If minimal test PASSES but LaTeX test FAILS → LaTeX conversion issue")
    print(f"C. If LaTeX test PASSES but controlled test FAILS → Complex LaTeX issue")
    print()
    print(f"💡 COMMON CANVAS QTI ISSUES:")
    print(f"- Invalid XML structure or namespaces")
    print(f"- Missing required QTI attributes")
    print(f"- Malformed LaTeX expressions")
    print(f"- Incorrect response processing logic")
    print(f"- Character encoding problems")

if __name__ == "__main__":
    run_canvas_diagnostics()
