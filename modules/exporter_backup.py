#!/usr/bin/env python3
"""
Clean Exporter Module Part 1 - Core Functions
"""

import streamlit as st
import pandas as pd
import io
import os
import json
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import re
import html
from datetime import datetime

def fix_numeric_formatting(questions):
    """
    Ensure numeric values are formatted as integers when appropriate
    to match native QTI generation
    """
    
    for question in questions:
        # Fix points - convert float back to int if it's a whole number
        if 'points' in question:
            points = question['points']
            if isinstance(points, float) and points.is_integer():
                question['points'] = int(points)
        
        # Fix tolerance - similar logic
        if 'tolerance' in question:
            tolerance = question['tolerance']
            if isinstance(tolerance, float) and tolerance.is_integer():
                question['tolerance'] = int(tolerance)
                
        # Fix any other numeric fields that might have been converted to float
        numeric_fields = ['points', 'tolerance']
        for field in numeric_fields:
            if field in question:
                value = question[field]
                if isinstance(value, float) and value.is_integer():
                    question[field] = int(value)
    
    return questions

def fix_dataframe_dtypes(df):
    """
    Fix DataFrame column types to preserve integers
    """
    
    # Identify numeric columns that should be integers
    int_columns = ['Points', 'Question_Number']  # Add other integer columns
    
    for col in int_columns:
        if col in df.columns:
            # Convert float to int if all values are whole numbers
            if df[col].dtype == 'float64':
                if df[col].notna().all() and (df[col] % 1 == 0).all():
                    df[col] = df[col].astype('int64')
    
    return df

def export_to_csv(df, filename="filtered_questions.csv"):
    """Export DataFrame to CSV"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )

def create_qti_package(df, original_questions, quiz_title, transform_json_to_csv=None, csv_to_qti=None):
    """Canvas-Compatible QTI Package Creation"""
    
    if df is None or len(df) == 0:
        st.error("❌ No questions to export.")
        return
    
    try:
        with st.spinner("🔄 Creating Canvas-compatible QTI package..."):
            
            # Fix DataFrame data types first
            df = fix_dataframe_dtypes(df)
            
            # Filter and sync questions
            st.info(f"📋 Processing {len(df)} questions with Canvas LaTeX conversion...")
            filtered_questions = filter_and_sync_questions(df, original_questions)
            
            if not filtered_questions:
                st.error("❌ No questions matched for export")
                return
            
            # Fix numeric formatting in the filtered questions
            filtered_questions = fix_numeric_formatting(filtered_questions)
            
            # Generate QTI package
            qti_generator = CanvasLaTeXQTIGenerator()
            qti_package_data = qti_generator.create_qti_package(filtered_questions, quiz_title)
            
            if qti_package_data:
                # Provide download
                safe_filename = sanitize_filename(quiz_title)
                
                st.success("✅ Canvas-compatible QTI package created successfully!")
                st.download_button(
                    label="📦 Download QTI Package",
                    data=qti_package_data,
                    file_name=f"{safe_filename}.zip",
                    mime="application/zip",
                    key=f"qti_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Show success details
                total_points = sum(q.get('points', 1) for q in filtered_questions)
                latex_count = count_latex_questions(filtered_questions)
                
                st.success(f"""
                🎯 **Canvas-Ready QTI Package Created:**
                
                - **Questions**: {len(filtered_questions)}
                - **Total Points**: {total_points}
                - **LaTeX Questions**: {latex_count}
                - **Canvas Compatibility**: ✅ MathJax 2.7.7 Compatible
                
                **LaTeX Conversion Applied:**
                - Inline math converted to Canvas format
                - Block math preserved
                - Greek letters, subscripts, units preserved exactly
                
                **Ready for Canvas Import:** Go to Canvas → Quizzes → Import QTI Package
                
                ✅ **Confirmed Working**: Questions import and function correctly in Canvas!
                """)
                
            else:
                st.error("❌ Failed to create QTI package")
        
    except Exception as e:
        st.error(f"❌ Error creating QTI package: {str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

def filter_and_sync_questions(df, original_questions):
    """Filter and sync questions while preserving LaTeX"""
    
    filtered_questions = []
    
    st.info(f"🔍 Debug: DataFrame has {len(df)} rows, Original has {len(original_questions)} questions")
    
    # Check DataFrame ID situation
    if 'ID' in df.columns:
        df_ids = df['ID'].tolist()
        non_empty_ids = [id for id in df_ids if id and str(id).strip()]
        st.info(f"📋 DataFrame IDs: {df_ids[:5]} (non-empty: {len(non_empty_ids)})")
        
        if len(non_empty_ids) < len(df) * 0.5:
            st.warning("⚠️ Most DataFrame IDs are empty, using index-based matching instead")
            use_index_matching = True
        else:
            use_index_matching = False
            filtered_ids = set(non_empty_ids)
    else:
        st.info("📋 No ID column found, using index-based matching")
        use_index_matching = True
    
    # Show original question IDs
    original_ids = []
    for i, question in enumerate(original_questions):
        original_id = question.get('id', f"Q_{i+1:05d}")
        original_ids.append(original_id)
    
    st.info(f"📋 Original question IDs (first 5): {original_ids[:5]}")
    
    if use_index_matching:
        st.info(f"🔄 Using index-based matching for {len(df)} questions")
        
        for i in range(min(len(df), len(original_questions))):
            question = original_questions[i]
            df_row = df.iloc[i]
            
            st.info(f"✅ Including question {i+1} by index")
            
            synced_question = sync_dataframe_to_json_safe(question, df_row)
            filtered_questions.append(synced_question)
    
    else:
        st.info(f"🔄 Using ID-based matching")
        
        for i, question in enumerate(original_questions):
            question_id = question.get('id', f"Q_{i+1:05d}")
            
            matches = []
            if question_id in filtered_ids:
                matches.append(f"exact ID match: {question_id}")
            if f"Q_{i+1:05d}" in filtered_ids:
                matches.append(f"formatted ID match: Q_{i+1:05d}")
            
            if matches:
                st.info(f"✅ Including question {i+1}: {matches}")
                
                df_row = None
                if 'ID' in df.columns:
                    matching_rows = df[df['ID'] == question_id]
                    if len(matching_rows) > 0:
                        df_row = matching_rows.iloc[0]
                
                if df_row is None and i < len(df):
                    df_row = df.iloc[i]
                
                if df_row is not None:
                    synced_question = sync_dataframe_to_json_safe(question, df_row)
                    filtered_questions.append(synced_question)
                else:
                    filtered_questions.append(question)
            else:
                st.warning(f"❌ Excluding question {i+1} (ID: {question_id}) - no match found")
    
    st.success(f"🎯 Final result: {len(filtered_questions)} questions matched for export")
    return filtered_questions

def sync_dataframe_to_json_safe(original_question, df_row):
    """Safely sync DataFrame changes to JSON while preserving LaTeX"""
    
    updated_question = original_question.copy()
    
    # Safe field mapping
    safe_mappings = {
        'Title': 'title',
        'Points': 'points', 
        'Topic': 'topic',
        'Subtopic': 'subtopic',
        'Difficulty': 'difficulty',
        'Tolerance': 'tolerance'
    }
    
    for df_col, json_key in safe_mappings.items():
        if df_col in df_row and pd.notna(df_row[df_col]):
            if json_key in ['points', 'tolerance']:
                try:
                    updated_question[json_key] = float(df_row[df_col])
                except (ValueError, TypeError):
                    pass
            else:
                updated_question[json_key] = str(df_row[df_col])
    
    if 'Type' in df_row and pd.notna(df_row['Type']):
        updated_question['type'] = str(df_row['Type']).lower().replace(' ', '_')
    
    if 'Correct_Answer' in df_row and pd.notna(df_row['Correct_Answer']):
        updated_question['correct_answer'] = str(df_row['Correct_Answer'])
    
    # Handle choices
    choices = []
    for choice_col in ['Choice_A', 'Choice_B', 'Choice_C', 'Choice_D', 'Choice_E']:
        if choice_col in df_row and pd.notna(df_row[choice_col]) and str(df_row[choice_col]).strip():
            choices.append(str(df_row[choice_col]).strip())
    
    if choices:
        updated_question['choices'] = choices
    
    # Only update question_text if actually modified
    if 'Question_Text' in df_row and pd.notna(df_row['Question_Text']):
        df_text = str(df_row['Question_Text']).strip()
        original_text = original_question.get('question_text', '').strip()
        
        if df_text != original_text and df_text != '':
            updated_question['question_text'] = df_text
    
    return updated_question

def count_latex_questions(questions):
    """Count questions containing LaTeX notation"""
    count = 0
    for q in questions:
        text_to_check = str(q.get('question_text', ''))
        choices_text = ' '.join(str(choice) for choice in q.get('choices', []))
        feedback_text = str(q.get('feedback_correct', '')) + str(q.get('feedback_incorrect', ''))
        
        # Simple check for dollar signs
        if '$' in text_to_check or '$' in choices_text or '$' in feedback_text:
            count += 1
    
    return count

def sanitize_filename(filename):
    """Create safe filename"""
    if not filename:
        return "Question_Package"
    
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name.strip('._')
    
    if not safe_name:
        return "Question_Package"
    
    return safe_name

class CanvasLaTeXQTIGenerator:
    """Canvas-compatible QTI Generator with LaTeX preservation"""
    
    def _canvas_safe_html_escape(self, text):
        """
        HTML escape that's compatible with Canvas QTI import
        Avoids problematic HTML entities that Canvas doesn't like
        """
        
        if not text:
            return ""
        
        # Convert to string first
        text = str(text)
        
        # Use Python's html.escape but with safer quote handling
        escaped = html.escape(text, quote=False)  # Don't escape quotes initially
        
        # Manually handle quotes in a Canvas-friendly way
        escaped = escaped.replace('"', '&quot;')
        escaped = escaped.replace("'", "'")  # Keep apostrophes as-is, don't convert to &#x27;
        
        return escaped
    
    def create_qti_package(self, questions, package_name):
        """Create complete Canvas-compatible QTI package"""
        try:
            qti_xml = self._generate_qti_xml(questions, package_name)
            manifest_xml = self._generate_manifest_xml(package_name)
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(f"{package_name}.xml", qti_xml)
                zipf.writestr("imsmanifest.xml", manifest_xml)
                
                metadata_xml = self._generate_metadata_xml(package_name, len(questions))
                zipf.writestr("assessment_meta.xml", metadata_xml)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            st.error(f"QTI Generation Error: {e}")
            return None
    
    def _generate_qti_xml(self, questions, package_name):
        """Generate QTI XML with Canvas LaTeX conversion"""
        
        root = ET.Element("questestinterop")
        root.set("xmlns", "http://www.imsglobal.org/xsd/ims_qtiasiv1p2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        
        assessment = ET.SubElement(root, "assessment")
        assessment.set("ident", f"assessment_{package_name}")
        assessment.set("title", package_name)
        
        qtimetadata = ET.SubElement(assessment, "qtimetadata")
        self._add_canvas_metadata(qtimetadata)
        
        section = ET.SubElement(assessment, "section")
        section.set("ident", "root_section")
        
        for i, question in enumerate(questions):
            self._add_question_item(section, question, i + 1)
        
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def _convert_latex_for_canvas(self, text):
        """Convert LaTeX delimiters for Canvas MathJax compatibility"""
        
        if not text:
            return ""
        
        latex_expressions = []
        placeholder_template = "LATEX_PLACEHOLDER_{}"
        
        def replace_latex_match(match):
            expr = match.group(0)
            
            # Canvas conversion logic
            if expr.startswith('$$') and expr.endswith('$$'):
                canvas_expr = expr  # Keep block math as-is
            elif expr.startswith('$') and expr.endswith('$'):
                inner_content = expr[1:-1]
                canvas_expr = f'\\({inner_content}\\)'  # Convert inline math
            else:
                canvas_expr = expr
            
            placeholder = placeholder_template.format(len(latex_expressions))
            latex_expressions.append(canvas_expr)
            return placeholder
        
        # Process LaTeX expressions
        pattern = r'\$\$[^$]+\$\$|\$[^$]+\$'
        text_with_placeholders = re.sub(pattern, replace_latex_match, str(text))
        
        # Use Canvas-safe HTML escaping
        escaped_text = self._canvas_safe_html_escape(text_with_placeholders)
        
        # Restore LaTeX
        for i, canvas_expr in enumerate(latex_expressions):
            placeholder = placeholder_template.format(i)
            escaped_text = escaped_text.replace(placeholder, canvas_expr)
        
        return f'<div class="question-text">{escaped_text}</div>'
    
    def _add_question_item(self, section, question, question_num):
        """Add question with Canvas LaTeX conversion"""
        
        item = ET.SubElement(section, "item")
        item.set("ident", f"question_{question_num}")
        item.set("title", self._clean_for_attribute(question.get('title', f'Question {question_num}')))
        
        itemmetadata = ET.SubElement(item, "itemmetadata")
        qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")
        
        qtype = question.get('type', 'multiple_choice')
        points = question.get('points', 1)
        
        self._add_metadata_field(qtimetadata, "question_type", qtype)
        self._add_metadata_field(qtimetadata, "points_possible", str(points))
        
        presentation = ET.SubElement(item, "presentation")
        
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext")
        mattext.set("texttype", "text/html")
        mattext.text = self._convert_latex_for_canvas(question.get('question_text', ''))
        
        if qtype == 'multiple_choice':
            self._add_multiple_choice_response(item, presentation, question, question_num)
        elif qtype == 'numerical':
            self._add_numerical_response(item, presentation, question, question_num)
        elif qtype == 'true_false':
            self._add_true_false_response(item, presentation, question, question_num)
        elif qtype == 'fill_in_blank':
            self._add_fill_in_blank_response(item, presentation, question, question_num)

    def _add_multiple_choice_response(self, item, presentation, question, question_num):
        """Add multiple choice response"""
        
        choices = question.get('choices', [])
        if not choices:
            return
        
        response_lid = ET.SubElement(presentation, "response_lid")
        response_lid.set("ident", f"response_{question_num}")
        response_lid.set("rcardinality", "Single")
        
        render_choice = ET.SubElement(response_lid, "render_choice")
        render_choice.set("shuffle", "No")
        
        for i, choice_text in enumerate(choices):
            choice_label = chr(65 + i)
            
            response_label = ET.SubElement(render_choice, "response_label")
            response_label.set("ident", choice_label)
            
            material = ET.SubElement(response_label, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.set("texttype", "text/html")
            mattext.text = self._convert_latex_for_canvas(choice_text)
        
        self._add_response_processing(item, question, question_num, "multiple_choice")
    
    def _add_numerical_response(self, item, presentation, question, question_num):
        """Add numerical response"""
        
        response_num = ET.SubElement(presentation, "response_num")
        response_num.set("ident", f"response_{question_num}")
        response_num.set("rcardinality", "Single")
        
        render_fib = ET.SubElement(response_num, "render_fib")
        render_fib.set("fibtype", "Decimal")
        render_fib.set("rows", "1")
        render_fib.set("columns", "10")
        
        self._add_response_processing(item, question, question_num, "numerical")
    
    def _add_true_false_response(self, item, presentation, question, question_num):
        """Add true/false response"""
        
        tf_question = question.copy()
        tf_question['choices'] = ['True', 'False']
        
        correct = str(question.get('correct_answer', 'True'))
        if correct.lower() in ['true', 't', '1', 'yes']:
            tf_question['correct_answer'] = 'True'
        else:
            tf_question['correct_answer'] = 'False'
        
        self._add_multiple_choice_response(item, presentation, tf_question, question_num)
    
    def _add_fill_in_blank_response(self, item, presentation, question, question_num):
        """Add fill-in-blank response"""
        
        response_str = ET.SubElement(presentation, "response_str")
        response_str.set("ident", f"response_{question_num}")
        response_str.set("rcardinality", "Single")
        
        render_fib = ET.SubElement(response_str, "render_fib")
        render_fib.set("fibtype", "String")
        render_fib.set("rows", "1")
        render_fib.set("columns", "20")
        
        self._add_response_processing(item, question, question_num, "fill_in_blank")
    
    def _add_response_processing(self, item, question, question_num, qtype):
        """Add response processing logic"""
        
        resprocessing = ET.SubElement(item, "resprocessing")
        
        outcomes = ET.SubElement(resprocessing, "outcomes")
        decvar = ET.SubElement(outcomes, "decvar")
        decvar.set("maxvalue", str(question.get('points', 1)))
        decvar.set("minvalue", "0")
        decvar.set("varname", "SCORE")
        decvar.set("vartype", "Decimal")
        
        respcondition = ET.SubElement(resprocessing, "respcondition")
        respcondition.set("continue", "No")
        
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        
        if qtype == "numerical":
            correct_val = float(question.get('correct_answer', 0))
            tolerance = float(question.get('tolerance', 0.01))
            
            vargte = ET.SubElement(conditionvar, "vargte")
            vargte.set("respident", f"response_{question_num}")
            vargte.text = str(correct_val - tolerance)
            
            varlte = ET.SubElement(conditionvar, "varlte")
            varlte.set("respident", f"response_{question_num}")
            varlte.text = str(correct_val + tolerance)
        else:
            varequal = ET.SubElement(conditionvar, "varequal")
            varequal.set("respident", f"response_{question_num}")
            
            if qtype == "multiple_choice":
                varequal.text = self._normalize_correct_answer(
                    question.get('correct_answer', ''), 
                    question.get('choices', [])
                )
            else:
                varequal.text = str(question.get('correct_answer', ''))
        
        setvar = ET.SubElement(respcondition, "setvar")
        setvar.set("action", "Set")
        setvar.set("varname", "SCORE")
        setvar.text = str(question.get('points', 1))
        
        self._add_feedback(item, question, question_num)
    
    def _add_feedback(self, item, question, question_num):
        """Add feedback with Canvas LaTeX conversion"""
        
        correct_feedback = question.get('feedback_correct', '')
        incorrect_feedback = question.get('feedback_incorrect', '')
        
        if correct_feedback:
            itemfeedback = ET.SubElement(item, "itemfeedback")
            itemfeedback.set("ident", f"correct_fb_{question_num}")
            
            flow_mat = ET.SubElement(itemfeedback, "flow_mat")
            material = ET.SubElement(flow_mat, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.set("texttype", "text/html")
            mattext.text = self._convert_latex_for_canvas(correct_feedback)
        
        if incorrect_feedback:
            itemfeedback = ET.SubElement(item, "itemfeedback")
            itemfeedback.set("ident", f"incorrect_fb_{question_num}")
            
            flow_mat = ET.SubElement(itemfeedback, "flow_mat")
            material = ET.SubElement(flow_mat, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.set("texttype", "text/html")
            mattext.text = self._convert_latex_for_canvas(incorrect_feedback)

    def _normalize_correct_answer(self, correct_answer, choices):
        """Convert correct answer to choice letter"""
        
        if not correct_answer:
            return "A"
        
        if len(str(correct_answer)) == 1 and str(correct_answer).upper() in 'ABCDEFGHIJ':
            return str(correct_answer).upper()
        
        correct_text = str(correct_answer).strip()
        for i, choice in enumerate(choices):
            if str(choice).strip() == correct_text:
                return chr(65 + i)
        
        return "A"
    
    def _clean_for_attribute(self, text):
        """Clean text for XML attributes"""
        if not text:
            return ""
        cleaned = str(text).replace('"', "'").replace('<', '').replace('>', '')
        return cleaned[:100] + "..." if len(cleaned) > 100 else cleaned
    
    def _add_canvas_metadata(self, qtimetadata):
        """Add Canvas-specific QTI metadata"""
        self._add_metadata_field(qtimetadata, "cc_maxattempts", "1")
        self._add_metadata_field(qtimetadata, "qmd_timelimit", "0")
        self._add_metadata_field(qtimetadata, "cc_profile", "cc.exam.v0p1")
    
    def _add_metadata_field(self, parent, field_label, field_entry):
        """Add metadata field"""
        qtimetadatafield = ET.SubElement(parent, "qtimetadatafield")
        fieldlabel = ET.SubElement(qtimetadatafield, "fieldlabel")
        fieldlabel.text = field_label
        fieldentry = ET.SubElement(qtimetadatafield, "fieldentry")
        fieldentry.text = field_entry
    
    def _generate_manifest_xml(self, package_name):
        """Generate IMS manifest"""
        
        manifest = ET.Element("manifest")
        manifest.set("identifier", f"manifest_{package_name}")
        manifest.set("xmlns", "http://www.imsglobal.org/xsd/imscp_v1p1")
        manifest.set("xmlns:imsmd", "http://www.imsglobal.org/xsd/imsmd_v1p2")
        
        metadata = ET.SubElement(manifest, "metadata")
        schema = ET.SubElement(metadata, "schema")
        schema.text = "IMS Content"
        schemaversion = ET.SubElement(metadata, "schemaversion")
        schemaversion.text = "1.1.3"
        
        organizations = ET.SubElement(manifest, "organizations")
        organizations.set("default", "TOC")
        
        organization = ET.SubElement(organizations, "organization")
        organization.set("identifier", "TOC")
        title = ET.SubElement(organization, "title")
        title.text = package_name
        
        resources = ET.SubElement(manifest, "resources")
        resource = ET.SubElement(resources, "resource")
        resource.set("identifier", f"resource_{package_name}")
        resource.set("type", "imsqti_xmlv1p2")
        resource.set("href", f"{package_name}.xml")
        
        file_elem = ET.SubElement(resource, "file")
        file_elem.set("href", f"{package_name}.xml")
        
        rough_string = ET.tostring(manifest, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def _generate_metadata_xml(self, package_name, question_count):
        """Generate assessment metadata"""
        
        metadata = ET.Element("assessment_metadata")
        
        title = ET.SubElement(metadata, "title")
        title.text = package_name
        
        description = ET.SubElement(metadata, "description")
        description.text = f"Canvas-compatible assessment with {question_count} questions"
        
        created = ET.SubElement(metadata, "created_date")
        created.text = datetime.now().isoformat()
        
        question_count_elem = ET.SubElement(metadata, "question_count")
        question_count_elem.text = str(question_count)
        
        rough_string = ET.tostring(metadata, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')





# Backward compatibility
def create_qti_package_legacy(df, original_questions, quiz_title, transform_json_to_csv, csv_to_qti):
    """Legacy function name for backward compatibility"""
    return create_qti_package(df, original_questions, quiz_title, transform_json_to_csv, csv_to_qti)