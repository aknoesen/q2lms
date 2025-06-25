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
        
        st.success(f"✅ Database loaded: {len(df)} questions ready")
        
        # Fork decision workflow
        if fork_available:
            mode_manager = fork_components['mode_manager']
            
            try:
                # Check if we should show fork decision
                has_mode = mode_manager.has_mode_been_chosen()
                
                if not has_mode:
                    
                    
                    # Show fork decision
                    mode_manager.render_mode_selection()
                    
                    # Add exit button and stop here during fork decision
                    exit_manager.render_exit_section_at_bottom()
                    return
                
                # Mode has been chosen - get current mode
                current_mode = mode_manager.get_current_mode()
                mode_name, mode_icon, mode_description = mode_manager.get_mode_display_info()
                
                # Show current mode status
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"{mode_icon} **Current Mode:** {mode_name} - {mode_description}")
                with col2:
                    if st.button("🔄 Change Mode", key="main_change_mode"):
                        mode_manager.reset_mode()
                        st.rerun()
                
                # Apply topic filtering
                filtered_df = ui_manager.enhanced_subject_filtering(df)
                
                # Create tabs with mode-specific edit tab
                edit_tab_label = f"📝 {mode_name}"
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Browse Questions", edit_tab_label, "📥 Export"])
                
                with tab1:
                    if app_config.is_available('ui_components'):
                        ui_components = app_config.get_feature('ui_components')
                        #ui_components['display_database_summary'](df, metadata)
                        st.markdown("---")
                        #ui_components['create_summary_charts'](df)
                
                with tab2:
                    if app_config.is_available('ui_components'):
                        ui_components = app_config.get_feature('ui_components')
                        ui_components['simple_browse_questions_tab'](filtered_df)
                
                with tab3:
                    # Mode-specific edit interface
                    if current_mode == 'select':
                        select_interface = fork_components['select_interface']
                        select_interface.render_selection_interface(filtered_df)
                    elif current_mode == 'delete':
                        delete_interface = fork_components['delete_interface']
                        delete_interface.render_deletion_interface(filtered_df)
                
                with tab4:
                    # Export with fork filtering
                    flag_manager = fork_components['flag_manager']
                    export_df, export_original = flag_manager.get_filtered_questions_for_export(
                        filtered_df, original_questions, current_mode
                    )
                    
                    # Show export preview
                    st.markdown("### 📊 Export Preview")
                    
                    if current_mode == 'select':
                        selected_count = len(export_df)
                        total_count = len(filtered_df)
                        st.info(f"🎯 **Select Mode:** Exporting {selected_count} of {total_count} selected questions")
                        
                        if selected_count == 0:
                            st.warning("⚠️ No questions selected for export. Use checkboxes in the edit tab to select questions.")
                            st.info("💡 **Tip:** Go to the edit tab and use the selection checkboxes or bulk controls.")
                        else:
                            ui_manager.render_export_tab(export_df, export_original)
                            
                    elif current_mode == 'delete':
                        remaining_count = len(export_df)
                        total_count = len(filtered_df)
                        deleted_count = total_count - remaining_count
                        st.info(f"🗑️ **Delete Mode:** Exporting {remaining_count} remaining questions ({deleted_count} excluded)")
                        
                        if remaining_count == 0:
                            st.warning("⚠️ All questions marked for deletion. Nothing to export.")
                            st.info("💡 **Tip:** Go to the edit tab and uncheck some questions to remove deletion marks.")
                        else:
                            ui_manager.render_export_tab(export_df, export_original)
                
            except Exception as e:
                st.error(f"Fork workflow error: {e}")
                st.info("Continuing with standard interface...")
                # Fall back to standard interface
                ui_manager._render_stats_summary_before_tabs(df, metadata)  # ADD THIS LINE
                ui_manager.render_main_tabs(df, metadata, original_questions)
        
        else:
            # No fork feature - use standard interface
            ui_manager._render_stats_summary_before_tabs(df, metadata)  # ADD THIS LINE
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