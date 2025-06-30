#!/usr/bin/env python3
"""
Q2LMS Exit Manager
Handles graceful exit functionality with data preservation options
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime

# Import AppConfig for consistent button styling
try:
    from .app_config import AppConfig
except ImportError:
    from app_config import AppConfig

class ExitManager:
    """Manages graceful exit functionality for Q2LMS"""
    
    def __init__(self):
        self.cleanup_items = []
    
    def cleanup_session_state(self):
        """Clean up session state and temporary data before exit"""
        self.cleanup_items = []
        
        # List of session state keys to clean up
        keys_to_clean = [
            'df', 'metadata', 'original_questions', 'selected_topics',
            'topic_filter_multi', 'difficulty_filter', 'type_filter',
            'uploaded_files', 'merge_conflicts', 'file_data'
        ]
        
        for key in keys_to_clean:
            if key in st.session_state:
                del st.session_state[key]
                self.cleanup_items.append(key)
        
        return self.cleanup_items
    
    def offer_data_preservation(self):
        """
        Offer user options to save their work before exiting.
        Returns True if user wants to proceed with exit, False to cancel.
        """
        st.markdown("### 💾 Save Your Work Before Exiting")
        
        # Check if there's data to save
        has_data = 'df' in st.session_state and not st.session_state['df'].empty
        
        if has_data:
            df = st.session_state['df']
            st.info(f"📊 You have {len(df)} questions loaded that will be lost on exit.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if AppConfig.create_red_button("💾 Quick Save as JSON", key="quick_save_json", button_type="primary-action"):
                    try:
                        # Create a quick export
                        export_data = {
                            "questions": st.session_state.get('original_questions', []),
                            "metadata": st.session_state.get('metadata', {}),
                            "export_timestamp": datetime.now().isoformat(),
                            "total_questions": len(df)
                        }
                        
                        # Create download
                        json_str = json.dumps(export_data, indent=2)
                        st.download_button(
                            "📥 Download JSON Backup",
                            data=json_str,
                            file_name=f"q2lms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key="download_backup"
                        )
                        st.success("✅ Backup ready for download!")
                        
                    except Exception as e:
                        st.error(f"❌ Error creating backup: {e}")
            
            with col2:
                # Show current filter status
                selected_topics = st.session_state.get('topic_filter_multi', [])
                if selected_topics:
                    st.write("**Current Filters:**")
                    st.write(f"• Topics: {len(selected_topics)} selected")
                    if len(selected_topics) < 5:
                        for topic in selected_topics:
                            st.write(f"  - {topic}")
                    else:
                        st.write(f"  - {', '.join(selected_topics[:3])}... (+{len(selected_topics)-3} more)")
        
        else:
            st.info("ℹ️ No data currently loaded - safe to exit.")
        
        return None  # No decision made yet
    
    def show_exit_interface(self):
        """Display the graceful exit interface with improved visibility"""
        
        # Force scroll to top and clear main content area
        st.markdown("""
        <script>
            window.scrollTo(0, 0);
        </script>
        """, unsafe_allow_html=True)
        
        # Clear visual space and make exit interface prominent
        st.markdown("# 🚪 Exit Q2LMS")
        st.markdown("**Safely close the application with optional data preservation.**")
        st.markdown("---")
        
        # Show current session info prominently at the top
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📊 Current Session Info")
            if 'df' in st.session_state and not st.session_state['df'].empty:
                df = st.session_state['df']
                st.success(f"**Questions Loaded:** {len(df)}")
                
                if 'metadata' in st.session_state:
                    metadata = st.session_state['metadata']
                    st.write(f"**Database:** {metadata.get('subject', 'Unknown')}")
                    st.write(f"**Format:** {metadata.get('format_version', 'Unknown')}")
                
                # Show active filters
                selected_topics = st.session_state.get('topic_filter_multi', [])
                if selected_topics:
                    filtered_count = len(df[df['Topic'].isin(selected_topics)]) if 'Topic' in df.columns else len(df)
                    st.write(f"**Filtered Questions:** {filtered_count} (from {len(selected_topics)} topics)")
            else:
                st.info("**No data currently loaded - safe to exit**")
            
            st.write(f"**Session Started:** {st.session_state.get('session_start_time', 'Unknown')}")
        
        with col2:
            # Quick return option prominently displayed
            st.markdown("### 🔙 Quick Actions")
            if AppConfig.create_red_button("🔙 Return to App", key="quick_return", use_container_width=True, button_type="secondary-action"):
                if 'show_exit_interface' in st.session_state:
                    del st.session_state['show_exit_interface']
                st.rerun()
        
        st.markdown("---")
        
        # Data preservation section
        has_data = 'df' in st.session_state and not st.session_state['df'].empty
        
        if has_data:
            st.markdown("### 💾 Save Your Work Before Exiting")
            df = st.session_state['df']
            
            # Make save option more prominent
            st.warning(f"⚠️ You have **{len(df)} questions** loaded that will be lost on exit.")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if AppConfig.create_red_button("💾 Quick Save as JSON", key="quick_save_json", use_container_width=True, button_type="primary-action"):
                    try:
                        # Create a quick export
                        export_data = {
                            "questions": st.session_state.get('original_questions', []),
                            "metadata": st.session_state.get('metadata', {}),
                            "export_timestamp": datetime.now().isoformat(),
                            "total_questions": len(df)
                        }
                        
                        # Create download
                        json_str = json.dumps(export_data, indent=2)
                        st.download_button(
                            "📥 Download JSON Backup",
                            data=json_str,
                            file_name=f"q2lms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key="download_backup",
                            use_container_width=True
                        )
                        st.success("✅ Backup ready for download!")
                        
                    except Exception as e:
                        st.error(f"❌ Error creating backup: {e}")
            
            with col2:
                # Show current filter status more clearly
                selected_topics = st.session_state.get('topic_filter_multi', [])
                if selected_topics:
                    st.markdown("**Current Filters:**")
                    st.write(f"📋 **Topics:** {len(selected_topics)} selected")
                    if len(selected_topics) <= 3:
                        for topic in selected_topics:
                            st.write(f"  • {topic}")
                    else:
                        st.write(f"  • {', '.join(selected_topics[:2])}... (+{len(selected_topics)-2} more)")
        else:
            st.success("✅ No data currently loaded - safe to exit")
        
        # Exit confirmation section - make it prominent
        st.markdown("---")
        st.markdown("### ⚠️ Confirm Exit")
        
        # Make exit/cancel buttons more prominent
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if AppConfig.create_red_button("🚪 Exit Q2LMS", key="confirm_exit", use_container_width=True, button_type="destructive-action"):
                # User confirmed exit
                st.balloons()  # Visual feedback
                st.success("👋 **Exiting Q2LMS...**")
                
                # Cleanup session
                cleaned_items = self.cleanup_session_state()
                
                if cleaned_items:
                    st.info(f"🧹 Cleaned up: {', '.join(cleaned_items[:3])}{'...' if len(cleaned_items) > 3 else ''}")
                
                # Show exit message prominently
                st.markdown("---")
                st.markdown("""
                ## ✅ Exit Complete
                
                **Thank you for using Q2LMS!**
                
                - ✅ Session data has been cleared
                - ✅ Resources have been freed  
                - ✅ Application is ready to close
                
                **To restart:** Refresh your browser or run `streamlit run streamlit_app.py`
                """)
                
                # Instructions for closing
                st.info("""
                **How to close this application:**
                - **Browser:** Close this tab or window
                - **Local/Terminal:** Press `Ctrl+C` in your command prompt
                """)
                
                # Stop the app from running further
                st.stop()
        
        with col2:
            if AppConfig.create_red_button("❌ Cancel Exit", key="cancel_exit", use_container_width=True, button_type="secondary-action"):
                # User cancelled - return to app
                if 'show_exit_interface' in st.session_state:
                    del st.session_state['show_exit_interface']
                st.success("Exit cancelled - returning to app...")
                st.rerun()
        
        with col3:
            # Show helpful tip
            st.markdown("💡 **Tip:** Use the sidebar exit button anytime")
    
    def add_exit_button_to_sidebar(self):
        """Add a prominent exit button at the very bottom of sidebar"""
        
        # This will be called at the END of sidebar content to ensure it's at bottom
        # The topic filter and other content should be rendered first
        pass  # We'll add content in a separate method
    
    def render_exit_section_at_bottom(self):
        """Render the exit section at the very bottom of the sidebar"""
        
        # Force this to bottom with spacer if needed
        st.sidebar.markdown("---")
        
        # Clear, user-friendly section title
        st.sidebar.markdown("### 🚪 Exit Application")
        
        # Add helpful description
        st.sidebar.markdown("**Safe exit** with option to save your work")
        
        # Make the exit button prominent and red
        exit_button_style = """
        <style>
        div[data-testid="stSidebar"] .element-container:last-child .stButton > button {
            background: linear-gradient(135deg, #dc3545, #c82333) !important;
            color: white !important;
            font-weight: bold !important;
            border: 2px solid #bd2130 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3) !important;
            width: 100% !important;
        }
        div[data-testid="stSidebar"] .element-container:last-child .stButton > button:hover {
            background: linear-gradient(135deg, #c82333, #bd2130) !important;
            box-shadow: 0 4px 8px rgba(220, 53, 69, 0.4) !important;
            transform: translateY(-1px) !important;
        }
        </style>
        """
        st.sidebar.markdown(exit_button_style, unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 Exit Q2LMS", 
                            key="bottom_exit_button", 
                            help="Safely exit with option to save your current work",
                            use_container_width=True):
            st.session_state['show_exit_interface'] = True
            st.session_state['exit_message'] = "Preparing exit interface..."
            st.rerun()
        
        # Add helpful tip at very bottom
        st.sidebar.caption("💡 Your work will be preserved if you choose to save it")
    
    def check_for_exit_request(self):
        """Check if exit interface should be shown and handle it"""
        
        if st.session_state.get('show_exit_interface', False):
            self.show_exit_interface()
            return True  # Exit interface is being shown
        return False  # Continue with normal app flow

# Global instance
_exit_manager = None

def get_exit_manager():
    """Get the global exit manager instance"""
    global _exit_manager
    if _exit_manager is None:
        _exit_manager = ExitManager()
    return _exit_manager