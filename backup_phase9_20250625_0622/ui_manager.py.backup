#!/usr/bin/env python3
"""
Q2LMS UI Manager
Handles user interface coordination, tab management, and rendering
"""

import streamlit as st
import pandas as pd
from datetime import datetime

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
            key="topic_filter_multi",
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
        """Render clean upload interface"""
        
        st.markdown("### 📁 Upload Question Database Files")
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        
        if self.app_config.is_available('upload_system'):
            # Use advanced upload system
            try:
                upload_system = self.app_config.get_feature('upload_system')
                upload_interface = upload_system['UploadInterfaceV2']()
                
                # Render individual sections directly to avoid duplicate headers
                upload_interface.render_upload_section()
                st.divider()
                upload_interface.render_preview_section()
                st.divider()
                upload_interface.render_results_section()
                
                # Check if we have a DataFrame loaded
                has_database = (
                    'df' in st.session_state and 
                    st.session_state['df'] is not None and 
                    len(st.session_state['df']) > 0
                )
            
            except Exception as e:
                st.error(f"Upload interface error: {e}")
                has_database = False
        
        elif self.app_config.is_available('basic_upload'):
            # Use basic upload system
            try:
                upload_system = self.app_config.get_feature('upload_system')
                has_database = upload_system['smart_upload_interface']()
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
    
    def render_export_tab(self, filtered_df, original_questions):
        """Render the export tab with optional fork filtering"""
        
        st.markdown('<div class="export-container">', unsafe_allow_html=True)
        
        if self.app_config.is_available('export_system'):
            # Show export badge
            st.markdown('<div class="export-badge">🚀 Export System</div>', unsafe_allow_html=True)
            
            # Use the modern export interface
            export_system = self.app_config.get_feature('export_system')
            export_system['integrate_with_existing_ui'](filtered_df, original_questions)
            
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
    
    def render_system_status(self):
        """Render overall system status - REMOVED for clean interface"""
        # This method is no longer needed - keeping empty for compatibility
        pass
    
    def render_branding_header(self):
        """Render the Q2LMS branding header"""
        
        st.markdown('<div class="q2lms-brand">Q2LMS</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-tagline">Transform questions into LMS-ready packages with seamless QTI export</div>', unsafe_allow_html=True)
    
    def render_getting_started_section(self):
        """Render the getting started section when no database is loaded"""
        
        st.markdown("---")
        st.markdown("## 🚀 Getting Started with Q2LMS")
        
        # Show fork feature status
        if self.app_config.is_available('fork_feature'):
            st.success("🎯 **Question Selection Fork Feature Enabled**")
            st.caption("After uploading questions, you can choose between Select Questions and Delete Questions modes.")
        else:
            st.info("📝 **Standard Editor Mode**")
            st.caption("Upload questions to access the standard question editor interface.")
        
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
            
            # Show fork features if available
            if self.app_config.is_available('fork_feature'):
                st.markdown('<div class="feature-card">', unsafe_allow_html=True)
                st.markdown("""
                ### 🎯 Question Selection Features:
                
                - **🎯 Select Mode** - Choose specific questions to export
                - **🗑️ Delete Mode** - Mark unwanted questions for exclusion
                - **🔄 Bulk Operations** - Select All, Clear All, Invert
                - **📊 Real-time Statistics** - Live selection counters
                - **💡 Dynamic Help** - Context-aware guidance
                """)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show export features if available
            if self.app_config.is_available('export_system'):
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
        self._render_sample_format_expander()
    
    def _render_sample_format_expander(self):
        """Render the sample JSON format expander"""
        
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
    
    def render_main_tabs(self, df, metadata, original_questions):
        """Render the main application tabs with fork feature integration"""
        
        # Show success message
        st.success(f"✅ Database loaded successfully! {len(df)} questions ready.")
        
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
            
            # Create tabs with mode-specific edit tab
            edit_tab_label = f"📝 {mode_name}"
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Browse Questions", edit_tab_label, "📥 Export"])
            
            # Render tab content with fork features
            self._render_tab_content_with_fork(tab1, tab2, tab3, tab4, df, filtered_df, original_questions, mode_manager, fork_feature)
            
        else:
            # Fallback to original interface if fork feature not available
            filtered_df = self.enhanced_subject_filtering(df)
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Browse Questions", "📝 Browse & Edit", "📥 Export"])
            
            # Render tab content without fork features
            self._render_tab_content_standard(tab1, tab2, tab3, tab4, df, filtered_df, original_questions)
        
        return True
    
    def _render_tab_content_with_fork(self, tab1, tab2, tab3, tab4, df, filtered_df, original_questions, mode_manager, fork_feature):
        """Render tab content with fork feature integration"""
        
        # Tab 1: Overview
        with tab1:
            if self.app_config.is_available('ui_components'):
                ui_components = self.app_config.get_feature('ui_components')
                ui_components['display_database_summary'](df, st.session_state['metadata'])
                st.markdown("---")
                ui_components['create_summary_charts'](df)
            else:
                st.error("❌ UI components not available for overview")
        
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
                ui_components['display_database_summary'](df, st.session_state['metadata'])
                st.markdown("---")
                ui_components['create_summary_charts'](df)
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

# Global instance
_ui_manager = None

def get_ui_manager(app_config):
    """Get the global UI manager instance"""
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = UIManager(app_config)
    return _ui_manager