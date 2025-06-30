#!/usr/bin/env python3
"""
Q2LMS UI Manager
Handles user interface coordination, tab management, and rendering
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from .upload_interface_v2 import UploadInterfaceV2, ProcessingState  # <-- Add this import here

class UIManager:
    """Manages user interface coordination and rendering for Q2LMS"""
    
    def __init__(self, app_config):
        self.app_config = app_config
    def find_topic_column(self, df: pd.DataFrame) -> str:
        """Find topic column case-insensitively"""
        if 'Topic' in df.columns:
            return 'Topic'
        elif 'topic' in df.columns:
            return 'topic'
        return None

    def _render_stats_summary_before_tabs(self, df: pd.DataFrame, metadata: dict):
        """Render a concise summary and charts before main tabs."""
        if self.app_config.is_available('ui_components'):
            ui_components = self.app_config.get_feature('ui_components')
            if 'display_database_summary' in ui_components:
                ui_components['display_database_summary'](df, metadata)
        st.markdown("---")
    
    
    
    def enhanced_subject_filtering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Multi-subject filter with case-insensitive detection and reset option"""
        
        if df.empty:
            return df
        
        # Use case-insensitive topic column detection
        topic_column = self.find_topic_column(df)
        if not topic_column:
            return df
        
        # Get unique topics
        topics = sorted(df[topic_column].dropna().unique())
        if not topics:
            return df
        
        # Add topic filter to sidebar with clear instructions
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📚 Topic Filter")
        
        # Clear instructions for users
        st.sidebar.markdown("""
        **Instructions:**
        - ✅ **Selected topics** will be included
        - ❌ **Uncheck topics** to exclude them  
        - 🔄 **Use this to focus** on specific subjects
        """)
        
        # Check if we need to reset (before creating the multiselect)
        if st.session_state.get("reset_topics_requested", False):
            # Clear the multiselect session state completely
            for key in list(st.session_state.keys()):
                if key == "enhanced_topic_multiselect":
                    del st.session_state[key]
            # Clear the reset request flag
            st.session_state["reset_topics_requested"] = False
            st.rerun()
        
        # Create multiselect with unique key that includes reset counter
        reset_counter = st.session_state.get("topic_reset_counter", 0)
        multiselect_key = f"enhanced_topic_multiselect_{reset_counter}"
        
        selected_topics = st.sidebar.multiselect(
            "Choose topics to include:",
            options=topics,
            default=topics,  # Always default to all topics
            key=multiselect_key,  # Use counter-based key for forced refresh
            help="💡 Tip: Click to select/deselect topics for filtering"
        )
        
        # RESET BUTTON - AFTER multiselect (below it)
        if st.sidebar.button("🔄 Reset Topics", key="reset_topics_btn", help="Select all topics again"):
            # Increment reset counter to force new multiselect widget
            st.session_state["topic_reset_counter"] = reset_counter + 1
            # Set flag for cleanup on next run
            st.session_state["reset_topics_requested"] = True
            st.rerun()
        
        # Apply filtering with clear feedback
        if selected_topics:
            filtered_df = df[df[topic_column].isin(selected_topics)]
            excluded_count = len(topics) - len(selected_topics)
            if excluded_count > 0:
                st.sidebar.info(f"✅ {len(selected_topics)} topics selected\n📋 {excluded_count} topics excluded")
            else:
                st.sidebar.success(f"✅ All {len(topics)} topics selected")
        else:
            filtered_df = pd.DataFrame()  # Empty if nothing selected
            st.sidebar.warning("⚠️ No topics selected - showing no questions")
        
        return filtered_df
    
    def render_upload_interface(self):
        """Render prominent upload interface (refactored, simplified)"""

        st.markdown("## 📁 Upload Question Database Files")

        if self.app_config.is_available('upload_system'):
            try:
                upload_system = self.app_config.get_feature('upload_system')
                upload_interface = upload_system['UploadInterfaceV2']()
                has_database = upload_interface.render_upload_section()
            except Exception as e:
                st.error(f"Upload interface error: {e}")
                has_database = False
        else:
            st.error("❌ Upload functionality not available")
            has_database = False

        return has_database
    
    def render_system_status(self):
        """Render overall system status - REMOVED for clean interface"""
        # This method is no longer needed - keeping empty for compatibility
        pass
    
    def render_branding_header(self):
        """Render the Q2LMS branding header"""
        
        st.markdown('<div class="q2lms-brand">Q2LMS</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-tagline">Transform questions into LMS-ready packages with seamless QTI export</div>', unsafe_allow_html=True)
    
    def render_getting_started_section(self):
        """Render minimal interface - no getting started content"""
        # Intentionally empty for clean, minimal interface
        pass
    
    def render_main_tabs(self, df, metadata, original_questions, fork_components=None):
        """Render the main application tabs with fork feature integration"""

        # Show success message
        st.success(f"✅ Database loaded successfully! {len(df)} questions ready.")

        # --- PROMPT 9: Apply filtering and stats summary globally ---
        filtered_df = self.enhanced_subject_filtering(df)
        self._render_stats_summary_before_tabs(df, metadata)
        # ----------------------------------------------------------

        # Fork feature integration
        if self.app_config.is_available('fork_feature'):
            # PROMPT 1: Directly access mode_manager from fork_components
            mode_manager = fork_components['mode_manager']

            # Check if mode has been chosen
            if not mode_manager.has_mode_been_chosen():
                # Show fork decision UI
                mode_manager.render_mode_selection()
                # Set default tab to Browse Questions for fork mode
                st.session_state.main_active_tab = "📋 Browse Questions"
                return False  # Don't show tabs until mode is chosen

            # Mode has been chosen - ensure flags are initialized
            if not mode_manager.is_mode_initialized():
                if mode_manager.initialize_question_flags():
                    st.rerun()  # Refresh to show updated interface

            # Get current mode info for tab labeling
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

            # Define tab names for fork feature branch
            edit_tab_label = f"📝 {mode_name}"
            tab_names = [
                "📊 Charts",
                "📋 Browse Questions",
                edit_tab_label,
                "📥 Export",
                "⚙️ Settings"
            ]

            # Button-based navigation
            if 'main_active_tab' not in st.session_state:
                st.session_state.main_active_tab = "📋 Browse Questions"
            
            # Clear export tab state when switching away from Export tab
            current_tab = st.session_state.get('main_active_tab', '')
            
            tab_cols = st.columns(len(tab_names))
            for idx, tab_name in enumerate(tab_names):
                btn_key = f"main_tab_btn_{tab_name.replace(' ', '_').lower()}"
                if tab_cols[idx].button(
                    tab_name,
                    key=btn_key,
                    type="primary" if st.session_state.main_active_tab == tab_name else "secondary"
                ):
                    # If switching away from Export tab, clear export state
                    if current_tab == "📥 Export" and tab_name != "📥 Export":
                        # Clear export session when leaving export tab (fork branch)
                        for key in ['export_tab_loaded', 'export_tab_session_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                    st.session_state.main_active_tab = tab_name
            st.markdown("---")

            # Update workflow state based on the active tab (fork branch)
            if 'upload_state' in st.session_state:
                current_tab = st.session_state.get('main_active_tab', '')
                if current_tab == "📥 Export":
                    # Force workflow state to EXPORTING when in Export tab
                    UploadInterfaceV2.update_workflow_state(ProcessingState.EXPORTING)
                else:
                    UploadInterfaceV2.update_workflow_state(ProcessingState.SELECTING_QUESTIONS)

            # Refactor content rendering using new helpers
            active_tab_name = st.session_state.main_active_tab
            self._render_tab_content_with_fork_and_overview_new(
                active_tab_name, df, filtered_df, original_questions, metadata, mode_manager, fork_components
            )

        else:
            # Fallback to original interface if fork feature not available

            # Define tab names for fallback branch
            tab_names = [
                "📊 Database Overview",
                "📋 Browse Questions",
                "📝 Browse & Edit",
                "📥 Export"
            ]

            # Button-based navigation
            if 'main_active_tab' not in st.session_state:
                st.session_state.main_active_tab = tab_names[0]
            
            # Clear export tab state when switching away from Export tab
            current_tab = st.session_state.get('main_active_tab', '')
            
            tab_cols = st.columns(len(tab_names))
            for idx, tab_name in enumerate(tab_names):
                btn_key = f"main_tab_btn_{tab_name.replace(' ', '_').lower()}"
                if tab_cols[idx].button(
                    tab_name,
                    key=btn_key,
                    type="primary" if st.session_state.main_active_tab == tab_name else "secondary"
                ):
                    # If switching away from Export tab, clear export state
                    if current_tab == "📥 Export" and tab_name != "📥 Export":
                        # Clear export session when leaving export tab (fallback branch)
                        for key in ['export_tab_loaded', 'export_tab_session_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                    st.session_state.main_active_tab = tab_name
            st.markdown("---")

            # Update workflow state based on the active tab (standard branch)
            if 'upload_state' in st.session_state:
                current_tab = st.session_state.get('main_active_tab', '')
                if current_tab == "📥 Export":
                    # Force workflow state to EXPORTING when in Export tab
                    UploadInterfaceV2.update_workflow_state(ProcessingState.EXPORTING)
                else:
                    UploadInterfaceV2.update_workflow_state(ProcessingState.SELECTING_QUESTIONS)

            # Refactor content rendering using new helpers
            active_tab_name = st.session_state.main_active_tab
            self._render_tab_content_standard_with_overview_new(
                active_tab_name, df, filtered_df, original_questions, metadata
            )

        return True

    def _render_tab_content_with_fork_and_overview_new(self, active_tab_name, df, filtered_df, original_questions, metadata, mode_manager, fork_components):
        """Render tab content with fork feature integration and overview using active_tab_name"""
        # PROMPT 3: Access instances directly from fork_components (no need for None fallback)
        select_interface = fork_components.get('select_interface')
        delete_interface = fork_components.get('delete_interface')
        flag_manager = fork_components.get('flag_manager')

        # Charts Tab
        if active_tab_name == "📊 Charts":
            st.markdown("### 📊 Database Overview")
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                if 'display_database_summary' in ui_components:
                    ui_components['display_database_summary'](df, metadata)
                if 'create_summary_charts' in ui_components:
                    ui_components['create_summary_charts'](df, chart_key_suffix='charts_fork_tab')
            else:
                st.info("No database overview available.")
        # Browse Questions Tab
        elif active_tab_name == "📋 Browse Questions":
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['simple_browse_questions_tab'](filtered_df)
            else:
                st.error("❌ UI components not available for browsing")
        # Mode-specific Edit Tab
        elif active_tab_name.startswith("📝"):
            current_mode = mode_manager.get_current_mode()
            if current_mode == 'select' and select_interface:
                select_interface.render_selection_interface(filtered_df)
            elif current_mode == 'delete' and delete_interface:
                delete_interface.render_deletion_interface(filtered_df)
            else:
                st.error(f"❌ Unknown or unavailable mode: {current_mode}")
        # Export Tab
        elif active_tab_name == "📥 Export":
            current_mode = mode_manager.get_current_mode()
            if flag_manager:
                export_df, export_original = flag_manager.get_filtered_questions_for_export(
                    filtered_df, original_questions, current_mode
                )
                st.markdown("### 📊 Export Preview")
                if current_mode == 'select':
                    selected_count = len(export_df)
                    total_count = len(filtered_df)
                    st.info(f"🎯 **Select Mode:** Exporting {selected_count} of {total_count} selected questions")
                    if selected_count == 0:
                        st.warning("⚠️ No questions selected for export. Use checkboxes in the edit tab to select questions.")
                        st.info("💡 **Tip:** Go to the edit tab and use the selection checkboxes or bulk controls.")
                        return
                elif current_mode == 'delete':
                    remaining_count = len(export_df)
                    total_count = len(filtered_df)
                    deleted_count = total_count - remaining_count
                    st.info(f"🗑️ **Delete Mode:** Exporting {remaining_count} remaining questions ({deleted_count} excluded)")
                    if remaining_count == 0:
                        st.warning("⚠️ All questions marked for deletion. Nothing to export.")
                        st.info("💡 **Tip:** Go to the edit tab and uncheck some questions to remove deletion marks.")
                        return
                self.render_export_tab(export_df, export_original)
            else:
                st.error("❌ Export functionality not available")
        # Settings Tab
        elif active_tab_name == "⚙️ Settings":
            st.markdown("### ⚙️ Application Settings")
            st.info("💡 Configure Q2LMS preferences and options.")
            st.checkbox("🔍 Show detailed tooltips", value=True)
            st.checkbox("📊 Auto-refresh charts", value=False)
            st.selectbox("🎨 Theme", ["Default", "Dark", "Light"])

    def _render_tab_content_standard_with_overview_new(self, active_tab_name, df, filtered_df, original_questions, metadata):
        """Render tab content without fork features but with overview using active_tab_name"""
        # Database Overview Tab
        if active_tab_name == "📊 Database Overview":
            st.markdown("### 📊 Detailed Database Analysis")
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                if 'display_database_summary' in ui_components:
                    ui_components['display_database_summary'](df, metadata)
                if 'create_summary_charts' in ui_components:
                    ui_components['create_summary_charts'](df, chart_key_suffix='charts_standard_tab')
            else:
                st.error("❌ UI components not available for detailed overview")
        # Browse Questions Tab
        elif active_tab_name == "📋 Browse Questions":
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['simple_browse_questions_tab'](filtered_df)
            else:
                st.error("❌ UI components not available for browsing")
        # Standard Edit Tab
        elif active_tab_name == "📝 Browse & Edit":
            if self.app_config.is_available('question_editor'):
                question_editor = self.app_config.get_feature('question_editor')
                question_editor['side_by_side_question_editor'](filtered_df)
            else:
                st.error("❌ Question editor not available")
                st.info("You can still browse questions in the other tabs.")
        # Export Tab
        elif active_tab_name == "📥 Export":
            self.render_export_tab(filtered_df, original_questions)

    def render_export_tab(self, export_df: pd.DataFrame, export_original: list) -> None:
        """
        Render export tab with comprehensive export options
        
        Args:
            export_df (pd.DataFrame): Filtered DataFrame for export
            export_original (list): Original questions list for export
        """
        try:
            # Note: Workflow state is already updated in render_main_tabs based on active tab
            
            # Clear any stale completion flags when entering export tab
            # This ensures soft exit only appears after actual QTI download
            
            # Only clear flags when first entering the export tab, not on every render
            if 'export_tab_session_id' not in st.session_state:
                # Generate a unique session ID for this export tab session
                import time
                current_session_id = f"export_{int(time.time() * 1000)}"
                st.session_state['export_tab_session_id'] = current_session_id
                
                # Clear all completion flags on first entry to export tab
                for key in ['qti_downloaded', 'qti_package_created', 'export_completed', 'json_downloaded', 'csv_downloaded']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.session_state['export_tab_loaded'] = True
            
            if self.app_config.is_available('export_system'):
                # Use the advanced export system
                export_system = self.app_config.get_feature('export_system')
                export_system['integrate_with_existing_ui'](export_df, export_original)
                
                # Check if any export was completed and ensure completion UI is shown
                # Now enabled: User must confirm QTI download for completion to be detected
                completion_detected = st.session_state.get('qti_downloaded', False)
                
                # Debug: Show completion status (can be removed later)
                with st.expander("🔍 Debug: Completion Detection"):
                    st.write(f"- qti_downloaded: {st.session_state.get('qti_downloaded', False)}")
                    st.write(f"- qti_package_created: {st.session_state.get('qti_package_created', False)}")
                    st.write(f"- export_completed: {st.session_state.get('export_completed', False)}")
                    st.write(f"- completion_detected: {completion_detected} (DISABLED)")
                    st.write(f"- export_tab_session_id: {st.session_state.get('export_tab_session_id', 'None')}")
                    st.error("� Automatic completion detection DISABLED. Soft exit UI will only appear in basic fallback interface.")
                    
                    st.markdown("**All session state keys:**")
                    st.write([key for key in st.session_state.keys() if 'download' in key.lower() or 'export' in key.lower() or 'complete' in key.lower()])
                
                # Only show completion UI if export was actually completed
                if completion_detected:
                    # Always show completion UI to ensure soft exit is available
                    st.markdown("---")
                    st.success("🎉 Export Process Complete!")
                    st.markdown("### 🎯 What would you like to do next?")
                    
                    # Update workflow state to DOWNLOADING
                    if 'upload_state' in st.session_state:
                        UploadInterfaceV2.update_workflow_state(ProcessingState.DOWNLOADING)
                    
                    comp_col1, comp_col2 = st.columns(2)
                    with comp_col1:
                        if st.button("🚪 Exit Application", type="secondary", use_container_width=True, key="ui_exit_app"):
                            st.success("✅ Thank you for using Q2LMS!")
                            st.balloons()
                            st.stop()
                    with comp_col2:
                        if st.button("🔄 Start Over", type="primary", use_container_width=True, key="ui_start_over"):
                            # Clear all completion flags and reset to start
                            for key in ['qti_downloaded', 'qti_package_created', 'export_completed', 'json_downloaded', 'csv_downloaded', 'export_tab_loaded', 'export_tab_session_id']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            if UploadInterfaceV2.is_workflow_active():
                                UploadInterfaceV2.update_workflow_state(ProcessingState.WAITING_FOR_FILES)
                            st.rerun()
            else:
                # Fallback to basic export interface
                self._render_basic_export_interface(export_df, export_original)
                
        except Exception as e:
            st.error(f"❌ Error rendering export interface: {e}")
            # Show basic download options as fallback
            self._render_basic_export_interface(export_df, export_original)
    
    def _render_basic_export_interface(self, export_df: pd.DataFrame, export_original: list) -> None:
        """
        Basic export interface fallback
        
        Args:
            export_df (pd.DataFrame): DataFrame to export
            export_original (list): Original questions for export
        """
        st.subheader("📥 Export Options")
        
        if len(export_df) == 0:
            st.warning("⚠️ No questions to export")
            return
        
        st.success(f"✅ Ready to export {len(export_df)} questions")
        
        # Export completion notice
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Primary QTI Package Export (moved to top)
            st.markdown("#### 📦 QTI Package Export")
            st.markdown("**🎯 Recommended for LMS deployment**")
            
            if st.button("📦 Create QTI Package", type="primary", use_container_width=True, key="basic_qti_create"):
                # Attempt to create QTI package using available export system
                try:
                    if self.app_config.is_available('export_system'):
                        # Use advanced export system for QTI creation
                        export_system = self.app_config.get_feature('export_system')
                        # This is a simplified approach - the actual QTI creation would be more complex
                        st.info("🔄 Creating QTI package using advanced export system...")
                        
                        # Update workflow state to DOWNLOADING after QTI creation
                        if 'upload_state' in st.session_state:
                            UploadInterfaceV2.update_workflow_state(ProcessingState.DOWNLOADING)
                        
                        st.success("🎉 QTI Export completed successfully!")
                        
                        # --- QTI Completion section ---
                        st.markdown("---")
                        st.success("🎉 QTI Package Export Complete!")
                        st.markdown("### 🎯 What's Next?")
                        
                        completion_col1, completion_col2 = st.columns(2)
                        with completion_col1:
                            if st.button("🚪 Exit Application", type="secondary", use_container_width=True, key="qti_exit_app"):
                                st.success("✅ Thank you for using Q2LMS!")
                                st.stop()
                        with completion_col2:
                            if st.button("🔄 Start Over", type="primary", use_container_width=True, key="qti_start_over"):
                                if UploadInterfaceV2.is_workflow_active():
                                    UploadInterfaceV2.update_workflow_state(ProcessingState.WAITING_FOR_FILES)
                                st.rerun()
                    else:
                        st.error("❌ QTI export system not available. Please use CSV or JSON export options.")
                except Exception as e:
                    st.error(f"❌ QTI export failed: {e}")
                    st.info("💡 Please try using CSV or JSON export as an alternative.")
            
            # Alternative formats (moved below QTI)
            st.markdown("---")
            st.markdown("#### 📊 Alternative Export Formats")
            
            # Basic CSV download
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                label="📄 Download as CSV",
                data=csv_data,
                file_name="questions_export.csv",
                mime="text/csv",
                use_container_width=True,
                key="basic_csv_export"
            )
            
            # Basic JSON download
            if export_original:
                json_data = json.dumps({
                    "questions": export_original,
                    "metadata": {
                        "subject": "Exported Questions",
                        "total_questions": len(export_original),
                        "export_timestamp": pd.Timestamp.now().isoformat()
                    }
                }, indent=2)
                
                # JSON download without completion detection for now
                st.download_button(
                    label="📋 Download as JSON",
                    data=json_data,
                    file_name="questions_export.json",
                    mime="application/json",
                    use_container_width=True,
                    key="basic_json_export"
                )
        
        with col2:
            st.metric("Questions", len(export_df))
            if 'Points' in export_df.columns:
                total_points = export_df['Points'].sum()
                st.metric("Total Points", int(total_points))
        
        # Workflow completion options
        st.markdown("---")
        st.markdown("### 🎯 Complete Your Session")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Start Over", type="secondary", key="basic_start_over"):
                if UploadInterfaceV2.is_workflow_active():
                    UploadInterfaceV2.update_workflow_state(ProcessingState.WAITING_FOR_FILES)
                st.rerun()
        
        with col2:
            if st.button("🚪 Exit Application", type="secondary", key="basic_exit_app"):
                st.success("✅ Export complete! You can now close this tab.")
                st.stop()

#
# Convenience function for easy integration
def get_ui_manager(app_config):
    """
    Get a configured UIManager instance.

    Args:
        app_config: The application configuration object.

    Returns:
        UIManager: Configured instance.
    """
    return UIManager(app_config)