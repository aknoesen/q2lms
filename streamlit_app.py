#!/usr/bin/env python3
"""
Question Database Manager - Main Streamlit Application
Clean production version with Phase 3D integration and Refactored Export System
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

# ========================================
# PHASE 3D DETECTION (SILENT)
# ========================================

def detect_phase3_modules():
    """Detect which Phase 3 modules are available (silent detection)"""
    
    phase3_status = {
        'phase3a': False,
        'phase3b': False, 
        'phase3c': False,
        'phase3d': False
    }
    
    # Check Phase 3A (silent)
    try:
        from modules.file_processor_module import FileProcessor
        phase3_status['phase3a'] = True
    except ImportError:
        pass
    
    # Check Phase 3B (silent)
    try:
        from modules.upload_state_manager import UploadState, get_upload_state
        phase3_status['phase3b'] = True
    except ImportError:
        pass
    
    # Check Phase 3C (silent)
    try:
        from modules.database_merger import MergeStrategy
        phase3_status['phase3c'] = True
    except ImportError:
        pass
    
    # Check Phase 3D (only if all others available)
    if all([phase3_status['phase3a'], phase3_status['phase3b'], phase3_status['phase3c']]):
        try:
            from modules.upload_interface_v2 import UploadInterfaceV2
            phase3_status['phase3d'] = True
        except ImportError:
            pass
    
    return phase3_status

# Import our modular components with safe error handling
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
except ImportError:
    LATEX_PROCESSOR_AVAILABLE = False

# Import existing backend modules (keeping for legacy compatibility)
try:
    from utilities.database_transformer import transform_json_to_csv
    from utilities.simple_qti import csv_to_qti
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

# ========================================
# NEW REFACTORED EXPORT SYSTEM
# ========================================

# Import the new refactored export system
try:
    from modules.exporter import integrate_with_existing_ui
    NEW_EXPORT_SYSTEM_AVAILABLE = True
    
    # Also import legacy functions for fallback
    try:
        from modules.exporter import export_to_csv, create_qti_package
        LEGACY_EXPORT_AVAILABLE = True
    except ImportError:
        LEGACY_EXPORT_AVAILABLE = False
        
except ImportError as e:
    NEW_EXPORT_SYSTEM_AVAILABLE = False
    LEGACY_EXPORT_AVAILABLE = False
    
    # Fall back to old exporter if new system not available
    try:
        from modules.exporter import export_to_csv, create_qti_package
        LEGACY_EXPORT_AVAILABLE = True
    except ImportError:
        LEGACY_EXPORT_AVAILABLE = False
        st.warning(f"⚠️ Export system not available: {e}")

# Page configuration
st.set_page_config(
    page_title="Question Database Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Detect phase status (keep for logic, don't display in sidebar)
phase3_status = detect_phase3_modules()

# Show essential module status only
if not SESSION_MANAGER_AVAILABLE:
    st.error("❌ Session management modules not available")

if not LATEX_PROCESSOR_AVAILABLE:
    st.warning("⚠️ LaTeX Processor not available")

if not BACKEND_AVAILABLE:
    st.warning("⚠️ Backend modules not found. Some legacy export features may not work.")

# Show export system status
if NEW_EXPORT_SYSTEM_AVAILABLE:
    # New system available - show success message in sidebar
    with st.sidebar:
        st.success("✅ Enhanced Export System Active")
        st.caption("• Custom filename support\n• Improved error handling\n• Better Canvas compatibility")
elif LEGACY_EXPORT_AVAILABLE:
    # Only legacy system available
    with st.sidebar:
        st.info("📦 Legacy Export System Active")
        st.caption("• Basic export functionality\n• Consider updating to enhanced system")
else:
    # No export system available
    with st.sidebar:
        st.error("❌ Export System Unavailable")

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
    
    /* Enhanced export section styling */
    .export-container {
        background: linear-gradient(135deg, #f0f8ff, #e8f5e8);
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border: 2px solid #28a745;
    }
    
    .export-enhanced-badge {
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

from modules.utils import render_latex_in_text, determine_correct_answer_letter
from modules.ui_components import display_database_summary, create_summary_charts, apply_filters
from modules.simple_browse import simple_browse_questions_tab

def render_upload_interface_smart():
    """Smart upload interface that uses Phase 3D if available, legacy otherwise"""
    
    if phase3_status['phase3d']:
        # Use Phase 3D Upload Interface V2
        st.markdown("### 📁 Upload Question Database Files")
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        
        try:
            from modules.upload_interface_v2 import UploadInterfaceV2
            upload_interface = UploadInterfaceV2()
            upload_interface.render_complete_interface()
            
            # Check if we have a DataFrame loaded
            if 'df' in st.session_state and st.session_state['df'] is not None and len(st.session_state['df']) > 0:
                has_database = True
            else:
                has_database = False
        
        except Exception as e:
            st.error(f"Upload interface error: {e}")
            st.info("Falling back to legacy interface...")
            has_database = smart_upload_interface()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # Use legacy interface
        st.markdown("### 📤 Upload Interface")
        has_database = smart_upload_interface()
    
    return has_database

def render_export_tab_enhanced(filtered_df, original_questions):
    """Render the enhanced export tab with new refactored system"""
    
    st.markdown('<div class="export-container">', unsafe_allow_html=True)
    
    if NEW_EXPORT_SYSTEM_AVAILABLE:
        # Show enhanced export badge
        st.markdown('<div class="export-enhanced-badge">🚀 Enhanced Export System</div>', unsafe_allow_html=True)
        
        # Use the new integrated export interface
        integrate_with_existing_ui(filtered_df, original_questions)
        
    else:
        # Fall back to legacy export interface
        st.warning("⚠️ Using legacy export system. For enhanced features, please update your export modules.")
        render_export_tab_legacy(filtered_df, original_questions)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_export_tab_legacy(filtered_df, original_questions):
    """Legacy export tab interface"""
    
    st.markdown("### 📥 Export Options")
    
    if not LEGACY_EXPORT_AVAILABLE:
        st.error("❌ Export functionality not available. Please check your module installation.")
        return
    
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
                if BACKEND_AVAILABLE:
                    create_qti_package(filtered_df, original_questions, qti_title, transform_json_to_csv, csv_to_qti)
                else:
                    create_qti_package(filtered_df, original_questions, qti_title)
        else:
            st.warning("No questions to export")
    
    # Show export summary
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

def main():
    """Main Streamlit application"""
    if SESSION_MANAGER_AVAILABLE:
        initialize_session_state()
    
    st.markdown("""
    # 📊 Question Database Manager
    **Web-based interface for managing educational question databases and generating Canvas-ready QTI packages**
    """)
    
    # Show system status in main interface if there are issues
    if NEW_EXPORT_SYSTEM_AVAILABLE:
        st.success("✅ Enhanced export system loaded - Custom filenames, improved Canvas compatibility, and better error handling available!")
    elif LEGACY_EXPORT_AVAILABLE:
        st.info("📦 Legacy export system active - Basic functionality available. Consider upgrading for enhanced features.")
    elif not LEGACY_EXPORT_AVAILABLE and not NEW_EXPORT_SYSTEM_AVAILABLE:
        st.error("❌ No export system available - Export functionality will be limited.")
    
    st.markdown("---")
    
    # ========================================
    # UPLOAD INTERFACE
    # ========================================
    if SESSION_MANAGER_AVAILABLE:
        has_database = render_upload_interface_smart()
    else:
        st.error("❌ Session management not available. Please check module imports.")
        has_database = False
    
    # ========================================
    # MAIN APPLICATION TABS
    # ========================================
    if has_database and 'df' in st.session_state:
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
            if SESSION_MANAGER_AVAILABLE:
                side_by_side_question_editor(filtered_df)
            else:
                st.error("❌ Question editor not available. Please check module imports.")
        
        with tab4:
            # Use the enhanced export tab
            render_export_tab_enhanced(filtered_df, original_questions)
    
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
            
            # Show enhanced features if available
            if NEW_EXPORT_SYSTEM_AVAILABLE:
                st.markdown("""
                ### 🚀 Enhanced Export Features:
                
                - **🏷️ Custom Filenames** with validation
                - **📋 Export Preview** before creating files
                - **🔢 LaTeX Analysis** and conversion
                - **⚠️ Better Error Handling** with clear messages
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
