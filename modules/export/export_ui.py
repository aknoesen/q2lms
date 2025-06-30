#!/usr/bin/env python3
"""
Export UI Module
Streamlit interface components for export functionality
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import io

# Import AppConfig for consistent button styling
try:
    from ..app_config import AppConfig
except ImportError:
    try:
        from .app_config import AppConfig
    except ImportError:
        from app_config import AppConfig

from .filename_utils import ExportNamingManager
from .latex_converter import LaTeXAnalyzer


class ExportInterface:
    """Main export interface for Streamlit"""
    
    def __init__(self):
        self.naming_manager = ExportNamingManager()
        self.latex_analyzer = LaTeXAnalyzer()
    
    def render_export_section(self, 
                            df: pd.DataFrame, 
                            original_questions: List[Dict[str, Any]],
                            export_callback) -> None:
        """
        Render the complete export interface
        
        Args:
            df: Current DataFrame with questions
            original_questions: Original question data
            export_callback: Function to call for actual export
        """
        if df is None or df.empty:
            st.warning("📋 No questions available for export. Please load a database first.")
            return
        
        st.header("📦 Export Questions")
        
        # Export type selection
        export_type = st.radio(
            "Choose Export Format:",
            ["CSV Export", "QTI Package for Canvas"],
            key="export_type_selection"
        )
        
        if export_type == "CSV Export":
            self._render_csv_export_section(df)
        else:
            self._render_qti_export_section(df, original_questions, export_callback)
    
    def _render_csv_export_section(self, df: pd.DataFrame) -> None:
        """Render CSV export interface"""
        
        st.subheader("📊 CSV Export")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Filename input
            suggested_name = f"questions_{len(df)}Q_{datetime.now().strftime('%Y%m%d')}"
            
            filename_input = st.text_input(
                "📝 Filename (without extension):",
                value=suggested_name,
                help="Enter a name for your CSV file. Extension will be added automatically.",
                key="csv_filename_input"
            )
            
            # Validate filename
            if filename_input:
                is_valid, message = self.naming_manager.validate_user_input(filename_input)
                if is_valid:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            st.metric("Questions to Export", len(df))
        
        # Export preview
        with st.expander("📋 Preview Export Data"):
            st.dataframe(df.head(3), use_container_width=True)
            st.caption(f"Showing first 3 of {len(df)} questions")
        
        # Export button
        if AppConfig.create_red_button("📥 Download CSV", key="csv_export_btn", button_type="primary-action"):
            csv_filename = self.naming_manager.get_csv_filename(filename_input)
            self._export_csv(df, csv_filename)
    
    def _render_qti_export_section(self, 
                                  df: pd.DataFrame, 
                                  original_questions: List[Dict[str, Any]],
                                  export_callback) -> None:
        """Render QTI export interface"""
        
        st.subheader("📦 Canvas QTI Package Export")
        
        # Analyze LaTeX usage
        latex_analysis = self._analyze_filtered_questions(df, original_questions)
        
        # Export configuration
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Quiz title input
            quiz_title = st.text_input(
                "🎯 Quiz/Assessment Title:",
                value="",
                help="This will be the title of your quiz in Canvas",
                key="qti_quiz_title"
            )
            
            # Filename input
            if quiz_title:
                suggested_name = self.naming_manager.suggest_name(quiz_title, len(df))
            else:
                suggested_name = f"Assessment_{len(df)}Q_{datetime.now().strftime('%Y%m%d')}"
            
            package_filename = st.text_input(
                "📝 Package Filename (without .zip):",
                value=suggested_name,
                help="Name for the QTI package file",
                key="qti_filename_input"
            )
            
            # Validate filename
            if package_filename:
                is_valid, message = self.naming_manager.validate_user_input(package_filename)
                if is_valid:
                    st.success(f"✅ {message}")
                    final_filename = self.naming_manager.get_qti_filename(package_filename)
                    st.caption(f"📁 Final filename: `{final_filename}`")
                else:
                    st.error(f"❌ {message}")
            
            # Advanced options
            with st.expander("⚙️ Advanced Options"):
                add_timestamp = st.checkbox(
                    "Add timestamp to filename",
                    help="Adds current date/time to prevent filename conflicts"
                )
                
                include_feedback = st.checkbox(
                    "Include question feedback",
                    value=True,
                    help="Include correct/incorrect feedback in exported questions"
                )
        
        with col2:
            # Export statistics
            self._render_export_stats(df, latex_analysis)
        
        # LaTeX information
        if latex_analysis['questions_with_latex'] > 0:
            self._render_latex_info(latex_analysis)
        
        # Export preview
        with st.expander("📋 Preview Questions for Export"):
            preview_df = df[['Title', 'Type', 'Topic', 'Points']].head(5)
            st.dataframe(preview_df, use_container_width=True)
            st.caption(f"Showing first 5 of {len(df)} questions")
        
        # Export button
        export_enabled = (
            package_filename and 
            self.naming_manager.validate_user_input(package_filename)[0]
        )
        
        if st.button(
            "📦 Create QTI Package", 
            type="primary", 
            disabled=not export_enabled,
            key="qti_export_btn"
        ):
            final_quiz_title = quiz_title if quiz_title else "Assessment"
            final_filename = self.naming_manager.get_qti_filename(
                package_filename, add_timestamp=add_timestamp
            )
            
            # Call the export function
            export_callback(df, original_questions, final_quiz_title, final_filename)
    
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
    
    def _analyze_filtered_questions(self, 
                                   df: pd.DataFrame, 
                                   original_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the questions that will be exported"""
        
        # Simple analysis based on DataFrame
        # In a real implementation, you'd want to sync with original_questions first
        return {
            'total_questions': len(df),
            'questions_with_latex': 0,  # Placeholder - would need actual analysis
            'latex_percentage': 0
        }
    
    def _render_export_stats(self, df: pd.DataFrame, latex_analysis: Dict[str, Any]) -> None:
        """Render export statistics"""
        
        total_points = 0
        if 'Points' in df.columns:
            total_points = df['Points'].sum()
        
        st.metric("📊 Questions", len(df))
        st.metric("🎯 Total Points", int(total_points))
        
        if latex_analysis['questions_with_latex'] > 0:
            st.metric("🔢 LaTeX Questions", latex_analysis['questions_with_latex'])
        
        # Question type breakdown
        if 'Type' in df.columns:
            type_counts = df['Type'].value_counts()
            with st.expander("📋 Question Types"):
                for qtype, count in type_counts.items():
                    st.write(f"• {qtype}: {count}")
    
    def _render_latex_info(self, latex_analysis: Dict[str, Any]) -> None:
        """Render LaTeX-specific information"""
        
        if latex_analysis['questions_with_latex'] == 0:
            return
        
        st.info(f"""
        🔢 **LaTeX Processing Information**
        
        Your export contains {latex_analysis['questions_with_latex']} questions with mathematical notation.
        
        **Canvas Compatibility:**
        - LaTeX expressions will be converted to Canvas-compatible format
        - Inline math: `$x^2$` → `\\(x^2\\)`
        - Block math: `$$E = mc^2$$` → `\\[E = mc^2\\]`
        - Compatible with Canvas MathJax 2.7.7
        
        ✅ **Ready for Canvas Import**
        """)


class ExportProgressIndicator:
    """Handles progress indication during export operations"""
    
    def __init__(self):
        self.progress_bar = None
        self.status_text = None
    
    def start_progress(self, title: str = "Processing..."):
        """Start showing progress"""
        self.status_text = st.empty()
        self.progress_bar = st.progress(0)
        self.status_text.text(title)
    
    def update_progress(self, progress: float, message: str):
        """Update progress (0.0 to 1.0)"""
        if self.progress_bar:
            self.progress_bar.progress(progress)
        if self.status_text:
            self.status_text.text(message)
    
    def finish_progress(self, success_message: str = "Complete!"):
        """Finish progress indication"""
        if self.progress_bar:
            self.progress_bar.progress(1.0)
        if self.status_text:
            self.status_text.success(success_message)


class ExportResultsDisplay:
    """Handles displaying export results and download links"""
    
    @staticmethod
    def show_success(export_type: str, 
                    filename: str, 
                    question_count: int,
                    additional_info: Optional[Dict[str, Any]] = None):
        """Show successful export results"""
        
        st.success(f"""
        ✅ **{export_type} Export Successful!**
        
        📁 **Filename:** `{filename}`
        📊 **Questions Exported:** {question_count}
        """)
        
        if additional_info:
            if export_type == "QTI Package":
                total_points = additional_info.get('total_points', 0)
                latex_count = additional_info.get('latex_questions', 0)
                
                st.info(f"""
                🎯 **Package Details:**
                - Total Points: {total_points}
                - LaTeX Questions: {latex_count}
                - Canvas Compatible: ✅
                
                **Next Steps:**
                1. Download the package below
                2. Go to Canvas → Quizzes → Import QTI Package
                3. Upload your downloaded file
                """)
    
    @staticmethod
    def show_error(error_message: str, details: Optional[str] = None):
        """Show export error"""
        st.error(f"❌ Export failed: {error_message}")
        
        if details:
            with st.expander("🔍 Error Details"):
                st.code(details)
    
    @staticmethod
    def show_warnings(warnings: List[str]):
        """Show export warnings"""
        if warnings:
            warning_text = "\n".join(f"• {warning}" for warning in warnings)
            st.warning(f"⚠️ **Warnings:**\n{warning_text}")


# Convenience functions for integration with existing code
def render_filename_input(label: str, 
                         default_value: str = "",
                         help_text: str = "") -> Tuple[str, bool]:
    """
    Render filename input with validation
    
    Returns:
        Tuple of (filename, is_valid)
    """
    naming_manager = ExportNamingManager()
    
    filename = st.text_input(label, value=default_value, help=help_text)
    
    if filename:
        is_valid, message = naming_manager.validate_user_input(filename)
        if is_valid:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        return filename, is_valid
    
    return "", False


def render_export_preview(df: pd.DataFrame, max_rows: int = 5):
    """Render export preview table"""
    if df is None or df.empty:
        st.warning("No data to preview")
        return
    
    preview_cols = ['Title', 'Type', 'Topic', 'Points']
    available_cols = [col for col in preview_cols if col in df.columns]
    
    if available_cols:
        preview_df = df[available_cols].head(max_rows)
        st.dataframe(preview_df, use_container_width=True)
        st.caption(f"Showing first {min(max_rows, len(df))} of {len(df)} questions")
    else:
        st.dataframe(df.head(max_rows), use_container_width=True)
