#!/usr/bin/env python3
"""
Q2LMS Output Manager
Handles clean output and suppresses verbose debugging information
"""

import streamlit as st
import contextlib
import io
import sys
from typing import Generator, Any

class OutputManager:
    """Manages clean output for Q2LMS operations"""
    
    def __init__(self):
        self.suppressed_outputs = []
    
    @contextlib.contextmanager
    def suppress_verbose_output(self, operation_name: str = "operation") -> Generator[None, None, None]:
        """
        Context manager to suppress verbose output during operations like merging.
        Shows a clean progress indicator instead of raw output.
        """
        # Create string buffers to capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            # Show clean progress indicator
            with st.spinner(f"🔄 Processing {operation_name}..."):
                # Redirect output to buffers
                sys.stdout = stdout_buffer
                sys.stderr = stderr_buffer
                
                yield
                
        except Exception as e:
            # If there's an error, we want to show it
            st.error(f"❌ Error during {operation_name}: {str(e)}")
            
            # Show captured output if there was an error (for debugging)
            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()
            
            if stdout_content.strip() or stderr_content.strip():
                with st.expander(f"🔍 Debug Output for {operation_name}", expanded=False):
                    if stdout_content.strip():
                        st.text("Standard Output:")
                        st.code(stdout_content, language="text")
                    if stderr_content.strip():
                        st.text("Error Output:")
                        st.code(stderr_content, language="text")
            
            raise  # Re-raise the exception
            
        finally:
            # Always restore original stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Store suppressed output for potential debugging
            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()
            
            if stdout_content.strip() or stderr_content.strip():
                self.suppressed_outputs.append({
                    'operation': operation_name,
                    'stdout': stdout_content,
                    'stderr': stderr_content,
                    'timestamp': st.session_state.get('session_start_time', 'unknown')
                })
    
    @contextlib.contextmanager 
    def clean_merge_operation(self) -> Generator[None, None, None]:
        """Specifically handle merge operations with clean output"""
        
        # Show clean progress for merge
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 **Merging question databases...**")
        
        try:
            with self.suppress_verbose_output("question database merge"):
                yield
            
            # Success message
            progress_placeholder.success("✅ **Questions merged successfully!**")
            
        except Exception as e:
            progress_placeholder.error(f"❌ **Merge failed:** {str(e)}")
            raise
    
    @contextlib.contextmanager
    def clean_renumbering_operation(self) -> Generator[None, None, None]:
        """Handle question renumbering with clean output"""
        
        progress_placeholder = st.empty()
        progress_placeholder.info("🔢 **Renumbering questions for consistency...**")
        
        try:
            with self.suppress_verbose_output("question renumbering"):
                yield
            
            # Success - brief and clean
            progress_placeholder.success("✅ **Questions renumbered successfully**")
            
        except Exception as e:
            progress_placeholder.error(f"❌ **Renumbering failed:** {str(e)}")
            raise
    
    def show_suppressed_output_debug(self):
        """Show suppressed output for debugging purposes (admin feature)"""
        
        if not self.suppressed_outputs:
            st.info("No suppressed output to display")
            return
        
        st.markdown("### 🔍 Suppressed Output Log")
        st.caption("This is debug information that was hidden from the main interface")
        
        for i, output in enumerate(self.suppressed_outputs):
            with st.expander(f"Operation {i+1}: {output['operation']} (Session: {output['timestamp']})", expanded=False):
                if output['stdout'].strip():
                    st.text("Standard Output:")
                    st.code(output['stdout'], language="text")
                if output['stderr'].strip():
                    st.text("Error Output:")  
                    st.code(output['stderr'], language="text")
    
    def clear_suppressed_output_log(self):
        """Clear the suppressed output log"""
        self.suppressed_outputs.clear()
        st.success("🧹 Suppressed output log cleared")
    
    def get_clean_success_message(self, operation: str, details: dict = None) -> str:
        """Generate clean, instructor-friendly success messages"""
        
        messages = {
            'upload': "✅ **Questions uploaded successfully!**",
            'merge': "✅ **Question databases merged successfully!**", 
            'renumber': "✅ **Questions renumbered for consistency**",
            'export': "✅ **Export package created successfully!**",
            'save': "✅ **Changes saved successfully!**",
            'delete': "✅ **Questions deleted successfully!**"
        }
        
        base_message = messages.get(operation, f"✅ **{operation.title()} completed successfully!**")
        
        if details:
            if 'count' in details:
                base_message += f" ({details['count']} questions)"
            if 'format' in details:
                base_message += f" Format: {details['format']}"
        
        return base_message
    
    def show_clean_operation_summary(self, operation: str, results: dict):
        """Show a clean summary of operation results"""
        
        if operation == "merge":
            st.info(f"📊 **Merge Summary:** {results.get('total_questions', 0)} questions from {results.get('file_count', 0)} files")
            
            if results.get('conflicts_resolved', 0) > 0:
                st.info(f"🔧 **Conflicts Resolved:** {results['conflicts_resolved']} duplicate questions handled")
                
        elif operation == "upload":
            st.info(f"📁 **Upload Summary:** {results.get('question_count', 0)} questions loaded")
            
            if results.get('format'):
                st.info(f"📋 **Format:** {results['format']}")

# Global instance
_output_manager = None

def get_output_manager():
    """Get the global output manager instance"""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager

# Convenience functions for common operations
def with_clean_merge():
    """Decorator/context manager for clean merge operations"""
    return get_output_manager().clean_merge_operation()

def with_clean_renumbering():
    """Decorator/context manager for clean renumbering operations"""
    return get_output_manager().clean_renumbering_operation()

def suppress_verbose(operation_name: str = "operation"):
    """Decorator/context manager for suppressing verbose output"""
    return get_output_manager().suppress_verbose_output(operation_name)