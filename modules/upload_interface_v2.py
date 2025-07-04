# upload_interface_v2.py - FIXED: Single Action Flow
import streamlit as st
import json
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import contextlib
import io
import sys
from enum import Enum, auto
from datetime import datetime  # <-- Add this import
from .app_config import AppConfig  # Import for red button styling

class ProcessingState(Enum):
    """Clear states for the upload workflow"""
    WAITING_FOR_FILES = auto()
    FILES_READY = auto()
    PROCESSING = auto()
    PREVIEW_READY = auto()
    DATABASE_LOADED = auto()      # Renamed from COMPLETED
    SELECTING_CATEGORIES = auto() # New: Category/filter selection interface
    SELECTING_QUESTIONS = auto()  # New: covers select/delete modes
    EXPORTING = auto()            # New
    DOWNLOADING = auto()          # Phase 13: after export completion
    FINISHED = auto()             # New

    # For backward compatibility, you may want to alias COMPLETED:
    COMPLETED = DATABASE_LOADED

@dataclass
class MergePreviewData:
    """Clean data structure for merge preview"""
    total_questions: int
    conflicts: List[Dict]
    conflict_count: int
    renumbered_count: int
    preview_questions: List[Dict]
    merge_ready: bool

class UploadInterfaceV2:
    """FIXED: Single action workflow - no multiple prompt bars"""

    def __init__(self):
        self._initialize_session_state()

    @staticmethod
    def update_workflow_state(new_state: ProcessingState):
        """Update workflow state only if not moving backwards - with debugging and loop protection"""
        # Loop protection: prevent recursive state updates
        if getattr(st.session_state, "_state_updating", False):
            return
        st.session_state._state_updating = True

        try:
            # Initialize upload_state if it doesn't exist
            if 'upload_state' not in st.session_state:
                st.session_state.upload_state = {
                    'current_state': ProcessingState.WAITING_FOR_FILES,
                    'uploaded_files': None,
                    'preview_data': None,
                    'error_message': None,
                    'final_database': None,
                    'last_update': datetime.now()
                }
            
            current_state = st.session_state.upload_state.get('current_state')
            
            # Prevent redundant state changes
            if current_state == new_state:
                return

            # Define state progression order
            state_order = [
                ProcessingState.WAITING_FOR_FILES,
                ProcessingState.FILES_READY,
                ProcessingState.PROCESSING,
                ProcessingState.PREVIEW_READY,
                ProcessingState.DATABASE_LOADED,
                ProcessingState.SELECTING_CATEGORIES,
                ProcessingState.SELECTING_QUESTIONS,
                ProcessingState.EXPORTING,
                ProcessingState.DOWNLOADING,
                ProcessingState.FINISHED
            ]
            
            try:
                current_index = state_order.index(current_state) if current_state in state_order else -1
                new_index = state_order.index(new_state) if new_state in state_order else -1
            except (ValueError, AttributeError):
                current_index = -1
                new_index = -1

            # Special case: allow EXPORTING -> SELECTING_QUESTIONS (tab switch)
            if current_state == ProcessingState.EXPORTING and new_state == ProcessingState.SELECTING_QUESTIONS:
                st.session_state.upload_state['current_state'] = new_state
                st.session_state.upload_state['last_update'] = datetime.now()
            # Special case: allow backwards navigation within selection flow (categories <-> questions)
            elif ((current_state == ProcessingState.SELECTING_CATEGORIES and new_state == ProcessingState.SELECTING_QUESTIONS) or
                  (current_state == ProcessingState.SELECTING_QUESTIONS and new_state == ProcessingState.SELECTING_CATEGORIES)):
                st.session_state.upload_state['current_state'] = new_state
                st.session_state.upload_state['last_update'] = datetime.now()
            # Only allow forward or same-state transitions otherwise
            elif new_index >= current_index:
                st.session_state.upload_state['current_state'] = new_state
                st.session_state.upload_state['last_update'] = datetime.now()
            else:
                pass
        finally:
            st.session_state._state_updating = False

    @staticmethod
    def is_workflow_active() -> bool:
        """Return True if workflow is active (not FINISHED), else False"""
        upload_state = st.session_state.get('upload_state')
        if upload_state and upload_state.get('current_state') != ProcessingState.FINISHED:
            return True
        return False

    def _initialize_session_state(self):
        """Initialize session state with clear workflow states"""
        if 'upload_state' not in st.session_state:
            st.session_state.upload_state = {
                'current_state': ProcessingState.WAITING_FOR_FILES,
                'uploaded_files': None,
                'preview_data': None,
                'error_message': None,
                'final_database': None,
                'last_update': datetime.now()
            }
        else:
            # Ensure it's the correct structure
            if not isinstance(st.session_state.upload_state, dict):
                st.session_state.upload_state = {
                    'current_state': ProcessingState.WAITING_FOR_FILES,
                    'uploaded_files': None,
                    'preview_data': None,
                    'error_message': None,
                    'final_database': None,
                    'last_update': datetime.now()
                }

    def _get_current_state(self) -> ProcessingState:
        """Get current processing state"""
        upload_state = st.session_state.get('upload_state', {})
        if isinstance(upload_state, dict):
            return upload_state.get('current_state', ProcessingState.WAITING_FOR_FILES)
        return ProcessingState.WAITING_FOR_FILES

    def _set_state(self, new_state: ProcessingState, **kwargs):
        """Update the current state and any additional data - with debugging"""
        if 'upload_state' not in st.session_state:
            st.session_state.upload_state = {}

        # Use the protected bridge method instead of direct assignment
        UploadInterfaceV2.update_workflow_state(new_state)
        
        # Update any additional data (but don't overwrite the protected state)
        for key, value in kwargs.items():
            if key != 'current_state':  # Don't allow overriding the protected state
                st.session_state.upload_state[key] = value

    @staticmethod
    def render_progress_indicator(current_state: ProcessingState = None):
        """Show clear progress through the workflow in the sidebar, always visible if workflow is active"""
        # Always get the current state from session state, not from parameter
        upload_state = st.session_state.get('upload_state', {})
        current_state = upload_state.get('current_state', ProcessingState.WAITING_FOR_FILES)

        # Map DATABASE_LOADED to SELECTING_CATEGORIES for visual display (new flow)
        if current_state == ProcessingState.DATABASE_LOADED:
            current_state = ProcessingState.SELECTING_CATEGORIES

        # Do NOT map EXPORTING to SELECTING_QUESTIONS; let EXPORTING highlight the Export stage
        # if current_state == ProcessingState.EXPORTING:
        #     current_state = ProcessingState.SELECTING_QUESTIONS

        if not UploadInterfaceV2.is_workflow_active():
            return
        with st.sidebar:
            st.markdown("### 🔄 Workflow Progress")
            stages = [
                (ProcessingState.WAITING_FOR_FILES, "📁 Upload Files"),
                (ProcessingState.FILES_READY, "🔄 Process Files"),
                (ProcessingState.PREVIEW_READY, "📊 Review & Load"),
                (ProcessingState.SELECTING_CATEGORIES, "🛤️ Choose Path"),
                (ProcessingState.SELECTING_QUESTIONS, "📝 Select Questions"),
                (ProcessingState.EXPORTING, "📥 Export"),
                (ProcessingState.DOWNLOADING, "📥 Download"),
                (ProcessingState.FINISHED, "✅ Complete")
            ]
            current_index = None
            # Highlight the current stage
            for i, (stage, label) in enumerate(stages):
                if stage == current_state:
                    current_index = i
                    break
            if current_index is None:
                current_index = 0

            for i, (stage, label) in enumerate(stages):
                if i < current_index:
                    st.markdown(f"<div style='color:green;font-weight:bold;'>✅ {label}</div>", unsafe_allow_html=True)
                elif i == current_index:
                    st.markdown(f"<div style='color:#1a73e8;font-weight:bold;'>🔄 {label}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='color:gray;'>⏳ {label}</div>", unsafe_allow_html=True)
            st.markdown("---")

    @contextlib.contextmanager
    def _clean_operation(self, operation_name: str):
        """Context manager for clean operations without verbose output"""
        progress_placeholder = st.empty()
        progress_placeholder.info(f"🔄 **{operation_name}...**")
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer
            
            yield progress_placeholder
            
            progress_placeholder.success(f"✅ **{operation_name} completed successfully**")
            
        except Exception as e:
            progress_placeholder.error(f"❌ **{operation_name} failed:** {str(e)}")
            
            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()
            
            if stdout_content.strip() or stderr_content.strip():
                with st.expander(f"🔍 Debug Output for {operation_name}", expanded=False):
                    if stdout_content.strip():
                        st.text("Processing Output:")
                        st.code(stdout_content, language="text")
                    if stderr_content.strip():
                        st.text("Error Output:")
                        st.code(stderr_content, language="text")
            
            raise
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def render_upload_section(self):
        """FIXED: Render based on current state - single action only"""
        current_state = self._get_current_state()
        
        # Show progress
        self.render_progress_indicator(current_state)
        st.divider()
        
        # State-specific rendering
        if current_state == ProcessingState.WAITING_FOR_FILES:
            self._render_file_upload_state()
        elif current_state == ProcessingState.FILES_READY:
            self._render_process_files_state()
        elif current_state == ProcessingState.PROCESSING:
            self._render_processing_state()
        elif current_state == ProcessingState.PREVIEW_READY:
            self._render_preview_and_load_state()
        elif current_state == ProcessingState.COMPLETED:
            self._render_completed_state()
        elif current_state == ProcessingState.DOWNLOADING:
            self._render_downloading_state()
        elif current_state == ProcessingState.FINISHED:
            self._render_finished_state()
    
    def _render_file_upload_state(self):
        """State 1: Waiting for file upload"""
 
        
        uploaded_files = st.file_uploader(
            "Drag and drop files here or click Browse",
            accept_multiple_files=True,
            type=['json', 'csv', 'xlsx'],
            key="file_uploader",
            help="Select 1 or more JSON, CSV, or Excel files to merge"
        )
        
        if uploaded_files and len(uploaded_files) >= 1:
            # Show upload summary
            st.markdown("#### 📊 Upload Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Files Selected", len(uploaded_files))
            with col2:
                total_size = sum(file.size for file in uploaded_files) / (1024*1024)
                st.metric("Total Size", f"{total_size:.1f} MB")
            with col3:
                mode = "Direct Load" if len(uploaded_files) == 1 else "Merge Files"
                st.metric("Processing Mode", mode)
            
            # Show file list
            with st.expander("📄 Selected Files", expanded=True):
                for i, file in enumerate(uploaded_files, 1):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"{i}. {file.name}")
                    with col2:
                        st.write(f"{file.size/1024:.1f} KB")
                    with col3:
                        st.write(file.type or "Unknown")
            
            # SINGLE ACTION BUTTON - Move to next state
            if AppConfig.create_red_button("🚀 Process Files", "primary-action", "process_files_btn", use_container_width=True):
                self._set_state(ProcessingState.FILES_READY, uploaded_files=uploaded_files)
                st.rerun()
    
    def _render_process_files_state(self):
        """State 2: Ready to process files"""
        st.header("🔄 Processing Files")
        
        uploaded_files = st.session_state.upload_state.get('uploaded_files', [])
        
        if not uploaded_files:
            st.error("❌ No files found. Please upload files again.")
            self._set_state(ProcessingState.WAITING_FOR_FILES)
            st.rerun()
            return
        
        st.info(f"Ready to process {len(uploaded_files)} file(s)")
        
        # Show what will happen
        if len(uploaded_files) == 1:
            st.write("📄 **Single file detected** - will load directly into database")
        else:
            st.write(f"📁 **Multiple files detected** - will merge {len(uploaded_files)} files with conflict resolution")
        
        # Process files automatically
        with st.spinner("Processing files..."):
            try:
                self._process_uploaded_files(uploaded_files)
                self._set_state(ProcessingState.PREVIEW_READY)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Processing failed: {e}")
                self._set_state(ProcessingState.WAITING_FOR_FILES, error_message=str(e))
    
    def _render_processing_state(self):
        """State 3: Currently processing (shouldn't be seen long)"""
        st.header("⏳ Processing...")
        st.info("Processing your files, please wait...")
    
    def _render_preview_and_load_state(self):
        """State 4: Show preview and single load action"""
        st.header("📊 Review Processing Results")
        
        upload_state = st.session_state.get('upload_state', {})
        preview_data = upload_state.get('preview_data')
        
        if not preview_data:
            st.error("❌ No preview data available.")
            self._set_state(ProcessingState.WAITING_FOR_FILES)
            st.rerun()
            return
        
        # Show results summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions", preview_data.total_questions)
        with col2:
            st.metric("Conflicts Resolved", preview_data.conflict_count)
        with col3:
            st.metric("Auto-Renumbered", preview_data.renumbered_count)
        
        # Show status
        if preview_data.conflict_count == 0:
            st.success("✅ **No conflicts detected - ready to load!**")
        else:
            st.warning(f"⚠️ **{preview_data.conflict_count} conflicts resolved automatically**")
            
            # Show conflict details in expander
            if preview_data.conflicts:
                with st.expander("📋 View Conflict Resolution Details"):
                    for conflict in preview_data.conflicts:
                        st.caption(f"• {conflict['description']}")
        
        # Preview questions
        with st.expander("👀 Preview First 10 Questions"):
            for i, q in enumerate(preview_data.preview_questions, 1):
                question_text = q.get('question_text', q.get('question', q.get('Question', 'No question text')))
                question_id = q.get('id', q.get('ID', 'N/A'))
                st.write(f"{i}. **ID {question_id}:** {question_text[:100]}...")
        
        # SINGLE ACTION BUTTON - Complete the process
        button_text = "📊 Load Database" if preview_data.conflict_count == 0 else "📊 Complete Merge & Load"
        
        if AppConfig.create_red_button(button_text, "primary-action", "load_database_btn", use_container_width=True):
            with st.spinner("Loading database..."):
                try:
                    self._execute_merge(preview_data)
                    # Only set to COMPLETED if not already in a later state  
                    current_state = st.session_state.upload_state.get('current_state')
                    later_states = [ProcessingState.SELECTING_QUESTIONS, ProcessingState.EXPORTING, ProcessingState.DOWNLOADING, ProcessingState.FINISHED]
                    if current_state not in later_states:
                        self._set_state(ProcessingState.COMPLETED)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Loading failed: {e}")

    def _render_completed_state(self):
        """State 5: Process completed successfully"""
        st.header("✅ Database Loaded Successfully!")
        
        upload_state = st.session_state.get('upload_state', {})
        preview_data = upload_state.get('preview_data')
        
        # Concise status indicator
        if preview_data:
            # Get topic count from the actual dataframe if available
            topics_count = 0
            if 'df' in st.session_state and not st.session_state['df'].empty:
                df = st.session_state['df']
                topics_count = df['Topic'].dropna().nunique() if 'Topic' in df.columns else 0
        
        # Show what user can do next
        st.info("""
        **🎯 What's Next?**
        - Browse and edit questions in the tabs above
        - Use topic filtering in the sidebar
        - Export to various formats when ready
        """)
        
        # Database Analysis Section
        if 'df' in st.session_state and not st.session_state['df'].empty:
            st.markdown("---")
            st.markdown("### 📊 Database Overview")
            
            # Quick stats in columns
            df = st.session_state['df']
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Questions", len(df))
            with col2:
                unique_topics = df['Topic'].dropna().nunique() if 'Topic' in df.columns else 0
                st.metric("Topics", unique_topics)
            with col3:
                unique_subtopics = df['Subtopic'].dropna().nunique() if 'Subtopic' in df.columns else 0
                st.metric("Subtopics", unique_subtopics)
            with col4:
                unique_difficulties = df['Difficulty'].dropna().nunique() if 'Difficulty' in df.columns else 0
                st.metric("Difficulty Levels", unique_difficulties)
            
            # Detailed Analysis (Expandable)
            with st.expander("🔍 **View Detailed Database Analysis**", expanded=False):
                self._render_database_analysis(df)
        
        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            if AppConfig.create_red_button("📁 Load Another Database", "secondary-action", "load_another_btn", use_container_width=True):
                self._reset_state()
                st.rerun()
        
        with col2:
            if AppConfig.create_red_button("📊 View Database Overview", "secondary-action", "view_overview_btn", use_container_width=True):
                # This will show the main interface above
                pass
    
    def _process_uploaded_files(self, files) -> None:
        """Process uploaded files and generate preview data with clean output"""
        try:
            # Step 1: Load and validate files
            file_data = self._load_files(files)
            
            # Step 2: Create merge preview with auto-renumbering
            preview_data = self._create_clean_preview(file_data)
            
            # Step 3: Store in session state
            self._set_state(
                ProcessingState.PREVIEW_READY,
                preview_data=preview_data,
                error_message=None
            )
                
        except Exception as e:
            self._set_state(ProcessingState.WAITING_FOR_FILES, error_message=str(e))
            raise
    
    def _load_files(self, files) -> List[Dict]:
        """Load and parse uploaded files"""
        file_data = []
        for file in files:
            data = self._parse_file(file)
            file_data.append({
                'name': file.name,
                'questions': data,
                'count': len(data)
            })
        return file_data
    
    def _parse_file(self, file):
        """Parse uploaded file based on type"""
        try:
            if file.name.endswith('.json'):
                content = file.read().decode('utf-8')
                data = json.loads(content)
                if 'questions' in data:
                    return data['questions']
                elif isinstance(data, list):
                    return data
                else:
                    return [data]
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file)
                return df.to_dict('records')
            else:
                raise ValueError(f"Unsupported file type: {file.name}")
        except Exception as e:
            st.error(f"Error parsing {file.name}: {e}")
            return []
    
    def _create_clean_preview(self, file_data: List[Dict]) -> MergePreviewData:
        """Create merge preview with clean data structure"""
        all_questions = []
        conflicts = []
        seen_ids = set()
        renumbered_count = 0
        
        if len(file_data) == 1:
            # Single file - just load questions
            all_questions = file_data[0]['questions']
            conflicts = []
            renumbered_count = 0
        else:
            # Multiple files - merge with conflict resolution
            for file_info in file_data:
                for question in file_info['questions']:
                    q_id = question.get('id', question.get('ID', ''))
                    
                    # Check for ID conflicts and auto-renumber
                    if q_id in seen_ids:
                        original_id = q_id
                        counter = 1
                        while f"{q_id}_{counter}" in seen_ids:
                            counter += 1
                        new_id = f"{q_id}_{counter}"
                        question['id'] = new_id
                        renumbered_count += 1
                        conflicts.append({
                            'id': original_id,
                            'description': f"ID {original_id} renamed to {new_id}"
                        })
                    
                    seen_ids.add(question.get('id', q_id))
                    all_questions.append(question)
        
        # Create preview data
        preview_data = MergePreviewData(
            total_questions=len(all_questions),
            conflicts=conflicts,
            conflict_count=len(conflicts),
            renumbered_count=renumbered_count,
            preview_questions=all_questions[:10],
            merge_ready=True
        )
        
        # Store ALL merged questions for later use
        preview_data.all_merged_questions = all_questions
        
        return preview_data
    
    def _execute_merge(self, preview: MergePreviewData):
        """Execute the final merge operation"""
        try:
            # Get all merged questions
            if hasattr(preview, 'all_merged_questions'):
                all_merged_questions = preview.all_merged_questions
            else:
                all_merged_questions = preview.preview_questions
            
            # Update upload state
            # Only set to COMPLETED if not already in a later state
            current_state = st.session_state.upload_state.get('current_state')
            later_states = [ProcessingState.SELECTING_QUESTIONS, ProcessingState.EXPORTING, ProcessingState.DOWNLOADING, ProcessingState.FINISHED]
            if current_state not in later_states:
                # Set to DATABASE_LOADED first, then immediately transition to SELECTING_CATEGORIES
                self._set_state(
                    ProcessingState.DATABASE_LOADED,
                    final_database=all_merged_questions,
                    error_message=None
                )
                # Automatically transition to SELECTING_CATEGORIES for the new workflow
                self._set_state(ProcessingState.SELECTING_CATEGORIES)
            
            # Transfer to main app session state
            df_data = []
            for q in all_merged_questions:
                # Handle choices
                choices = q.get('choices', q.get('Choices', []))
                choice_a = choices[0] if len(choices) > 0 else ''
                choice_b = choices[1] if len(choices) > 1 else ''
                choice_c = choices[2] if len(choices) > 2 else ''
                choice_d = choices[3] if len(choices) > 3 else ''
                choice_e = choices[4] if len(choices) > 4 else ''
                
                # Handle image_file array
                image_files = q.get('image_file', [])
                image_file_str = ', '.join(image_files) if image_files else ''
                
                df_data.append({
                    'ID': q.get('id', ''),
                    'Title': q.get('title', ''),
                    'Type': q.get('type', 'multiple_choice'),
                    'Question_Text': q.get('question_text', ''),
                    'Topic': q.get('topic', ''),
                    'Subtopic': q.get('subtopic', ''),
                    'Difficulty': q.get('difficulty', 'Medium'),
                    'Points': q.get('points', 1),
                    'Correct_Answer': q.get('correct_answer', 'A'),
                    'Tolerance': q.get('tolerance', 0.05),
                    'Choice_A': choice_a,
                    'Choice_B': choice_b,
                    'Choice_C': choice_c,
                    'Choice_D': choice_d,
                    'Choice_E': choice_e,
                    'Correct_Feedback': q.get('feedback_correct', ''),
                    'Incorrect_Feedback': q.get('feedback_incorrect', ''),
                    'Feedback_Correct': q.get('feedback_correct', ''),
                    'Feedback_Incorrect': q.get('feedback_incorrect', ''),
                    'Image_File': image_file_str,
                    'Image_Files': image_files,
                    'Choices': choices,
                    'Question': q.get('question_text', ''),
                    'Answer': q.get('correct_answer', 'A'),
                    'Explanation': q.get('feedback_correct', ''),
                    'Category': q.get('topic', ''),
                    'Level': q.get('difficulty', 'Medium'),
                })
            
            # Set main app session state
            st.session_state['df'] = pd.DataFrame(df_data)
            st.session_state['original_questions'] = all_merged_questions
            st.session_state['metadata'] = {
                'source': 'merged_database',
                'total_questions': len(all_merged_questions),
                'conflicts_resolved': preview.conflict_count
            }
                
        except Exception as e:
            st.error(f"Error completing merge: {e}")
            raise
    
    def _reset_state(self):
        """Reset to initial state for new upload"""
        st.session_state.upload_state = {
            'uploaded_files': None,
            'preview_data': None,
            'error_message': None,
            'final_database': None
        }
        
        # Use bridge method for state reset
        UploadInterfaceV2.update_workflow_state(ProcessingState.WAITING_FOR_FILES)
        
        # Clear main session state
        for key in ['df', 'original_questions', 'metadata']:
            if key in st.session_state:
                del st.session_state[key]
    
    def render_complete_interface(self):
        """FIXED: Render the complete interface with single action flow"""
        # Error handling
        upload_state = st.session_state.get('upload_state', {})
        if isinstance(upload_state, dict) and upload_state.get('error_message'):
            st.error(f"❌ {upload_state['error_message']}")
            st.divider()
        
        # Main interface - single method handles all states
        self.render_upload_section()
        
        # Debug section (optional)
        if st.checkbox("🔧 Show Debug Info", value=False):
            st.json(upload_state if isinstance(upload_state, dict) else str(upload_state))
    
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
            # Transition to DOWNLOADING state
            if 'upload_state' in st.session_state:
                UploadInterfaceV2.update_workflow_state(ProcessingState.DOWNLOADING)
            st.success("🎉 Export completed successfully!")
            st.rerun()  # Trigger re-render to show DOWNLOADING state UI
            # --- Completion section ---
            st.markdown("---")
            st.success("🎉 Export Complete!")
            st.markdown("### What's Next?")
            col1, col2 = st.columns(2)
            with col1:
                if AppConfig.create_red_button("🚪 Exit Application", "destructive-action", "export_exit_btn", use_container_width=True):
                    # Use the existing working exit interface from exit_manager
                    st.session_state['show_exit_interface'] = True
                    st.session_state['exit_message'] = "Opening graceful exit interface..."
                    st.rerun()
            with col2:
                if AppConfig.create_red_button("🔄 Start Over", "primary-action", "export_restart_btn", use_container_width=True):
                    UploadInterfaceV2.update_workflow_state(ProcessingState.WAITING_FOR_FILES)
                    st.rerun()
        
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
                # Transition to DOWNLOADING state
                if 'upload_state' in st.session_state:
                    UploadInterfaceV2.update_workflow_state(ProcessingState.DOWNLOADING)
                st.success("🎉 Export completed successfully!")
                st.rerun()  # Trigger re-render to show DOWNLOADING state UI
                # --- Completion section ---
                st.markdown("---")
                st.success("🎉 Export Complete!")
                st.markdown("### What's Next?")
                col1, col2 = st.columns(2)
                with col1:
                    if AppConfig.create_red_button("🚪 Exit Application", "destructive-action", "json_exit_btn", use_container_width=True):
                        # Use the existing working exit interface from exit_manager
                        st.session_state['show_exit_interface'] = True
                        st.session_state['exit_message'] = "Opening graceful exit interface..."
                        st.rerun()
                with col2:
                    if AppConfig.create_red_button("🔄 Start Over", "primary-action", "json_restart_btn", use_container_width=True):
                        UploadInterfaceV2.update_workflow_state(ProcessingState.WAITING_FOR_FILES)
                        st.rerun()
    
    def _render_downloading_state(self):
        """State 6: Download in progress - Phase 13 graceful exit implementation"""
        st.header("📥 Download in Progress")
        
        st.info("🔄 **Your export download is being processed...**")
        
        # Show that we're in download state
        st.markdown("""
        **📋 Download Status:**
        
        ✅ Export processing completed  
        🔄 File download initiated  
        ⏳ Waiting for download confirmation  
        
        **📌 Note:** This screen will update once your download is complete.
        """)
        
        # Manual completion button for users whose downloads completed
        st.markdown("---")
        st.markdown("### ✅ Download Complete?")
        
        col1, col2 = st.columns(2)
        with col1:
            if AppConfig.create_red_button("✅ My Download is Complete", "confirmation-action", "download_complete_btn", use_container_width=True):
                # Transition to FINISHED state
                self._set_state(ProcessingState.FINISHED)
                st.rerun()
        
        with col2:
            if AppConfig.create_red_button("🔄 Start Over", "secondary-action", "download_restart_btn", use_container_width=True):
                self._reset_state()
                st.rerun()
    
    def _render_finished_state(self):
        """State 7: Final graceful exit state - Phase 13 implementation"""
        st.header("🎉 Session Complete!")
        
        # Celebration and summary
        st.success("✨ **Congratulations! Your Q2LMS session has been completed successfully.**")
        
        st.markdown("""
        **📋 Session Summary:**
        
        ✅ Questions processed and loaded  
        ✅ Export completed successfully  
        ✅ Files downloaded to your device  
        
        **🎯 Thank you for using Q2LMS!**
        """)
        
        # Final exit options
        st.markdown("---")
        st.markdown("### 🚪 What would you like to do?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if AppConfig.create_red_button("🔄 Start New Session", "primary-action", "new_session_btn", use_container_width=True):
                # Reset everything and start over
                self._reset_state()
                st.rerun()
        
        with col2:
            if AppConfig.create_red_button("🚪 Exit Application", "destructive-action", "finished_exit_btn", use_container_width=True):
                # Use the existing working exit interface from exit_manager
                st.session_state['show_exit_interface'] = True
                st.session_state['exit_message'] = "Opening graceful exit interface..."
                st.rerun()

    def _render_database_analysis(self, df: pd.DataFrame):
        """Render detailed database analysis for course planning"""
        st.markdown("#### 📋 **Detailed Database Analysis for Course Planning**")
        
        # Topic Analysis
        if 'Topic' in df.columns:
            st.markdown("##### 🏷️ **Topic Distribution**")
            topic_counts = df['Topic'].value_counts().sort_values(ascending=False)
            
            if not topic_counts.empty:
                # Create two columns for topic display
                topic_col1, topic_col2 = st.columns(2)
                
                with topic_col1:
                    st.markdown("**Questions per Topic:**")
                    for topic, count in topic_counts.head(10).items():
                        percentage = (count / len(df)) * 100
                        st.write(f"• **{topic}:** {count} questions ({percentage:.1f}%)")
                    
                    if len(topic_counts) > 10:
                        st.caption(f"... and {len(topic_counts) - 10} more topics")
                
                with topic_col2:
                    # Topic coverage chart
                    try:
                        import plotly.express as px
                        fig = px.pie(
                            values=topic_counts.head(8).values,
                            names=topic_counts.head(8).index,
                            title="Topic Distribution (Top 8)"
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        # Fallback to simple bar chart with matplotlib/streamlit
                        st.bar_chart(topic_counts.head(8))
            else:
                st.info("No topic information available")
        
        st.markdown("---")
        
        # Subtopic Analysis
        if 'Subtopic' in df.columns:
            st.markdown("##### 🎯 **Subtopic Breakdown**")
            subtopic_counts = df['Subtopic'].value_counts().sort_values(ascending=False)
            
            if not subtopic_counts.empty:
                # Group by topic if possible
                if 'Topic' in df.columns:
                    st.markdown("**Subtopics by Topic:**")
                    for topic in df['Topic'].unique()[:5]:  # Show top 5 topics
                        if pd.notna(topic):
                            topic_subtopics = df[df['Topic'] == topic]['Subtopic'].value_counts()
                            if not topic_subtopics.empty:
                                st.write(f"**{topic}:**")
                                for subtopic, count in topic_subtopics.head(5).items():
                                    if pd.notna(subtopic):
                                        st.write(f"  • {subtopic}: {count} questions")
                else:
                    st.markdown("**All Subtopics:**")
                    for subtopic, count in subtopic_counts.head(15).items():
                        if pd.notna(subtopic):
                            percentage = (count / len(df)) * 100
                            st.write(f"• **{subtopic}:** {count} questions ({percentage:.1f}%)")
            else:
                st.info("No subtopic information available")
        
        st.markdown("---")
        
        # Difficulty Analysis
        if 'Difficulty' in df.columns:
            st.markdown("##### ⚡ **Difficulty Distribution**")
            difficulty_counts = df['Difficulty'].value_counts()
            
            if not difficulty_counts.empty:
                diff_col1, diff_col2 = st.columns(2)
                
                with diff_col1:
                    st.markdown("**Question Difficulty Breakdown:**")
                    total_questions = len(df)
                    for difficulty, count in difficulty_counts.items():
                        if pd.notna(difficulty):
                            percentage = (count / total_questions) * 100
                            # Color code by difficulty
                            if difficulty.lower() in ['easy', 'beginner', 'basic']:
                                st.success(f"🟢 **{difficulty}:** {count} questions ({percentage:.1f}%)")
                            elif difficulty.lower() in ['medium', 'intermediate', 'moderate']:
                                st.warning(f"🟡 **{difficulty}:** {count} questions ({percentage:.1f}%)")
                            elif difficulty.lower() in ['hard', 'difficult', 'advanced', 'expert']:
                                st.error(f"🔴 **{difficulty}:** {count} questions ({percentage:.1f}%)")
                            else:
                                st.info(f"⚪ **{difficulty}:** {count} questions ({percentage:.1f}%)")
                
                with diff_col2:
                    # Difficulty balance analysis
                    st.markdown("**Difficulty Balance Analysis:**")
                    if len(difficulty_counts) >= 2:
                        # Calculate balance score
                        std_dev = difficulty_counts.std()
                        mean_count = difficulty_counts.mean()
                        balance_score = (1 - (std_dev / mean_count)) * 100 if mean_count > 0 else 0
                        
                        if balance_score > 80:
                            st.success(f"✅ Well balanced ({balance_score:.0f}% balance score)")
                        elif balance_score > 60:
                            st.warning(f"⚠️ Moderately balanced ({balance_score:.0f}% balance score)")
                        else:
                            st.error(f"❌ Unbalanced ({balance_score:.0f}% balance score)")
                        
                        st.caption("Balance score indicates how evenly distributed questions are across difficulty levels")
            else:
                st.info("No difficulty information available")
        
        st.markdown("---")
        
        # Question Type Analysis
        if 'Type' in df.columns:
            st.markdown("##### 📝 **Question Type Summary**")
            type_counts = df['Type'].value_counts()
            
            if not type_counts.empty:
                type_col1, type_col2 = st.columns(2)
                
                with type_col1:
                    st.markdown("**Question Types:**")
                    for qtype, count in type_counts.items():
                        if pd.notna(qtype):
                            percentage = (count / len(df)) * 100
                            # Add icons for common question types
                            if 'multiple' in qtype.lower() or 'choice' in qtype.lower():
                                st.write(f"🔘 **Multiple Choice:** {count} questions ({percentage:.1f}%)")
                            elif 'true' in qtype.lower() or 'false' in qtype.lower():
                                st.write(f"✓/✗ **True/False:** {count} questions ({percentage:.1f}%)")
                            elif 'essay' in qtype.lower() or 'open' in qtype.lower():
                                st.write(f"📝 **Essay/Open:** {count} questions ({percentage:.1f}%)")
                            elif 'fill' in qtype.lower() or 'blank' in qtype.lower():
                                st.write(f"📝 **Fill-in-blank:** {count} questions ({percentage:.1f}%)")
                            else:
                                st.write(f"❓ **{qtype}:** {count} questions ({percentage:.1f}%)")
                
                with type_col2:
                    # Question type recommendations
                    st.markdown("**Assessment Recommendations:**")
                    total = len(df)
                    mc_count = sum(count for qtype, count in type_counts.items() 
                                 if 'multiple' in str(qtype).lower() or 'choice' in str(qtype).lower())
                    
                    if mc_count / total > 0.8:
                        st.info("💡 Consider adding essay questions for deeper assessment")
                    elif mc_count / total < 0.3:
                        st.info("💡 Multiple choice questions can speed up grading")
                    else:
                        st.success("✅ Good mix of question types")
            else:
                st.info("No question type information available")
        
        st.markdown("---")
        
        # Points Analysis
        if 'Points' in df.columns:
            st.markdown("##### 🎯 **Point Distribution Analysis**")
            
            # Clean points data
            points_data = pd.to_numeric(df['Points'], errors='coerce').dropna()
            
            if not points_data.empty:
                points_col1, points_col2 = st.columns(2)
                
                with points_col1:
                    st.markdown("**Point Statistics:**")
                    st.write(f"• **Total Possible Points:** {points_data.sum()}")
                    st.write(f"• **Average Points per Question:** {points_data.mean():.1f}")
                    st.write(f"• **Point Range:** {points_data.min()} - {points_data.max()}")
                    st.write(f"• **Most Common Point Value:** {points_data.mode().iloc[0] if not points_data.mode().empty else 'N/A'}")
                
                with points_col2:
                    st.markdown("**Point Distribution:**")
                    point_counts = points_data.value_counts().sort_index()
                    for points, count in point_counts.items():
                        percentage = (count / len(points_data)) * 100
                        st.write(f"• **{points} points:** {count} questions ({percentage:.1f}%)")
                
                # Assessment planning insights
                st.markdown("**📋 Assessment Planning Insights:**")
                total_points = points_data.sum()
                avg_points = points_data.mean()
                
                if total_points > 100:
                    st.info(f"💡 High point total ({total_points}). Consider multiple assessments or scaling.")
                elif total_points < 50:
                    st.info(f"💡 Low point total ({total_points}). Good for quick assessments or quizzes.")
                else:
                    st.success(f"✅ Balanced point total ({total_points}) for standard assessment.")
                
                if avg_points > 5:
                    st.info("💡 High average points per question. Consider detailed rubrics.")
                elif avg_points < 1:
                    st.info("💡 Low average points per question. Efficient for large assessments.")
            else:
                st.info("No valid point information available")
        
        # Course Planning Summary
        st.markdown("---")
        st.markdown("##### 🎓 **Course Planning Summary**")
        
        total_questions = len(df)
        
        # Generate planning recommendations
        recommendations = []
        
        if total_questions < 20:
            recommendations.append("📝 Small question set - ideal for quizzes or focused assessments")
        elif total_questions < 100:
            recommendations.append("📚 Medium question set - good for unit tests or midterm exams")
        else:
            recommendations.append("🏛️ Large question set - suitable for comprehensive final exams or question banks")
        
        if 'Topic' in df.columns:
            topic_count = df['Topic'].nunique()
            if topic_count > 5:
                recommendations.append(f"🎯 {topic_count} topics covered - consider topic-based modules")
            elif topic_count < 3:
                recommendations.append(f"🎯 {topic_count} topics - focused content area")
        
        if 'Difficulty' in df.columns and len(df['Difficulty'].value_counts()) >= 3:
            recommendations.append("⚡ Multiple difficulty levels - supports progressive learning")
        
        for rec in recommendations:
            st.success(rec)
        
        # Export planning note
        st.info("💡 **Planning Tip:** Use this analysis to plan your course structure, assessment distribution, and student progression path.")

    # ...existing code...
