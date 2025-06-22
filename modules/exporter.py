#!/usr/bin/env python3
"""
Question Export Module - Main Interface
Enhanced with JSON export capability for native format preservation
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import io
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Import our modular components
try:
    from .export.data_processor import ExportDataManager
    from .export.latex_converter import LaTeXAnalyzer
    from .export.canvas_adapter import CanvasQTIAdapter
    from .export.filename_utils import ExportNamingManager
    EXPORT_SYSTEM_AVAILABLE = True
except ImportError as e:
    EXPORT_SYSTEM_AVAILABLE = False
    logger.error(f"Export components not available: {e}")


class QuestionExporter:
    """Main class for handling question exports"""
    
    def __init__(self):
        if EXPORT_SYSTEM_AVAILABLE:
            self.data_manager = ExportDataManager()
            self.latex_analyzer = LaTeXAnalyzer()
            self.naming_manager = ExportNamingManager()
        else:
            raise ImportError("Export system components not available")
    
    def render_export_interface(self, 
                               df: pd.DataFrame, 
                               original_questions: List[Dict[str, Any]]) -> None:
        """
        Render the complete export interface with JSON support
        
        Args:
            df: Current DataFrame with filtered questions
            original_questions: Original question data with LaTeX preserved
        """
        try:
            st.markdown("### 📥 Export System")
            st.success("✅ Export system ready with custom filename support!")
            
            # Export type selection with JSON option
            export_type = st.radio(
                "Choose Export Format:",
                [
                    "📊 CSV Export", 
                    "📦 QTI Package for Canvas",
                    "📄 JSON Database (Native Format)"
                ],
                key="export_type_selection"
            )
            
            if export_type == "📊 CSV Export":
                self._render_csv_export(df)
            elif export_type == "📦 QTI Package for Canvas":
                self._render_qti_export(df, original_questions)
            else:  # JSON export
                self._render_json_export(df, original_questions)
            
        except Exception as e:
            logger.exception("Error rendering export interface")
            st.error(f"❌ Error loading export interface: {str(e)}")
    
    def _render_json_export(self, df: pd.DataFrame, original_questions: List[Dict[str, Any]]):
        """Render JSON export interface"""
        
        st.subheader("📄 JSON Database Export")
        st.info("📋 **Native Format Export**: Preserves complete question structure with LaTeX formatting intact")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Filename input with validation
            suggested_name = f"questions_filtered_{len(df)}Q_{datetime.now().strftime('%Y%m%d')}"
            
            filename_input = st.text_input(
                "📝 Custom Filename (without .json extension):",
                value=suggested_name,
                help="Enter a name for your JSON database file. Extension will be added automatically.",
                key="json_filename_input"
            )
            
            # Validate filename
            if filename_input:
                is_valid, message = self.naming_manager.validate_user_input(filename_input)
                if is_valid:
                    st.success(f"✅ {message}")
                    final_filename = f"{filename_input}.json"
                    st.caption(f"📁 Final filename: `{final_filename}`")
                else:
                    st.error(f"❌ {message}")
            
            # Export options
            with st.expander("⚙️ JSON Export Options"):
                include_metadata = st.checkbox(
                    "Include metadata section",
                    value=True,
                    help="Include course/instructor metadata in the JSON file"
                )
                
                format_style = st.selectbox(
                    "JSON formatting:",
                    ["Compact", "Pretty (indented)"],
                    index=1,
                    help="Choose formatting style for the JSON output"
                )
                
                preserve_ids = st.checkbox(
                    "Preserve original question IDs",
                    value=True,
                    help="Keep original question ID numbering from source"
                )
        
        with col2:
            st.metric("Questions to Export", len(df))
            if 'Points' in df.columns:
                total_points = df['Points'].sum()
                st.metric("Total Points", int(total_points))
            
            # JSON-specific info
            st.info("""
            📄 **JSON Export Benefits:**
            • Complete data preservation
            • LaTeX formatting intact
            • Re-importable to Q2LMS
            • Human-readable format
            • Version control friendly
            """)
        
        # Export preview
        with st.expander("📋 Preview Export Structure"):
            # Show what the JSON structure will look like
            if original_questions:
                sample_question = original_questions[0] if original_questions else {}
                st.json({
                    "questions": [sample_question],
                    "metadata": {
                        "subject": "Sample Course",
                        "exported_date": datetime.now().isoformat(),
                        "total_questions": len(df),
                        "format_version": "Phase Four"
                    }
                })
            st.caption(f"Sample structure - actual export will contain {len(df)} questions")
        
        # Export button
        if st.button("📄 Download JSON Database", type="primary", key="json_export_btn"):
            json_filename = f"{filename_input}.json" if filename_input else f"{suggested_name}.json"
            self._export_json(
                df, 
                original_questions, 
                json_filename, 
                include_metadata, 
                format_style, 
                preserve_ids
            )
    
    def _export_json(self, 
                    df: pd.DataFrame, 
                    original_questions: List[Dict[str, Any]], 
                    filename: str,
                    include_metadata: bool = True,
                    format_style: str = "Pretty (indented)",
                    preserve_ids: bool = True) -> None:
        """
        Export filtered questions to JSON format
        
        Args:
            df: Filtered DataFrame
            original_questions: Original question data  
            filename: Output filename
            include_metadata: Whether to include metadata section
            format_style: JSON formatting style
            preserve_ids: Whether to preserve original IDs
        """
        try:
            with st.spinner("🔄 Preparing JSON export..."):
                
                # Process questions for export
                st.info("📊 Processing question data...")
                processed_questions, report = self.data_manager.prepare_questions_for_export(
                    df, original_questions
                )
                
                if not report["success"]:
                    st.error(f"❌ Data processing failed: {report['errors']}")
                    return
                
                if report.get("warnings"):
                    st.warning("⚠️ " + "; ".join(report["warnings"]))
                
                # Create JSON structure
                json_data = {
                    "questions": processed_questions
                }
                
                # Add metadata if requested
                if include_metadata:
                    json_data["metadata"] = self._create_export_metadata(df, processed_questions)
                
                # Format JSON based on style preference
                if format_style == "Pretty (indented)":
                    json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
                else:
                    json_string = json.dumps(json_data, ensure_ascii=False)
                
                # Provide download
                st.download_button(
                    label="📄 Download JSON File",
                    data=json_string,
                    file_name=filename,
                    mime="application/json",
                    key=f"json_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Show success details
                st.success(f"""
                ✅ **JSON Database Export Ready!**
                
                📁 **Filename:** `{filename}`
                📊 **Questions:** {len(processed_questions)}
                🎯 **Total Points:** {sum(q.get('points', 1) for q in processed_questions)}
                📄 **Format:** Q2LMS Native JSON
                
                **Features:**
                • Complete question data preserved
                • LaTeX mathematical notation intact
                • Re-importable to Q2LMS
                • Compatible with version control
                
                **Usage:**
                1. Download the JSON file above
                2. Store as backup or share with colleagues  
                3. Re-import to Q2LMS using Upload tab
                4. Edit with any text editor if needed
                """)
                
        except Exception as e:
            logger.exception("Error in JSON export")
            st.error(f"❌ JSON export failed: {str(e)}")
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())
    
    def _create_export_metadata(self, df: pd.DataFrame, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create metadata section for JSON export"""
        
        # Analyze question data
        topics = set()
        difficulties = set()
        question_types = set()
        
        for question in questions:
            if question.get('topic'):
                topics.add(question['topic'])
            if question.get('difficulty'):
                difficulties.add(question['difficulty'])
            if question.get('type'):
                question_types.add(question['type'])
        
        # Calculate statistics
        total_points = sum(q.get('points', 1) for q in questions)
        latex_analysis = self.latex_analyzer.analyze_questions(questions)
        
        metadata = {
            "exported_date": datetime.now().isoformat(),
            "export_source": "Q2LMS Export System",
            "format_version": "Phase Four",
            "total_questions": len(questions),
            "total_points": total_points,
            "question_types": list(question_types),
            "topics": list(topics),
            "difficulties": list(difficulties),
            "latex_questions": latex_analysis.get('questions_with_latex', 0),
            "statistics": {
                "avg_points_per_question": round(total_points / len(questions), 2) if questions else 0,
                "latex_percentage": latex_analysis.get('latex_percentage', 0),
                "type_distribution": {qtype: sum(1 for q in questions if q.get('type') == qtype) 
                                   for qtype in question_types}
            }
        }
        
        return metadata
    
    # Keep existing CSV and QTI methods unchanged
    def _render_csv_export(self, df: pd.DataFrame):
        """Render CSV export interface"""
        
        st.subheader("📊 CSV Export")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Filename input with validation
            suggested_name = f"questions_{len(df)}Q_{datetime.now().strftime('%Y%m%d')}"
            
            filename_input = st.text_input(
                "📝 Custom Filename (without .csv extension):",
                value=suggested_name,
                help="Enter a name for your CSV file. Extension will be added automatically.",
                key="csv_filename_input"
            )
            
            # Validate filename
            if filename_input:
                is_valid, message = self.naming_manager.validate_user_input(filename_input)
                if is_valid:
                    st.success(f"✅ {message}")
                    final_filename = self.naming_manager.get_csv_filename(filename_input)
                    st.caption(f"📁 Final filename: `{final_filename}`")
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            st.metric("Questions to Export", len(df))
            if 'Points' in df.columns:
                total_points = df['Points'].sum()
                st.metric("Total Points", int(total_points))
        
        # Export preview
        with st.expander("📋 Preview Export Data"):
            preview_cols = ['Title', 'Type', 'Topic', 'Points'] if all(col in df.columns for col in ['Title', 'Type', 'Topic', 'Points']) else df.columns[:4]
            st.dataframe(df[preview_cols].head(3), use_container_width=True)
            st.caption(f"Showing first 3 of {len(df)} questions")
        
        # Export button
        if st.button("📥 Download CSV", type="primary", key="csv_export_btn"):
            csv_filename = self.naming_manager.get_csv_filename(filename_input) if filename_input else f"{suggested_name}.csv"
            self._export_csv(df, csv_filename)
    
    def _render_qti_export(self, df: pd.DataFrame, original_questions: List[Dict[str, Any]]):
        """Render QTI export interface"""
        
        st.subheader("📦 QTI Package Export")
        
        # Analyze LaTeX usage
        if original_questions:
            latex_analysis = self.latex_analyzer.analyze_questions(original_questions)
            if latex_analysis['questions_with_latex'] > 0:
                st.info(f"""
                🔢 **LaTeX Detection:** Found {latex_analysis['questions_with_latex']} questions with mathematical notation ({latex_analysis['latex_percentage']:.1f}% of total)
                
                Your export will be optimized for Canvas MathJax compatibility.
                """)
        
        # Export configuration
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Smart default quiz title based on current date and question count
            today = datetime.now()
            default_quiz_title = f"Quiz {today.strftime('%B %Y')} ({len(df)} Questions)"
            
            # Quiz title input with helpful default
            quiz_title = st.text_input(
                "🎯 Quiz/Assessment Title:",
                value=default_quiz_title,
                help="This will be the title of your quiz in Canvas. Feel free to customize!",
                key="qti_quiz_title"
            )
            
            # Show a helpful tip
            st.caption("💡 **Tip:** The title above will appear in Canvas. You can edit it to match your course.")
            
            # Filename input with smart default based on title
            if quiz_title and quiz_title.strip():
                suggested_name = self.naming_manager.suggest_name(quiz_title, len(df))
            else:
                suggested_name = f"Assessment_{len(df)}Q_{datetime.now().strftime('%Y%m%d')}"
            
            package_filename = st.text_input(
                "📝 Package Filename (without .zip extension):",
                value=suggested_name,
                help="This is the filename for the ZIP package you'll download",
                key="qti_filename_input"
            )
            
            # Validate filename with helpful feedback
            if package_filename:
                is_valid, message = self.naming_manager.validate_user_input(package_filename)
                if is_valid:
                    st.success(f"✅ {message}")
                    final_filename = self.naming_manager.get_qti_filename(package_filename)
                    st.caption(f"📁 Download filename: `{final_filename}`")
                else:
                    st.error(f"❌ {message}")
                    # Show what the corrected version would be
                    corrected = self.naming_manager.filename_handler.sanitize_filename(package_filename)
                    st.caption(f"🔧 Suggested fix: `{corrected}`")
        
        with col2:
            # Export statistics
            st.metric("📊 Questions", len(df))
            total_points = df['Points'].sum() if 'Points' in df.columns else len(df)
            st.metric("🎯 Total Points", int(total_points))
            
            # Question type breakdown
            if 'Type' in df.columns:
                type_counts = df['Type'].value_counts()
                with st.expander("📋 Question Types"):
                    for qtype, count in type_counts.items():
                        st.caption(f"• {qtype}: {count}")
        
        # Export preview
        with st.expander("📋 Preview Questions for Export"):
            preview_cols = ['Title', 'Type', 'Topic', 'Points'] if all(col in df.columns for col in ['Title', 'Type', 'Topic', 'Points']) else df.columns[:4]
            st.dataframe(df[preview_cols].head(5), use_container_width=True)
            st.caption(f"Showing first 5 of {len(df)} questions")
        
        # Export button with clear requirements
        export_enabled = (
            quiz_title and quiz_title.strip() and
            package_filename and package_filename.strip() and
            self.naming_manager.validate_user_input(package_filename)[0]
        )
        
        # Show clear status
        if not export_enabled:
            missing_items = []
            if not (quiz_title and quiz_title.strip()):
                missing_items.append("Quiz title")
            if not (package_filename and package_filename.strip()):
                missing_items.append("Package filename")
            if package_filename and not self.naming_manager.validate_user_input(package_filename)[0]:
                missing_items.append("Valid filename (fix special characters)")
            
            if missing_items:
                st.warning(f"⚠️ **Almost ready!** Please check: {', '.join(missing_items)}")
        
        # Always show the button, but with helpful state
        button_text = "📦 Create QTI Package" if export_enabled else "📦 Create QTI Package (Complete fields above)"
        
        if st.button(
            button_text,
            type="primary", 
            disabled=not export_enabled,
            key="qti_export_btn",
            help="Creates a Canvas-compatible QTI package ready for import" if export_enabled else "Complete the required fields above to enable export"
        ):
            final_quiz_title = quiz_title if quiz_title else default_quiz_title
            final_filename = self.naming_manager.get_qti_filename(package_filename) if package_filename else f"{suggested_name}.zip"
            
            # Call the export function
            self._handle_qti_export(df, original_questions, final_quiz_title, final_filename)
    
    def _handle_qti_export(self, 
                          df: pd.DataFrame, 
                          original_questions: List[Dict[str, Any]], 
                          quiz_title: str,
                          filename: str) -> None:
        """Handle QTI package export"""
        
        try:
            with st.spinner("🔄 Creating QTI package..."):
                
                # Step 1: Process data
                st.info("📊 Processing question data...")
                processed_questions, report = self.data_manager.prepare_questions_for_export(
                    df, original_questions
                )
                
                if not report["success"]:
                    st.error(f"❌ Data processing failed: {report['errors']}")
                    return
                
                if report.get("warnings"):
                    st.warning("⚠️ " + "; ".join(report["warnings"]))
                
                # Step 2: Create QTI package
                st.info("📦 Generating Canvas-compatible QTI package...")
                qti_builder = CanvasQTIAdapter()
                package_data = qti_builder.create_package(
                    processed_questions, 
                    quiz_title,
                    filename.replace('.zip', '')
                )
                
                if package_data:
                    # Provide download
                    st.download_button(
                        label="📦 Download QTI Package",
                        data=package_data,
                        file_name=filename,
                        mime="application/zip",
                        key=f"qti_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    
                    # Show success details
                    total_points = sum(q.get('points', 1) for q in processed_questions)
                    latex_analysis = self.latex_analyzer.analyze_questions(processed_questions)
                    latex_count = latex_analysis['questions_with_latex']
                    
                    st.success(f"""
                    ✅ **QTI Package Created Successfully!**
                    
                    📁 **Filename:** `{filename}`
                    🎯 **Quiz Title:** {quiz_title}
                    📊 **Questions:** {len(processed_questions)}
                    🎯 **Total Points:** {total_points}
                    🔢 **LaTeX Questions:** {latex_count}
                    
                    **Canvas Compatibility:** ✅ Optimized for Canvas MathJax
                    
                    **Next Steps:**
                    1. Download the package above
                    2. Go to Canvas → Quizzes → Import QTI Package
                    3. Upload your downloaded file
                    4. Verify questions import correctly
                    """)
                else:
                    st.error("❌ Failed to create QTI package")
                
        except Exception as e:
            logger.exception("Error in QTI export")
            st.error(f"❌ Export failed: {str(e)}")
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())
    
    def _export_csv(self, df: pd.DataFrame, filename: str) -> None:
        """Export DataFrame to CSV"""
        try:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download CSV File",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                key=f"csv_download_{datetime.now().strftime('%H%M%S')}"
            )
            
            st.success(f"✅ CSV export ready: `{filename}`")
            
        except Exception as e:
            st.error(f"❌ Error creating CSV export: {str(e)}")


# Main interface function
def integrate_with_existing_ui(df: pd.DataFrame, 
                              original_questions: List[Dict[str, Any]]) -> None:
    """
    Main function to render the complete export interface
    
    This is the primary function that should be called from streamlit_app.py
    """
    
    if df is None or df.empty:
        st.info("""
        📋 **No Database Loaded**
        
        Please load a question database first:
        1. Go to the **Upload** tab
        2. Upload your JSON question files
        3. Return here to export questions
        """)
        return
    
    # Show current database stats
    st.info(f"""
    📊 **Current Database:** {len(df)} questions loaded
    
    🚀 Export system ready with custom filename support, LaTeX optimization, Canvas compatibility, and native JSON export.
    """)
    
    # Create and use the exporter
    if EXPORT_SYSTEM_AVAILABLE:
        exporter = QuestionExporter()
        exporter.render_export_interface(df, original_questions)
    else:
        st.error("❌ Export system components not available")
        st.info("Please ensure all export modules are properly installed.")


# Legacy compatibility functions (simplified)
def export_to_csv(df: pd.DataFrame, filename: str = "filtered_questions.csv") -> None:
    """Legacy CSV export function for backward compatibility"""
    if EXPORT_SYSTEM_AVAILABLE:
        exporter = QuestionExporter()
        exporter._export_csv(df, filename)
    else:
        st.error("❌ Export system not available")


def export_to_json(df: pd.DataFrame, 
                  original_questions: List[Dict[str, Any]], 
                  filename: str = "filtered_questions.json") -> None:
    """New JSON export function for backward compatibility"""
    if EXPORT_SYSTEM_AVAILABLE:
        exporter = QuestionExporter()
        exporter._export_json(df, original_questions, filename)
    else:
        st.error("❌ Export system not available")


def create_qti_package(df: pd.DataFrame, 
                      original_questions: List[Dict[str, Any]], 
                      quiz_title: str,
                      *args) -> None:  # Accept any legacy parameters
    """Legacy QTI export function for backward compatibility"""
    
    if EXPORT_SYSTEM_AVAILABLE:
        exporter = QuestionExporter()
        naming_manager = ExportNamingManager()
        filename = naming_manager.get_qti_filename(quiz_title)
        exporter._handle_qti_export(df, original_questions, quiz_title, filename)
    else:
        st.error("❌ Export system not available")