#!/usr/bin/env python3
"""
Q2LMS - Question Database Manager
Final working version with fork feature
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
from modules.upload_interface_v2 import UploadInterfaceV2, ProcessingState  # <-- Fixed import

# Page configuration
st.set_page_config(
    page_title="Q2LMS - Question Database Manager",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session():
    """Initialize session state"""
    if 'session_start_time' not in st.session_state:
        st.session_state['session_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def load_core_modules():
    """Load core modules safely"""
    modules = {}
    
    try:
        from modules.app_config import get_app_config
        modules['app_config'] = get_app_config()
    except Exception as e:
        st.error(f"App config failed: {e}")
        return None
    
    try:
        from modules.exit_manager import get_exit_manager
        modules['exit_manager'] = get_exit_manager()
    except Exception as e:
        st.error(f"Exit manager failed: {e}")
        return None
    
    try:
        from modules.ui_manager import get_ui_manager
        modules['ui_manager'] = get_ui_manager(modules['app_config'])
    except Exception as e:
        st.error(f"UI manager failed: {e}")
        return None
    
    return modules

def load_fork_components():
    """Load fork components directly (bypass app_config detection)"""
    fork_components = {}
    
    try:
        from modules.operation_mode_manager import get_operation_mode_manager
        fork_components['mode_manager'] = get_operation_mode_manager()
        
        from modules.question_flag_manager import QuestionFlagManager
        fork_components['flag_manager'] = QuestionFlagManager()
        
        from modules.interface_select_questions import SelectQuestionsInterface
        fork_components['select_interface'] = SelectQuestionsInterface()
        
        from modules.interface_delete_questions import DeleteQuestionsInterface
        fork_components['delete_interface'] = DeleteQuestionsInterface()
        
        return fork_components
        
    except Exception as e:
        st.warning(f"Fork feature not available: {e}")
        return None

def main():
    """Main application with working fork feature"""
    
    # Initialize session
    initialize_session()
    
    # Load core modules
    modules = load_core_modules()
    if not modules:
        st.error("❌ Failed to load core modules")
        return
    
    app_config = modules['app_config']
    exit_manager = modules['exit_manager']
    ui_manager = modules['ui_manager']
    
    # Load fork components directly
    fork_components = load_fork_components()
    fork_available = fork_components is not None
    
    # Apply configuration
    app_config.apply_mathjax_config()
    app_config.apply_custom_css()
    
    # Initialize session if session manager available
    if app_config.is_available('session_manager'):
        session_manager = app_config.get_feature('session_manager')
        session_manager['initialize_session_state']()
    
    # Sidebar with logo
    app_config.render_sidebar_header()

    # Check for exit request
    if exit_manager.check_for_exit_request():
        return
    
    # Main branding
    ui_manager.render_branding_header()
    st.markdown("---")
    
    # Upload interface
    if app_config.is_available('session_manager'):
        has_database = ui_manager.render_upload_interface()
    else:
        st.error("❌ Session management not available")
        has_database = False
    
    # Check what we have in session state
    has_df = 'df' in st.session_state and st.session_state['df'] is not None and len(st.session_state['df']) > 0
    has_ui_components = app_config.is_available('ui_components')
    
    # Main application logic
    if has_df and has_ui_components:
        df = st.session_state['df']
        metadata = st.session_state.get('metadata', {})
        original_questions = st.session_state.get('original_questions', [])

        # PROMPT 3: Remove redundant st.success message
        # st.success(f"✅ Database loaded: {len(df)} questions ready")

        # PROMPT 1 & 2: Remove st.tabs() block and replace with render_main_tabs
        if fork_available:
            ui_manager.render_main_tabs(df, metadata, original_questions, fork_components)
        else:
            ui_manager.render_main_tabs(df, metadata, original_questions)
        
        # Exit button at bottom
        exit_manager.render_exit_section_at_bottom()
        
    elif has_df and not has_ui_components:
        st.error("❌ Database loaded but UI components not available")
        exit_manager.render_exit_section_at_bottom()
        
    else:
        # No database - show getting started
        ui_manager.render_getting_started_section()
        exit_manager.render_exit_section_at_bottom()

if __name__ == "__main__":
    main()