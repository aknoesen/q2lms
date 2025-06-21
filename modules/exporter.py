#!/usr/bin/env python3
"""
Refactored Exporter Module - Main Interface
Clean, modular approach to question export functionality
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import io
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Import our new modular components with error handling
try:
    from .export.data_processor import ExportDataManager
    DATA_PROCESSOR_AVAILABLE = True
except ImportError as e:
    DATA_PROCESSOR_AVAILABLE = False
    logger.warning(f"Data processor not available: {e}")

try:
    from .export.latex_converter import LaTeXAnalyzer
    LATEX_CONVERTER_AVAILABLE = True
except ImportError as e:
    LATEX_CONVERTER_AVAILABLE = False
    logger.warning(f"LaTeX converter not available: {e}")

try:
    from .export.canvas_adapter import CanvasQTIAdapter
    CANVAS_ADAPTER_AVAILABLE = True
except ImportError as e:
    CANVAS_ADAPTER_AVAILABLE = False
    logger.warning(f"Canvas adapter not available: {e}")

try:
    from .export.filename_utils import ExportNamingManager
    FILENAME_UTILS_AVAILABLE = True
except ImportError as e:
    FILENAME_UTILS_AVAILABLE = False
    logger.warning(f"Filename utils not available: {e}")

# Check if we have all components for the full system
FULL_SYSTEM_AVAILABLE = all([
    DATA_PROCESSOR_AVAILABLE,
    LATEX_CONVERTER_AVAILABLE, 
    CANVAS_ADAPTER_AVAILABLE,
    FILENAME_UTILS_AVAILABLE
])


class QuestionExporter:
    """Main class for handling question exports"""
    
    def __init__(self):
        if FULL_SYSTEM_AVAILABLE:
            self.data_manager = ExportDataManager()
            self.latex_analyzer = LaTeXAnalyzer()
            self.naming_manager = ExportNamingManager()
        else:
            self.data_manager = None
            self.latex_analyzer = None
            self.naming_manager = None
    
    def render_export_interface(self, 
                               df: pd.DataFrame, 
                               original_questions: List[Dict[str, Any]]) -> None:
        """
        Render the complete export interface
        
        Args:
            df: Current DataFrame with filtered questions
            original_questions: Original question data with LaTeX preserved
        """
        try:
            if FULL_SYSTEM_AVAILABLE:
                self._render_full_export_interface(df, original_questions)
            else:
                self._render_basic_export_interface(df, original_questions)
            
        except Exception as e:
            logger.exception("Error rendering export interface")
            st.error(f"❌ Error loading export interface: {str(e)}")
    
    def _render_full_export_interface(self, df: pd.DataFrame, original_questions: List[Dict[str, Any]]):
        """Render the full enhanced export interface"""
        
        st.markdown("### 📥 Enhanced Export System")
        st.success("✅ Full modular export system loaded with custom filename support!")
        
        # Export type selection
        export_type = st.radio(
            "Choose Export Format:",
            ["📊 Enhanced CSV Export", "📦 Enhanced QTI Package for Canvas"],
            key="export_type_selection"
        )
        
        if export_type == "📊 Enhanced CSV Export":
            self._render_enhanced_csv_export(df)
        else:
            self._render_enhanced_qti_export(df, original_questions)
    
    def _render_enhanced_csv_export(self, df: pd.DataFrame):
        """Render enhanced CSV export interface"""
        
        st.subheader("📊 Enhanced CSV Export")
        
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
            if filename_input and self.naming_manager:
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
        if st.button("📥 Download Enhanced CSV", type="primary", key="csv_export_btn"):
            if filename_input and self.naming_manager:
                csv_filename = self.naming_manager.get_csv_filename(filename_input)
            else:
                csv_filename = f"{suggested_name}.csv"
            
            self._export_csv(df, csv_filename)
    
    def _render_enhanced_qti_export(self, df: pd.DataFrame, original_questions: List[Dict[str, Any]]):
        """Render enhanced QTI export interface with better UX"""
        
        st.subheader("📦 Enhanced QTI Package Export")
        
        # Analyze LaTeX usage
        if self.latex_analyzer and original_questions:
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
                value=default_quiz_title,  # Provide a smart default
                help="This will be the title of your quiz in Canvas. Feel free to customize!",
                key="qti_quiz_title"
            )
            
            # Show a helpful tip
            st.caption("💡 **Tip:** The title above will appear in Canvas. You can edit it to match your course.")
            
            # Filename input with smart default based on title
            if quiz_title and quiz_title.strip():
                if self.naming_manager:
                    suggested_name = self.naming_manager.suggest_name(quiz_title, len(df))
                else:
                    # Simple fallback if naming manager not available
                    clean_title = quiz_title.replace(' ', '_').replace('(', '').replace(')', '')
                    suggested_name = f"{clean_title}_{len(df)}Q"
            else:
                suggested_name = f"Assessment_{len(df)}Q_{datetime.now().strftime('%Y%m%d')}"
            
            package_filename = st.text_input(
                "📝 Package Filename (without .zip extension):",
                value=suggested_name,
                help="This is the filename for the ZIP package you'll download",
                key="qti_filename_input"
            )
            
            # Validate filename with helpful feedback
            if package_filename and self.naming_manager:
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
            (not self.naming_manager or self.naming_manager.validate_user_input(package_filename)[0])
        )
        
        # Show clear status
        if not export_enabled:
            missing_items = []
            if not (quiz_title and quiz_title.strip()):
                missing_items.append("Quiz title")
            if not (package_filename and package_filename.strip()):
                missing_items.append("Package filename")
            if self.naming_manager and package_filename and not self.naming_manager.validate_user_input(package_filename)[0]:
                missing_items.append("Valid filename (fix special characters)")
            
            if missing_items:
                st.warning(f"⚠️ **Almost ready!** Please check: {', '.join(missing_items)}")
        
        # Always show the button, but with helpful state
        button_text = "📦 Create Enhanced QTI Package" if export_enabled else "📦 Create QTI Package (Complete fields above)"
        
        if st.button(
            button_text,
            type="primary", 
            disabled=not export_enabled,
            key="qti_export_btn",
            help="Creates a Canvas-compatible QTI package ready for import" if export_enabled else "Complete the required fields above to enable export"
        ):
            final_quiz_title = quiz_title if quiz_title else default_quiz_title
            if package_filename and self.naming_manager:
                final_filename = self.naming_manager.get_qti_filename(package_filename)
            else:
                final_filename = f"{suggested_name}.zip"
            
            # Call the export function
            self._handle_qti_export(df, original_questions, final_quiz_title, final_filename)
    
    def _render_basic_export_interface(self, df: pd.DataFrame, original_questions: List[Dict[str, Any]]):
        """Render basic export interface when full system not available"""
        
        st.markdown("### 📥 Basic Export System")
        st.warning("⚠️ Enhanced modules not fully available. Using basic export functionality.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 CSV Export**")
            if st.button("📥 Export CSV", key="basic_csv_btn"):
                self._export_csv(df, f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        with col2:
            st.markdown("**📦 QTI Package**")
            quiz_title = st.text_input("Quiz Title:", "Question Package", key="basic_qti_title")
            if st.button("📦 Create QTI", key="basic_qti_btn"):
                st.info("Basic QTI export - enhanced features not available")
    
    def _handle_qti_export(self, 
                          df: pd.DataFrame, 
                          original_questions: List[Dict[str, Any]], 
                          quiz_title: str,
                          filename: str) -> None:
        """Handle QTI package export"""
        
        try:
            with st.spinner("🔄 Creating enhanced QTI package..."):
                
                # Step 1: Process data
                st.info("📊 Processing question data...")
                if self.data_manager:
                    processed_questions, report = self.data_manager.prepare_questions_for_export(
                        df, original_questions
                    )
                    
                    if not report["success"]:
                        st.error(f"❌ Data processing failed: {report['errors']}")
                        return
                    
                    if report.get("warnings"):
                        st.warning("⚠️ " + "; ".join(report["warnings"]))
                else:
                    processed_questions = original_questions
                
                # Step 2: Create QTI package
                st.info("📦 Generating Canvas-compatible QTI package...")
                if CANVAS_ADAPTER_AVAILABLE:
                    qti_builder = CanvasQTIAdapter()
                    package_data = qti_builder.create_package(
                        processed_questions, 
                        quiz_title,
                        filename.replace('.zip', '')
                    )
                    
                    if package_data:
                        # Provide download
                        st.download_button(
                            label="📦 Download Enhanced QTI Package",
                            data=package_data,
                            file_name=filename,
                            mime="application/zip",
                            key=f"qti_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        )
                        
                        # Show success details
                        total_points = sum(q.get('points', 1) for q in processed_questions)
                        latex_count = 0
                        if self.latex_analyzer:
                            latex_analysis = self.latex_analyzer.analyze_questions(processed_questions)
                            latex_count = latex_analysis['questions_with_latex']
                        
                        st.success(f"""
                        ✅ **Enhanced QTI Package Created Successfully!**
                        
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
                else:
                    st.error("❌ QTI export not available - Canvas adapter missing")
                
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
                label="📥 Download Enhanced CSV File",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                key=f"csv_download_{datetime.now().strftime('%H%M%S')}"
            )
            
            st.success(f"✅ Enhanced CSV export ready: `{filename}`")
            
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
    
    🚀 Enhanced export system active with custom filename support, LaTeX optimization, and improved Canvas compatibility.
    """)
    
    # Create and use the exporter
    exporter = QuestionExporter()
    exporter.render_export_interface(df, original_questions)


# Legacy compatibility functions
def export_to_csv(df: pd.DataFrame, filename: str = "filtered_questions.csv") -> None:
    """Legacy CSV export function for backward compatibility"""
    exporter = QuestionExporter()
    exporter._export_csv(df, filename)


def create_qti_package(df: pd.DataFrame, 
                      original_questions: List[Dict[str, Any]], 
                      quiz_title: str,
                      transform_json_to_csv=None,  # Legacy parameter
                      csv_to_qti=None) -> None:  # Legacy parameter
    """Legacy QTI export function for backward compatibility"""
    
    # Generate filename automatically for legacy calls
    if FILENAME_UTILS_AVAILABLE:
        naming_manager = ExportNamingManager()
        filename = naming_manager.get_qti_filename(quiz_title)
    else:
        filename = f"{quiz_title.replace(' ', '_')}.zip"
    
    exporter = QuestionExporter()
    exporter._handle_qti_export(df, original_questions, quiz_title, filename)
