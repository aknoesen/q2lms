#!/usr/bin/env python3
"""
Question Database Manager - Main Streamlit Application (Modular Version)
Replaces MATLAB QuestionDatabaseManager with modern web interface
Supports Phase 3 & 4 JSON formats with subtopic organization
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import zipfile
import os
import io
import base64
from datetime import datetime
import re
from modules.question_editor import side_by_side_question_editor

# Import modules
import sys
import os

# Add modules directory to Python path
modules_path = os.path.join(os.path.dirname(__file__), 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# Import our modular components
try:
    from modules.session_manager import (
        initialize_session_state, clear_session_state, 
        display_enhanced_database_status, has_active_database
    )
    from modules.upload_handler import smart_upload_interface
    from modules.database_processor import (
        save_question_changes, delete_question, validate_single_question
    )
    SESSION_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Module import error: {e}")
    SESSION_MANAGER_AVAILABLE = False

# Test LaTeX processor integration
try:
    from modules.latex_processor import LaTeXProcessor, clean_text
    LATEX_PROCESSOR_AVAILABLE = True
except ImportError as e:
    LATEX_PROCESSOR_AVAILABLE = False

# Import existing backend modules
try:
    from utilities.database_transformer import transform_json_to_csv
    from utilities.simple_qti import csv_to_qti
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Question Database Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Show module status
if SESSION_MANAGER_AVAILABLE:
    st.success("✅ Modular session management ready!")
else:
    st.error("❌ Session management modules not available")

if LATEX_PROCESSOR_AVAILABLE:
    st.success("✅ LaTeX Processor ready!")
else:
    st.error("❌ LaTeX Processor not available")

if not BACKEND_AVAILABLE:
    st.error("⚠️ Backend modules not found. Please ensure database_transformer.py and simple_qti.py are in the 'modules' folder.")

# Custom CSS for better LaTeX rendering and styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .latex-preview {
        background-color: #fafafa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        font-family: 'Times New Roman', serif;
    }
    .question-preview {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Make tabs more prominent */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #f1f3f4;
        padding: 12px;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        padding: 15px 25px;
        background-color: white;
        border-radius: 10px;
        color: #333;
        font-weight: 700;
        font-size: 17px;
        border: 2px solid #e0e0e0;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(0,0,0,0.15);
        border-color: #1f77b4;
        background-color: #f8f9ff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1f77b4, #0d6efd);
        color: white !important;
        border-color: #0d6efd;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(31, 119, 180, 0.3);
    }
</style>
""", unsafe_allow_html=True)

from modules.utils import render_latex_in_text, determine_correct_answer_letter
from modules.ui_components import display_database_summary, create_summary_charts, apply_filters
from modules.exporter import export_to_csv, create_qti_package
from modules.simple_browse import simple_browse_questions_tab

def main():
    """Main Streamlit application with modular architecture"""
    if SESSION_MANAGER_AVAILABLE:
        initialize_session_state()
    st.markdown("""
    # 📊 Question Database Manager
    **Web-based interface for managing educational question databases and generating Canvas-ready QTI packages**
    ---
    """)
    if SESSION_MANAGER_AVAILABLE:
        has_database = smart_upload_interface()
    else:
        st.error("❌ Session management not available. Please check module imports.")
        has_database = False
    if has_database and 'df' in st.session_state:
        df = st.session_state['df']
        metadata = st.session_state['metadata']
        original_questions = st.session_state['original_questions']
        filtered_df = apply_filters(df)
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Browse Questions", "📝 Browse & Edit", "📥 Export"])
        with tab1:
            display_database_summary(df, metadata)
            st.markdown("---")
            create_summary_charts(df)
        with tab2:
            simple_browse_questions_tab(filtered_df)
        with tab3:
            if SESSION_MANAGER_AVAILABLE:
                side_by_side_question_editor(filtered_df)
            else:
                st.error("❌ Question editor not available. Please check module imports.")
        with tab4:
            st.markdown("### 📥 Export Options")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📊 CSV Export**")
                st.markdown("Export filtered questions as CSV file for further analysis or backup.")
                if len(filtered_df) > 0:
                    export_to_csv(filtered_df, f"filtered_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                else:
                    st.warning("No questions to export")
            with col2:
                st.markdown("**📦 QTI Package**")
                st.markdown("Create Canvas-ready QTI package for direct import into your LMS.")
                if len(filtered_df) > 0:
                    qti_title = st.text_input("QTI Package Name", "Question_Package")
                    if st.button("🚀 Generate QTI Package"):
                        create_qti_package(filtered_df, original_questions, qti_title, transform_json_to_csv, csv_to_qti)
                else:
                    st.warning("No questions to export")
            st.markdown("---")
            st.markdown("### 📋 Export Summary")
            if len(filtered_df) > 0:
                difficulty_counts = filtered_df['Difficulty'].value_counts()
                type_counts = filtered_df['Type'].value_counts()
                topic_counts = filtered_df['Topic'].value_counts()
                total_points = filtered_df['Points'].sum()
                avg_points = filtered_df['Points'].mean()
                st.info(f"""**Current Selection:**\n- **Questions:** {len(filtered_df)}\n- **Total Points:** {total_points:.0f}\n- **Average Points:** {avg_points:.1f}\n\n**Difficulty Distribution:**\n{chr(10).join([f"- {diff}: {count}" for diff, count in difficulty_counts.items()])}\n\n**Question Types:**\n{chr(10).join([f"- {qtype}: {count}" for qtype, count in type_counts.items()])}\n\n**Topics Covered:**\n{chr(10).join([f"- {topic}: {count}" for topic, count in topic_counts.items()])}""")
            else:
                st.warning("No questions selected for export")
    else:
        # No database loaded - show helpful information
        st.markdown("---")
        st.markdown("## 🚀 Getting Started")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📋 What You Can Do:
            
            1. **📤 Upload** JSON question databases
            2. **📝 Browse** questions with live LaTeX preview
            3. **🎯 Filter** by topic, difficulty, and type
            4. **📦 Export** to Canvas-ready QTI packages
            5. **📊 Analyze** question distributions and statistics
            """)
        
        with col2:
            st.markdown("""
            ### 🎓 Perfect for Instructors:
            
            - **Course Planning** with mathematical notation
            - **LaTeX Support** for engineering formulas
            - **Multiple Question Types** (MC, numerical, T/F)
            - **Topic Organization** with subtopics
            - **Canvas Integration** via QTI export
            """)
        
        # Show sample file format
        with st.expander("📄 Sample JSON Format", expanded=False):
            sample_json = {
                "questions": [
                    {
                        "title": "Circuit Analysis",
                        "type": "multiple_choice",
                        "question_text": "What is the impedance of a circuit with R = 100 Ω and L = 50 mH at f = 1000 Hz?",
                        "choices": [
                            "100 + j314 Ω",
                            "100 + j50 Ω", 
                            "314 + j100 Ω",
                            "50 + j100 Ω"
                        ],
                        "correct_answer": "A",
                        "points": 2,
                        "topic": "Circuit Analysis",
                        "subtopic": "AC Circuits",
                        "difficulty": "Medium",
                        "feedback_correct": "Correct! Z = R + jωL = 100 + j(2π×1000×0.05) = 100 + j314 Ω",
                        "feedback_incorrect": "Remember that impedance Z = R + jωL for an RL circuit."
                    }
                ],
                "metadata": {
                    "subject": "Electrical Engineering",
                    "format_version": "Phase Four",
                    "generation_date": "2024-12-19"
                }
            }
            
            st.json(sample_json, expanded=False)


if __name__ == "__main__":
    main()