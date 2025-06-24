#!/usr/bin/env python3
"""
Q2LMS - Question Database Manager
Web-based interface for managing educational question databases and generating LMS-ready QTI packages
"""

import streamlit as st


# Page configuration with new branding
st.set_page_config(
    page_title="Q2LMS - Question Database Manager",
    page_icon="assets/favicon.ico",  # ← Your browser tab icon
    layout="wide",
    initial_sidebar_state="expanded"
)


# Add MathJax configuration
st.markdown("""
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']]
  }
};
</script>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
""", unsafe_allow_html=True)



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



# Show system status in sidebar
with st.sidebar:
        # Add logo at top of sidebar
    st.image("assets/q2lms_icon.svg", width=120)  # Slightly smaller for sidebar
    st.markdown("---")  # Nice separator
    
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
        st.caption("• Custom filenames\n• LMS compatibility\n• LaTeX optimization")
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

# Custom CSS with Q2LMS branding colors
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .q2lms-brand {
    color: #1f77b4; /* Blue to match the Q2 elements in icon */
    font-weight: 800;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 1rem;
    }
    
    .brand-tagline {
        color: #6b7280;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 500;
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
    
    /* Q2LMS feature highlights */
    .feature-card {
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# CLEAN MULTI-SUBJECT FILTER - Add at line 279 in streamlit_app.py
# ====================================================================

def enhanced_subject_filtering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Multi-subject filter using the correct 'Topic' column
    """
    if df.empty:
        return df
    
    # Use 'Topic' instead of 'Subject'
    if 'Topic' not in df.columns:
        return df
    
    # Get unique topics
    topics = sorted(df['Topic'].dropna().unique())
    if not topics:
        return df
    
    # Add topic filter to sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Topic Filter")
    
    selected_topics = st.sidebar.multiselect(
        "Choose topics:",
        options=topics,
        default=topics,  # Start with all topics selected
        key="topic_filter_multi",
        help="Select multiple topics to include questions from any chosen topic"
    )
    
    # Apply filtering
    if selected_topics:
        filtered_df = df[df['Topic'].isin(selected_topics)]
        st.sidebar.success(f"✅ {len(selected_topics)} of {len(topics)} topics selected")
    else:
        filtered_df = pd.DataFrame()  # Empty if nothing selected
        st.sidebar.warning("⚠️ No topics selected")
    
    st.sidebar.markdown("---")
    
    return filtered_df
# ====================================================================
# INTEGRATION: Replace this ONE line in main():
# 
# OLD: filtered_df = apply_filters(df)
# NEW: filtered_df = enhanced_subject_filtering(df)
# ====================================================================

# ====================================================================
# PHASE 8B: GRACEFUL EXIT MECHANISM
# Add these functions to your streamlit_app.py after the topic filtering functions
# ====================================================================

import os
import sys

def cleanup_session_state():
    """
    Clean up session state and temporary data before exit.
    """
    cleanup_items = []
    
    # List of session state keys to clean up
    keys_to_clean = [
        'df', 'metadata', 'original_questions', 'selected_topics',
        'topic_filter_multi', 'difficulty_filter', 'type_filter',
        'uploaded_files', 'merge_conflicts', 'file_data'
    ]
    
    for key in keys_to_clean:
        if key in st.session_state:
            del st.session_state[key]
            cleanup_items.append(key)
    
    return cleanup_items

def offer_data_preservation():
    """
    Offer user options to save their work before exiting.
    Returns True if user wants to proceed with exit, False to cancel.
    """
    st.markdown("### 💾 Save Your Work Before Exiting")
    
    # Check if there's data to save
    has_data = 'df' in st.session_state and not st.session_state['df'].empty
    
    if has_data:
        df = st.session_state['df']
        st.info(f"📊 You have {len(df)} questions loaded that will be lost on exit.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Quick Save as JSON", key="quick_save_json"):
                try:
                    # Create a quick export
                    export_data = {
                        "questions": st.session_state.get('original_questions', []),
                        "metadata": st.session_state.get('metadata', {}),
                        "export_timestamp": datetime.now().isoformat(),
                        "total_questions": len(df)
                    }
                    
                    # Create download
                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        "📥 Download JSON Backup",
                        data=json_str,
                        file_name=f"q2lms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_backup"
                    )
                    st.success("✅ Backup ready for download!")
                    
                except Exception as e:
                    st.error(f"❌ Error creating backup: {e}")
        
        with col2:
            # Show current filter status
            selected_topics = st.session_state.get('topic_filter_multi', [])
            if selected_topics:
                st.write("**Current Filters:**")
                st.write(f"• Topics: {len(selected_topics)} selected")
                if len(selected_topics) < 5:
                    for topic in selected_topics:
                        st.write(f"  - {topic}")
                else:
                    st.write(f"  - {', '.join(selected_topics[:3])}... (+{len(selected_topics)-3} more)")
    
    else:
        st.info("ℹ️ No data currently loaded - safe to exit.")
    
    # Exit confirmation
    st.markdown("---")
    st.markdown("### ⚠️ Confirm Exit")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚪 Exit Q2LMS", type="primary", key="confirm_exit"):
            return True
    
    with col2:
        if st.button("❌ Cancel", key="cancel_exit"):
            return False
    
    with col3:
        st.write("")  # Spacer
    
    return None  # No decision made yet

def show_exit_interface():
    """
    Display the graceful exit interface with improved visibility.
    """
    # Force scroll to top and clear main content area
    st.markdown("""
    <script>
        window.scrollTo(0, 0);
    </script>
    """, unsafe_allow_html=True)
    
    # Clear visual space and make exit interface prominent
    st.markdown("# 🚪 Exit Q2LMS")
    st.markdown("**Safely close the application with optional data preservation.**")
    st.markdown("---")
    
    # Show current session info prominently at the top
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Current Session Info")
        if 'df' in st.session_state and not st.session_state['df'].empty:
            df = st.session_state['df']
            st.success(f"**Questions Loaded:** {len(df)}")
            
            if 'metadata' in st.session_state:
                metadata = st.session_state['metadata']
                st.write(f"**Database:** {metadata.get('subject', 'Unknown')}")
                st.write(f"**Format:** {metadata.get('format_version', 'Unknown')}")
            
            # Show active filters
            selected_topics = st.session_state.get('topic_filter_multi', [])
            if selected_topics:
                filtered_count = len(df[df['Topic'].isin(selected_topics)]) if 'Topic' in df.columns else len(df)
                st.write(f"**Filtered Questions:** {filtered_count} (from {len(selected_topics)} topics)")
        else:
            st.info("**No data currently loaded - safe to exit**")
        
        st.write(f"**Session Started:** {st.session_state.get('session_start_time', 'Unknown')}")
    
    with col2:
        # Quick return option prominently displayed
        st.markdown("### 🔙 Quick Actions")
        if st.button("🔙 Return to App", type="secondary", key="quick_return", use_container_width=True):
            if 'show_exit_interface' in st.session_state:
                del st.session_state['show_exit_interface']
            st.rerun()
    
    st.markdown("---")
    
    # Data preservation section
    has_data = 'df' in st.session_state and not st.session_state['df'].empty
    
    if has_data:
        st.markdown("### 💾 Save Your Work Before Exiting")
        df = st.session_state['df']
        
        # Make save option more prominent
        st.warning(f"⚠️ You have **{len(df)} questions** loaded that will be lost on exit.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 Quick Save as JSON", key="quick_save_json", type="primary", use_container_width=True):
                try:
                    # Create a quick export
                    export_data = {
                        "questions": st.session_state.get('original_questions', []),
                        "metadata": st.session_state.get('metadata', {}),
                        "export_timestamp": datetime.now().isoformat(),
                        "total_questions": len(df)
                    }
                    
                    # Create download
                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        "📥 Download JSON Backup",
                        data=json_str,
                        file_name=f"q2lms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_backup",
                        use_container_width=True
                    )
                    st.success("✅ Backup ready for download!")
                    
                except Exception as e:
                    st.error(f"❌ Error creating backup: {e}")
        
        with col2:
            # Show current filter status more clearly
            selected_topics = st.session_state.get('topic_filter_multi', [])
            if selected_topics:
                st.markdown("**Current Filters:**")
                st.write(f"📋 **Topics:** {len(selected_topics)} selected")
                if len(selected_topics) <= 3:
                    for topic in selected_topics:
                        st.write(f"  • {topic}")
                else:
                    st.write(f"  • {', '.join(selected_topics[:2])}... (+{len(selected_topics)-2} more)")
    else:
        st.success("✅ No data currently loaded - safe to exit")
    
    # Exit confirmation section - make it prominent
    st.markdown("---")
    st.markdown("### ⚠️ Confirm Exit")
    
    # Make exit/cancel buttons more prominent
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚪 Exit Q2LMS", type="primary", key="confirm_exit", use_container_width=True):
            # User confirmed exit
            st.balloons()  # Visual feedback
            st.success("👋 **Exiting Q2LMS...**")
            
            # Cleanup session
            cleaned_items = cleanup_session_state()
            
            if cleaned_items:
                st.info(f"🧹 Cleaned up: {', '.join(cleaned_items[:3])}{'...' if len(cleaned_items) > 3 else ''}")
            
            # Show exit message prominently
            st.markdown("---")
            st.markdown("""
            ## ✅ Exit Complete
            
            **Thank you for using Q2LMS!**
            
            - ✅ Session data has been cleared
            - ✅ Resources have been freed  
            - ✅ Application is ready to close
            
            **To restart:** Refresh your browser or run `streamlit run streamlit_app.py`
            """)
            
            # Instructions for closing
            st.info("""
            **How to close this application:**
            - **Browser:** Close this tab or window
            - **Local/Terminal:** Press `Ctrl+C` in your command prompt
            """)
            
            # Stop the app from running further
            st.stop()
    
    with col2:
        if st.button("❌ Cancel Exit", type="secondary", key="cancel_exit", use_container_width=True):
            # User cancelled - return to app
            if 'show_exit_interface' in st.session_state:
                del st.session_state['show_exit_interface']
            st.success("Exit cancelled - returning to app...")
            st.rerun()
    
    with col3:
        # Show helpful tip
        st.markdown("💡 **Tip:** Use the sidebar exit button anytime")

# Alternative: Enhanced exit button function with better UX
def add_exit_button_to_sidebar():
    """
    Add an exit button to the sidebar with improved UX.
    """
    # Add exit button at bottom of sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚪 Application")
    
    # Make the exit button more prominent in sidebar
    if st.sidebar.button("🚪 Exit Q2LMS", 
                        key="sidebar_exit_button", 
                        help="Safely exit the application with data preservation options",
                        use_container_width=True):
        st.session_state['show_exit_interface'] = True
        # Clear any existing error messages
        st.session_state['exit_message'] = "Preparing exit interface..."
        st.rerun()

def add_exit_button_to_sidebar():
    """
    Add an exit button to the sidebar.
    Call this function in your main() function.
    """
    # Add exit button at bottom of sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚪 Application")
    
    if st.sidebar.button("🚪 Exit Q2LMS", key="sidebar_exit_button", help="Safely exit the application"):
        st.session_state['show_exit_interface'] = True
        st.rerun()

# ====================================================================
# INTEGRATION INSTRUCTIONS FOR MAIN APPLICATION
# ====================================================================

def integrate_graceful_exit_with_main():
    """
    Integration instructions for your main() function:
    
    1. Add this call in your main() function BEFORE the tab creation:
       add_exit_button_to_sidebar()
    
    2. Add this check BEFORE your existing tabs:
       if st.session_state.get('show_exit_interface', False):
           show_exit_interface()
           return  # Exit early, don't show main tabs
    
    3. Add session start time tracking at the beginning of main():
       if 'session_start_time' not in st.session_state:
           st.session_state['session_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    """
    pass

# ====================================================================
# EXAMPLE INTEGRATION - Modify your main() function like this:
# ====================================================================

def example_main_function_with_exit():
    """
    Example showing how to integrate graceful exit into your existing main() function
    """
    # Initialize session state
    if SESSION_MANAGER_AVAILABLE:
        initialize_session_state()
    
    # Track session start time
    if 'session_start_time' not in st.session_state:
        st.session_state['session_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add exit button to sidebar
    add_exit_button_to_sidebar()
    
    # Check if exit interface should be shown
    if st.session_state.get('show_exit_interface', False):
        show_exit_interface()
        return  # Exit early, don't show main application
    
    # Your existing branding header
    st.markdown('<div class="q2lms-brand">Q2LMS</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-tagline">Transform questions into LMS-ready packages with seamless QTI export</div>', unsafe_allow_html=True)
    



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
    
    # Track session start time
    if 'session_start_time' not in st.session_state:
        st.session_state['session_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

   # Check if exit interface should be shown
    if st.session_state.get('show_exit_interface', False):
        show_exit_interface()
        return  # Exit early, don't show main application
    
    # Updated branding header
    #col1, col2, col3 = st.columns([1, 2, 1])
    #with col2:
    #    st.image("assets/q2lms_icon.svg", width=150)  # ← Always crisp

    st.markdown('<div class="q2lms-brand">Q2LMS</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-tagline">Transform questions into LMS-ready packages with seamless QTI export</div>', unsafe_allow_html=True)
    add_exit_button_to_sidebar()



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
        filtered_df = enhanced_subject_filtering(df)
        
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
        st.markdown("## 🚀 Getting Started with Q2LMS")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("""
            ### 📋 Core Features:
            
            1. **📤 Upload** JSON question databases (single or multiple files)
            2. **📝 Browse** questions with live LaTeX preview  
            3. **🎯 Filter** by topic, difficulty, and type
            4. **📦 Export** to LMS-ready QTI packages
            5. **📊 Analyze** question distributions and statistics
            6. **🔧 Edit** questions with real-time preview
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show export features if available
            if EXPORT_SYSTEM_AVAILABLE:
                st.markdown('<div class="feature-card">', unsafe_allow_html=True)
                st.markdown("""
                ### 🚀 Export Features:
                
                - **🏷️ Custom Filenames** with validation
                - **📋 Export Preview** before creating files
                - **🔢 LaTeX Analysis** and conversion
                - **⚠️ Clear Error Handling** with helpful messages
                - **🎯 LMS Optimization** for seamless import
                """)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("""
            ### 🎓 Perfect for Instructors:
            
            - **Course Planning** with mathematical notation
            - **LaTeX Support** for engineering formulas
            - **Multiple Question Types** (MC, numerical, T/F, fill-in-blank)
            - **Topic Organization** with subtopics
            - **LMS Integration** via QTI export
            - **Conflict Resolution** when merging multiple files
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("""
            ### 🔄 Supported LMS Platforms:
            
            - **Canvas** (primary optimization)
            - **Blackboard** Learn
            - **Moodle**
            - **D2L Brightspace**
            - **Any QTI 2.1 compatible** system
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
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