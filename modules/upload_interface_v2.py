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

class ProcessingState(Enum):
    """Clear states for the upload workflow"""
    WAITING_FOR_FILES = auto()
    FILES_READY = auto()
    PROCESSING = auto()
    PREVIEW_READY = auto()
    DATABASE_LOADED = auto()      # Renamed from COMPLETED
    SELECTING_QUESTIONS = auto()  # New: covers select/delete modes
    EXPORTING = auto()            # New
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
    
    def _initialize_session_state(self):
        """Initialize session state with clear workflow states"""
        if 'upload_state' not in st.session_state:
            st.session_state.upload_state = {
                'current_state': ProcessingState.WAITING_FOR_FILES,
                'uploaded_files': None,
                'preview_data': None,
                'error_message': None,
                'final_database': None
            }
        else:
            # Ensure it's the correct structure
            if not isinstance(st.session_state.upload_state, dict):
                st.session_state.upload_state = {
                    'current_state': ProcessingState.WAITING_FOR_FILES,
                    'uploaded_files': None,
                    'preview_data': None,
                    'error_message': None,
                    'final_database': None
                }
    
    def _get_current_state(self) -> ProcessingState:
        """Get current processing state"""
        upload_state = st.session_state.get('upload_state', {})
        if isinstance(upload_state, dict):
            return upload_state.get('current_state', ProcessingState.WAITING_FOR_FILES)
        return ProcessingState.WAITING_FOR_FILES
    
    def _set_state(self, new_state: ProcessingState, **kwargs):
        """Update the current state and any additional data"""
        if 'upload_state' not in st.session_state:
            st.session_state.upload_state = {}
        
        st.session_state.upload_state['current_state'] = new_state
        
        # Update any additional data
        for key, value in kwargs.items():
            st.session_state.upload_state[key] = value
    
    def _render_progress_indicator(self, current_state: ProcessingState):
        """Show clear progress through the workflow in the sidebar"""
        with st.sidebar:
            st.markdown("### 🔄 Workflow Progress")
            stages = [
                (ProcessingState.WAITING_FOR_FILES, "📁 Upload Files"),
                (ProcessingState.FILES_READY, "🔄 Process Files"),
                (ProcessingState.PREVIEW_READY, "📊 Review & Load"),
                (ProcessingState.SELECTING_QUESTIONS, "📝 Select Questions"),
                (ProcessingState.EXPORTING, "📥 Export"),
                (ProcessingState.FINISHED, "✅ Complete")
            ]
            current_index = None
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
        self._render_progress_indicator(current_state)
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
            if st.button("🚀 Process Files", type="primary", use_container_width=True):
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
        
        if st.button(button_text, type="primary", use_container_width=True):
            with st.spinner("Loading database..."):
                try:
                    self._execute_merge(preview_data)
                    self._set_state(ProcessingState.COMPLETED)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Loading failed: {e}")
    
    def _render_completed_state(self):
        """State 5: Process completed successfully"""
        st.header("✅ Database Loaded Successfully!")
        
        upload_state = st.session_state.get('upload_state', {})
        preview_data = upload_state.get('preview_data')
        
        if preview_data:
            st.success(f"🎉 **{preview_data.total_questions} questions** loaded and ready to use!")
        
        # Show what user can do next
        st.info("""
        **🎯 What's Next?**
        - Browse and edit questions in the tabs above
        - Use topic filtering in the sidebar
        - Export to various formats when ready
        """)
        
        # Option to load another database
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📁 Load Another Database", use_container_width=True):
                self._reset_state()
                st.rerun()
        
        with col2:
            if st.button("📊 View Database Overview", use_container_width=True):
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
            self._set_state(
                ProcessingState.COMPLETED,
                final_database=all_merged_questions,
                error_message=None
            )
            
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
            'current_state': ProcessingState.WAITING_FOR_FILES,
            'uploaded_files': None,
            'preview_data': None,
            'error_message': None,
            'final_database': None
        }
        
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

# Usage in your main app remains the same
def main():
    interface = UploadInterfaceV2()
    interface.render_complete_interface()

if __name__ == "__main__":
    main()
