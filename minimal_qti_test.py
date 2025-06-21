#!/usr/bin/env python3
"""
Minimal QTI Test Generator
Create ultra-simple QTI packages to isolate what causes Canvas "1 issues"
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import io
from datetime import datetime

def create_minimal_qti_test():
    """Create the absolute minimal QTI package that should work in Canvas"""
    
    # Minimal question data
    minimal_question = {
        "type": "multiple_choice",
        "title": "Simple Test Question",
        "question_text": "What is 2 + 2?",
        "choices": ["3", "4", "5", "6"],
        "correct_answer": "4",
        "points": 1
    }
    
    package_name = "Minimal_Test"
    qti_xml = generate_minimal_qti_xml([minimal_question], package_name)
    manifest_xml = generate_minimal_manifest_xml(package_name)
    
    # Create ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"{package_name}.xml", qti_xml)
        zipf.writestr("imsmanifest.xml", manifest_xml)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def create_latex_qti_test():
    """Create QTI with just LaTeX content to test math rendering"""
    
    # LaTeX-heavy question
    latex_question = {
        "type": "multiple_choice", 
        "title": "LaTeX Math Test",
        "question_text": "What is the impedance $Z$ for a circuit with $R = 100\\,\\Omega$?",
        "choices": [
            "$Z = 100\\,\\Omega$",
            "$Z = 200\\,\\Omega$", 
            "$Z = 50\\,\\Omega$",
            "$Z = 150\\,\\Omega$"
        ],
        "correct_answer": "$Z = 100\\,\\Omega$",
        "points": 1
    }
    
    package_name = "LaTeX_Test"
    qti_xml = generate_latex_qti_xml([latex_question], package_name)
    manifest_xml = generate_minimal_manifest_xml(package_name)
    
    # Create ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"{package_name}.xml", qti_xml)
        zipf.writestr("imsmanifest.xml", manifest_xml)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def generate_minimal_qti_xml(questions, package_name):
    """Generate absolute minimal QTI XML"""
    
    # Minimal QTI structure
    qti_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <assessment ident="assessment_{package_name}" title="{package_name}">
    <qtimetadata>
      <qtimetadatafield>
        <fieldlabel>cc_profile</fieldlabel>
        <fieldentry>cc.exam.v0p1</fieldentry>
      </qtimetadatafield>
    </qtimetadata>
    <section ident="root_section">
      <item ident="question_1" title="{questions[0]['title']}">
        <itemmetadata>
          <qtimetadata>
            <qtimetadatafield>
              <fieldlabel>question_type</fieldlabel>
              <fieldentry>multiple_choice_question</fieldentry>
            </qtimetadatafield>
            <qtimetadatafield>
              <fieldlabel>points_possible</fieldlabel>
              <fieldentry>{questions[0]['points']}</fieldentry>
            </qtimetadatafield>
          </qtimetadata>
        </itemmetadata>
        <presentation>
          <material>
            <mattext texttype="text/html">{questions[0]['question_text']}</mattext>
          </material>
          <response_lid ident="response_1" rcardinality="Single">
            <render_choice>
              <response_label ident="A">
                <material>
                  <mattext texttype="text/html">{questions[0]['choices'][0]}</mattext>
                </material>
              </response_label>
              <response_label ident="B">
                <material>
                  <mattext texttype="text/html">{questions[0]['choices'][1]}</mattext>
                </material>
              </response_label>
              <response_label ident="C">
                <material>
                  <mattext texttype="text/html">{questions[0]['choices'][2]}</mattext>
                </material>
              </response_label>
              <response_label ident="D">
                <material>
                  <mattext texttype="text/html">{questions[0]['choices'][3]}</mattext>
                </material>
              </response_label>
            </render_choice>
          </response_lid>
        </presentation>
        <resprocessing>
          <outcomes>
            <decvar maxvalue="{questions[0]['points']}" minvalue="0" varname="SCORE" vartype="Decimal"/>
          </outcomes>
          <respcondition continue="No">
            <conditionvar>
              <varequal respident="response_1">B</varequal>
            </conditionvar>
            <setvar action="Set" varname="SCORE">{questions[0]['points']}</setvar>
          </respcondition>
        </resprocessing>
      </item>
    </section>
  </assessment>
</questestinterop>'''
    
    return qti_xml

def generate_latex_qti_xml(questions, package_name):
    """Generate QTI XML with Canvas-converted LaTeX"""
    
    # Convert LaTeX for Canvas
    question_text = questions[0]['question_text']
    # Convert $...$ to \\(...\\) for Canvas
    import re
    canvas_question = re.sub(r'\$([^$]+)\$', r'\\(\\1\\)', question_text)
    
    canvas_choices = []
    for choice in questions[0]['choices']:
        canvas_choice = re.sub(r'\$([^$]+)\$', r'\\(\\1\\)', choice)
        canvas_choices.append(canvas_choice)
    
    canvas_correct = re.sub(r'\$([^$]+)\$', r'\\(\\1\\)', questions[0]['correct_answer'])
    
    # Find which choice matches the correct answer
    correct_letter = "A"
    for i, choice in enumerate(canvas_choices):
        if choice == canvas_correct:
            correct_letter = chr(65 + i)
            break
    
    qti_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <assessment ident="assessment_{package_name}" title="{package_name}">
    <qtimetadata>
      <qtimetadatafield>
        <fieldlabel>cc_profile</fieldlabel>
        <fieldentry>cc.exam.v0p1</fieldentry>
      </qtimetadatafield>
    </qtimetadata>
    <section ident="root_section">
      <item ident="question_1" title="{questions[0]['title']}">
        <itemmetadata>
          <qtimetadata>
            <qtimetadatafield>
              <fieldlabel>question_type</fieldlabel>
              <fieldentry>multiple_choice_question</fieldentry>
            </qtimetadatafield>
            <qtimetadatafield>
              <fieldlabel>points_possible</fieldlabel>
              <fieldentry>{questions[0]['points']}</fieldentry>
            </qtimetadatafield>
          </qtimetadata>
        </itemmetadata>
        <presentation>
          <material>
            <mattext texttype="text/html">{canvas_question}</mattext>
          </material>
          <response_lid ident="response_1" rcardinality="Single">
            <render_choice>
              <response_label ident="A">
                <material>
                  <mattext texttype="text/html">{canvas_choices[0]}</mattext>
                </material>
              </response_label>
              <response_label ident="B">
                <material>
                  <mattext texttype="text/html">{canvas_choices[1]}</mattext>
                </material>
              </response_label>
              <response_label ident="C">
                <material>
                  <mattext texttype="text/html">{canvas_choices[2]}</mattext>
                </material>
              </response_label>
              <response_label ident="D">
                <material>
                  <mattext texttype="text/html">{canvas_choices[3]}</mattext>
                </material>
              </response_label>
            </render_choice>
          </response_lid>
        </presentation>
        <resprocessing>
          <outcomes>
            <decvar maxvalue="{questions[0]['points']}" minvalue="0" varname="SCORE" vartype="Decimal"/>
          </outcomes>
          <respcondition continue="No">
            <conditionvar>
              <varequal respident="response_1">{correct_letter}</varequal>
            </conditionvar>
            <setvar action="Set" varname="SCORE">{questions[0]['points']}</setvar>
          </respcondition>
        </resprocessing>
      </item>
    </section>
  </assessment>
</questestinterop>'''
    
    return qti_xml

def generate_minimal_manifest_xml(package_name):
    """Generate minimal IMS manifest"""
    
    manifest_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="manifest_{package_name}" xmlns="http://www.imsglobal.org/xsd/imscp_v1p1">
  <metadata>
    <schema>IMS Content</schema>
    <schemaversion>1.1.3</schemaversion>
  </metadata>
  <organizations default="TOC">
    <organization identifier="TOC">
      <title>{package_name}</title>
    </organization>
  </organizations>
  <resources>
    <resource identifier="resource_{package_name}" type="imsqti_xmlv1p2" href="{package_name}.xml">
      <file href="{package_name}.xml"/>
    </resource>
  </resources>
</manifest>'''
    
    return manifest_xml

def run_minimal_tests():
    """Generate test packages for Canvas import testing"""
    
    print("🧪 Generating Minimal QTI Test Packages")
    print("=" * 50)
    
    # Test 1: Minimal package
    print("📦 Creating minimal test package...")
    minimal_package = create_minimal_qti_test()
    
    minimal_filename = f"minimal_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with open(minimal_filename, 'wb') as f:
        f.write(minimal_package)
    
    print(f"✅ Created: {minimal_filename}")
    print("   📋 Contains: 1 simple question, no LaTeX, minimal structure")
    
    # Test 2: LaTeX package  
    print("\n📦 Creating LaTeX test package...")
    latex_package = create_latex_qti_test()
    
    latex_filename = f"latex_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with open(latex_filename, 'wb') as f:
        f.write(latex_package)
    
    print(f"✅ Created: {latex_filename}")
    print("   📋 Contains: 1 LaTeX question with Canvas-converted delimiters")
    
    print(f"\n🎯 TESTING INSTRUCTIONS:")
    print(f"1. Import {minimal_filename} into Canvas")
    print(f"   - If this shows '1 issues', the problem is basic QTI structure")
    print(f"   - If this imports cleanly, the problem is in our complex content")
    print(f"")
    print(f"2. Import {latex_filename} into Canvas") 
    print(f"   - If this shows '1 issues', the problem is LaTeX conversion")
    print(f"   - If this imports cleanly, the problem is in question quantity/complexity")
    print(f"")
    print(f"3. Compare results with your full web app export")
    print(f"   - This will isolate what specific content causes the issue")
    
    return minimal_filename, latex_filename

if __name__ == "__main__":
    run_minimal_tests()
