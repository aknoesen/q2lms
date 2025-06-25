#!/usr/bin/env python3
"""
Q2LMS - Question Database Manager
Web-based interface for managing educational question databases and generating LMS-ready QTI packages

REFACTORED VERSION - Clean modular architecture
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration with Q2LMS branding
st.set_page_config(
    page_title="Q2LMS - Question Database Manager",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import refactored modules
try:
    from modules.app_config import get_app_config
    from modules.exit_manager import get_exit_manager
    from modules.ui_manager import get_ui_manager
    from modules.fork_coordinator import get_fork_coordinator
    REFACTORED_MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Refactored modules not available: {e}")
    st.info("Falling back to original implementation...")
    REFACTORED_MODULES_AVAILABLE = False

def initialize_session_tracking():
    """Initialize session tracking"""
    if 'session_start_time' not in st.session_state:
        st.session_state['session_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def main():
    """Main Streamlit application with clean modular architecture"""
    
    # Initialize session tracking
    initialize_session_tracking()
    
    if not REFACTORED_MODULES_AVAILABLE:
        st.error("❌ Refactored modules not available - cannot start application")
        st.info("Please ensure all refactored modules are properly installed.")
        return
    
    # Initialize core components
    app_config = get_app_config()
    exit_manager = get_exit_manager()
    ui_manager = get_ui_manager(app_config)
    fork_coordinator = get_fork_coordinator(app_config)
    
    # Apply styling and configuration
    app_config.apply_mathjax_config()
    app_config.apply_custom_css()
    
    # Initialize session state if session manager available
    if app_config.is_available('session_manager'):
        session_manager = app_config.get_feature('session_manager')
        session_manager['initialize_session_state']()
    
    # Render sidebar with system status and exit button
    app_config.render_sidebar_status()
    exit_manager.add_exit_button_to_sidebar()
    
    # Check for exit request - if showing exit interface, stop here
    if exit_manager.check_for_exit_request():
        return
    
    # Render main branding header
    ui_manager.render_branding_header()
    
    # Show overall system health status
    ui_manager.render_system_status()
    st.markdown("---")
    
    # Render upload interface
    if app_config.is_available('session_manager'):
        has_database = ui_manager.render_upload_interface()
    else:
        st.error("❌ Cannot load upload interface - session management unavailable")
        has_database = False
    
    # Main application logic based on database status
    if has_database and 'df' in st.session_state and app_config.is_available('ui_components'):
        df = st.session_state['df']
        metadata = st.session_state['metadata']
        original_questions = st.session_state['original_questions']
        
        # Handle fork decision workflow
        if fork_coordinator.handle_fork_decision():
            return  # Fork decision is being shown, don't proceed to tabs
        
        # Ensure mode initialization if fork feature is active
        if fork_coordinator.ensure_mode_initialization():
            st.rerun()
            return
        
        # Render main application tabs
        ui_manager.render_main_tabs(df, metadata, original_questions)
        
    elif has_database and not app_config.is_available('ui_components'):
        st.error("❌ Database loaded but UI components not available")
        st.info("Please check that all required modules are installed.")
    
    else:
        # No database loaded - show getting started guide
        ui_manager.render_getting_started_section()

if __name__ == "__main__":
    main()