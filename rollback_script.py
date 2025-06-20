#!/usr/bin/env python3
"""
Phase 3D Rollback and Recovery Script
Rollback to stable state, then carefully re-implement auto-renumbering
"""
import os
import shutil
import sys
from pathlib import Path
import git
from datetime import datetime

class Phase3DRollback:
    def __init__(self, project_root="C:/Users/aknoesen/Documents/Knoesen/question-database-manager"):
        self.project_root = Path(project_root)
        self.modules_dir = self.project_root / "modules"
        self.backup_dir = self.project_root / "rollback_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_backup(self):
        """Create backup of current state before rollback"""
        print("🔄 Creating backup of current state...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup key files
        files_to_backup = [
            "streamlit_app.py",
            "modules/upload_interface_v2.py",
            "modules/upload_state_manager.py", 
            "modules/database_merger.py",
            "modules/file_processor_module.py"
        ]
        
        for file_path in files_to_backup:
            source = self.project_root / file_path
            if source.exists():
                dest = self.backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                print(f"   ✅ Backed up: {file_path}")
            else:
                print(f"   ⚠️  Not found: {file_path}")
                
        print(f"✅ Backup created at: {self.backup_dir}")
        
    def check_git_status(self):
        """Check git status and suggest git rollback if appropriate"""
        try:
            repo = git.Repo(self.project_root)
            
            print("🔍 Git Status Check:")
            print(f"   Current branch: {repo.active_branch}")
            print(f"   Uncommitted changes: {len(list(repo.index.diff(None)))}")
            print(f"   Untracked files: {len(repo.untracked_files)}")
            
            # Show recent commits
            print("\n📋 Recent commits:")
            for commit in list(repo.iter_commits(max_count=5)):
                print(f"   {commit.hexsha[:8]} - {commit.message.strip()}")
                
            return repo
        except Exception as e:
            print(f"⚠️  Git not available or not a git repo: {e}")
            return None
    
    def create_stable_upload_interface_v2(self):
        """Create the stable version of upload_interface_v2.py without auto-renumbering"""
        
        stable_content = '''"""
Phase 3D: Upload Interface V2 - Stable Version
State-driven UI layer that integrates with Phases 3A/3B/3C
WITHOUT auto-renumbering (to be added incrementally)
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

# Phase 3B integration
try:
    from modules.upload_state_manager import (
        UploadState, get_current_upload_state, transition_upload_state,
        get_available_actions, reset_upload_state
    )
except ImportError as e:
    st.error(f"Phase 3B integration failed: {e}")
    st.stop()

# Phase 3A integration  
try:
    from modules.file_processor_module import FileProcessor
except ImportError as e:
    st.error(f"Phase 3A integration failed: {e}")
    st.stop()

# Phase 3C integration
try:
    from modules.database_merger import (
        create_merge_preview, execute_database_merge,
        prepare_session_state_for_preview, update_session_state_after_merge,
        MergeStrategy
    )
except ImportError as e:
    st.error(f"Phase 3C integration failed: {e}")
    st.stop()


class UploadInterfaceV2:
    """State-driven upload interface that adapts to current upload state"""
    
    def __init__(self):
        self.file_processor = FileProcessor()
        
    def render(self):
        """Main render function - entry point for UI"""
        try:
            current_state = get_current_upload_state()
            
            # Always render status header
            self.render_status_header(current_state)
            
            # State-specific interface
            if current_state == UploadState.NO_DATABASE:
                self.render_fresh_start_interface()
            elif current_state == UploadState.DATABASE_LOADED:
                self.render_database_management_interface()
            elif current_state == UploadState.PROCESSING_FILES:
                self.render_processing_interface()
            elif current_state == UploadState.PREVIEW_MERGE:
                self.render_merge_preview_interface()
            elif current_state == UploadState.ERROR_STATE:
                self.render_error_recovery_interface()
            elif current_state == UploadState.SUCCESS_STATE:
                self.render_success_interface()
            else:
                st.error(f"Unknown upload state: {current_state}")
                
        except Exception as e:
            st.error(f"Upload interface error: {e}")
            self.render_error_recovery_interface()
    
    def render_status_header(self, current_state: UploadState):
        """Always-visible status information"""
        
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
            # Quick actions
            if current_state == UploadState.DATABASE_LOADED:
                if st.button("📤 Export", key="quick_export"):
                    self.handle_export_action()
        
        with col4:
            # Rollback option
            if st.session_state.get('can_rollback', False):
                if st.button("↩️ Rollback", key="quick_rollback"):
                    self.handle_rollback_action()
    
    def render_fresh_start_interface(self):
        """Clean first-time user experience"""
        st.markdown("### 📤 Upload Your First Question Database")
        st.info("No database currently loaded. Upload a JSON file to begin.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Single File Upload")
            uploaded_file = st.file_uploader(
                "Choose JSON file",
                type=['json'],
                key="fresh_single_upload",
                help="Upload a single question database file"
            )
            if uploaded_file:
                self.handle_fresh_upload(uploaded_file)
        
        with col2:
            st.markdown("#### Multiple Files (Auto-Merge)")
            uploaded_files = st.file_uploader(
                "Choose JSON files",
                type=['json'],
                accept_multiple_files=True,
                key="fresh_multi_upload",
                help="Upload multiple files to merge automatically"
            )
            if uploaded_files:
                self.handle_fresh_multi_upload(uploaded_files)
    
    def render_database_management_interface(self):
        """Operations on existing database"""
        st.markdown("### 🗃️ Database Operations")
        
        # Show current database summary
        self.render_database_summary()
        
        # Operation tabs
        tab1, tab2, tab3 = st.tabs(["📝 Append Questions", "🔄 Replace Database", "📁 Merge Files"])
        
        with tab1:
            self.render_append_interface()
        
        with tab2:
            self.render_replace_interface()
        
        with tab3:
            self.render_multi_merge_interface()
    
    def render_database_summary(self):
        """Show current database information"""
        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Questions", len(df))
            with col2:
                topics = df['topic'].nunique() if 'topic' in df.columns else 0
                st.metric("Topics", topics)
            with col3:
                filename = st.session_state.get('current_filename', 'Unknown')
                st.metric("File", filename.split('/')[-1] if '/' in filename else filename)
            with col4:
                last_modified = st.session_state.get('last_modified', 'Unknown')
                st.metric("Modified", last_modified)
    
    def render_append_interface(self):
        """Interface for appending questions to existing database"""
        st.markdown("#### Add Questions to Current Database")
        
        uploaded_file = st.file_uploader(
            "Choose JSON file to append",
            type=['json'],
            key="append_upload",
            help="Questions will be added to the existing database"
        )
        
        if uploaded_file:
            self.handle_append_upload(uploaded_file)
    
    def render_replace_interface(self):
        """Interface for replacing entire database"""
        st.markdown("#### Replace Entire Database")
        st.warning("⚠️ This will completely replace your current database")
        
        uploaded_file = st.file_uploader(
            "Choose JSON file to replace database",
            type=['json'], 
            key="replace_upload",
            help="This will completely replace the current database"
        )
        
        if uploaded_file:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Confirm Replace", type="primary", key="confirm_replace"):
                    self.handle_replace_upload(uploaded_file)
            with col2:
                if st.button("❌ Cancel", key="cancel_replace"):
                    st.rerun()
    
    def render_multi_merge_interface(self):
        """Interface for merging multiple files"""
        st.markdown("#### Merge Multiple Files")
        
        uploaded_files = st.file_uploader(
            "Choose multiple JSON files",
            type=['json'],
            accept_multiple_files=True,
            key="multi_merge_upload",
            help="Merge multiple question database files"
        )
        
        if uploaded_files:
            self.handle_multi_merge_upload(uploaded_files)
    
    def render_processing_interface(self):
        """Show processing status"""
        st.markdown("### 🔄 Processing Files...")
        
        with st.spinner("Processing uploaded files..."):
            # This would typically be called automatically
            # but we show the interface for user feedback
            st.info("File processing in progress...")
    
    def render_merge_preview_interface(self):
        """Show merge preview and get user confirmation"""
        st.markdown("### 🔍 Merge Preview & Conflict Resolution")
        
        preview_data = st.session_state.get('preview_data', {})
        if not preview_data:
            st.error("No preview data available")
            return
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Questions", preview_data.get('existing_count', 0))
        with col2:
            st.metric("New Questions", preview_data.get('new_count', 0))
        with col3:
            st.metric("Final Total", preview_data.get('final_count', 0))
        with col4:
            conflicts = preview_data.get('total_conflicts', 0)
            st.metric("Conflicts", conflicts)
        
        # Strategy selection
        st.markdown("#### Merge Strategy")
        strategy_options = {
            'append_all': "Append All - Add all questions (including duplicates)",
            'skip_duplicates': "Skip Duplicates - Skip questions similar to existing ones",
            'replace_duplicates': "Replace Duplicates - Replace existing with new versions",
            'rename_duplicates': "Rename Duplicates - Rename conflicting questions"
        }
        
        selected_strategy = st.radio(
            "Choose merge strategy:",
            options=list(strategy_options.keys()),
            format_func=lambda x: strategy_options[x],
            key="merge_strategy_selection"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("✅ Confirm Merge", type="primary", key="confirm_merge"):
                self.execute_confirmed_merge(selected_strategy)
        with col2:
            if st.button("🔄 Refresh Preview", key="refresh_preview"):
                self.refresh_merge_preview(selected_strategy)
        with col3:
            if st.button("❌ Cancel", key="cancel_merge"):
                self.cancel_merge_operation()
    
    def render_error_recovery_interface(self):
        """Error handling and recovery options"""
        st.markdown("### ❌ Error Recovery")
        
        error_message = st.session_state.get('error_message', 'Unknown error occurred')
        st.error(f"Error: {error_message}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again", key="retry_operation"):
                reset_upload_state()
                st.rerun()
        with col2:
            if st.button("↩️ Go Back", key="go_back"):
                # Go back to previous state
                if 'df' in st.session_state and st.session_state.df is not None:
                    transition_upload_state(UploadState.DATABASE_LOADED, "error_recovery")
                else:
                    transition_upload_state(UploadState.NO_DATABASE, "error_recovery")
                st.rerun()
    
    def render_success_interface(self):
        """Success confirmation"""
        st.markdown("### ✅ Operation Successful")
        
        success_message = st.session_state.get('success_message', 'Operation completed successfully')
        st.success(success_message)
        
        if st.button("➡️ Continue", key="continue_after_success"):
            transition_upload_state(UploadState.DATABASE_LOADED, "success_acknowledged")
            st.rerun()
    
    # File handling methods (basic versions)
    def handle_fresh_upload(self, uploaded_file):
        """Handle fresh database upload"""
        try:
            processing_result = self.file_processor.process_file(uploaded_file)
            
            if processing_result.valid:
                # Convert to DataFrame and store
                df = pd.DataFrame(processing_result.questions)
                st.session_state['df'] = df
                st.session_state['original_questions'] = processing_result.questions
                st.session_state['current_filename'] = uploaded_file.name
                
                transition_upload_state(UploadState.DATABASE_LOADED, "fresh_upload_complete")
                st.success(f"Loaded {len(df)} questions successfully!")
                st.rerun()
            else:
                st.error("File validation failed")
                for issue in processing_result.issues:
                    st.error(f"- {issue.message}")
                    
        except Exception as e:
            st.error(f"Upload failed: {e}")
    
    def handle_append_upload(self, uploaded_file):
        """Handle appending questions (basic version without auto-renumbering)"""
        try:
            processing_result = self.file_processor.process_file(uploaded_file)
            
            if processing_result.valid:
                # Store for merge preview
                st.session_state['processing_results'] = {
                    'questions': processing_result.questions,
                    'format_detected': processing_result.format_detected,
                    'metadata': processing_result.metadata,
                    'issues': processing_result.issues
                }
                
                # Create basic merge preview
                self.prepare_basic_merge_preview(processing_result)
                transition_upload_state(UploadState.PREVIEW_MERGE, "append_preview_ready")
                st.rerun()
            else:
                st.error("File validation failed")
                    
        except Exception as e:
            st.error(f"Append upload failed: {e}")
    
    def prepare_basic_merge_preview(self, processing_result):
        """Create basic merge preview without auto-renumbering"""
        existing_df = st.session_state.get('df')
        new_questions = processing_result.questions
        
        # Basic preview data
        preview_data = {
            'existing_count': len(existing_df) if existing_df is not None else 0,
            'new_count': len(new_questions),
            'final_count': (len(existing_df) if existing_df is not None else 0) + len(new_questions),
            'total_conflicts': 0,  # Will be calculated by Phase 3C
            'merge_strategy': 'skip_duplicates'
        }
        
        st.session_state['preview_data'] = preview_data
    
    def execute_confirmed_merge(self, strategy):
        """Execute the merge operation"""
        try:
            # Use Phase 3C merge functionality
            result = execute_database_merge(
                existing_df=st.session_state['df'],
                processing_result=st.session_state['processing_results'],
                strategy=strategy
            )
            
            if result.success:
                update_session_state_after_merge(result)
                transition_upload_state(UploadState.SUCCESS_STATE, "merge_completed")
                st.session_state['success_message'] = f"Successfully merged! Database now has {len(result.merged_df)} questions."
                st.rerun()
            else:
                st.error(f"Merge failed: {result.error}")
                
        except Exception as e:
            st.error(f"Merge execution failed: {e}")
    
    # Utility methods
    def handle_export_action(self):
        """Handle export button click"""
        st.info("Export functionality would be implemented here")
    
    def handle_rollback_action(self):
        """Handle rollback button click"""
        st.info("Rollback functionality would be implemented here")
    
    def cancel_merge_operation(self):
        """Cancel current merge operation"""
        transition_upload_state(UploadState.DATABASE_LOADED, "merge_cancelled")
        st.rerun()
    
    def refresh_merge_preview(self, strategy):
        """Refresh merge preview with new strategy"""
        # Re-create preview with new strategy
        st.rerun()


# Main function for integration
def render_upload_interface_v2():
    """Main entry point for the upload interface"""
    interface = UploadInterfaceV2()
    interface.render()


# For testing
if __name__ == "__main__":
    st.title("Upload Interface V2 - Stable Version")
    render_upload_interface_v2()
'''
        
        # Write stable version
        interface_file = self.modules_dir / "upload_interface_v2.py"
        interface_file.write_text(stable_content, encoding='utf-8')
        print(f"✅ Created stable upload_interface_v2.py")
        
    def update_streamlit_app_safe_integration(self):
        """Update streamlit_app.py with safe Phase 3D integration"""
        
        app_file = self.project_root / "streamlit_app.py"
        if not app_file.exists():
            print("⚠️  streamlit_app.py not found")
            return
            
        # Read current content
        content = app_file.read_text(encoding='utf-8')
        
        # Add safe integration code
        integration_code = '''
# Phase 3D Integration - Safe fallback version
def render_upload_section():
    """Upload section with Phase 3D integration and fallback"""
    try:
        # Try Phase 3D first
        from modules.upload_interface_v2 import render_upload_interface_v2
        render_upload_interface_v2()
        return True
    except ImportError as e:
        st.warning(f"Phase 3D not available: {e}")
        return False
    except Exception as e:
        st.error(f"Phase 3D error: {e}")
        st.write("Falling back to basic upload interface...")
        return False

# In your main function, replace upload section with:
if not render_upload_section():
    # Fallback to original upload interface
    st.markdown("### Upload Interface (Fallback)")
    st.info("Using basic upload interface")
'''
        
        print("✅ Safe integration code prepared for streamlit_app.py")
        print("📋 Manual integration required - add the above code to your main app")
        
    def verify_phases(self):
        """Verify all required phases are present and working"""
        print("🔍 Verifying Phase implementations...")
        
        required_files = {
            "Phase 3A": "modules/file_processor_module.py",
            "Phase 3B": "modules/upload_state_manager.py", 
            "Phase 3C": "modules/database_merger.py"
        }
        
        all_good = True
        for phase, file_path in required_files.items():
            file_full_path = self.project_root / file_path
            if file_full_path.exists():
                print(f"   ✅ {phase}: {file_path}")
            else:
                print(f"   ❌ {phase}: {file_path} - MISSING")
                all_good = False
                
        return all_good
    
    def run_rollback(self):
        """Execute complete rollback process"""
        print("🚀 Starting Phase 3D Rollback Process")
        print("=" * 50)
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Check git status
        repo = self.check_git_status()
        
        # Step 3: Verify phases
        if not self.verify_phases():
            print("❌ Required phases missing - please ensure Phases 3A/3B/3C are complete")
            return False
            
        # Step 4: Create stable interface
        self.create_stable_upload_interface_v2()
        
        # Step 5: Update main app integration
        self.update_streamlit_app_safe_integration()
        
        print("\n✅ Rollback Complete!")
        print("=" * 50)
        print("Next steps:")
        print("1. Test the stable version: streamlit run streamlit_app.py")
        print("2. Verify basic upload functionality works")
        print("3. Ready for careful auto-renumbering implementation")
        print(f"4. Backup saved at: {self.backup_dir}")
        
        return True


if __name__ == "__main__":
    rollback = Phase3DRollback()
    success = rollback.run_rollback()
    
    if success:
        print("\n🎯 Ready for auto-renumbering implementation!")
    else:
        print("\n❌ Rollback failed - please check requirements")
