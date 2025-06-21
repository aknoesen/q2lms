#!/usr/bin/env python3
"""
QTI Generator Module
Core QTI XML generation functionality
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QTIItemGenerator:
    """Generates individual QTI question items"""
    
    def __init__(self, latex_converter=None):
        self.latex_converter = latex_converter
    
    def create_item(self, question: Dict[str, Any], question_num: int) -> ET.Element:
        """
        Create a QTI item element for a question
        
        Args:
            question: Question data dictionary
            question_num: Question number for ID generation
            
        Returns:
            QTI item XML element
        """
        item = ET.Element("item")
        item.set("ident", f"question_{question_num}")
        item.set("title", self._clean_for_attribute(
            question.get('title', f'Question {question_num}')
        ))
        
        # Add metadata
        self._add_item_metadata(item, question)
        
        # Add presentation (question content)
        presentation = ET.SubElement(item, "presentation")
        self._add_question_material(presentation, question)
        
        # Add response section based on question type
        question_type = question.get('type', 'multiple_choice').lower()
        
        if question_type == 'multiple_choice':
            self._add_multiple_choice_response(presentation, question, question_num)
        elif question_type == 'numerical':
            self._add_numerical_response(presentation, question, question_num)
        elif question_type == 'true_false':
            self._add_true_false_response(presentation, question, question_num)
        elif question_type == 'fill_in_blank':
            self._add_fill_in_blank_response(presentation, question, question_num)
        else:
            logger.warning(f"Unknown question type: {question_type}, using multiple choice")
            self._add_multiple_choice_response(presentation, question, question_num)
        
        # Add response processing (scoring logic)
        self._add_response_processing(item, question, question_num)
        
        # Add feedback if available
        self._add_feedback(item, question, question_num)
        
        return item
    
    def _add_item_metadata(self, item: ET.Element, question: Dict[str, Any]) -> None:
        """Add item-level metadata"""
        itemmetadata = ET.SubElement(item, "itemmetadata")
        qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")
        
        # Question type
        qtype = question.get('type', 'multiple_choice')
        self._add_metadata_field(qtimetadata, "question_type", qtype)
        
        # Points
        points = question.get('points', 1)
        self._add_metadata_field(qtimetadata, "points_possible", str(points))
        
        # Topic and difficulty if available
        if 'topic' in question:
            self._add_metadata_field(qtimetadata, "topic", str(question['topic']))
        
        if 'difficulty' in question:
            self._add_metadata_field(qtimetadata, "difficulty", str(question['difficulty']))
    
    def _add_question_material(self, presentation: ET.Element, question: Dict[str, Any]) -> None:
        """Add question text material"""
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext")
        mattext.set("texttype", "text/html")
        
        question_text = question.get('question_text', '')
        if self.latex_converter:
            question_text = self.latex_converter.convert_for_canvas(question_text)
        else:
            question_text = f'<div class="question-text">{question_text}</div>'
        
        mattext.text = question_text
    
    def _add_multiple_choice_response(self, presentation: ET.Element, 
                                    question: Dict[str, Any], 
                                    question_num: int) -> None:
        """Add multiple choice response section"""
        choices = question.get('choices', [])
        if not choices:
            logger.warning(f"Question {question_num} has no choices")
            return
        
        response_lid = ET.SubElement(presentation, "response_lid")
        response_lid.set("ident", f"response_{question_num}")
        response_lid.set("rcardinality", "Single")
        
        render_choice = ET.SubElement(response_lid, "render_choice")
        render_choice.set("shuffle", "No")
        
        for i, choice_text in enumerate(choices):
            choice_label = chr(65 + i)  # A, B, C, D, E...
            
            response_label = ET.SubElement(render_choice, "response_label")
            response_label.set("ident", choice_label)
            
            material = ET.SubElement(response_label, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.set("texttype", "text/html")
            
            if self.latex_converter:
                choice_text = self.latex_converter.convert_for_canvas(choice_text)
            
            mattext.text = str(choice_text)
    
    def _add_numerical_response(self, presentation: ET.Element, 
                              question: Dict[str, Any], 
                              question_num: int) -> None:
        """Add numerical response section"""
        response_num = ET.SubElement(presentation, "response_num")
        response_num.set("ident", f"response_{question_num}")
        response_num.set("rcardinality", "Single")
        
        render_fib = ET.SubElement(response_num, "render_fib")
        render_fib.set("fibtype", "Decimal")
        render_fib.set("rows", "1")
        render_fib.set("columns", "10")
    
    def _add_true_false_response(self, presentation: ET.Element, 
                               question: Dict[str, Any], 
                               question_num: int) -> None:
        """Add true/false response section"""
        # True/false is essentially multiple choice with True/False options
        tf_question = question.copy()
        tf_question['choices'] = ['True', 'False']
        
        self._add_multiple_choice_response(presentation, tf_question, question_num)
    
    def _add_fill_in_blank_response(self, presentation: ET.Element, 
                                  question: Dict[str, Any], 
                                  question_num: int) -> None:
        """Add fill-in-blank response section"""
        response_str = ET.SubElement(presentation, "response_str")
        response_str.set("ident", f"response_{question_num}")
        response_str.set("rcardinality", "Single")
        
        render_fib = ET.SubElement(response_str, "render_fib")
        render_fib.set("fibtype", "String")
        render_fib.set("rows", "1")
        render_fib.set("columns", "20")
    
    def _add_response_processing(self, item: ET.Element, 
                               question: Dict[str, Any], 
                               question_num: int) -> None:
        """Add response processing (scoring) logic"""
        resprocessing = ET.SubElement(item, "resprocessing")
        
        # Outcomes (score variable)
        outcomes = ET.SubElement(resprocessing, "outcomes")
        decvar = ET.SubElement(outcomes, "decvar")
        decvar.set("maxvalue", str(question.get('points', 1)))
        decvar.set("minvalue", "0")
        decvar.set("varname", "SCORE")
        decvar.set("vartype", "Decimal")
        
        # Response condition (correct answer)
        respcondition = ET.SubElement(resprocessing, "respcondition")
        respcondition.set("continue", "No")
        
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        
        question_type = question.get('type', 'multiple_choice').lower()
        
        if question_type == 'numerical':
            self._add_numerical_condition(conditionvar, question, question_num)
        else:
            self._add_choice_condition(conditionvar, question, question_num)
        
        # Set score for correct answer
        setvar = ET.SubElement(respcondition, "setvar")
        setvar.set("action", "Set")
        setvar.set("varname", "SCORE")
        setvar.text = str(question.get('points', 1))
    
    def _add_numerical_condition(self, conditionvar: ET.Element, 
                               question: Dict[str, Any], 
                               question_num: int) -> None:
        """Add numerical answer condition with tolerance"""
        correct_val = float(question.get('correct_answer', 0))
        tolerance = float(question.get('tolerance', 0.01))
        
        # Greater than or equal to (correct - tolerance)
        vargte = ET.SubElement(conditionvar, "vargte")
        vargte.set("respident", f"response_{question_num}")
        vargte.text = str(correct_val - tolerance)
        
        # Less than or equal to (correct + tolerance)
        varlte = ET.SubElement(conditionvar, "varlte")
        varlte.set("respident", f"response_{question_num}")
        varlte.text = str(correct_val + tolerance)
    
    def _add_choice_condition(self, conditionvar: ET.Element, 
                            question: Dict[str, Any], 
                            question_num: int) -> None:
        """Add choice-based answer condition"""
        varequal = ET.SubElement(conditionvar, "varequal")
        varequal.set("respident", f"response_{question_num}")
        
        question_type = question.get('type', 'multiple_choice').lower()
        
        if question_type in ['multiple_choice', 'true_false']:
            correct_answer = self._normalize_correct_answer(
                question.get('correct_answer', ''), 
                question.get('choices', [])
            )
            varequal.text = correct_answer
        else:
            varequal.text = str(question.get('correct_answer', ''))
    
    def _add_feedback(self, item: ET.Element, 
                     question: Dict[str, Any], 
                     question_num: int) -> None:
        """Add feedback sections"""
        # Check multiple possible feedback field names
        correct_feedback = (
            question.get('feedback_correct') or 
            question.get('correct_feedback') or 
            question.get('correct_fb', '')
        )
        
        incorrect_feedback = (
            question.get('feedback_incorrect') or 
            question.get('incorrect_feedback') or 
            question.get('incorrect_fb', '')
        )
        
        if correct_feedback:
            itemfeedback = ET.SubElement(item, "itemfeedback")
            itemfeedback.set("ident", f"correct_fb_{question_num}")
            
            flow_mat = ET.SubElement(itemfeedback, "flow_mat")
            material = ET.SubElement(flow_mat, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.set("texttype", "text/html")
            
            if self.latex_converter:
                correct_feedback = self.latex_converter.convert_for_canvas(correct_feedback)
            
            mattext.text = str(correct_feedback)
        
        if incorrect_feedback:
            itemfeedback = ET.SubElement(item, "itemfeedback")
            itemfeedback.set("ident", f"incorrect_fb_{question_num}")
            
            flow_mat = ET.SubElement(itemfeedback, "flow_mat")
            material = ET.SubElement(flow_mat, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.set("texttype", "text/html")
            
            if self.latex_converter:
                incorrect_feedback = self.latex_converter.convert_for_canvas(incorrect_feedback)
            
            mattext.text = str(incorrect_feedback)
    
    def _normalize_correct_answer(self, correct_answer: str, choices: List[str]) -> str:
        """Convert correct answer to choice letter (A, B, C, etc.)"""
        if not correct_answer:
            return "A"
        
        # If already a letter, use it
        answer_str = str(correct_answer).strip().upper()
        if len(answer_str) == 1 and answer_str in 'ABCDEFGHIJ':
            return answer_str
        
        # Try to match with choice text
        correct_text = str(correct_answer).strip()
        for i, choice in enumerate(choices):
            if str(choice).strip() == correct_text:
                return chr(65 + i)  # Convert to A, B, C...
        
        # Default to A if no match found
        logger.warning(f"Could not match correct answer '{correct_answer}' to choices, using A")
        return "A"
    
    def _clean_for_attribute(self, text: str) -> str:
        """Clean text for use in XML attributes"""
        if not text:
            return ""
        
        # Remove problematic characters
        cleaned = str(text).replace('"', "'").replace('<', '').replace('>', '')
        
        # Truncate if too long
        if len(cleaned) > 100:
            cleaned = cleaned[:97] + "..."
        
        return cleaned
    
    def _add_metadata_field(self, parent: ET.Element, 
                           field_label: str, 
                           field_entry: str) -> None:
        """Add a metadata field"""
        qtimetadatafield = ET.SubElement(parent, "qtimetadatafield")
        fieldlabel = ET.SubElement(qtimetadatafield, "fieldlabel")
        fieldlabel.text = field_label
        fieldentry = ET.SubElement(qtimetadatafield, "fieldentry")
        fieldentry.text = str(field_entry)


class QTIAssessmentGenerator:
    """Generates complete QTI assessment XML"""
    
    def __init__(self, latex_converter=None):
        self.item_generator = QTIItemGenerator(latex_converter)
    
    def create_assessment(self, questions: List[Dict[str, Any]], 
                         assessment_title: str) -> str:
        """
        Create complete QTI assessment XML
        
        Args:
            questions: List of question dictionaries
            assessment_title: Title for the assessment
            
        Returns:
            QTI XML as string
        """
        # Create root element
        root = ET.Element("questestinterop")
        root.set("xmlns", "http://www.imsglobal.org/xsd/ims_qtiasiv1p2")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        
        # Create assessment
        assessment = ET.SubElement(root, "assessment")
        assessment.set("ident", f"assessment_{assessment_title.replace(' ', '_')}")
        assessment.set("title", assessment_title)
        
        # Add assessment metadata
        qtimetadata = ET.SubElement(assessment, "qtimetadata")
        self._add_assessment_metadata(qtimetadata)
        
        # Create main section
        section = ET.SubElement(assessment, "section")
        section.set("ident", "root_section")
        
        # Add questions as items
        for i, question in enumerate(questions):
            item = self.item_generator.create_item(question, i + 1)
            section.append(item)
        
        # Convert to pretty XML string
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def _add_assessment_metadata(self, qtimetadata: ET.Element) -> None:
        """Add assessment-level metadata"""
        metadata_fields = [
            ("cc_maxattempts", "1"),
            ("qmd_timelimit", "0"),
            ("cc_profile", "cc.exam.v0p1")
        ]
        
        for field_label, field_entry in metadata_fields:
            self.item_generator._add_metadata_field(qtimetadata, field_label, field_entry)


class QTIPackageBuilder:
    """Builds complete QTI packages with manifest and metadata"""
    
    def __init__(self, latex_converter=None):
        self.assessment_generator = QTIAssessmentGenerator(latex_converter)
    
    def create_package(self, questions: List[Dict[str, Any]], 
                      assessment_title: str,
                      package_filename: str) -> Optional[bytes]:
        """
        Create complete QTI package as ZIP file
        
        Args:
            questions: List of question dictionaries
            assessment_title: Title for the assessment
            package_filename: Base filename for the package
            
        Returns:
            ZIP file data as bytes, or None if error
        """
        try:
            # Generate QTI XML
            qti_xml = self.assessment_generator.create_assessment(questions, assessment_title)
            
            # Generate manifest
            manifest_xml = self._create_manifest(assessment_title, package_filename)
            
            # Generate metadata
            metadata_xml = self._create_metadata(assessment_title, len(questions))
            
            # Create ZIP package
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add main QTI file
                zipf.writestr(f"{package_filename}.xml", qti_xml)
                
                # Add manifest
                zipf.writestr("imsmanifest.xml", manifest_xml)
                
                # Add metadata
                zipf.writestr("assessment_meta.xml", metadata_xml)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.exception("Error creating QTI package")
            return None
    
    def _create_manifest(self, assessment_title: str, package_filename: str) -> str:
        """Create IMS manifest XML"""
        manifest = ET.Element("manifest")
        manifest.set("identifier", f"manifest_{package_filename}")
        manifest.set("xmlns", "http://www.imsglobal.org/xsd/imscp_v1p1")
        manifest.set("xmlns:imsmd", "http://www.imsglobal.org/xsd/imsmd_v1p2")
        
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
        title.text = assessment_title
        
        # Resources
        resources = ET.SubElement(manifest, "resources")
        resource = ET.SubElement(resources, "resource")
        resource.set("identifier", f"resource_{package_filename}")
        resource.set("type", "imsqti_xmlv1p2")
        resource.set("href", f"{package_filename}.xml")
        
        file_elem = ET.SubElement(resource, "file")
        file_elem.set("href", f"{package_filename}.xml")
        
        # Convert to string
        rough_string = ET.tostring(manifest, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def _create_metadata(self, assessment_title: str, question_count: int) -> str:
        """Create assessment metadata XML"""
        metadata = ET.Element("assessment_metadata")
        
        title = ET.SubElement(metadata, "title")
        title.text = assessment_title
        
        description = ET.SubElement(metadata, "description")
        description.text = f"Assessment with {question_count} questions"
        
        created = ET.SubElement(metadata, "created_date")
        created.text = datetime.now().isoformat()
        
        question_count_elem = ET.SubElement(metadata, "question_count")
        question_count_elem.text = str(question_count)
        
        # Convert to string
        rough_string = ET.tostring(metadata, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
