#!/usr/bin/env python3
"""
Updated Windows-Compatible QTI Generator for MATLAB Question Database
Converts CSV question database to QTI 2.1 XML format
Now handles new subtopic field in the database
"""

import csv
import xml.etree.ElementTree as ET
import zipfile
import os
import sys
import uuid
from datetime import datetime

def create_qti_manifest(quiz_title, item_files):
    """Create QTI 2.1 manifest file"""
    manifest = ET.Element('manifest')
    manifest.set('xmlns', 'http://www.imsglobal.org/xsd/imscp_v1p1')
    manifest.set('xmlns:imsmd', 'http://www.imsglobal.org/xsd/imsmd_v1p2')
    manifest.set('xmlns:imsqti', 'http://www.imsglobal.org/xsd/imsqti_v2p1')
    manifest.set('identifier', f'MANIFEST_{uuid.uuid4().hex}')
    
    # Metadata
    metadata = ET.SubElement(manifest, 'metadata')
    schema = ET.SubElement(metadata, 'schema')
    schema.text = 'IMS Content'
    schemaversion = ET.SubElement(metadata, 'schemaversion')
    schemaversion.text = '1.1.3'
    
    # Organizations (empty for assessment)
    organizations = ET.SubElement(manifest, 'organizations')
    
    # Resources
    resources = ET.SubElement(manifest, 'resources')
    
    # Add each question as a resource
    for item_file in item_files:
        resource = ET.SubElement(resources, 'resource')
        resource.set('identifier', f'RES_{item_file.replace(".xml", "")}')
        resource.set('type', 'imsqti_item_xmlv2p1')
        resource.set('href', item_file)
        
        file_elem = ET.SubElement(resource, 'file')
        file_elem.set('href', item_file)
    
    return manifest

def add_item_metadata(item, question_data):
    """Add metadata to QTI item including topic and subtopic information"""
    # Add QTI metadata if topic or subtopic information is available
    topic = question_data.get('Topic', '').strip()
    subtopic = question_data.get('Subtopic', '').strip()
    
    if topic or subtopic:
        # Create a simple metadata section as a comment for now
        # Full QTI metadata is more complex and may not be supported by all LMS
        metadata_comment = f" Topic: {topic}"
        if subtopic and subtopic != 'N/A' and subtopic != '':
            metadata_comment += f", Subtopic: {subtopic}"
        metadata_comment += " "
        
        # Add as XML comment (visible in source but doesn't affect rendering)
        item.insert(0, ET.Comment(metadata_comment))

def create_multiple_choice_item(question_data):
    """Create QTI XML for multiple choice question"""
    item_id = question_data['ID']
    
    # Root element
    item = ET.Element('assessmentItem')
    item.set('xmlns', 'http://www.imsglobal.org/xsd/imsqti_v2p1')
    item.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    item.set('xsi:schemaLocation', 'http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/qti/qtiv2p1/imsqti_v2p1.xsd')
    item.set('identifier', item_id)
    item.set('title', question_data['Title'])
    item.set('adaptive', 'false')
    item.set('timeDependent', 'false')
    
    # Add metadata (topic/subtopic)
    add_item_metadata(item, question_data)
    
    # Response declaration
    response_decl = ET.SubElement(item, 'responseDeclaration')
    response_decl.set('identifier', 'RESPONSE')
    response_decl.set('cardinality', 'single')
    response_decl.set('baseType', 'identifier')
    
    correct_response = ET.SubElement(response_decl, 'correctResponse')
    value = ET.SubElement(correct_response, 'value')
    
    # Find correct answer identifier
    correct_answer = question_data['Correct_Answer']
    choices = ['A', 'B', 'C', 'D']
    choice_texts = [question_data.get(f'Choice_{c}', '') for c in choices]
    
    correct_id = 'A'  # default
    for i, choice_text in enumerate(choice_texts):
        if choice_text and choice_text.strip() == correct_answer.strip():
            correct_id = choices[i]
            break
    
    value.text = f'CHOICE_{correct_id}'
    
    # Outcome declaration
    outcome_decl = ET.SubElement(item, 'outcomeDeclaration')
    outcome_decl.set('identifier', 'SCORE')
    outcome_decl.set('cardinality', 'single')
    outcome_decl.set('baseType', 'float')
    
    default_value = ET.SubElement(outcome_decl, 'defaultValue')
    value_elem = ET.SubElement(default_value, 'value')
    value_elem.text = '0'
    
    # Item body
    item_body = ET.SubElement(item, 'itemBody')
    
    # Question text
    question_p = ET.SubElement(item_body, 'p')
    question_p.text = question_data['Question_Text']
    
    # Choice interaction
    choice_interaction = ET.SubElement(item_body, 'choiceInteraction')
    choice_interaction.set('responseIdentifier', 'RESPONSE')
    choice_interaction.set('shuffle', 'false')
    choice_interaction.set('maxChoices', '1')
    
    # Add choices
    for i, choice_letter in enumerate(choices):
        choice_text = question_data.get(f'Choice_{choice_letter}', '').strip()
        if choice_text:
            choice = ET.SubElement(choice_interaction, 'simpleChoice')
            choice.set('identifier', f'CHOICE_{choice_letter}')
            choice.text = choice_text
    
    # Response processing
    response_processing = ET.SubElement(item, 'responseProcessing')
    response_processing.set('template', 'http://www.imsglobal.org/question/qti_v2p1/rptemplates/match_correct')
    
    return item

def create_numerical_item(question_data):
    """Create QTI XML for numerical question"""
    item_id = question_data['ID']
    
    # Root element
    item = ET.Element('assessmentItem')
    item.set('xmlns', 'http://www.imsglobal.org/xsd/imsqti_v2p1')
    item.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    item.set('xsi:schemaLocation', 'http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/qti/qtiv2p1/imsqti_v2p1.xsd')
    item.set('identifier', item_id)
    item.set('title', question_data['Title'])
    item.set('adaptive', 'false')
    item.set('timeDependent', 'false')
    
    # Add metadata (topic/subtopic)
    add_item_metadata(item, question_data)
    
    # Response declaration
    response_decl = ET.SubElement(item, 'responseDeclaration')
    response_decl.set('identifier', 'RESPONSE')
    response_decl.set('cardinality', 'single')
    response_decl.set('baseType', 'float')
    
    correct_response = ET.SubElement(response_decl, 'correctResponse')
    value = ET.SubElement(correct_response, 'value')
    value.text = str(question_data['Correct_Answer'])
    
    # Outcome declaration
    outcome_decl = ET.SubElement(item, 'outcomeDeclaration')
    outcome_decl.set('identifier', 'SCORE')
    outcome_decl.set('cardinality', 'single')
    outcome_decl.set('baseType', 'float')
    
    default_value = ET.SubElement(outcome_decl, 'defaultValue')
    value_elem = ET.SubElement(default_value, 'value')
    value_elem.text = '0'
    
    # Item body
    item_body = ET.SubElement(item, 'itemBody')
    
    # Question text
    question_p = ET.SubElement(item_body, 'p')
    question_p.text = question_data['Question_Text']
    
    # Text entry interaction
    text_interaction = ET.SubElement(item_body, 'textEntryInteraction')
    text_interaction.set('responseIdentifier', 'RESPONSE')
    text_interaction.set('expectedLength', '10')
    
    # Response processing for numerical with tolerance
    response_processing = ET.SubElement(item, 'responseProcessing')
    
    response_condition = ET.SubElement(response_processing, 'responseCondition')
    response_if = ET.SubElement(response_condition, 'responseIf')
    
    # Check if answer is within tolerance
    tolerance = question_data.get('Tolerance', 0)
    if tolerance and float(tolerance) > 0:
        # Use tolerance-based matching
        and_elem = ET.SubElement(response_if, 'and')
        
        gte = ET.SubElement(and_elem, 'gte')
        variable1 = ET.SubElement(gte, 'variable')
        variable1.set('identifier', 'RESPONSE')
        base_value1 = ET.SubElement(gte, 'baseValue')
        base_value1.set('baseType', 'float')
        base_value1.text = str(float(question_data['Correct_Answer']) - float(tolerance))
        
        lte = ET.SubElement(and_elem, 'lte')
        variable2 = ET.SubElement(lte, 'variable')
        variable2.set('identifier', 'RESPONSE')
        base_value2 = ET.SubElement(lte, 'baseValue')
        base_value2.set('baseType', 'float')
        base_value2.text = str(float(question_data['Correct_Answer']) + float(tolerance))
    else:
        # Exact match
        equal = ET.SubElement(response_if, 'equal')
        variable = ET.SubElement(equal, 'variable')
        variable.set('identifier', 'RESPONSE')
        base_value = ET.SubElement(equal, 'baseValue')
        base_value.set('baseType', 'float')
        base_value.text = str(question_data['Correct_Answer'])
    
    # Set score
    set_outcome = ET.SubElement(response_if, 'setOutcomeValue')
    set_outcome.set('identifier', 'SCORE')
    base_value_score = ET.SubElement(set_outcome, 'baseValue')
    base_value_score.set('baseType', 'float')
    base_value_score.text = str(question_data.get('Points', 1))
    
    return item

def create_true_false_item(question_data):
    """Create QTI XML for true/false question"""
    item_id = question_data['ID']
    
    # Root element
    item = ET.Element('assessmentItem')
    item.set('xmlns', 'http://www.imsglobal.org/xsd/imsqti_v2p1')
    item.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    item.set('xsi:schemaLocation', 'http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/qti/qtiv2p1/imsqti_v2p1.xsd')
    item.set('identifier', item_id)
    item.set('title', question_data['Title'])
    item.set('adaptive', 'false')
    item.set('timeDependent', 'false')
    
    # Add metadata (topic/subtopic)
    add_item_metadata(item, question_data)
    
    # Response declaration
    response_decl = ET.SubElement(item, 'responseDeclaration')
    response_decl.set('identifier', 'RESPONSE')
    response_decl.set('cardinality', 'single')
    response_decl.set('baseType', 'identifier')
    
    correct_response = ET.SubElement(response_decl, 'correctResponse')
    value = ET.SubElement(correct_response, 'value')
    
    # Set correct answer
    correct_answer = question_data['Correct_Answer'].lower()
    if correct_answer == 'true':
        value.text = 'CHOICE_TRUE'
    else:
        value.text = 'CHOICE_FALSE'
    
    # Outcome declaration
    outcome_decl = ET.SubElement(item, 'outcomeDeclaration')
    outcome_decl.set('identifier', 'SCORE')
    outcome_decl.set('cardinality', 'single')
    outcome_decl.set('baseType', 'float')
    
    default_value = ET.SubElement(outcome_decl, 'defaultValue')
    value_elem = ET.SubElement(default_value, 'value')
    value_elem.text = '0'
    
    # Item body
    item_body = ET.SubElement(item, 'itemBody')
    
    # Question text
    question_p = ET.SubElement(item_body, 'p')
    question_p.text = question_data['Question_Text']
    
    # Choice interaction
    choice_interaction = ET.SubElement(item_body, 'choiceInteraction')
    choice_interaction.set('responseIdentifier', 'RESPONSE')
    choice_interaction.set('shuffle', 'false')
    choice_interaction.set('maxChoices', '1')
    
    # True choice
    true_choice = ET.SubElement(choice_interaction, 'simpleChoice')
    true_choice.set('identifier', 'CHOICE_TRUE')
    true_choice.text = 'True'
    
    # False choice
    false_choice = ET.SubElement(choice_interaction, 'simpleChoice')
    false_choice.set('identifier', 'CHOICE_FALSE')
    false_choice.text = 'False'
    
    # Response processing
    response_processing = ET.SubElement(item, 'responseProcessing')
    response_processing.set('template', 'http://www.imsglobal.org/question/qti_v2p1/rptemplates/match_correct')
    
    return item

def create_fill_in_blank_item(question_data):
    """Create QTI XML for fill-in-the-blank question"""
    item_id = question_data['ID']
    
    # Root element
    item = ET.Element('assessmentItem')
    item.set('xmlns', 'http://www.imsglobal.org/xsd/imsqti_v2p1')
    item.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    item.set('xsi:schemaLocation', 'http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/qti/qtiv2p1/imsqti_v2p1.xsd')
    item.set('identifier', item_id)
    item.set('title', question_data['Title'])
    item.set('adaptive', 'false')
    item.set('timeDependent', 'false')
    
    # Add metadata (topic/subtopic)
    add_item_metadata(item, question_data)
    
    # Response declaration
    response_decl = ET.SubElement(item, 'responseDeclaration')
    response_decl.set('identifier', 'RESPONSE')
    response_decl.set('cardinality', 'single')
    response_decl.set('baseType', 'string')
    
    correct_response = ET.SubElement(response_decl, 'correctResponse')
    value = ET.SubElement(correct_response, 'value')
    value.text = str(question_data['Correct_Answer'])
    
    # Outcome declaration
    outcome_decl = ET.SubElement(item, 'outcomeDeclaration')
    outcome_decl.set('identifier', 'SCORE')
    outcome_decl.set('cardinality', 'single')
    outcome_decl.set('baseType', 'float')
    
    default_value = ET.SubElement(outcome_decl, 'defaultValue')
    value_elem = ET.SubElement(default_value, 'value')
    value_elem.text = '0'
    
    # Item body
    item_body = ET.SubElement(item, 'itemBody')
    
    # Question text
    question_p = ET.SubElement(item_body, 'p')
    question_p.text = question_data['Question_Text']
    
    # Text entry interaction
    text_interaction = ET.SubElement(item_body, 'textEntryInteraction')
    text_interaction.set('responseIdentifier', 'RESPONSE')
    text_interaction.set('expectedLength', '20')
    
    # Response processing
    response_processing = ET.SubElement(item, 'responseProcessing')
    
    response_condition = ET.SubElement(response_processing, 'responseCondition')
    response_if = ET.SubElement(response_condition, 'responseIf')
    
    # String match (case-insensitive)
    equal = ET.SubElement(response_if, 'equal')
    equal.set('toleranceMode', 'exact')
    
    # Convert response to lowercase for comparison
    lower_resp = ET.SubElement(equal, 'stringMatch')
    lower_resp.set('caseSensitive', 'false')
    variable = ET.SubElement(lower_resp, 'variable')
    variable.set('identifier', 'RESPONSE')
    base_value = ET.SubElement(lower_resp, 'baseValue')
    base_value.set('baseType', 'string')
    base_value.text = str(question_data['Correct_Answer'])
    
    # Set score
    set_outcome = ET.SubElement(response_if, 'setOutcomeValue')
    set_outcome.set('identifier', 'SCORE')
    base_value_score = ET.SubElement(set_outcome, 'baseValue')
    base_value_score.set('baseType', 'float')
    base_value_score.text = str(question_data.get('Points', 1))
    
    return item

def csv_to_qti(csv_file, quiz_title):
    """Main function to convert CSV to QTI format with subtopic support"""
    try:
        print(f"Starting QTI conversion for: {quiz_title}")
        print(f"Reading CSV file: {csv_file}")
        
        if not os.path.exists(csv_file):
            print(f"Error: CSV file '{csv_file}' not found")
            return False
        
        # Read CSV file
        questions = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Use comma delimiter (updated from semicolon)
            reader = csv.DictReader(file, delimiter=',')
            questions = list(reader)
        
        print(f"Found {len(questions)} questions in CSV")
        
        if not questions:
            print("No questions found in CSV file")
            return False
        
        # Display summary of topics and subtopics
        topics = set()
        subtopics = set()
        for q in questions:
            if 'Topic' in q and q['Topic'].strip():
                topics.add(q['Topic'].strip())
            if 'Subtopic' in q and q['Subtopic'].strip() and q['Subtopic'].strip() != 'N/A':
                subtopics.add(q['Subtopic'].strip())
        
        if topics:
            print(f"Topics found: {', '.join(sorted(topics))}")
        if subtopics:
            print(f"Subtopics found: {', '.join(sorted(subtopics))}")
        
        # Create XML files for each question
        item_files = []
        
        for i, question in enumerate(questions):
            try:
                # Clean the question data (remove extra quotes and whitespace)
                clean_question = {}
                for key, value in question.items():
                    if isinstance(value, str):
                        # Remove outer quotes if present
                        cleaned_value = value.strip()
                        if cleaned_value.startswith("'") and cleaned_value.endswith("'"):
                            cleaned_value = cleaned_value[1:-1]
                        elif cleaned_value.startswith('"') and cleaned_value.endswith('"'):
                            cleaned_value = cleaned_value[1:-1]
                        clean_question[key] = cleaned_value
                    else:
                        clean_question[key] = value
                
                question_type = clean_question.get('Type', '').lower()
                question_id = clean_question.get('ID', f'Q_{i+1}')
                
                # Display topic/subtopic info for this question
                topic_info = ""
                if 'Topic' in clean_question and clean_question['Topic'].strip():
                    topic_info = f" (Topic: {clean_question['Topic']}"
                    if 'Subtopic' in clean_question and clean_question['Subtopic'].strip() and clean_question['Subtopic'].strip() != 'N/A':
                        topic_info += f", Subtopic: {clean_question['Subtopic']}"
                    topic_info += ")"
                
                print(f"Processing question {i+1}: {question_type} - {question_id}{topic_info}")
                
                # Create appropriate QTI item based on type
                if question_type == 'multiple_choice':
                    item_xml = create_multiple_choice_item(clean_question)
                elif question_type == 'numerical':
                    item_xml = create_numerical_item(clean_question)
                elif question_type == 'true_false':
                    item_xml = create_true_false_item(clean_question)
                elif question_type == 'fill_in_blank':
                    item_xml = create_fill_in_blank_item(clean_question)
                else:
                    print(f"Warning: Unknown question type '{question_type}', skipping")
                    continue
                
                # Save individual item file
                item_filename = f"{question_id}.xml"
                item_files.append(item_filename)
                
                # Write XML with proper formatting
                rough_string = ET.tostring(item_xml, 'unicode')
                print(f"Created XML for {item_filename}")
                
                with open(item_filename, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write(rough_string)
                
            except Exception as e:
                print(f"Error processing question {i+1}: {str(e)}")
                continue
        
        if not item_files:
            print("No valid questions were processed")
            return False
        
        # Create manifest
        print("Creating QTI manifest...")
        manifest_xml = create_qti_manifest(quiz_title, item_files)
        
        with open('imsmanifest.xml', 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(ET.tostring(manifest_xml, 'unicode'))
        
        # Create ZIP file
        zip_filename = f"{quiz_title}.zip"
        print(f"Creating QTI package: {zip_filename}")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as qti_zip:
            # Add manifest
            qti_zip.write('imsmanifest.xml')
            
            # Add all item files
            for item_file in item_files:
                if os.path.exists(item_file):
                    qti_zip.write(item_file)
        
        # Clean up temporary files
        os.remove('imsmanifest.xml')
        for item_file in item_files:
            if os.path.exists(item_file):
                os.remove(item_file)
        
        print(f"SUCCESS! QTI package created: {zip_filename}")
        print(f"Package contains {len(item_files)} questions")
        if topics:
            print(f"Covering topics: {', '.join(sorted(topics))}")
        if subtopics:
            print(f"Covering subtopics: {', '.join(sorted(subtopics))}")
        
        return True
        
    except Exception as e:
        print(f"Error in QTI conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python simple_qti.py <csv_file> <quiz_title>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    quiz_title = sys.argv[2]
    
    success = csv_to_qti(csv_file, quiz_title)
    sys.exit(0 if success else 1)