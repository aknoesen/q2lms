# upload_interface_v2.py - Clean Production Version with Output Management
import streamlit as st
import json
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import contextlib
import io
import sys

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
    """Simplified upload interface with clear state management and clean output"""
    
    def __init__(self):
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state with clear defaults"""
        # Only initialize if completely missing - don't reset existing state
        if 'upload_state' not in st.session_state:
            st.session_state.upload_state = {
                'files_uploaded': False,
                'preview_generated': False,
                'merge_completed': False,
                'current_preview': None,
                'error_message': None,
                'final_database': None
            }
        else:
            # If upload_state exists but isn't a dict (could be an enum), force it to dict
            if not isinstance(st.session_state.upload_state, dict):
                st.session_state.upload_state = {
                    'files_uploaded': False,
                    'preview_generated': False,
                    'merge_completed': False,
                    'current_preview': None,
                    'error_message': None,
                    'final_database': None
                }
    
    @contextlib.contextmanager
    def _clean_operation(self, operation_name: str):
        """Context manager for clean operations without verbose output"""
        # Create progress placeholder
        progress_placeholder = st.empty()
        progress_placeholder.info(f"🔄 **{operation_name}...**")
        
        # Capture stdout to prevent verbose logging
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            # Redirect output during processing
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer
            
            yield progress_placeholder
            
            # Success message
            progress_placeholder.success(f"✅ **{operation_name} completed successfully**")
            
        except Exception as e:
            progress_placeholder.error(f"❌ **{operation_name} failed:** {str(e)}")
            
            # Show captured output only on error for debugging
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
            # Always restore original stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def render_upload_section(self):
        """Render file upload with immediate processing - no redundant title"""
        
        uploaded_files = st.file_uploader(
            "Select files to merge (1 or more files)",
            accept_multiple_files=True,
            type=['json', 'csv', 'xlsx'],
            key="file_uploader"
        )
        
        if uploaded_files and len(uploaded_files) >= 1:
            if len(uploaded_files) == 1:
                st.info("📄 Single file selected - will load directly without merging")
            else:
                st.info(f"📁 {len(uploaded_files)} files selected - will merge with conflict resolution")
            
            if st.button("Process Files", type="primary"):
                self._process_uploaded_files(uploaded_files)
    
    def _process_uploaded_files(self, files) -> None:
        """Process uploaded files and generate preview data with clean output"""
        try:
            with self._clean_operation("Processing files and generating preview"):
                # Step 1: Load and validate files
                file_data = self._load_files(files)
                
                # Step 2: Create merge preview with auto-renumbering (this is where the verbose output was)
                preview_data = self._create_clean_preview(file_data)
                
                # Step 3: Store in session state
                st.session_state.upload_state = {
                    'files_uploaded': True,
                    'preview_generated': True,
                    'current_preview': preview_data,
                    'error_message': None,
                    'merge_completed': False,
                    'final_database': None
                }
                
        except Exception as e:
            upload_state = st.session_state.get('upload_state', {})
            if isinstance(upload_state, dict):
                upload_state['error_message'] = str(e)
                st.session_state.upload_state = upload_state
    
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
                # Handle different JSON structures
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
        """Create merge preview with clean data structure - NO VERBOSE OUTPUT"""
        all_questions = []
        conflicts = []
        seen_ids = set()
        renumbered_count = 0
        
        # Handle single file vs multiple files
        if len(file_data) == 1:
            # Single file - just load questions without conflict checking
            all_questions = file_data[0]['questions']
            conflicts = []
            renumbered_count = 0
        else:
            # Multiple files - merge with conflict resolution
            # THIS IS WHERE THE VERBOSE OUTPUT WAS COMING FROM
            for file_info in file_data:
                for question in file_info['questions']:
                    q_id = question.get('id', question.get('ID', ''))
                    
                    # Check for ID conflicts and auto-renumber
                    if q_id in seen_ids:
                        # Find new ID
                        original_id = q_id
                        counter = 1
                        while f"{q_id}_{counter}" in seen_ids:
                            counter += 1
                        new_id = f"{q_id}_{counter}"
                        question['id'] = new_id
                        renumbered_count += 1
                        # REMOVED: The print/st.write that was causing verbose output
                        conflicts.append({
                            'id': original_id,
                            'description': f"ID {original_id} renamed to {new_id}"
                        })
                    
                    seen_ids.add(question.get('id', q_id))
                    all_questions.append(question)
        
        # Store ALL questions in the preview object
        preview_data = MergePreviewData(
            total_questions=len(all_questions),
            conflicts=conflicts,
            conflict_count=len(conflicts),
            renumbered_count=renumbered_count,
            preview_questions=all_questions[:10],  # First 10 for display
            merge_ready=True  # Always ready
        )
        
        # Store ALL merged questions for later use
        preview_data.all_merged_questions = all_questions
        
        return preview_data
    
    def render_preview_section(self):
        """Render merge preview if data is available"""
        upload_state = st.session_state.get('upload_state', {})
        
        # Check if it's a dictionary and has the data we need
        if not isinstance(upload_state, dict):
            st.info("Upload files above to see results")
            return
        
        if upload_state.get('error_message'):
            st.error(upload_state['error_message'])
            return
        
        if not upload_state.get('preview_generated') or not upload_state.get('current_preview'):
            st.info("Upload files above to see results")
            return
        
        preview = upload_state.get('current_preview')
        if not preview:
            st.info("Upload files above to see results")
            return
        
        # Display preview summary with clean styling
        st.header("🔍 File Processing Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions", preview.total_questions)
        with col2:
            st.metric("Conflicts", preview.conflict_count)
        with col3:
            st.metric("Auto-Renumbered", preview.renumbered_count)
        
        # Show conflicts summary in a clean, condensed format
        if preview.conflict_count == 0 and preview.renumbered_count == 0:
            st.success("✅ **File processed successfully - ready to load!**")
        elif preview.conflicts:
            # CLEAN CONFLICT DISPLAY - No verbose list
            st.warning(f"⚠️ **Conflicts detected and resolved:** {preview.conflict_count} questions auto-renumbered")
            
            # Optional: Show conflicts in a collapsible section instead of main interface
            if st.checkbox("📋 Show conflict details", key="show_conflicts"):
                with st.expander("Conflict Resolution Details", expanded=True):
                    for conflict in preview.conflicts:
                        st.caption(f"• {conflict['description']}")
        else:
            st.success("✅ **No conflicts detected - ready to merge!**")
        
        # Preview questions
        with st.expander("Preview First 10 Questions"):
            for i, q in enumerate(preview.preview_questions, 1):
                question_text = q.get('question_text', q.get('question', q.get('Question', 'No question text')))
                question_id = q.get('id', q.get('ID', 'N/A'))
                st.write(f"{i}. ID {question_id}: {question_text[:100]}...")
        
        # Load/Merge action
        if preview.merge_ready:
            button_text = "Load Database" if preview.conflict_count == 0 else "Complete Merge"
            if st.button(button_text, type="primary", key="complete_merge"):
                self._execute_merge(preview)
    
    def _execute_merge(self, preview: MergePreviewData):
        """Execute the final merge operation with clean output"""
        try:
            with self._clean_operation("Completing merge and loading database"):
                upload_state = st.session_state.get('upload_state', {})
                
                if isinstance(upload_state, dict) and 'current_preview' in upload_state:
                    # Get the preview object which contains our merged questions
                    preview_obj = upload_state['current_preview']
                    
                    # Use ALL merged questions
                    if hasattr(preview_obj, 'all_merged_questions'):
                        all_merged_questions = preview_obj.all_merged_questions
                    else:
                        # Fallback to preview questions if all_merged_questions not available
                        all_merged_questions = preview_obj.preview_questions
                    
                    # Update upload state
                    new_upload_state = {
                        'files_uploaded': True,
                        'preview_generated': True,
                        'merge_completed': True,
                        'current_preview': preview_obj,
                        'final_database': all_merged_questions,
                        'error_message': None
                    }
                    
                    st.session_state.upload_state = new_upload_state
                    
                    # Transfer to main app session state
                    df_data = []
                    for q in all_merged_questions:
                        # Handle choices - convert array to individual choice columns
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
                            # Basic question info
                            'ID': q.get('id', ''),
                            'Title': q.get('title', ''),
                            'Type': q.get('type', 'multiple_choice'),
                            'Question_Text': q.get('question_text', ''),
                            'Topic': q.get('topic', ''),
                            'Subtopic': q.get('subtopic', ''),
                            'Difficulty': q.get('difficulty', 'Medium'),
                            'Points': q.get('points', 1),
                            
                            # Answer and tolerance
                            'Correct_Answer': q.get('correct_answer', 'A'),
                            'Tolerance': q.get('tolerance', 0.05),
                            
                            # Individual choice columns (what your editor expects)
                            'Choice_A': choice_a,
                            'Choice_B': choice_b,
                            'Choice_C': choice_c,
                            'Choice_D': choice_d,
                            'Choice_E': choice_e,
                            
                            # Feedback columns (multiple naming conventions)
                            'Correct_Feedback': q.get('feedback_correct', ''),
                            'Incorrect_Feedback': q.get('feedback_incorrect', ''),
                            'Feedback_Correct': q.get('feedback_correct', ''),
                            'Feedback_Incorrect': q.get('feedback_incorrect', ''),
                            
                            # Image handling
                            'Image_File': image_file_str,
                            'Image_Files': image_files,
                            
                            # Keep original structure for compatibility
                            'Choices': choices,
                            
                            # Additional common column names that might be expected
                            'Question': q.get('question_text', ''),  # Alternative name
                            'Answer': q.get('correct_answer', 'A'),   # Alternative name
                            'Explanation': q.get('feedback_correct', ''),  # Some systems use this
                            'Category': q.get('topic', ''),           # Alternative name
                            'Level': q.get('difficulty', 'Medium'),  # Alternative name
                        })
                    
                    # Set main app session state
                    st.session_state['df'] = pd.DataFrame(df_data)
                    st.session_state['original_questions'] = all_merged_questions
                    st.session_state['metadata'] = {
                        'source': 'merged_database',
                        'total_questions': len(all_merged_questions),
                        'conflicts_resolved': preview.conflict_count
                    }
                
                # Show clean success message
                st.success(f"✅ **Database loaded successfully!** {preview.total_questions} questions ready.")
                st.balloons()
                
                # Force a rerun to trigger the main app detection and fork decision
                st.rerun()
                
        except Exception as e:
            st.error(f"Error completing merge: {e}")
    
    def render_results_section(self):
        """Render final results if merge is completed"""
        upload_state = st.session_state.get('upload_state', {})
        
        if isinstance(upload_state, dict) and upload_state.get('merge_completed'):
            st.header("✅ Merge Complete")
            st.success("Your question database has been successfully merged!")
            
            # Download button for merged database
            if 'final_database' in upload_state:
                st.download_button(
                    label="Download Merged Database",
                    data=self._serialize_database(upload_state['final_database']),
                    file_name="merged_questions.json",
                    mime="application/json"
                )
            
            # Reset button
            if st.button("Start New Merge"):
                self._reset_state()
                st.rerun()
    
    def _serialize_database(self, database):
        """Convert database to downloadable JSON format"""
        return json.dumps({
            "questions": database,
            "metadata": {
                "source": "merged_database",
                "total_questions": len(database),
                "format_version": "Phase Four"
            }
        }, indent=2)
    
    def _reset_state(self):
        """Reset all session state for new merge"""
        st.session_state.upload_state = {
            'files_uploaded': False,
            'preview_generated': False,
            'merge_completed': False,
            'current_preview': None,
            'error_message': None,
            'final_database': None
        }
    
    def render_complete_interface(self):
        """Render the complete upload interface with clean output"""
        st.title("Question Database Merger")
        
        # Main workflow sections
        self.render_upload_section()
        st.divider()
        self.render_preview_section()
        st.divider()
        self.render_results_section()
        
        # Debug section (optional, hidden by default)
        if st.checkbox("Show Debug Info", value=False):
            upload_state = st.session_state.get('upload_state', {})
            st.json(upload_state if isinstance(upload_state, dict) else str(upload_state))

# Usage in your main app
def main():
    interface = UploadInterfaceV2()
    interface.render_complete_interface()

if __name__ == "__main__":
    main()