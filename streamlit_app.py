#!/usr/bin/env python3
"""
Question Database Manager - Main Streamlit Application
Clean production version with integrated upload and export systems
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

# Import modules
import sys
import os

# Add modules directory to Python path
modules_path = os.path.join(os.path.dirname(__file__), 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# ========================================
# IMPORT CORE COMPONENTS
# ========================================

# Import session management
try:
    from modules.session_manager import (
        initialize_session_state, clear_session_state, 
        display_enhanced_database_status, has_active_database
    )
    from modules.database_processor import (
        save_question_changes, delete_question, validate_single_question
    )
    SESSION_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Session management modules not available: {e}")
    SESSION_MANAGER_AVAILABLE = False

# Import upload system
try:
    from modules.upload_interface_v2 import UploadInterfaceV2
    UPLOAD_SYSTEM_AVAILABLE = True
except ImportError as e:
    # Fallback to basic upload
    try:
        from modules.upload_handler import smart_upload_interface
        UPLOAD_SYSTEM_AVAILABLE = False
        BASIC_UPLOAD_AVAILABLE = True
    except ImportError:
        st.error(f"❌ Upload system not available: {e}")
        UPLOAD_SYSTEM_AVAILABLE = False
        BASIC_UPLOAD_AVAILABLE = False

# Import question editor
try:
    from modules.question_editor import side_by_side_question_editor
    QUESTION_EDITOR_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Question editor not available: {e}")
    QUESTION_EDITOR_AVAILABLE = False

# Import LaTeX processor
try:
    from modules.latex_processor import LaTeXProcessor, clean_text
    LATEX_PROCESSOR_AVAILABLE = True
except ImportError:
    LATEX_PROCESSOR_AVAILABLE = False

# Import export system
try:
    from modules.exporter import integrate_with_existing_ui
    EXPORT_SYSTEM_AVAILABLE = True
except ImportError as e:
    EXPORT_SYSTEM_AVAILABLE = False
    st.error(f"❌ Export system not available: {e}")

# Import UI components
try:
    from modules.utils import render_latex_in_text, determine_correct_answer_letter
    from modules.ui_components import display_database_summary, create_summary_charts, apply_filters
    from modules.simple_browse import simple_browse_questions_tab
    UI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ UI components not available: {e}")
    UI_COMPONENTS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Question Database Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Show system status in sidebar
with st.sidebar:
    st.markdown("### 🔧 System Status")
    
    if SESSION_MANAGER_AVAILABLE:
        st.success("✅ Session Management")
    else:
        st.error("❌ Session Management")
    
    if UPLOAD_SYSTEM_AVAILABLE:
        st.success("✅ Advanced Upload System")
    elif BASIC_UPLOAD_AVAILABLE:
        st.info("📤 Basic Upload System")
    else:
        st.error("❌ Upload System")
    
    if EXPORT_SYSTEM_AVAILABLE:
        st.success("✅ Export System")
        st.caption("• Custom filenames\n• Canvas compatibility\n• LaTeX optimization")
    else:
        st.error("❌ Export System")
    
    if QUESTION_EDITOR_AVAILABLE:
        st.success("✅ Question Editor")
    else:
        st.error("❌ Question Editor")
    
    if LATEX_PROCESSOR_AVAILABLE:
        st.success("✅ LaTeX Processor")
    else:
        st.warning("⚠️ LaTeX Processor")

# Custom CSS
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
    
    /* Upload interface container styling */
    .upload-container {
        background: linear-gradient(135deg, #e3f2fd, #f0f8ff);
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border: 2px solid #2196f3;
    }
    
    /* Export section styling */
    .export-container {
        background: linear-gradient(135deg, #f0f8ff, #e8f5e8);
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border: 2px solid #28a745;
    }
    
    .export-badge {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
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

def render_upload_interface():
    """Render the upload interface"""
    
    st.markdown("### 📁 Upload Question Database Files")
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    
    if UPLOAD_SYSTEM_AVAILABLE:
        # Use advanced upload system
        try:
            upload_interface = UploadInterfaceV2()
            upload_interface.render_complete_interface()
            
            # Check if we have a DataFrame loaded
            has_database = (
                'df' in st.session_state and 
                st.session_state['df'] is not None and 
                len(st.session_state['df']) > 0
            )
        
        except Exception as e:
            st.error(f"Upload interface error: {e}")
            has_database = False
    
    elif BASIC_UPLOAD_AVAILABLE:
        # Use basic upload system
        try:
            has_database = smart_upload_interface()
        except Exception as e:
            st.error(f"Basic upload error: {e}")
            has_database = False
    
    else:
        # No upload system available
        st.error("❌ Upload functionality not available")
        st.info("Please ensure upload modules are properly installed.")
        has_database = False
    
    st.markdown('</div>', unsafe_allow_html=True)
    return has_database

def render_export_tab(filtered_df, original_questions):
    """Render the export tab"""
    
    st.markdown('<div class="export-container">', unsafe_allow_html=True)
    
    if EXPORT_SYSTEM_AVAILABLE:
        # Show export badge
        st.markdown('<div class="export-badge">🚀 Export System</div>', unsafe_allow_html=True)
        
        # Use the modern export interface
        integrate_with_existing_ui(filtered_df, original_questions)
        
    else:
        # Export system not available
        st.error("❌ Export functionality not available")
        st.info("""
        **Export system is not properly installed.**
        
        Please ensure all required modules are available:
        - modules/export/ package
        - All export module dependencies
        
        Check the error messages above for specific missing components.
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    if SESSION_MANAGER_AVAILABLE:
        initialize_session_state()
    
    st.markdown("""
    # 📊 Question Database Manager
    **Web-based interface for managing educational question databases and generating Canvas-ready QTI packages**
    """)
    
    # Show overall system status
    critical_systems = [SESSION_MANAGER_AVAILABLE, UI_COMPONENTS_AVAILABLE]
    essential_systems = [UPLOAD_SYSTEM_AVAILABLE or BASIC_UPLOAD_AVAILABLE, EXPORT_SYSTEM_AVAILABLE]
    
    if all(critical_systems) and all(essential_systems):
        st.success("✅ All systems operational - Full functionality available!")
    elif all(critical_systems):
        st.warning("⚠️ Core systems operational - Some features may be limited")
    else:
        st.error("❌ Critical systems offline - Functionality severely limited")
    
    st.markdown("---")
    
    # ========================================
    # UPLOAD INTERFACE
    # ========================================
    if SESSION_MANAGER_AVAILABLE:
        has_database = render_upload_interface()
    else:
        st.error("❌ Cannot load upload interface - session management unavailable")
        has_database = False
    
    # ========================================
    # MAIN APPLICATION TABS
    # ========================================
    if has_database and 'df' in st.session_state and UI_COMPONENTS_AVAILABLE:
        df = st.session_state['df']
        metadata = st.session_state['metadata']
        original_questions = st.session_state['original_questions']
        filtered_df = apply_filters(df)
        
        # Show success message
        st.success(f"✅ Database loaded successfully! {len(df)} questions ready.")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Browse Questions", "📝 Browse & Edit", "📥 Export"])
        
        with tab1:
            display_database_summary(df, metadata)
            st.markdown("---")
            create_summary_charts(df)
        
        with tab2:
            simple_browse_questions_tab(filtered_df)
        
        with tab3:
            if QUESTION_EDITOR_AVAILABLE:
                side_by_side_question_editor(filtered_df)
            else:
                st.error("❌ Question editor not available")
                st.info("You can still browse questions in the other tabs.")
        
        with tab4:
            render_export_tab(filtered_df, original_questions)
    
    elif has_database and not UI_COMPONENTS_AVAILABLE:
        st.error("❌ Database loaded but UI components not available")
        st.info("Please check that all required modules are installed.")
    
    else:
        # No database loaded - show getting started
        st.markdown("---")
        st.markdown("## 🚀 Getting Started")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📋 What You Can Do:
            
            1. **📤 Upload** JSON question databases (single or multiple files)
            2. **📝 Browse** questions with live LaTeX preview
            3. **🎯 Filter** by topic, difficulty, and type
            4. **📦 Export** to Canvas-ready QTI packages
            5. **📊 Analyze** question distributions and statistics
            6. **🔧 Edit** questions with real-time preview
            """)
            
            # Show export features if available
            if EXPORT_SYSTEM_AVAILABLE:
                st.markdown("""
                ### 🚀 Export Features:
                
                - **🏷️ Custom Filenames** with validation
                - **📋 Export Preview** before creating files
                - **🔢 LaTeX Analysis** and conversion
                - **⚠️ Clear Error Handling** with helpful messages
                - **🎯 Canvas Optimization** for seamless import
                """)
        
        with col2:
            st.markdown("""
            ### 🎓 Perfect for Instructors:
            
            - **Course Planning** with mathematical notation
            - **LaTeX Support** for engineering formulas
            - **Multiple Question Types** (MC, numerical, T/F, fill-in-blank)
            - **Topic Organization** with subtopics
            - **Canvas Integration** via QTI export
            - **Conflict Resolution** when merging multiple files
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
