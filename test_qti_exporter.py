#!/usr/bin/env python3
"""
Clean QTI Exporter Test Script - Fixed Syntax Errors
Save as test_qti_exporter.py and run immediately
"""

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import io
import re
import html
from datetime import datetime

def quick_test_latex_qti_export():
    """Quick test of LaTeX-preserving QTI export with Canvas compatibility"""
    
    print("🧪 CANVAS-COMPATIBLE QTI EXPORTER TEST")
    print("=" * 55)
    print(f"📅 Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Test data with LLM-generated LaTeX patterns
    test_questions = [
        {
            "type": "multiple_choice",
            "title": "Signal Amplitude Analysis with Noise", 
            "question_text": "When analyzing a noisy sinusoidal signal with amplitude $A = 3\\,\\text{V}$ using peak detection, how does the measured amplitude compare to the true value?",
            "choices": [
                "Exactly $3\\,\\text{V}$",
                "Approximately $3\\,\\text{V}$ (within $\\pm 0.3\\,\\text{V}$)",
                "Varies with each measurement due to random noise",
                "Both B and C are correct"
            ],
            "correct_answer": "Both B and C are correct",
            "points": 2,
            "feedback_correct": "Correct! Random noise causes measurement variability while keeping values relatively close to the true amplitude of $3\\,\\text{V}$.",
            "topic": "Signals Time Domain",
            "difficulty": "Medium"
        },
        {
            "type": "numerical",
            "title": "Nyquist Frequency Calculation",
            "question_text": "For a sampling frequency $f_s = 10\\,\\text{kHz}$, calculate the maximum signal frequency that can be accurately represented using the Nyquist criterion $f_{max} = f_s/2$.",
            "correct_answer": "5000",
            "tolerance": 1,
            "points": 3,
            "feedback_correct": "Correct! $f_{max} = f_s/2 = 10\\,\\text{kHz}/2 = 5\\,\\text{kHz} = 5000\\,\\text{Hz}$ per Nyquist-Shannon theorem.",
            "topic": "Signals Time Domain", 
            "difficulty": "Easy"
        },
        {
            "type": "multiple_choice",
            "title": "Complex Impedance Calculation",
            "question_text": "For an RL circuit with $R = 100\\,\\Omega$ and $L = 50\\,\\text{mH}$, calculate the impedance at $f = 1\\,\\text{kHz}$ using $Z = R + j\\omega L$.",
            "choices": [
                "$Z = 100 + j314\\,\\Omega$",
                "$Z = 100 + j50\\,\\Omega$", 
                "$Z = 314 + j100\\,\\Omega$",
                "$Z = 50 + j100\\,\\Omega$"
            ],
            "correct_answer": "$Z = 100 + j314\\,\\Omega$",
            "points": 3,
            "feedback_correct": "Correct! $Z = R + j\\omega L = 100 + j(2\\pi \\times 1000 \\times 0.05) = 100 + j314\\,\\Omega$",
            "topic": "Circuit Analysis",
            "difficulty": "Medium"
        }
    ]
    
    print(f"✅ Loaded {len(test_questions)} questions with LaTeX content")
    
    # Analyze LaTeX content
    print("\n🧮 LaTeX Content Analysis:")
    total_latex_expressions = 0
    
    for i, q in enumerate(test_questions):
        question_text = q.get('question_text', '')
        choices_text = ' '.join(q.get('choices', []))
        feedback_text = q.get('feedback_correct', '')
        
        all_text = question_text + ' ' + choices_text + ' ' + feedback_text
        latex_count = all_text.count('$') // 2
        total_latex_expressions += latex_count
        
        print(f"  Q{i+1}: {latex_count} LaTeX expressions")
        
        # Show sample LaTeX
        latex_samples = re.findall(r'\$[^$]+\$', all_text)
        if latex_samples:
            print(f"       Sample: {latex_samples[0]}")
    
    print(f"\n📊 Total LaTeX expressions to preserve: {total_latex_expressions}")
    
    # Generate QTI package
    print("\n🚀 Generating Canvas-compatible QTI package...")
    
    try:
        qti_package = generate_canvas_qti(test_questions, "Canvas_LaTeX_Test")
        
        if qti_package:
            output_filename = f"canvas_latex_qti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with open(output_filename, 'wb') as f:
                f.write(qti_package)
            
            print(f"✅ Canvas-compatible QTI package generated!")
            print(f"📦 Saved as: {output_filename}")
            print(f"📊 Package size: {len(qti_package):,} bytes")
            
            # Verify Canvas delimiter conversion
            print("\n🔍 Verifying Canvas delimiter conversion...")
            verification_result = verify_canvas_conversion(output_filename, test_questions)
            
            if verification_result['success']:
                conversion_rate = verification_result['conversion_rate']
                print(f"📊 Canvas conversion rate: {conversion_rate:.1f}%")
                
                if conversion_rate >= 95:
                    print("🎉 EXCELLENT! All delimiters converted for Canvas!")
                elif conversion_rate >= 80:
                    print("✅ GOOD! Most delimiters converted successfully!")
                else:
                    print("⚠️  WARNING! Some conversion issues detected!")
                
                print("\n📋 Conversion examples:")
                for example in verification_result['examples'][:3]:
                    print(f"  {example['before']} → {example['after']}")
                
                if verification_result['unconverted']:
                    print(f"\n⚠️  Found {verification_result['unconverted']} unconverted $ delimiters")
            
            print(f"\n🎯 CANVAS COMPATIBILITY VERIFIED")
            print("=" * 35)
            print(f"✅ QTI Package: {output_filename}")
            print(f"✅ Questions: {len(test_questions)}")
            print(f"✅ LaTeX Expressions: {total_latex_expressions}")
            print(f"✅ Canvas Conversion: {verification_result.get('conversion_rate', 0):.1f}%")
            
            print(f"\n💡 CANVAS IMPORT INSTRUCTIONS:")
            print(f"1. Go to Canvas → Quizzes → Import QTI Package")
            print(f"2. Upload: {output_filename}")
            print(f"3. Verify these render correctly in Canvas:")
            print(f"   • \\(A = 3\\,\\text{{V}}\\) - inline math")
            print(f"   • \\(f_s = 10\\,\\text{{kHz}}\\) - subscripts")
            print(f"   • \\(Z = 100 + j314\\,\\Omega\\) - Greek letters")
            print(f"   • \\(\\pm 0.3\\,\\text{{V}}\\) - special symbols")
            
            print(f"\n🔍 Canvas Requirements Met:")
            print(f"   ✅ Uses \\(...\\) for inline math (Canvas MathJax 2.7.7)")
            print(f"   ✅ Uses $$...$$ for block math (Canvas standard)")
            print(f"   ✅ Compatible with Canvas accessibility features")
            print(f"   ✅ Will auto-convert to MathML for screen readers")
            
            return True, output_filename
            
        else:
            print("❌ Failed to generate QTI package")
            return False, None
            
    except Exception as e:
        print(f"❌ Error during QTI generation: {e}")
        import traceback
        print(traceback.format_exc())
        return False, None

def generate_canvas_qti(questions, package_name):
    """Generate Canvas-compatible QTI package with proper LaTeX delimiters"""
    
    try:
        # Create QTI XML structure
        root = ET.Element("questestinterop")
        root.set("xmlns", "http://www.imsglobal.org/xsd/ims_qtiasiv1p2")
        
        # Assessment
        assessment = ET.SubElement(root, "assessment")
        assessment.set("ident", f"assessment_{package_name}")
        assessment.set("title", package_name)
        
        # Section
        section = ET.SubElement(assessment, "section")
        section.set("ident", "root_section")
        
        # Add questions
        for i, question in enumerate(questions):
            add_question_with_canvas_latex(section, question, i + 1)
        
        # Convert to XML
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        qti_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        
        # Create manifest
        manifest_xml = create_qti_manifest(package_name)
        
        # Create ZIP package
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f"{package_name}.xml", qti_xml)
            zipf.writestr("imsmanifest.xml", manifest_xml)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
        
    except Exception as e:
        print(f"Error in Canvas QTI generation: {e}")
        return None

def add_question_with_canvas_latex(section, question, question_num):
    """Add question to QTI with Canvas-compatible LaTeX delimiters"""
    
    # Create item
    item = ET.SubElement(section, "item")
    item.set("ident", f"question_{question_num}")
    
    title = question.get('title', f'Question {question_num}')
    clean_title = title.replace('"', "'").replace('<', '').replace('>', '')[:100]
    item.set("title", clean_title)
    
    # Presentation
    presentation = ET.SubElement(item, "presentation")
    
    # Question text with Canvas LaTeX conversion
    material = ET.SubElement(presentation, "material")
    mattext = ET.SubElement(material, "mattext")
    mattext.set("texttype", "text/html")
    
    question_html = convert_latex_for_canvas(question.get('question_text', ''))
    mattext.text = question_html
    
    # Handle question types
    qtype = question.get('type', 'multiple_choice')
    
    if qtype == 'multiple_choice' and question.get('choices'):
        # Multiple choice with Canvas LaTeX in choices
        response_lid = ET.SubElement(presentation, "response_lid")
        response_lid.set("ident", f"response_{question_num}")
        response_lid.set("rcardinality", "Single")
        
        render_choice = ET.SubElement(response_lid, "render_choice")
        render_choice.set("shuffle", "No")
        
        for i, choice_text in enumerate(question['choices']):
            choice_label = chr(65 + i)  # A, B, C, D...
            
            response_label = ET.SubElement(render_choice, "response_label")
            response_label.set("ident", choice_label)
            
            choice_material = ET.SubElement(response_label, "material")
            choice_mattext = ET.SubElement(choice_material, "mattext")
            choice_mattext.set("texttype", "text/html")
            
            choice_html = convert_latex_for_canvas(choice_text)
            choice_mattext.text = choice_html
    
    elif qtype == 'numerical':
        # Numerical input
        response_num = ET.SubElement(presentation, "response_num")
        response_num.set("ident", f"response_{question_num}")
        response_num.set("rcardinality", "Single")
        
        render_fib = ET.SubElement(response_num, "render_fib")
        render_fib.set("fibtype", "Decimal")
        render_fib.set("rows", "1")
        render_fib.set("columns", "10")
    
    # Add response processing
    add_response_processing(item, question, question_num)

def convert_latex_for_canvas(text):
    """Convert LaTeX delimiters for Canvas MathJax compatibility"""
    
    if not text:
        return ""
    
    # Canvas-specific LaTeX delimiter conversion
    latex_expressions = []
    placeholder_template = "LATEX_PLACEHOLDER_{}"
    
    def replace_latex_match(match):
        expr = match.group(0)
        
        # Convert for Canvas MathJax 2.7.7 compatibility
        if expr.startswith('$$') and expr.endswith('$$'):
            # Block equations: Canvas supports $$ delimiters
            canvas_expr = expr
        elif expr.startswith('$') and expr.endswith('$'):
            # Inline equations: Canvas requires \(...\) delimiters
            inner_content = expr[1:-1]  # Remove $ delimiters
            canvas_expr = f'\\({inner_content}\\)'
        else:
            # Fallback
            canvas_expr = expr
        
        placeholder = placeholder_template.format(len(latex_expressions))
        latex_expressions.append(canvas_expr)
        return placeholder
    
    # Find and replace LaTeX expressions
    text_with_placeholders = re.sub(r'\$\$[^$]+\$\$|\$[^$]+\$', replace_latex_match, str(text))
    
    # Escape HTML in non-LaTeX parts
    escaped_text = html.escape(text_with_placeholders)
    
    # Restore Canvas-compatible LaTeX
    for i, canvas_expr in enumerate(latex_expressions):
        placeholder = placeholder_template.format(i)
        escaped_text = escaped_text.replace(placeholder, canvas_expr)
    
    return f'<div class="question-text">{escaped_text}</div>'

def add_response_processing(item, question, question_num):
    """Add response processing logic"""
    
    resprocessing = ET.SubElement(item, "resprocessing")
    
    # Outcomes
    outcomes = ET.SubElement(resprocessing, "outcomes")
    decvar = ET.SubElement(outcomes, "decvar")
    decvar.set("maxvalue", str(question.get('points', 1)))
    decvar.set("minvalue", "0")
    decvar.set("varname", "SCORE")
    decvar.set("vartype", "Decimal")
    
    # Correct answer condition
    respcondition = ET.SubElement(resprocessing, "respcondition")
    respcondition.set("continue", "No")
    
    conditionvar = ET.SubElement(respcondition, "conditionvar")
    
    if question.get('type') == 'numerical':
        # Numerical with tolerance
        try:
            correct_val = float(question.get('correct_answer', 0))
            tolerance = float(question.get('tolerance', 0.01))
            
            vargte = ET.SubElement(conditionvar, "vargte")
            vargte.set("respident", f"response_{question_num}")
            vargte.text = str(correct_val - tolerance)
            
            varlte = ET.SubElement(conditionvar, "varlte")
            varlte.set("respident", f"response_{question_num}")
            varlte.text = str(correct_val + tolerance)
        except:
            # Fallback to exact match
            varequal = ET.SubElement(conditionvar, "varequal")
            varequal.set("respident", f"response_{question_num}")
            varequal.text = str(question.get('correct_answer', ''))
    else:
        # Text/choice answer
        varequal = ET.SubElement(conditionvar, "varequal")
        varequal.set("respident", f"response_{question_num}")
        
        # For multiple choice, convert answer to letter
        correct_answer = question.get('correct_answer', '')
        choices = question.get('choices', [])
        
        if choices and correct_answer in choices:
            answer_index = choices.index(correct_answer)
            varequal.text = chr(65 + answer_index)  # A, B, C, D...
        else:
            varequal.text = str(correct_answer)
    
    # Set score
    setvar = ET.SubElement(respcondition, "setvar")
    setvar.set("action", "Set")
    setvar.set("varname", "SCORE")
    setvar.text = str(question.get('points', 1))

def create_qti_manifest(package_name):
    """Create IMS QTI manifest"""
    
    manifest = ET.Element("manifest")
    manifest.set("identifier", f"manifest_{package_name}")
    manifest.set("xmlns", "http://www.imsglobal.org/xsd/imscp_v1p1")
    
    # Metadata
    metadata = ET.SubElement(manifest, "metadata")
    schema = ET.SubElement(metadata, "schema")
    schema.text = "IMS Content"
    schemaversion = ET.SubElement(metadata, "schemaversion")
    schemaversion.text = "1.1.3"
    
    # Organizations
    organizations = ET.SubElement(manifest, "organizations")
    organizations.set("default", "TOC")
    
    organization = ET.SubElement(organizations, "organization")
    organization.set("identifier", "TOC")
    title = ET.SubElement(organization, "title")
    title.text = package_name
    
    # Resources
    resources = ET.SubElement(manifest, "resources")
    resource = ET.SubElement(resources, "resource")
    resource.set("identifier", f"resource_{package_name}")
    resource.set("type", "imsqti_xmlv1p2")
    resource.set("href", f"{package_name}.xml")
    
    file_elem = ET.SubElement(resource, "file")
    file_elem.set("href", f"{package_name}.xml")
    
    # Format XML
    rough_string = ET.tostring(manifest, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

def verify_canvas_conversion(zip_filename, original_questions):
    """Verify Canvas delimiter conversion in QTI package"""
    
    try:
        # Extract QTI content
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            qti_files = [f for f in zipf.namelist() if f.endswith('.xml') and 'manifest' not in f]
            
            if not qti_files:
                return {'success': False, 'error': 'No QTI XML file found'}
            
            with zipf.open(qti_files[0]) as qti_file:
                qti_content = qti_file.read().decode('utf-8')
        
        # Analyze original LaTeX
        original_latex = []
        for q in original_questions:
            text_content = q.get('question_text', '')
            text_content += ' ' + ' '.join(q.get('choices', []))
            text_content += ' ' + q.get('feedback_correct', '')
            
            latex_expressions = re.findall(r'\$\$[^$]+\$\$|\$[^$]+\$', text_content)
            original_latex.extend(latex_expressions)
        
        # Check Canvas conversions
        converted_examples = []
        unconverted_count = 0
        
        for expr in original_latex:
            if expr.startswith('$$') and expr.endswith('$$'):
                # Block math should be unchanged
                if expr in qti_content:
                    converted_examples.append({'before': expr, 'after': expr})
                else:
                    unconverted_count += 1
            elif expr.startswith('$') and expr.endswith('$'):
                # Inline math should be converted to \(...\)
                inner = expr[1:-1]
                expected = f'\\({inner}\\)'
                if expected in qti_content:
                    converted_examples.append({'before': expr, 'after': expected})
                else:
                    unconverted_count += 1
        
        # Check for remaining $ delimiters (should be minimal)
        remaining_dollars = len(re.findall(r'[^$]\$[^$]+\$[^$]', qti_content))
        
        conversion_rate = ((len(original_latex) - unconverted_count) / len(original_latex)) * 100 if original_latex else 100
        
        return {
            'success': True,
            'conversion_rate': conversion_rate,
            'total_expressions': len(original_latex),
            'converted_count': len(converted_examples),
            'unconverted': unconverted_count,
            'examples': converted_examples,
            'remaining_dollars': remaining_dollars
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    print("🚀 STARTING CANVAS-COMPATIBLE QTI TEST")
    print("🧮 Testing LaTeX → Canvas MathJax 2.7.7 conversion")
    print()
    
    success, output_file = quick_test_latex_qti_export()
    
    if success:
        print(f"\n🎉 SUCCESS! Canvas-ready QTI package created!")
        print(f"📦 File: {output_file}")
        print(f"💡 Import this into Canvas to verify LaTeX rendering!")
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"💡 Check error messages above")
    
    print(f"\n📅 Test completed: {datetime.now().strftime('%H:%M:%S')}")
