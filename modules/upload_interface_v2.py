"""
Upload Interface V2 - State-Driven UI Layer
Phase 3D: Complete upload interface rebuild

Integrates with:
- Phase 3A: file_processor_module.py (File processing and validation)
- Phase 3B: upload_state_manager.py (State management and transitions)  
- Phase 3C: database_merger.py (Database merging and conflict resolution)

Author: Phase 3D Implementation
Created: Based on proven backend foundation
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
import traceback
from pathlib import Path

# Import all proven backend modules
try:
    from modules.file_processor_module import FileProcessor
    from modules.upload_state_manager import (
        UploadState, 
        get_upload_state, 
        transition_upload_state,
        get_upload_actions,
        reset_upload
    )
    from modules.database_merger import (
        create_merge_preview,
        execute_database_merge, 
        prepare_session_state_for_preview,
        update_session_state_after_merge,
        get_merge_strategy_description,
        MergeStrategy
    )
except ImportError as e:
    st.error(f"Backend module import failed: {e}")
    st.stop()


class UploadInterfaceV2:
    """
    State-driven upload interface that adapts based on current upload state.
    Provides clean, intuitive workflows for all database operations.
    """
    
    def __init__(self):
        self.file_processor = FileProcessor()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state if needed (backward compatible)"""
        
        # Core state initialization
        if 'upload_state' not in st.session_state:
            st.session_state.upload_state = UploadState.NO_DATABASE
        
        # Processing state
        if 'processing_results' not in st.session_state:
            st.session_state.processing_results = {}
        
        if 'preview_data' not in st.session_state:
            st.session_state.preview_data = {}
        
        # UI state
        if 'error_message' not in st.session_state:
            st.session_state.error_message = ''
        
        if 'success_message' not in st.session_state:
            st.session_state.success_message = ''
    
    def render(self):
        """Main render method - adapts interface based on current state"""
        
        try:
            # Get current state
            current_state = get_upload_state()
            
            # Always render status header
            self.render_status_header(current_state)
            
            # Show messages if any
            self.render_messages()
            
            # State-specific interface
            interface_map = {
                UploadState.NO_DATABASE: self.render_fresh_start_interface,
                UploadState.DATABASE_LOADED: self.render_database_management_interface,
                UploadState.PROCESSING_FILES: self.render_processing_interface,
                UploadState.PREVIEW_MERGE: self.render_merge_preview_interface,
                UploadState.ERROR_STATE: self.render_error_recovery_interface,
                UploadState.SUCCESS_STATE: self.render_success_interface
            }
            
            interface_renderer = interface_map.get(current_state)
            if interface_renderer:
                interface_renderer()
            else:
                st.error(f"Unknown upload state: {current_state}")
                
        except Exception as e:
            st.error("Interface rendering error occurred")
            st.exception(e)
    
    # ========================================
    # STATUS HEADER COMPONENT
    # ========================================
    
    def render_status_header(self, current_state: UploadState):
        """Always-visible status information"""
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        
        with col1:
            # State indicator with emoji and color
            state_info = {
                UploadState.NO_DATABASE: ("🟡", "No Database"),
                UploadState.DATABASE_LOADED: ("🟢", "Database Loaded"),
                UploadState.PROCESSING_FILES: ("🔄", "Processing"),
                UploadState.PREVIEW_MERGE: ("🔍", "Preview Merge"),
                UploadState.ERROR_STATE: ("❌", "Error"),
                UploadState.SUCCESS_STATE: ("✅", "Success")
            }
            emoji, label = state_info.get(current_state, ("❓", "Unknown"))
            st.markdown(f"{emoji} **{label}**")
        
        with col2:
            # Database summary
            if hasattr(st.session_state, 'df') and st.session_state.df is not None:
                count = len(st.session_state.df)
                filename = st.session_state.get('current_filename', 'Unknown')
                st.markdown(f"📊 **{count} questions** in `{filename}`")
            else:
                st.markdown("📊 No database loaded")
        
        with col3:
            # Quick actions based on state
            if current_state == UploadState.DATABASE_LOADED:
                if st.button("📤 Export", key="quick_export", help="Export current database"):
                    self.handle_export_action()
        
        with col4:
            # Rollback option
            if st.session_state.get('can_rollback', False):
                if st.button("↩️ Rollback", key="quick_rollback", help="Undo last operation"):
                    self.handle_rollback_action()
        
        st.markdown("---")
    
    def render_messages(self):
        """Display success/error messages"""
        
        if st.session_state.get('error_message'):
            st.error(st.session_state.error_message)
            # Clear after display
            st.session_state.error_message = ''
        
        if st.session_state.get('success_message'):
            st.success(st.session_state.success_message)
            # Clear after display  
            st.session_state.success_message = ''
    
    # ========================================
    # FRESH START INTERFACE (NO_DATABASE)
    # ========================================
    
    def render_fresh_start_interface(self):
        """Clean interface for first-time users"""
        
        st.markdown("### 📤 Upload Your First Question Database")
        st.info("No database currently loaded. Upload a JSON file to begin working with questions.")
        
        # Create two columns for different upload options
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 Single File Upload")
            st.markdown("Upload one JSON question database file")
            
            uploaded_file = st.file_uploader(
                "Choose JSON file",
                type=['json'],
                key="fresh_single_upload",
                help="Upload a single question database file (Phase 3, 4, or Legacy format)"
            )
            
            if uploaded_file is not None:
                if st.button("Process File", key="process_fresh_single", type="primary"):
                    self.handle_fresh_upload(uploaded_file)
        
        with col2:
            st.markdown("#### 📁 Multiple Files (Auto-Merge)")
            st.markdown("Upload multiple JSON files to merge automatically")
            
            uploaded_files = st.file_uploader(
                "Choose JSON files",
                type=['json'],
                accept_multiple_files=True,
                key="fresh_multi_upload",
                help="Upload multiple files - they will be merged with conflict detection"
            )
            
            if uploaded_files:
                st.info(f"Selected {len(uploaded_files)} files for merging")
                if st.button("Process Files", key="process_fresh_multi", type="primary"):
                    self.handle_fresh_multi_upload(uploaded_files)
        
        # Help section
        with st.expander("ℹ️ Supported Formats & Help"):
            st.markdown("""
            **Supported Formats:**
            - Phase 4 format (recommended)
            - Phase 3 format 
            - Legacy format (auto-detected)
            
            **File Requirements:**
            - Valid JSON syntax
            - Proper question structure
            - LaTeX content supported
            
            **What happens next:**
            - File validation and format detection
            - Question extraction and processing
            - Database loading (single file) or merge preview (multiple files)
            """)
    
    # ========================================
    # DATABASE MANAGEMENT INTERFACE (DATABASE_LOADED)
    # ========================================
    
    def render_database_management_interface(self):
        """Interface when database exists - append/replace operations"""
        
        st.markdown("### 🗃️ Database Operations")
        
        # Show current database summary
        self.render_database_summary()
        
        # Operation tabs
        tab1, tab2, tab3 = st.tabs(["📝 Append Questions", "🔄 Replace Database", "📁 Merge Multiple Files"])
        
        with tab1:
            self.render_append_interface()
        
        with tab2:
            self.render_replace_interface()
        
        with tab3:
            self.render_multi_merge_interface()
    
    def render_database_summary(self):
        """Show summary of current database"""
        
        if not hasattr(st.session_state, 'df') or st.session_state.df is None:
            st.warning("No database loaded")
            return
        
        df = st.session_state.df
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Questions", len(df))
        
        with col2:
            # Count question types
            types = df.get('type', pd.Series()).value_counts()
            most_common = types.index[0] if len(types) > 0 else "Unknown"
            st.metric("Most Common Type", most_common)
        
        with col3:
            # Count topics
            topics = df.get('topic', pd.Series()).nunique()
            st.metric("Topics", topics)
        
        with col4:
            # File info
            filename = st.session_state.get('current_filename', 'Unknown')
            st.metric("Current File", filename)
        
        # Option to view details
        if st.checkbox("Show database details", key="show_db_details"):
            st.dataframe(df.head(10), use_container_width=True)
            if len(df) > 10:
                st.info(f"Showing first 10 of {len(df)} questions")
    
    def render_append_interface(self):
        """Interface for appending questions to existing database"""
        
        st.markdown("Add new questions to your existing database with conflict detection.")
        
        # Debug: Show current state
        st.write("🔍 **Debug**: Current upload state:", get_upload_state())
        st.write("🔍 **Debug**: Has database:", hasattr(st.session_state, 'df') and st.session_state.df is not None)
        
        uploaded_file = st.file_uploader(
            "Choose JSON file to append",
            type=['json'],
            key="append_upload_v2",  # Changed key to avoid conflicts
            help="Upload questions to add to current database"
        )
        
        # Debug: Show file upload status
        st.write("🔍 **Debug**: File uploaded:", uploaded_file is not None)
        if uploaded_file:
            st.write("🔍 **Debug**: File name:", uploaded_file.name)
            st.write("🔍 **Debug**: File size:", uploaded_file.size)
        
        if uploaded_file is not None:
            st.success(f"✅ File selected: {uploaded_file.name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Preview Merge", key="preview_append_v2", type="primary"):
                    st.write("🔍 **Debug**: Preview button clicked!")
                    with st.spinner("Processing file and detecting conflicts..."):
                        try:
                            self.handle_append_upload(uploaded_file)
                            st.write("🔍 **Debug**: handle_append_upload completed")
                        except Exception as e:
                            st.error(f"🔍 **Debug**: Error in handle_append_upload: {e}")
                            st.exception(e)
            
            with col2:
                st.info("📋 Preview will show conflicts and merge options")
        else:
            st.info("📤 Please select a JSON file to append to your database")
            
        # Debug: Show session state keys
        st.write("🔍 **Debug**: Session state keys:", list(st.session_state.keys()))
    
    def render_replace_interface(self):
        """Interface for replacing entire database"""
        
        st.markdown("⚠️ **Replace entire database** - This will permanently replace your current database.")
        
        # Warning about destructive action
        st.warning("This action will permanently replace your current database. Consider exporting first.")
        
        uploaded_file = st.file_uploader(
            "Choose JSON file for replacement",
            type=['json'],
            key="replace_upload",
            help="This file will completely replace your current database"
        )
        
        if uploaded_file is not None:
            st.error("**DESTRUCTIVE ACTION**: This will replace your entire database")
            
            col1, col2 = st.columns(2)
            
            with col1:
                confirm_replace = st.checkbox("I understand this will replace my database", key="confirm_replace")
            
            with col2:
                if confirm_replace:
                    if st.button("Replace Database", key="execute_replace", type="primary"):
                        self.handle_replace_upload(uploaded_file)
    
    def render_multi_merge_interface(self):
        """Interface for merging multiple files with existing database"""
        
        st.markdown("Merge multiple JSON files with your existing database.")
        
        uploaded_files = st.file_uploader(
            "Choose JSON files to merge",
            type=['json'],
            accept_multiple_files=True,
            key="multi_merge_upload",
            help="Select multiple files to merge with current database"
        )
        
        if uploaded_files:
            st.info(f"Selected {len(uploaded_files)} files for merging with existing database")
            
            if st.button("Preview Multi-Merge", key="preview_multi_merge", type="primary"):
                self.handle_multi_merge_upload(uploaded_files)
    
    # ========================================
    # PROCESSING INTERFACE (PROCESSING_FILES)
    # ========================================
    
    def render_processing_interface(self):
        """Show processing status and results"""
        
        st.markdown("### 🔄 Processing Files")
        
        # Show processing progress/results
        processing_results = st.session_state.get('processing_results', {})
        
        if processing_results:
            self.render_processing_results(processing_results)
        else:
            st.info("Processing files...")
    
    def render_processing_results(self, results: Dict[str, Any]):
        """Display file processing results"""
        
        st.markdown("#### Processing Results")
        
        # Overall status
        valid = results.get('valid', False)
        
        if valid:
            st.success("✅ File processing completed successfully")
        else:
            st.error("❌ File processing encountered issues")
        
        # Details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Format Detected:**")
            st.code(results.get('format_detected', 'Unknown'))
            
            st.markdown("**Questions Found:**")
            questions = results.get('questions', [])
            st.code(f"{len(questions)} questions")
        
        with col2:
            st.markdown("**Metadata:**")
            metadata = results.get('metadata', {})
            for key, value in metadata.items():
                st.text(f"{key}: {value}")
        
        # Issues (if any)
        issues = results.get('issues', [])
        if issues:
            with st.expander(f"⚠️ Issues Found ({len(issues)})"):
                for issue in issues:
                    severity = issue.get('severity', 'info')
                    message = issue.get('message', 'No message')
                    st.markdown(f"**{severity.upper()}**: {message}")
    
    # ========================================
    # MERGE PREVIEW INTERFACE (PREVIEW_MERGE)
    # ========================================
    
    def render_merge_preview_interface(self):
        """Complete merge preview with conflict resolution - Key new component"""
        
        st.markdown("### 🔍 Merge Preview & Conflict Resolution")
        
        preview_data = st.session_state.get('preview_data', {})
        if not preview_data:
            st.error("No preview data available")
            return
        
        # Top-level statistics
        self.render_merge_statistics(preview_data)
        
        # Strategy selection
        self.render_strategy_selection(preview_data)
        
        # Conflict details (if any)
        conflicts = preview_data.get('conflict_details', [])
        if conflicts:
            self.render_conflict_details_section(conflicts)
        else:
            st.success("🎉 No conflicts detected! Merge can proceed smoothly.")
        
        # Action buttons
        self.render_merge_actions(preview_data)
    
    def render_merge_statistics(self, preview_data: Dict[str, Any]):
        """Show merge statistics dashboard"""
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Questions", preview_data.get('existing_count', 0))
        
        with col2:
            st.metric("New Questions", preview_data.get('new_count', 0))
        
        with col3:
            final_count = preview_data.get('final_count', 0)
            existing_count = preview_data.get('existing_count', 0)
            delta = final_count - existing_count
            st.metric("Final Total", final_count, delta=f"+{delta}" if delta > 0 else str(delta))
        
        with col4:
            conflicts = preview_data.get('total_conflicts', 0)
            delta_text = f"{conflicts} to resolve" if conflicts > 0 else "None"
            st.metric("Conflicts", conflicts, delta=delta_text)
    
    def render_strategy_selection(self, preview_data: Dict[str, Any]):
        """Strategy selection with real-time preview updates"""
        
        st.markdown("#### Merge Strategy")
        
        current_strategy = preview_data.get('merge_strategy', 'skip_duplicates')
        
        strategy_options = {
            'append_all': "**Append All** - Add all questions (including duplicates)",
            'skip_duplicates': "**Skip Duplicates** - Skip questions similar to existing ones",
            'replace_duplicates': "**Replace Duplicates** - Replace existing with new versions", 
            'rename_duplicates': "**Rename Duplicates** - Rename conflicting questions"
        }
        
        selected_strategy = st.radio(
            "Choose how to handle conflicts:",
            options=list(strategy_options.keys()),
            format_func=lambda x: strategy_options[x],
            index=list(strategy_options.keys()).index(current_strategy) if current_strategy in strategy_options else 0,
            key="merge_strategy_selection"
        )
        
        # Show strategy description
        strategy_description = get_merge_strategy_description(selected_strategy)
        st.info(f"📝 {strategy_description}")
        
        # Update preview if strategy changed
        if selected_strategy != current_strategy:
            if st.button("🔄 Update Preview", key="update_strategy"):
                self.update_merge_preview_strategy(selected_strategy)
    
    def render_conflict_details_section(self, conflicts: List[Dict[str, Any]]):
        """Expandable conflict details"""
        
        st.markdown("#### Conflict Details")
        
        # Group conflicts by severity
        severity_groups = {}
        for conflict in conflicts:
            severity = conflict.get('severity', 'medium')
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(conflict)
        
        # Show each severity group
        severity_order = ['critical', 'high', 'medium', 'low']
        severity_colors = {
            'critical': '🔴',
            'high': '🟠', 
            'medium': '🟡',
            'low': '🟢'
        }
        
        for severity in severity_order:
            if severity in severity_groups:
                conflicts_group = severity_groups[severity]
                emoji = severity_colors[severity]
                
                with st.expander(f"{emoji} {severity.title()} Severity ({len(conflicts_group)} conflicts)"):
                    for i, conflict in enumerate(conflicts_group):
                        st.markdown(f"**Conflict {i+1}**: {conflict.get('description', 'No description')}")
                        st.markdown(f"*Suggestion*: {conflict.get('suggestion', 'No suggestion')}")
                        
                        if 'existing_question' in conflict and 'new_question' in conflict:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Existing:**")
                                existing_text = conflict['existing_question'].get('text', 'No text')
                                st.code(existing_text[:100] + "..." if len(existing_text) > 100 else existing_text)
                            with col2:
                                st.markdown("**New:**")
                                new_text = conflict['new_question'].get('text', 'No text')
                                st.code(new_text[:100] + "..." if len(new_text) > 100 else new_text)
                        
                        st.markdown("---")
    
    def render_merge_actions(self, preview_data: Dict[str, Any]):
        """Action buttons for merge confirmation"""
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("✅ Confirm Merge", type="primary", key="confirm_merge"):
                self.execute_confirmed_merge()
        
        with col2:
            if st.button("🔄 Change Strategy", key="change_strategy"):
                st.info("Use the strategy selection above to choose a different approach")
        
        with col3:
            if st.button("❌ Cancel", key="cancel_merge"):
                self.cancel_merge_operation()
    
    # ========================================
    # ERROR AND SUCCESS INTERFACES
    # ========================================
    
    def render_error_recovery_interface(self):
        """Interface for error state with recovery options"""
        
        st.markdown("### ❌ Error Recovery")
        
        error_msg = st.session_state.get('error_message', 'Unknown error occurred')
        st.error(f"Error: {error_msg}")
        
        st.markdown("#### Recovery Options:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Try Again", key="retry_operation"):
                self.handle_retry_operation()
        
        with col2:
            if st.button("↩️ Return to Previous", key="return_previous"):
                self.handle_return_to_previous()
        
        # Clear error and reset
        if st.button("🧹 Clear Error & Reset", key="clear_error"):
            self.handle_clear_error()
    
    def render_success_interface(self):
        """Interface for success state"""
        
        st.markdown("### ✅ Operation Successful")
        
        success_msg = st.session_state.get('success_message', 'Operation completed successfully')
        st.success(success_msg)
        
        # Transition back to appropriate state
        if st.button("Continue", key="continue_after_success"):
            self.handle_continue_after_success()
    
    # ========================================
    # FILE UPLOAD HANDLERS
    # ========================================
    
    def handle_fresh_upload(self, uploaded_file):
        """Handle fresh database upload (Phase 3A integration)"""
        
        try:
            # Transition to processing state
            transition_upload_state(UploadState.PROCESSING_FILES, "fresh_upload_started")
            
            # Process file using Phase 3A
            processing_result = self.file_processor.process_file(uploaded_file)
            
            # Check if processing was successful - try different attribute names
            is_valid = False
            if hasattr(processing_result, 'valid'):
                is_valid = processing_result.valid
            elif hasattr(processing_result, 'is_valid'):
                is_valid = processing_result.is_valid
            elif hasattr(processing_result, 'success'):
                is_valid = processing_result.success
            else:
                # If no clear validity attribute, check if we have questions
                is_valid = hasattr(processing_result, 'questions') and len(getattr(processing_result, 'questions', [])) > 0
            
            if is_valid:
                # Store processing results
                st.session_state.processing_results = {
                    'questions': getattr(processing_result, 'questions', []),
                    'format_detected': getattr(processing_result, 'format_detected', 'Unknown'),
                    'metadata': getattr(processing_result, 'metadata', {}),
                    'issues': getattr(processing_result, 'issues', []),
                    'valid': is_valid
                }
                
                # Apply fresh database directly (no merge needed)
                self.apply_fresh_database(processing_result, uploaded_file.name)
                
                # Success - but stay in DATABASE_LOADED state
                questions_count = len(getattr(processing_result, 'questions', []))
                st.session_state.success_message = f"Successfully loaded {questions_count} questions!"
                # Don't transition to SUCCESS_STATE - already in DATABASE_LOADED
                
            else:
                # Handle processing errors
                issues = getattr(processing_result, 'issues', [])
                if issues:
                    self.handle_processing_errors(issues)
                else:
                    st.session_state.error_message = "File processing failed - no valid questions found"
                    transition_upload_state(UploadState.ERROR_STATE, "processing_failed")
                
            # Trigger rerun to update UI
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "fresh upload")
    
    def handle_fresh_multi_upload(self, uploaded_files):
        """Handle multiple file upload for fresh start"""
        
        try:
            # Transition to processing state
            transition_upload_state(UploadState.PROCESSING_FILES, "multi_upload_started")
            
            # Process all files
            all_questions = []
            all_issues = []
            
            for uploaded_file in uploaded_files:
                processing_result = self.file_processor.process_file(uploaded_file)
                
                if processing_result.valid:
                    all_questions.extend(processing_result.questions)
                else:
                    all_issues.extend(processing_result.issues)
            
            if all_questions and not all_issues:
                # No conflicts in fresh start - merge everything
                self.apply_fresh_multi_database(all_questions, uploaded_files)
                
                st.session_state.success_message = f"Successfully merged {len(uploaded_files)} files into {len(all_questions)} questions!"
                transition_upload_state(UploadState.SUCCESS_STATE, "multi_upload_complete")
                
            else:
                # Handle errors
                if all_issues:
                    self.handle_processing_errors(all_issues)
                else:
                    st.session_state.error_message = "No valid questions found in uploaded files"
                    transition_upload_state(UploadState.ERROR_STATE, "no_valid_questions")
            
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "multi-file upload")
    
    def handle_append_upload(self, uploaded_file):
        """Handle append operation (Phase 3C integration)"""
        
        try:
            # Process file first using Phase 3A
            processing_result = self.file_processor.process_file(uploaded_file)
            
            # Check if processing was successful - try different attribute names
            is_valid = False
            if hasattr(processing_result, 'valid'):
                is_valid = processing_result.valid
            elif hasattr(processing_result, 'is_valid'):
                is_valid = processing_result.is_valid
            elif hasattr(processing_result, 'success'):
                is_valid = processing_result.success
            else:
                # If no clear validity attribute, check if we have questions
                is_valid = hasattr(processing_result, 'questions') and len(getattr(processing_result, 'questions', [])) > 0
            
            if is_valid:
                # Store processing results with safe attribute access
                st.session_state.processing_results = {
                    'questions': getattr(processing_result, 'questions', []),
                    'format_detected': getattr(processing_result, 'format_detected', 'Unknown'),
                    'metadata': getattr(processing_result, 'metadata', {}),
                    'issues': getattr(processing_result, 'issues', []),
                    'valid': is_valid
                }
                
                # Create merge preview using Phase 3C
                self.prepare_merge_preview(processing_result)
                
            else:
                # Handle processing errors
                issues = getattr(processing_result, 'issues', [])
                if issues:
                    self.handle_processing_errors(issues)
                else:
                    st.session_state.error_message = "File processing failed - no valid questions found"
                    transition_upload_state(UploadState.ERROR_STATE, "processing_failed")
            
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "append upload")
    
    def handle_replace_upload(self, uploaded_file):
        """Handle database replacement"""
        
        try:
            # Process file
            processing_result = self.file_processor.process_file(uploaded_file)
            
            if processing_result.valid:
                # Replace directly (no merge needed)
                self.apply_fresh_database(processing_result, uploaded_file.name)
                
                st.session_state.success_message = f"Successfully replaced database with {len(processing_result.questions)} questions!"
                transition_upload_state(UploadState.SUCCESS_STATE, "replace_complete")
                
            else:
                self.handle_processing_errors(processing_result.issues)
            
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "replace upload")
    
    def handle_multi_merge_upload(self, uploaded_files):
        """Handle multiple file merge with existing database"""
        
        # Implementation will be added in Phase 3D-C
        st.info("Multi-merge functionality will be implemented in next phase")
    
    # ========================================
    # DATABASE OPERATIONS
    # ========================================
    
    def apply_fresh_database(self, processing_result, filename: str):
        """Apply fresh database from processing result"""
        
        # Extract questions using safe attribute access
        questions = getattr(processing_result, 'questions', [])
        
        if not questions:
            st.session_state.error_message = "No questions found in processed file"
            transition_upload_state(UploadState.ERROR_STATE, "no_questions_found")
            return
        
        # Convert questions to DataFrame
        df = pd.DataFrame(questions)
        
        # Debug: Show original columns
        st.write("🔍 **Debug - Original columns:**", df.columns.tolist())
        
        # Map common question field variations to standard column names
        column_mappings = {
            'question_text': 'Question_Text',
            'text': 'Question_Text',
            'question': 'Question_Text',
            'title': 'Title',
            'question_title': 'Title',
            'type': 'Type',
            'question_type': 'Type',
            'difficulty': 'Difficulty',
            'topic': 'Topic',
            'subtopic': 'Subtopic',
            'points': 'Points',
            'correct_answer': 'Correct_Answer',
            'choices': 'Choices',
            'options': 'Choices',
            'feedback_correct': 'Correct_Feedback',
            'feedback_incorrect': 'Incorrect_Feedback',
            'explanation': 'Explanation'
        }
        
        # Apply column mappings
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns and new_name not in df.columns:
                df[new_name] = df[old_name]
                st.write(f"✅ Mapped {old_name} → {new_name}")
        
        # Handle choices array -> individual choice columns
        if 'Choices' in df.columns or 'choices' in df.columns:
            choices_col = 'Choices' if 'Choices' in df.columns else 'choices'
            
            # Create individual choice columns from choices array
            for i, choice_letter in enumerate(['A', 'B', 'C', 'D']):
                choice_col = f'Choice_{choice_letter}'
                if choice_col not in df.columns:
                    df[choice_col] = df[choices_col].apply(
                        lambda x: x[i] if isinstance(x, list) and len(x) > i else f'Option {choice_letter}'
                    )
                    st.write(f"✅ Created {choice_col}")
        
        # Ensure required columns exist for UI compatibility
        required_columns = {
            'Topic': 'General',
            'Subtopic': 'General',
            'Difficulty': 'Medium',
            'Type': 'multiple_choice',
            'Points': 1,
            'Question_Text': 'Sample question text',
            'Title': 'Sample Question',
            'Correct_Answer': 'A',
            'Choices': ['Option A', 'Option B', 'Option C', 'Option D'],
            'Choice_A': 'Option A',
            'Choice_B': 'Option B', 
            'Choice_C': 'Option C',
            'Choice_D': 'Option D',
            'Correct_Feedback': 'Correct!',
            'Incorrect_Feedback': 'Please try again.',
            'Explanation': 'This is the explanation.',
            'Tolerance': 0.05,  # For numerical questions
            'Units': '',        # For numerical questions
            'Format': 'decimal' # For numerical questions
        }
        
        st.write("🔍 **Debug - Adding required columns:**")
        for col, default_value in required_columns.items():
            if col not in df.columns:
                df[col] = default_value
                st.write(f"✅ Added missing column: {col}")
            else:
                st.write(f"⚠️ Column {col} already exists")
        
        # Final debug - show all columns
        st.write("🔍 **Debug - Final columns:**", df.columns.tolist())
        st.write("🔍 **Debug - DataFrame shape:**", df.shape)
        
        # Show first row to verify data
        if len(df) > 0:
            st.write("🔍 **Debug - First row data:**")
            st.dataframe(df.head(1))
        
        # Store in session state
        st.session_state.df = df
        st.session_state.original_questions = questions.copy()
        st.session_state.metadata = getattr(processing_result, 'metadata', {})
        st.session_state.current_filename = filename
        
        # Update state
        transition_upload_state(UploadState.DATABASE_LOADED, "database_applied")
    
    def apply_fresh_multi_database(self, all_questions: List[Dict], uploaded_files):
        """Apply fresh database from multiple files"""
        
        # Convert to DataFrame
        df = pd.DataFrame(all_questions)
        
        # Store in session state
        st.session_state.df = df
        st.session_state.original_questions = all_questions.copy()
        st.session_state.metadata = {'source': f'Merged from {len(uploaded_files)} files'}
        st.session_state.current_filename = f"Merged_Database_{len(uploaded_files)}_files.json"
        
        # Update state
        transition_upload_state(UploadState.DATABASE_LOADED, "multi_database_applied")
    
    def prepare_merge_preview(self, processing_result):
        """Create merge preview using Phase 3C API"""
        
        try:
            # Get current database
            existing_df = st.session_state.get('df')
            new_questions = getattr(processing_result, 'questions', [])
            
            if not new_questions:
                st.session_state.error_message = "No questions found in uploaded file"
                transition_upload_state(UploadState.ERROR_STATE, "no_questions_for_merge")
                return
            
            # Create preview with default strategy
            preview = create_merge_preview(
                existing_df=existing_df,
                new_questions=new_questions,
                strategy=MergeStrategy.SKIP_DUPLICATES,
                auto_renumber=True
            )
            
            # Prepare UI-friendly data using safe attribute access
            processing_results_dict = {
                'questions': new_questions,
                'format_detected': getattr(processing_result, 'format_detected', 'Unknown'),
                'metadata': getattr(processing_result, 'metadata', {}),
                'issues': getattr(processing_result, 'issues', [])
            }
            
            preview_data = prepare_session_state_for_preview(preview, processing_results_dict)
            st.session_state.preview_data = preview_data
            
            # Transition to preview state
            transition_upload_state(UploadState.PREVIEW_MERGE, "preview_prepared")
            
        except Exception as e:
            self.handle_merge_error(e)
    
    def update_merge_preview_strategy(self, selected_strategy: str):
        """Update merge preview with new strategy"""
        
        try:
            # Get processing result and existing database
            processing_result = st.session_state.get('processing_results', {})
            existing_df = st.session_state.get('df')
            
            if not processing_result or existing_df is None:
                st.error("Missing data for preview update")
                return
            
            # Map string to enum
            strategy_map = {
                'append_all': MergeStrategy.APPEND_ALL,
                'skip_duplicates': MergeStrategy.SKIP_DUPLICATES,
                'replace_duplicates': MergeStrategy.REPLACE_DUPLICATES,
                'rename_duplicates': MergeStrategy.RENAME_DUPLICATES
            }
            
            strategy = strategy_map.get(selected_strategy, MergeStrategy.SKIP_DUPLICATES)
            
            # Create new preview
            preview = create_merge_preview(
                existing_df=existing_df,
                new_questions=processing_result['questions'],
                strategy=strategy
            )
            
            # Update preview data
            preview_data = prepare_session_state_for_preview(preview, processing_result)
            st.session_state.preview_data = preview_data
            
        except Exception as e:
            self.handle_merge_error(e)
    
    def execute_confirmed_merge(self):
        """Execute merge using Phase 3C API"""
        
        try:
            # Get merge parameters
            preview_data = st.session_state.get('preview_data', {})
            selected_strategy = st.session_state.get('merge_strategy_selection', 'skip_duplicates')
            processing_result = st.session_state.get('processing_results', {})
            
            # Map string to enum
            strategy_map = {
                'append_all': MergeStrategy.APPEND_ALL,
                'skip_duplicates': MergeStrategy.SKIP_DUPLICATES,
                'replace_duplicates': MergeStrategy.REPLACE_DUPLICATES,
                'rename_duplicates': MergeStrategy.RENAME_DUPLICATES
            }
            
            strategy = strategy_map.get(selected_strategy, MergeStrategy.SKIP_DUPLICATES)
            
            # Execute merge
            merge_result = execute_database_merge(
                existing_df=st.session_state['df'],
                processing_result=processing_result,
                strategy=strategy
            )
            
            if merge_result.success:
                # Update session state using Phase 3C API
                update_session_state_after_merge(merge_result)
                
                # Success message
                final_count = len(merge_result.merged_df)
                st.session_state.success_message = f"Successfully merged! Database now has {final_count} questions."
                
                # Transition to success state
                transition_upload_state(UploadState.SUCCESS_STATE, "merge_completed")
                
            else:
                # Handle merge failure
                error_msg = getattr(merge_result, 'error', 'Unknown merge error')
                self.handle_merge_failure(error_msg)
            
            st.rerun()
            
        except Exception as e:
            self.handle_merge_error(e)
    
    def cancel_merge_operation(self):
        """Cancel merge and return to database loaded state"""
        
        try:
            # Clear preview data
            st.session_state.preview_data = {}
            st.session_state.processing_results = {}
            
            # Return to database loaded state
            transition_upload_state(UploadState.DATABASE_LOADED, "merge_cancelled")
            
            st.info("Merge operation cancelled")
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "cancel merge")
    
    # ========================================
    # ACTION HANDLERS
    # ========================================
    
    def handle_export_action(self):
        """Handle export action"""
        
        # This will integrate with existing export functionality
        st.info("Export functionality - integrate with existing export module")
    
    def handle_rollback_action(self):
        """Handle rollback action using Phase 3B API"""
        
        try:
            # Use Phase 3B rollback functionality
            from modules.upload_state_manager import rollback_to_previous_state
            
            success = rollback_to_previous_state()
            
            if success:
                st.session_state.success_message = "Successfully rolled back to previous state"
            else:
                st.session_state.error_message = "Unable to rollback - no previous state available"
            
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "rollback")
    
    def handle_retry_operation(self):
        """Retry the last failed operation"""
        
        # Clear error state and return to previous
        st.session_state.error_message = ''
        
        # Determine appropriate state to return to
        if hasattr(st.session_state, 'df') and st.session_state.df is not None:
            transition_upload_state(UploadState.DATABASE_LOADED, "retry_from_error")
        else:
            transition_upload_state(UploadState.NO_DATABASE, "retry_from_error")
        
        st.rerun()
    
    def handle_return_to_previous(self):
        """Return to previous state"""
        
        # Use Phase 3B state management
        try:
            from modules.upload_state_manager import get_previous_state
            
            previous_state = get_previous_state()
            if previous_state:
                transition_upload_state(previous_state, "return_to_previous")
            else:
                # Default fallback
                if hasattr(st.session_state, 'df') and st.session_state.df is not None:
                    transition_upload_state(UploadState.DATABASE_LOADED, "fallback_to_loaded")
                else:
                    transition_upload_state(UploadState.NO_DATABASE, "fallback_to_no_db")
            
            st.rerun()
            
        except Exception as e:
            self.handle_upload_error(e, "return to previous")
    
    def handle_clear_error(self):
        """Clear error state and reset"""
        
        # Clear all error-related session state
        st.session_state.error_message = ''
        st.session_state.processing_results = {}
        st.session_state.preview_data = {}
        
        # Reset to appropriate state
        reset_upload()
        
        st.rerun()
    
    def handle_continue_after_success(self):
        """Continue after successful operation"""
        
        # Clear success message
        st.session_state.success_message = ''
        
        # Transition to database loaded state
        transition_upload_state(UploadState.DATABASE_LOADED, "continue_after_success")
        
        st.rerun()
    
    # ========================================
    # ERROR HANDLERS
    # ========================================
    
    def handle_upload_error(self, error: Exception, operation: str):
        """Handle upload-related errors"""
        
        error_msg = f"Error during {operation}: {str(error)}"
        st.session_state.error_message = error_msg
        
        # Log the full traceback for debugging
        st.error(f"Upload error in {operation}")
        st.exception(error)
        
        # Transition to error state
        transition_upload_state(UploadState.ERROR_STATE, f"error_in_{operation}")
        
        st.rerun()
    
    def handle_processing_errors(self, issues: List[Dict]):
        """Handle file processing errors"""
        
        # Format issues for display
        error_messages = []
        for issue in issues:
            severity = issue.get('severity', 'error')
            message = issue.get('message', 'Unknown issue')
            error_messages.append(f"{severity.upper()}: {message}")
        
        full_error = "File processing failed:\n" + "\n".join(error_messages)
        st.session_state.error_message = full_error
        
        # Transition to error state
        transition_upload_state(UploadState.ERROR_STATE, "processing_errors")
        
        st.rerun()
    
    def handle_merge_error(self, error: Exception):
        """Handle merge-related errors"""
        
        error_msg = f"Merge operation failed: {str(error)}"
        st.session_state.error_message = error_msg
        
        # Log for debugging
        st.error("Merge error occurred")
        st.exception(error)
        
        # Transition to error state
        transition_upload_state(UploadState.ERROR_STATE, "merge_error")
        
        st.rerun()
    
    def handle_merge_failure(self, error_msg: str):
        """Handle merge operation failure"""
        
        st.session_state.error_message = f"Merge failed: {error_msg}"
        
        # Transition to error state
        transition_upload_state(UploadState.ERROR_STATE, "merge_failed")
        
        st.rerun()


# ========================================
# MAIN INTEGRATION FUNCTIONS
# ========================================

def render_upload_interface_v2():
    """
    Main function to render the complete upload interface.
    
    This replaces the old upload_handler functionality with a clean,
    state-driven interface that integrates with all Phase 3A/3B/3C modules.
    """
    
    try:
        # Create and render interface
        interface = UploadInterfaceV2()
        interface.render()
        
    except Exception as e:
        st.error("Critical error in upload interface")
        st.exception(e)
        
        # Emergency fallback
        st.markdown("### Emergency Upload")
        st.file_uploader(
            "Emergency file upload", 
            type=['json'], 
            key="emergency_upload",
            help="Use this if the main interface fails"
        )


# ========================================
# UTILITY FUNCTIONS
# ========================================

def get_upload_interface_status():
    """Get current status of upload interface for debugging"""
    
    return {
        'current_state': get_current_upload_state(),
        'has_database': hasattr(st.session_state, 'df') and st.session_state.df is not None,
        'database_size': len(st.session_state.df) if hasattr(st.session_state, 'df') and st.session_state.df is not None else 0,
        'has_preview_data': bool(st.session_state.get('preview_data')),
        'has_processing_results': bool(st.session_state.get('processing_results')),
        'can_rollback': st.session_state.get('can_rollback', False)
    }


def clear_upload_interface_state():
    """Clear all upload interface state - useful for testing"""
    
    keys_to_clear = [
        'processing_results',
        'preview_data', 
        'error_message',
        'success_message',
        'merge_strategy_selection'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Reset upload state
    reset_upload_state()


# ========================================
# TESTING SUPPORT
# ========================================

def test_upload_interface_v2():
    """Test function for upload interface - for development use"""
    
    st.markdown("### Upload Interface V2 Test")
    
    # Show current status
    status = get_upload_interface_status()
    st.json(status)
    
    # Test controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear State", key="test_clear_state"):
            clear_upload_interface_state()
            st.rerun()
    
    with col2:
        if st.button("Force Error State", key="test_error_state"):
            transition_upload_state(UploadState.ERROR_STATE, "test_error")
            st.session_state.error_message = "Test error message"
            st.rerun()
    
    # Render main interface
    st.markdown("---")
    render_upload_interface_v2()


if __name__ == "__main__":
    # For testing when run directly
    test_upload_interface_v2()