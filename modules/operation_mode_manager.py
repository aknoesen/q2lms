# modules/operation_mode_manager.py
"""
Operation Mode Manager - Handles the fork decision between Select and Delete modes
Coordinates the user's choice of operation mode and manages the transition between modes
"""

import streamlit as st
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime

# Import AppConfig for consistent button styling
try:
    from .app_config import AppConfig
except ImportError:
    from app_config import AppConfig

class OperationModeManager:
    """
    Manages the fork decision point between Select Questions and Delete Questions modes.
    Handles mode selection, initialization, and coordination with other components.
    """
    
    def __init__(self):
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for operation mode management"""
        if 'operation_mode' not in st.session_state:
            st.session_state.operation_mode = None
        
        if 'mode_initialized' not in st.session_state:
            st.session_state.mode_initialized = False
        
        if 'mode_selection_timestamp' not in st.session_state:
            st.session_state.mode_selection_timestamp = None
    
    def has_mode_been_chosen(self) -> bool:
        """
        Check if user has chosen an operation mode
        
        Returns:
            bool: True if mode has been chosen, False otherwise
        """
        return (st.session_state.operation_mode is not None and 
                st.session_state.operation_mode in ['select', 'delete'])
    
    def get_current_mode(self) -> Optional[str]:
        """
        Get the currently selected operation mode
        
        Returns:
            Optional[str]: 'select', 'delete', or None if no mode chosen
        """
        return st.session_state.operation_mode
    
    def reset_mode(self):
        """
        Reset the operation mode and return to fork decision
        Clears all mode-related session state
        """
        st.session_state.operation_mode = None
        st.session_state.mode_initialized = False
        st.session_state.mode_selection_timestamp = None
        
        # Clear any existing flags from DataFrame if present
        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            # Remove flag columns if they exist
            flag_columns = ['selected', 'deleted', 'flag_selected', 'flag_deleted']
            for col in flag_columns:
                if col in df.columns:
                    st.session_state.df = df.drop(columns=[col])
        
        st.success("🔄 Mode reset - you can now choose a different operation mode")
    
    def set_mode(self, mode: str):
        """
        Set the operation mode programmatically
        
        Args:
            mode (str): 'select' or 'delete'
        """
        if mode in ['select', 'delete']:
            st.session_state.operation_mode = mode
            st.session_state.mode_selection_timestamp = datetime.now().isoformat()
            st.session_state.mode_initialized = False  # Will be set to True when flags are initialized
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'select' or 'delete'")
    
    def render_mode_selection(self) -> None:
        """
        Render the fork decision UI for choosing between Select and Delete modes
        This is the main decision point after successful file upload
        """

        
        # Database summary section - show this FIRST, right after the header
        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            total_questions = len(df)
            
            # Database summary with metrics
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown("### 📊 Current Database")
                
                if 'metadata' in st.session_state:
                    metadata = st.session_state.metadata
                    if 'source' in metadata:
                        st.write(f"**Source:** {metadata.get('source', 'Unknown')}")
                
                # Show topic breakdown if available
                if 'Topic' in df.columns:
                    unique_topics = df['Topic'].nunique()
                    st.write(f"**Topics:** {unique_topics} different topics")
            
            with col2:
                if 'Points' in df.columns:
                    total_points = df['Points'].sum()
                    st.metric("Total Points", f"{int(total_points)}")
                else:
                    st.metric("Questions", total_questions)
            
            with col3:
                if 'Type' in df.columns:
                    question_types = df['Type'].nunique()
                    st.metric("Question Types", question_types)
        
        st.markdown("---")
        
        # Mode selection section - same font size as main header
        st.markdown("# 🛤️ Choose Your Path")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Clean Select Questions section - NO colored boxes
            st.markdown("### 🎯 Select Questions")
            st.markdown("""
            **Purpose:** Choose specific questions to export
            
            **How it works:**
            - ✅ Check questions you want to include
            - 📝 Edit questions as needed
            - 📤 Export only the selected questions
            
            **Best for:**
            - Building targeted quizzes/exams
            - Creating topic-specific assessments
            - Curating question sets
            """)
            
            if AppConfig.create_red_button("🎯 Choose Select Mode", 
                        key="select_mode_btn",
                        use_container_width=True,
                        button_type="primary-action",
                        help="Flag questions you want to INCLUDE in export"):
                self._handle_mode_selection('select')
        
        with col2:
            # Clean Delete Questions section - NO colored boxes
            st.markdown("### 🗑️ Delete Questions")
            st.markdown("""
            **Purpose:** Remove unwanted questions from export
            
            **How it works:**
            - ❌ Mark questions you want to remove
            - 📝 Edit remaining questions as needed  
            - 📤 Export everything that wasn't deleted
            
            **Best for:**
            - Cleaning up question banks
            - Removing outdated questions
            - Filtering large databases
            """)
            
            if AppConfig.create_red_button("🗑️ Choose Delete Mode", 
                        key="delete_mode_btn",
                        use_container_width=True,
                        button_type="destructive-action",
                        help="Flag questions you want to EXCLUDE from export"):
                self._handle_mode_selection('delete')
        
        # Help section at the bottom
        with st.expander("ℹ️ Need Help Choosing?"):
            st.markdown("""
            **Choose Select Mode if:**
            - You want to build a quiz from specific questions
            - You're working with a large database and need just a few questions
            - You want to create themed assessments (e.g., "Chapter 3 Quiz")
            
            **Choose Delete Mode if:**
            - You want to clean up an existing question bank
            - You need to remove outdated or incorrect questions
            - You're starting with mostly good questions but need to remove some
            
            **Remember:** Both modes let you edit questions and export in all formats (CSV, QTI, JSON)
            """)
    
    def _handle_mode_selection(self, mode: str):
        """
        Handle the user's mode selection
        
        Args:
            mode (str): 'select' or 'delete'
        """
        try:
            self.set_mode(mode)
            
            # Show confirmation
            mode_display = "Select Questions" if mode == 'select' else "Delete Questions"
            st.success(f"✅ **{mode_display} Mode** selected!")
            
            # Initialize flags for the selected mode
            if self.initialize_question_flags():
                st.success("🏷️ Question flags initialized successfully")
            
            # Brief pause for user to see confirmation, then rerun
            st.info("🔄 Loading interface...")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error setting mode: {e}")
    
    def initialize_question_flags(self) -> bool:
        """
        Initialize flag columns in the DataFrame based on the selected mode
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if 'df' not in st.session_state or st.session_state.df is None:
                st.error("❌ No DataFrame available for flag initialization")
                return False
            
            df = st.session_state.df
            current_mode = self.get_current_mode()
            
            if current_mode == 'select':
                # Add 'selected' column, default to False (nothing selected initially)
                if 'selected' not in df.columns:
                    st.session_state.df['selected'] = False
                    
            elif current_mode == 'delete':
                # Add 'deleted' column, default to False (nothing deleted initially)
                if 'deleted' not in df.columns:
                    st.session_state.df['deleted'] = False
            
            else:
                st.error(f"❌ Cannot initialize flags for unknown mode: {current_mode}")
                return False
            
            # Mark as initialized
            st.session_state.mode_initialized = True
            return True
            
        except Exception as e:
            st.error(f"❌ Error initializing question flags: {e}")
            return False
    
    def get_mode_display_info(self) -> Tuple[str, str, str]:
        """
        Get display information for the current mode
        
        Returns:
            Tuple[str, str, str]: (mode_name, icon, description)
        """
        current_mode = self.get_current_mode()
        
        if current_mode == 'select':
            return ("Select Questions", "🎯", "Choose questions to include in export")
        elif current_mode == 'delete':
            return ("Delete Questions", "🗑️", "Mark questions to exclude from export")
        else:
            return ("No Mode Selected", "❓", "Choose an operation mode first")
    
    def render_mode_status(self):
        """
        Render current mode status in sidebar or main area
        Shows which mode is active and provides option to change
        """
        if not self.has_mode_been_chosen():
            return
        
        mode_name, icon, description = self.get_mode_display_info()
        
        # Show current mode
        st.markdown(f"### {icon} Current Mode: {mode_name}")
        st.caption(description)
        
        # Show selection timestamp if available
        if st.session_state.mode_selection_timestamp:
            timestamp = st.session_state.mode_selection_timestamp
            st.caption(f"Mode selected: {timestamp}")
        
        # Option to change mode
        if AppConfig.create_red_button("🔄 Change Mode", 
                    key="change_mode_btn",
                    button_type="secondary-action",
                    help="Return to mode selection screen"):
            self.reset_mode()
            st.rerun()
    
    def is_mode_initialized(self) -> bool:
        """
        Check if the current mode has been properly initialized
        
        Returns:
            bool: True if mode is initialized, False otherwise
        """
        return (self.has_mode_been_chosen() and 
                st.session_state.mode_initialized and
                'df' in st.session_state and
                st.session_state.df is not None)
    
    def get_flag_column_name(self) -> Optional[str]:
        """
        Get the appropriate flag column name for the current mode
        
        Returns:
            Optional[str]: 'selected' for select mode, 'deleted' for delete mode, None if no mode
        """
        current_mode = self.get_current_mode()
        
        if current_mode == 'select':
            return 'selected'
        elif current_mode == 'delete':
            return 'deleted'
        else:
            return None


# Convenience functions for easy integration
def get_operation_mode_manager() -> OperationModeManager:
    """
    Get a configured OperationModeManager instance
    
    Returns:
        OperationModeManager: Configured instance
    """
    return OperationModeManager()


def has_mode_been_chosen() -> bool:
    """
    Quick check if operation mode has been chosen
    
    Returns:
        bool: True if mode chosen, False otherwise
    """
    manager = OperationModeManager()
    return manager.has_mode_been_chosen()


def get_current_mode() -> Optional[str]:
    """
    Quick get current operation mode
    
    Returns:
        Optional[str]: Current mode or None
    """
    manager = OperationModeManager()
    return manager.get_current_mode()


# Example usage and testing
if __name__ == "__main__":
    # This code runs when the module is executed directly
    # Useful for testing the module independently
    
    st.title("Operation Mode Manager Test")
    
    manager = OperationModeManager()
    
    # Test the mode selection interface
    if not manager.has_mode_been_chosen():
        manager.render_mode_selection()
    else:
        # Show current mode status
        manager.render_mode_status()
        
        # Show some debug info
        with st.expander("Debug Info"):
            st.write(f"Current mode: {manager.get_current_mode()}")
            st.write(f"Mode initialized: {manager.is_mode_initialized()}")
            st.write(f"Flag column: {manager.get_flag_column_name()}")
            
            if 'df' in st.session_state:
                st.write(f"DataFrame columns: {list(st.session_state.df.columns)}")
