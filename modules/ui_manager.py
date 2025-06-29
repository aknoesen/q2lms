#!/usr/bin/env python3
"""
Q2LMS UI Manager
Handles user interface coordination, tab management, and rendering
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.upload_interface_v2 import UploadInterfaceV2, ProcessingState  # <-- Add this import here

class UIManager:
    """Manages user interface coordination and rendering for Q2LMS"""
    
    def __init__(self, app_config):
        self.app_config = app_config
    
    def enhanced_subject_filtering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Multi-subject filter using the correct 'Topic' column with clear instructions"""
        
        if df.empty:
            return df
        
        # Use 'Topic' instead of 'Subject'
        if 'Topic' not in df.columns:
            return df
        
        # Get unique topics
        topics = sorted(df['Topic'].dropna().unique())
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
        
        selected_topics = st.sidebar.multiselect(
            "Choose topics to include:",
            options=topics,
            default=topics,  # Start with all topics selected
            key=f"topic_filter_multi_{id(self)}",
            help="💡 Tip: Uncheck topics you want to exclude from the current view"
        )
        
        # Apply filtering with clear feedback
        if selected_topics:
            filtered_df = df[df['Topic'].isin(selected_topics)]
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
    
    def render_main_tabs(self, df, metadata, original_questions):
        """Render the main application tabs with fork feature integration"""
        
        # Only update workflow state if upload interface is active
        if 'upload_state' in st.session_state:
            UploadInterfaceV2.update_workflow_state(ProcessingState.SELECTING_QUESTIONS)
        
        # Show success message
        st.success(f"✅ Database loaded successfully! {len(df)} questions ready.")

        # TEST: Check which branch we're using
        st.error("🧪 CHECKING FORK FEATURE AVAILABILITY")
        
        # Fork feature integration
        if self.app_config.is_available('fork_feature'):
            fork_feature = self.app_config.get_feature('fork_feature')
            mode_manager = fork_feature['get_operation_mode_manager']()
            
            # Check if mode has been chosen
            if not mode_manager.has_mode_been_chosen():
                # Show fork decision UI
                mode_manager.render_mode_selection()
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
            
            # Apply topic filtering
            filtered_df = self.enhanced_subject_filtering(df)
            
            # STATS SUMMARY BEFORE TABS - Quick overview metrics
            self._render_stats_summary_before_tabs(df, metadata)
            
            # Create tabs - Database Overview is now optional for detailed info
            edit_tab_label = f"📝 {mode_name}"
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Charts",  # Changed from "📊 Database Overview"
                "📋 Browse Questions", 
                edit_tab_label, 
                "📥 Export",
                "⚙️ Settings"
            ])
            
            # FIXED: Use the correct fork method with all 5 tabs and proper parameters
            self._render_tab_content_with_fork_and_overview(tab1, tab2, tab3, tab4, tab5, df, filtered_df, original_questions, mode_manager, fork_feature)
            
        else:
            # Fallback to original interface if fork feature not available
            filtered_df = self.enhanced_subject_filtering(df)
            
            # STATS SUMMARY BEFORE TABS - Quick overview metrics (fallback case)
            self._render_stats_summary_before_tabs(df, metadata)
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Database Overview", 
                "📋 Browse Questions", 
                "📝 Browse & Edit", 
                "📥 Export"
            ])
            
            # Render tab content without fork features - correct method for 4 tabs
            self._render_tab_content_standard_with_overview(tab1, tab2, tab3, tab4, df, filtered_df, original_questions)
        
        return True
    
    def _render_tab_content_with_fork(self, tab1, tab2, tab3, tab4, df, filtered_df, original_questions, mode_manager, fork_feature):
        """Render tab content with fork feature integration"""
        
        # Tab 1: Overview - Clean and simple, no database summary (moved before tabs)
        with tab1:
            st.markdown("### 🎯 Current Workflow Guide")
            
            current_mode = mode_manager.get_current_mode()
            mode_name, mode_icon, _ = mode_manager.get_mode_display_info()
            
            if current_mode == 'select':
                st.info(f"""
                **{mode_icon} You're in {mode_name} Mode**
                
                **Next Steps:**
                1. Use **Browse Questions** to review all available questions
                2. Use **{mode_name}** tab to select specific questions for export
                3. Use **Export** tab to download your selected questions
                """)
            elif current_mode == 'delete':
                st.info(f"""
                **{mode_icon} You're in {mode_name} Mode**
                
                **Next Steps:**
                1. Use **Browse Questions** to review all available questions  
                2. Use **{mode_name}** tab to mark unwanted questions for removal
                3. Use **Export** tab to download remaining questions
                """)
            
            st.markdown("### 🔧 Available Tools")
            st.markdown("""
            - **Topic Filtering:** Use the sidebar to focus on specific subjects
            - **Question Editing:** Edit questions directly in the mode-specific tab
            - **Bulk Operations:** Use bulk controls for faster selection/deletion
            - **Export Options:** Multiple format options (CSV, JSON, QTI) available
            """)
            
            # Show current filter status
            if 'topic_filter_multi' in st.session_state:
                selected_topics = st.session_state.get(f'topic_filter_multi_{id(self)}', [])
                if selected_topics:
                    if len(selected_topics) < len(df['Topic'].unique()):
                        st.warning(f"🔍 **Topic Filter Active:** Only showing {len(selected_topics)} of {len(df['Topic'].unique())} topics")
                    else:
                        st.success("✅ **All Topics Visible:** No filtering applied")
        
        # Tab 2: Browse Questions
        with tab2:
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['simple_browse_questions_tab'](filtered_df)
            else:
                st.error("❌ UI components not available for browsing")
        
        # Tab 3: Mode-specific Edit Tab
        with tab3:
            current_mode = mode_manager.get_current_mode()
            
            if current_mode == 'select':
                # Use Select Questions interface
                select_interface = fork_feature['SelectQuestionsInterface']()
                select_interface.render_selection_interface(filtered_df)
                
            elif current_mode == 'delete':
                # Use Delete Questions interface
                delete_interface = fork_feature['DeleteQuestionsInterface']()
                delete_interface.render_deletion_interface(filtered_df)
                
            else:
                st.error(f"❌ Unknown mode: {current_mode}")
        
        # Tab 4: Export with Filtering
        with tab4:
            # Apply fork filtering before export
            current_mode = mode_manager.get_current_mode()
            flag_manager = fork_feature['QuestionFlagManager']()
            
            # Get filtered questions based on mode
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
            
            # Use existing export interface with filtered data
            self.render_export_tab(export_df, export_original)
    
    def _render_tab_content_standard(self, tab1, tab2, tab3, tab4, df, filtered_df, original_questions):
        """Render tab content without fork features (fallback)"""
        
        # Tab 1: Overview
        with tab1:
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                #ui_components['display_database_summary'](df, st.session_state['metadata'])
                st.markdown("---")
                #ui_components['create_summary_charts'](df)
            else:
                st.error("❌ UI components not available for overview")
        
        # Tab 2: Browse Questions
        with tab2:
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['simple_browse_questions_tab'](filtered_df)
            else:
                st.error("❌ UI components not available for browsing")
        
        # Tab 3: Standard Edit Tab
        with tab3:
            if self.app_config.is_available('question_editor'):
                question_editor = self.app_config.get_feature('question_editor')
                question_editor['side_by_side_question_editor'](filtered_df)
            else:
                st.error("❌ Question editor not available")
                st.info("You can still browse questions in the other tabs.")
        
        # Tab 4: Standard Export
        with tab4:
            self.render_export_tab(filtered_df, original_questions)
    def render_export_tab(self, export_df: pd.DataFrame, export_original: list) -> None:
        """
        Render export tab with given filtered data
        
        Args:
            export_df (pd.DataFrame): Filtered DataFrame for export
            export_original (list): Original questions list for export
        """
        # Only update workflow state if upload interface is active
        if 'upload_state' in st.session_state:
            UploadInterfaceV2.update_workflow_state(ProcessingState.EXPORTING)

        try:
            if self.app_config.is_available('export_system'):
                export_system = self.app_config.get_feature('export_system')
                export_system['integrate_with_existing_ui'](export_df, export_original)
            else:
                # Fallback basic export interface
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
        
        # Basic CSV download
        csv_data = export_df.to_csv(index=False)
        csv_downloaded = st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name="questions_export.csv",
            mime="text/csv",
            use_container_width=True
        )
        if csv_downloaded:
            if 'upload_state' in st.session_state:
                UploadInterfaceV2.update_workflow_state(ProcessingState.FINISHED)
            st.success("🎉 Export completed successfully!")
        
        # Basic JSON download
        if export_original:
            import json
            json_data = json.dumps({
                "questions": export_original,
                "metadata": {
                    "total_questions": len(export_original),
                    "export_timestamp": pd.Timestamp.now().isoformat()
                }
            }, indent=2)
            
            json_downloaded = st.download_button(
                label="📋 Download as JSON",
                data=json_data,
                file_name="questions_export.json",
                mime="application/json",
                use_container_width=True
            )
            if json_downloaded:
                if 'upload_state' in st.session_state:
                    UploadInterfaceV2.update_workflow_state(ProcessingState.FINISHED)
                st.success("🎉 Export completed successfully!")

    def _render_stats_summary_before_tabs(self, df, metadata):
        """Render quick stats summary before tabs - key metrics only with expandable details"""
        
        st.markdown("---")
        
        # Quick stats in a compact format (keep existing)
        total_questions = len(df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📚 Total Questions", total_questions)
        
        with col2:
            if 'Topic' in df.columns:
                topics = df['Topic'].nunique()
                st.metric("📂 Topics", topics)
            else:
                st.metric("📂 Topics", "N/A")
        
        with col3:
            if 'Points' in df.columns:
                total_points = int(df['Points'].sum())
                st.metric("🎯 Total Points", total_points)
            else:
                st.metric("🎯 Total Points", "N/A")
        
        with col4:
            if 'Type' in df.columns:
                question_types = df['Type'].nunique()
                st.metric("🏷️ Question Types", question_types)
            else:
                st.metric("🏷️ Question Types", "N/A")
        
        # Optional: Show source info compactly
        if metadata and 'source' in metadata:
            source = metadata.get('source', 'Unknown')
            st.caption(f"📁 **Source:** {source}")
        
        # ADD: Expandable detailed analysis
        with st.expander("📊 **View Detailed Analysis**", expanded=False):
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                
                # Detailed database summary
                st.markdown("#### 📋 Database Details")
                ui_components['display_database_summary'](df, metadata)
                
                st.markdown("---")
                
                # Charts and visualizations
                st.markdown("#### 📈 Visual Analysis")
                ui_components['create_summary_charts'](df)
            else:
                st.error("❌ Detailed analysis components not available")
        
        st.markdown("---")

    def _render_tab_content_with_fork_and_overview(self, tab1, tab2, tab3, tab4, tab5, df, filtered_df, original_questions, mode_manager, fork_feature):
        """Render tab content with fork feature integration and separate overview tab"""
        
        # Tab 1: Database Overview - Detailed analysis (OPTIONAL)
        with tab1:
            st.markdown("### 🧪 Test - Tab Content Removed")
            st.info("If you see this message and NO database overview content above, then we've found the source of the problem.")
            st.markdown("The database overview content was coming from this tab.")
        
        # Tab 2: Browse Questions
        with tab2:
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['simple_browse_questions_tab'](filtered_df)
            else:
                st.error("❌ UI components not available for browsing")
        
        # Tab 3: Mode-specific Edit Tab
        with tab3:
            current_mode = mode_manager.get_current_mode()
            
            if current_mode == 'select':
                select_interface = fork_feature['SelectQuestionsInterface']()
                select_interface.render_selection_interface(filtered_df)
                
            elif current_mode == 'delete':
                delete_interface = fork_feature['DeleteQuestionsInterface']()
                delete_interface.render_deletion_interface(filtered_df)
                
            else:
                st.error(f"❌ Unknown mode: {current_mode}")
        
        # Tab 4: Export with Filtering
        with tab4:
            current_mode = mode_manager.get_current_mode()
            flag_manager = fork_feature['QuestionFlagManager']()
            
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
        
        # Tab 5: Settings (Optional)
        with tab5:
            st.markdown("### ⚙️ Application Settings")
            st.info("💡 Configure Q2LMS preferences and options.")
            
            # Add settings options here
            st.checkbox("🔍 Show detailed tooltips", value=True)
            st.checkbox("📊 Auto-refresh charts", value=False)
            st.selectbox("🎨 Theme", ["Default", "Dark", "Light"])

    def _render_tab_content_standard_with_overview(self, tab1, tab2, tab3, tab4, df, filtered_df, original_questions):
        """Render tab content without fork features but with overview tab"""
        
        # Tab 1: Database Overview - Detailed analysis
        with tab1:
            st.markdown("### 📊 Detailed Database Analysis") 
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                #ui_components['create_summary_charts'](df)
            else:
                st.error("❌ UI components not available for detailed overview")
        
        # Tab 2: Browse Questions
        with tab2:
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['simple_browse_questions_tab'](filtered_df)
            else:
                st.error("❌ UI components not available for browsing")
        
        # Tab 3: Standard Edit Tab
        with tab3:
            if self.app_config.is_available('question_editor'):
                question_editor = self.app_config.get_feature('question_editor')
                question_editor['side_by_side_question_editor'](filtered_df)
            else:
                st.error("❌ Question editor not available")
                st.info("You can still browse questions in the other tabs.")
        
        # Tab 4: Standard Export
        with tab4:
            self.render_export_tab(filtered_df, original_questions)
# Global instance
_ui_manager = None

def get_ui_manager(app_config):
    """Get the global UI manager instance"""
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = UIManager(app_config)
    return _ui_manager