#!/usr/bin/env python3
"""
Q2LMS Fork Coordinator
Handles the fork decision workflow and mode routing logic
"""

import streamlit as st

class ForkCoordinator:
    """Coordinates the fork decision workflow and mode routing"""
    
    def __init__(self, app_config):
        self.app_config = app_config
    
    def should_show_fork_decision(self):
        """
        Determine if the fork decision interface should be shown.
        Returns True if we have a database loaded but no mode chosen.
        """
        # Check if we have database loaded
        has_database = (
            'df' in st.session_state and 
            st.session_state['df'] is not None and 
            len(st.session_state['df']) > 0
        )
        
        if not has_database:
            return False
        
        # Check if fork feature is available
        if not self.app_config.is_available('fork_feature'):
            return False
        
        # Check if mode has been chosen
        fork_feature = self.app_config.get_feature('fork_feature')
        mode_manager = fork_feature['get_operation_mode_manager']()
        
        return not mode_manager.has_mode_been_chosen()
    
    def handle_fork_decision(self):
        """
        Handle the fork decision workflow.
        Returns True if fork decision was shown, False if should proceed to main tabs.
        """
        if not self.should_show_fork_decision():
            return False
        
        # Show fork decision interface
        fork_feature = self.app_config.get_feature('fork_feature')
        mode_manager = fork_feature['get_operation_mode_manager']()
        mode_manager.render_mode_selection()
        
        return True  # Fork decision was shown, don't proceed to main tabs
    
    def ensure_mode_initialization(self):
        """
        Ensure that the chosen mode is properly initialized.
        Returns True if a rerun is needed, False otherwise.
        """
        if not self.app_config.is_available('fork_feature'):
            return False
        
        fork_feature = self.app_config.get_feature('fork_feature')
        mode_manager = fork_feature['get_operation_mode_manager']()
        
        # Check if mode has been chosen but not initialized
        if mode_manager.has_mode_been_chosen() and not mode_manager.is_mode_initialized():
            if mode_manager.initialize_question_flags():
                return True  # Need to rerun to show updated interface
        
        return False  # No rerun needed
    
    def get_current_mode_info(self):
        """
        Get information about the current mode.
        Returns tuple of (current_mode, mode_name, mode_icon, mode_description) or None if no mode.
        """
        if not self.app_config.is_available('fork_feature'):
            return None
        
        fork_feature = self.app_config.get_feature('fork_feature')
        mode_manager = fork_feature['get_operation_mode_manager']()
        
        if not mode_manager.has_mode_been_chosen():
            return None
        
        current_mode = mode_manager.get_current_mode()
        mode_name, mode_icon, mode_description = mode_manager.get_mode_display_info()
        
        return current_mode, mode_name, mode_icon, mode_description
    
    def render_mode_status_bar(self):
        """Render the current mode status bar with change mode option"""
        
        mode_info = self.get_current_mode_info()
        if mode_info is None:
            return
        
        current_mode, mode_name, mode_icon, mode_description = mode_info
        
        # Show current mode status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"{mode_icon} **Current Mode:** {mode_name} - {mode_description}")
        with col2:
            if st.button("🔄 Change Mode", key="fork_change_mode"):
                fork_feature = self.app_config.get_feature('fork_feature')
                mode_manager = fork_feature['get_operation_mode_manager']()
                mode_manager.reset_mode()
                st.rerun()
    
    def get_filtered_export_data(self, filtered_df, original_questions):
        """
        Get export data filtered based on current fork mode.
        Returns tuple of (export_df, export_original, export_info_message) or None if no filtering needed.
        """
        if not self.app_config.is_available('fork_feature'):
            return None
        
        fork_feature = self.app_config.get_feature('fork_feature')
        mode_manager = fork_feature['get_operation_mode_manager']()
        
        if not mode_manager.has_mode_been_chosen():
            return None
        
        current_mode = mode_manager.get_current_mode()
        flag_manager = fork_feature['QuestionFlagManager']()
        
        # Get filtered questions based on mode
        export_df, export_original = flag_manager.get_filtered_questions_for_export(
            filtered_df, original_questions, current_mode
        )
        
        # Generate info message
        if current_mode == 'select':
            selected_count = len(export_df)
            total_count = len(filtered_df)
            info_message = f"🎯 **Select Mode:** Exporting {selected_count} of {total_count} selected questions"
            
            if selected_count == 0:
                return export_df, export_original, {
                    'type': 'warning',
                    'message': "⚠️ No questions selected for export. Use checkboxes in the edit tab to select questions.",
                    'tip': "💡 **Tip:** Go to the edit tab and use the selection checkboxes or bulk controls."
                }
        
        elif current_mode == 'delete':
            remaining_count = len(export_df)
            total_count = len(filtered_df)
            deleted_count = total_count - remaining_count
            info_message = f"🗑️ **Delete Mode:** Exporting {remaining_count} remaining questions ({deleted_count} excluded)"
            
            if remaining_count == 0:
                return export_df, export_original, {
                    'type': 'warning',
                    'message': "⚠️ All questions marked for deletion. Nothing to export.",
                    'tip': "💡 **Tip:** Go to the edit tab and uncheck some questions to remove deletion marks."
                }
        
        else:
            info_message = f"❓ **Unknown Mode:** {current_mode}"
        
        return export_df, export_original, {
            'type': 'info',
            'message': info_message,
            'show_export': True
        }
    
    def render_export_preview(self, filtered_df, original_questions):
        """
        Render export preview with fork filtering if applicable.
        Returns tuple of (export_df, export_original, should_continue) where should_continue
        indicates whether the export interface should be shown.
        """
        export_data = self.get_filtered_export_data(filtered_df, original_questions)
        
        if export_data is None:
            # No fork filtering - use original data
            return filtered_df, original_questions, True
        
        export_df, export_original, info = export_data
        
        # Show export preview section
        st.markdown("### 📊 Export Preview")
        
        # Display appropriate message based on info type
        if info['type'] == 'warning':
            st.warning(info['message'])
            if 'tip' in info:
                st.info(info['tip'])
            return export_df, export_original, info.get('show_export', True)
        else:
            st.info(info['message'])
        
        return export_df, export_original, info.get('show_export', True)
    
    def get_edit_tab_interface(self, filtered_df):
        """
        Get the appropriate edit interface based on current mode.
        Returns the interface object to render, or None if not available.
        """
        if not self.app_config.is_available('fork_feature'):
            return None
        
        mode_info = self.get_current_mode_info()
        if mode_info is None:
            return None
        
        current_mode, _, _, _ = mode_info
        fork_feature = self.app_config.get_feature('fork_feature')
        
        if current_mode == 'select':
            return fork_feature['SelectQuestionsInterface']()
        elif current_mode == 'delete':
            return fork_feature['DeleteQuestionsInterface']()
        else:
            return None
    
    def get_edit_tab_label(self):
        """Get the label for the edit tab based on current mode"""
        
        mode_info = self.get_current_mode_info()
        if mode_info is None:
            return "📝 Browse & Edit"  # Default label
        
        _, mode_name, _, _ = mode_info
        return f"📝 {mode_name}"
    
    def is_fork_feature_enabled(self):
        """Check if fork feature is enabled and available"""
        return self.app_config.is_available('fork_feature')

# Global instance
_fork_coordinator = None

def get_fork_coordinator(app_config):
    """Get the global fork coordinator instance"""
    global _fork_coordinator
    if _fork_coordinator is None:
        _fork_coordinator = ForkCoordinator(app_config)
    return _fork_coordinator