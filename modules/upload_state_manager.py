# modules/upload_state_manager.py
"""
Upload State Manager Module
Handles state transitions and management for the upload interface system.

Part of the systematic upload interface rebuild for question database manager.
Integrates with existing session_manager.py and new file_processor_module.py.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UploadState(Enum):
    """Upload state definitions for the interface system."""
    NO_DATABASE = "no_database"
    DATABASE_LOADED = "database_loaded"
    PROCESSING_FILES = "processing_files"
    PREVIEW_MERGE = "preview_merge"
    ERROR_STATE = "error_state"
    SUCCESS_STATE = "success_state"


@dataclass
class StateTransition:
    """Represents a state transition with metadata."""
    from_state: UploadState
    to_state: UploadState
    action: str
    timestamp: datetime
    user_data: Dict[str, Any] = None


class UploadStateManager:
    """
    Manages upload state transitions and session state integration.
    
    Core responsibilities:
    - Determine current upload state
    - Handle valid state transitions
    - Maintain state consistency with session
    - Provide state-specific available actions
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS = {
        UploadState.NO_DATABASE: [
            UploadState.PROCESSING_FILES,
            UploadState.ERROR_STATE
        ],
        UploadState.DATABASE_LOADED: [
            UploadState.PROCESSING_FILES,
            UploadState.PREVIEW_MERGE,      # Add this line - enables append operations
            UploadState.NO_DATABASE,
            UploadState.SUCCESS_STATE,  # Add this line
        UploadState.ERROR_STATE
        ],
        UploadState.PROCESSING_FILES: [
            UploadState.DATABASE_LOADED,
            UploadState.PREVIEW_MERGE,
            UploadState.SUCCESS_STATE,
            UploadState.ERROR_STATE
        ],
        UploadState.PREVIEW_MERGE: [
            UploadState.DATABASE_LOADED,
            UploadState.PROCESSING_FILES,
            UploadState.SUCCESS_STATE,
            UploadState.ERROR_STATE
        ],
        UploadState.ERROR_STATE: [
            UploadState.NO_DATABASE,
            UploadState.DATABASE_LOADED,
            UploadState.PROCESSING_FILES,
            UploadState.PREVIEW_MERGE
        ],
        UploadState.SUCCESS_STATE: [
            UploadState.DATABASE_LOADED,
            UploadState.NO_DATABASE
        ]
    }
    
    # Define state-specific available actions
    STATE_ACTIONS = {
        UploadState.NO_DATABASE: [
            "upload_single_file",
            "upload_multiple_files"
        ],
        UploadState.DATABASE_LOADED: [
            "replace_database",
            "append_questions",
            "clear_database",
            "export_database",
            "edit_questions"
        ],
        UploadState.PROCESSING_FILES: [
            "cancel_processing",
            "view_progress"
        ],
        UploadState.PREVIEW_MERGE: [
            "confirm_merge",
            "cancel_merge",
            "modify_options",
            "preview_changes"
        ],
        UploadState.ERROR_STATE: [
            "retry_operation",
            "cancel_operation",
            "view_error_details"
        ],
        UploadState.SUCCESS_STATE: [
            "continue_to_database",
            "upload_more_files"
        ]
    }
    
    def __init__(self):
        """Initialize the state manager."""
        self.transition_history: List[StateTransition] = []
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables if they don't exist."""
        default_state = {
            # Core upload state
            'upload_state': UploadState.NO_DATABASE,
            'upload_state_history': [],
            
            # Core database state (maintain compatibility)
            'df': None,
            'original_questions': [],
            'metadata': {},
            'current_filename': '',
            
            # Upload operation state
            'uploaded_files': [],
            'processing_results': {},
            'preview_data': {},
            'last_operation': '',
            'operation_timestamp': None,
            
            # History and rollback
            'database_history': [],
            'can_rollback': False,
            'rollback_point': None,
            
            # UI state
            'show_advanced_options': False,
            'selected_operation': None,
            'error_message': '',
            'success_message': '',
            
            # Processing state
            'processing_progress': 0.0,
            'processing_status': '',
            'files_processed': 0,
            'total_files': 0
        }
        
        # Initialize only missing keys to preserve existing state
        for key, value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def get_current_state(self) -> UploadState:
        """
        Determine current upload state based on session state.
        
        Returns:
            Current UploadState enum value
        """
        # Check if explicitly set
        if 'upload_state' in st.session_state:
            current_state = st.session_state.get('upload_state')
            if isinstance(current_state, UploadState):
                return current_state
            elif isinstance(current_state, str):
                try:
                    return UploadState(current_state)
                except ValueError:
                    logger.warning(f"Invalid upload state string: {current_state}")
        
        # Determine state from session data
        return self._infer_state_from_session()
    
    def _infer_state_from_session(self) -> UploadState:
        """
        Infer current state from session state data.
        
        Returns:
            Inferred UploadState based on session data
        """
        # Check for error state
        if st.session_state.get('error_message'):
            return UploadState.ERROR_STATE
        
        # Check for success state
        if st.session_state.get('success_message'):
            return UploadState.SUCCESS_STATE
        
        # Check for processing state
        if (st.session_state.get('processing_results') and 
            st.session_state.get('last_operation') == 'processing'):
            return UploadState.PROCESSING_FILES
        
        # Check for preview state
        if st.session_state.get('preview_data'):
            return UploadState.PREVIEW_MERGE
        
        # Check for database loaded state
        if (st.session_state.get('df') is not None and 
            not st.session_state.get('df').empty):
            return UploadState.DATABASE_LOADED
        
        # Default to no database
        return UploadState.NO_DATABASE
    
    def can_transition(self, from_state: UploadState, to_state: UploadState) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            from_state: Current state
            to_state: Desired state
            
        Returns:
            True if transition is valid, False otherwise
        """
        return to_state in self.VALID_TRANSITIONS.get(from_state, [])
    
    def transition_to_state(self, new_state: UploadState, action: str = "", 
                           user_data: Dict[str, Any] = None) -> bool:
        """
        Transition to a new state if valid.
        
        Args:
            new_state: Target state to transition to
            action: Action that triggered the transition
            user_data: Additional data about the transition
            
        Returns:
            True if transition successful, False otherwise
        """
        current_state = self.get_current_state()
        
        # Check if transition is valid
        if not self.can_transition(current_state, new_state):
            logger.warning(f"Invalid transition from {current_state} to {new_state}")
            return False
        
        # Record the transition
        transition = StateTransition(
            from_state=current_state,
            to_state=new_state,
            action=action,
            timestamp=datetime.now(),
            user_data=user_data or {}
        )
        
        self.transition_history.append(transition)
        
        # Update session state
        st.session_state['upload_state'] = new_state
        st.session_state['last_operation'] = action
        st.session_state['operation_timestamp'] = transition.timestamp
        
        # Add to history for rollback purposes
        if 'upload_state_history' not in st.session_state:
            st.session_state['upload_state_history'] = []
        st.session_state['upload_state_history'].append({
            'state': current_state.value,
            'timestamp': transition.timestamp.isoformat(),
            'action': action
        })
        
        # State-specific cleanup and setup
        self._handle_state_entry(new_state, transition)
        
        logger.info(f"State transition: {current_state} -> {new_state} (action: {action})")
        return True
    
    def _handle_state_entry(self, new_state: UploadState, transition: StateTransition):
        """
        Handle state-specific setup when entering a new state.
        
        Args:
            new_state: State being entered
            transition: Transition information
        """
        if new_state == UploadState.NO_DATABASE:
            self._enter_no_database_state()
        elif new_state == UploadState.DATABASE_LOADED:
            self._enter_database_loaded_state()
        elif new_state == UploadState.PROCESSING_FILES:
            self._enter_processing_state()
        elif new_state == UploadState.PREVIEW_MERGE:
            self._enter_preview_state()
        elif new_state == UploadState.ERROR_STATE:
            self._enter_error_state()
        elif new_state == UploadState.SUCCESS_STATE:
            self._enter_success_state()
    
    def _enter_no_database_state(self):
        """Setup for NO_DATABASE state."""
        # Clear database-related session state
        st.session_state['df'] = None
        st.session_state['original_questions'] = []
        st.session_state['metadata'] = {}
        st.session_state['current_filename'] = ''
        
        # Clear operation state
        st.session_state['uploaded_files'] = []
        st.session_state['processing_results'] = {}
        st.session_state['preview_data'] = {}
        
        # Clear messages
        st.session_state['error_message'] = ''
        st.session_state['success_message'] = ''
    
    def _enter_database_loaded_state(self):
        """Setup for DATABASE_LOADED state."""
        # Clear operation state but preserve database
        st.session_state['uploaded_files'] = []
        st.session_state['processing_results'] = {}
        st.session_state['preview_data'] = {}
        
        # Clear messages
        st.session_state['error_message'] = ''
        st.session_state['success_message'] = ''
        
        # Enable rollback if we have history
        st.session_state['can_rollback'] = len(st.session_state.get('database_history', [])) > 0
    
    def _enter_processing_state(self):
        """Setup for PROCESSING_FILES state."""
        st.session_state['processing_progress'] = 0.0
        st.session_state['processing_status'] = 'Starting processing...'
        st.session_state['files_processed'] = 0
        
        # Clear messages
        st.session_state['error_message'] = ''
        st.session_state['success_message'] = ''
    
    def _enter_preview_state(self):
        """Setup for PREVIEW_MERGE state."""
        st.session_state['processing_status'] = 'Ready for preview'
        # Keep preview_data as set by the calling process
    
    def _enter_error_state(self):
        """Setup for ERROR_STATE."""
        # Keep error_message as set by the calling process
        st.session_state['success_message'] = ''
    
    def _enter_success_state(self):
        """Setup for SUCCESS_STATE."""
        # Keep success_message as set by the calling process
        st.session_state['error_message'] = ''
    
    def get_available_actions(self, state: Optional[UploadState] = None) -> List[str]:
        """
        Get available actions for the current or specified state.
        
        Args:
            state: State to get actions for (defaults to current state)
            
        Returns:
            List of available action strings
        """
        if state is None:
            state = self.get_current_state()
        
        return self.STATE_ACTIONS.get(state, [])
    
    def reset_upload_state(self, preserve_database: bool = False):
        """
        Reset upload state to initial conditions.
        
        Args:
            preserve_database: If True, keep current database loaded
        """
        # Clear operation state
        st.session_state['uploaded_files'] = []
        st.session_state['processing_results'] = {}
        st.session_state['preview_data'] = {}
        st.session_state['last_operation'] = ''
        st.session_state['operation_timestamp'] = None
        
        # Clear UI state
        st.session_state['show_advanced_options'] = False
        st.session_state['selected_operation'] = None
        st.session_state['error_message'] = ''
        st.session_state['success_message'] = ''
        
        # Clear processing state
        st.session_state['processing_progress'] = 0.0
        st.session_state['processing_status'] = ''
        st.session_state['files_processed'] = 0
        st.session_state['total_files'] = 0
        
        # Determine target state
        if preserve_database and st.session_state.get('df') is not None:
            target_state = UploadState.DATABASE_LOADED
        else:
            target_state = UploadState.NO_DATABASE
            # Clear database state too
            st.session_state['df'] = None
            st.session_state['original_questions'] = []
            st.session_state['metadata'] = {}
            st.session_state['current_filename'] = ''
        
        # Transition to target state
        self.transition_to_state(target_state, "reset_upload_state")
        
        # Clear transition history
        self.transition_history = []
        st.session_state['upload_state_history'] = []
        
        logger.info(f"Upload state reset to {target_state}")
    
    def create_rollback_point(self, description: str = ""):
        """
        Create a rollback point for the current database state.
        
        Args:
            description: Description of the rollback point
        """
        if st.session_state.get('df') is not None:
            rollback_data = {
                'df': st.session_state['df'].copy(),
                'original_questions': st.session_state.get('original_questions', []).copy() if st.session_state.get('original_questions') else [],
                'metadata': st.session_state.get('metadata', {}).copy(),
                'current_filename': st.session_state.get('current_filename', ''),
                'timestamp': datetime.now().isoformat(),
                'description': description
            }
            
            st.session_state['rollback_point'] = rollback_data
            st.session_state['can_rollback'] = True
            
            # Also add to history
            if 'database_history' not in st.session_state:
                st.session_state['database_history'] = []
            st.session_state['database_history'].append(rollback_data)
            
            # Keep only last 5 history entries to manage memory
            if len(st.session_state['database_history']) > 5:
                st.session_state['database_history'] = st.session_state['database_history'][-5:]
            
            logger.info(f"Rollback point created: {description}")
    
    def rollback_to_point(self) -> bool:
        """
        Rollback to the last rollback point.
        
        Returns:
            True if rollback successful, False otherwise
        """
        if not st.session_state.get('can_rollback') or not st.session_state.get('rollback_point'):
            logger.warning("No rollback point available")
            return False
        
        try:
            rollback_data = st.session_state['rollback_point']
            
            # Restore database state
            st.session_state['df'] = rollback_data['df'].copy()
            st.session_state['original_questions'] = rollback_data['original_questions'].copy()
            st.session_state['metadata'] = rollback_data['metadata'].copy()
            st.session_state['current_filename'] = rollback_data['current_filename']
            
            # Clear rollback point
            st.session_state['rollback_point'] = None
            st.session_state['can_rollback'] = False
            
            # Transition to database loaded state
            self.transition_to_state(UploadState.DATABASE_LOADED, "rollback_operation")
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            st.session_state['error_message'] = f"Rollback failed: {str(e)}"
            self.transition_to_state(UploadState.ERROR_STATE, "rollback_failed")
            return False
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current state for debugging/monitoring.
        
        Returns:
            Dictionary with state summary information
        """
        current_state = self.get_current_state()
        
        df = st.session_state.get('df')
        database_size = len(df) if df is not None else 0
        
        summary = {
            'current_state': current_state.value,
            'available_actions': self.get_available_actions(current_state),
            'has_database': df is not None,
            'database_size': database_size,
            'processing_files': len(st.session_state.get('uploaded_files', [])),
            'can_rollback': st.session_state.get('can_rollback', False),
            'last_operation': st.session_state.get('last_operation', ''),
            'error_state': bool(st.session_state.get('error_message')),
            'success_state': bool(st.session_state.get('success_message')),
            'transition_count': len(self.transition_history)
        }
        
        return summary
    
    def validate_session_consistency(self) -> List[str]:
        """
        Validate that session state is consistent with current state.
        
        Returns:
            List of inconsistency warnings
        """
        warnings = []
        current_state = self.get_current_state()
        
        # Check database state consistency
        has_df = st.session_state.get('df') is not None
        if current_state == UploadState.DATABASE_LOADED and not has_df:
            warnings.append("State is DATABASE_LOADED but no DataFrame in session")
        elif current_state == UploadState.NO_DATABASE and has_df:
            warnings.append("State is NO_DATABASE but DataFrame exists in session")
        
        # Check error state consistency
        has_error = bool(st.session_state.get('error_message'))
        if current_state == UploadState.ERROR_STATE and not has_error:
            warnings.append("State is ERROR_STATE but no error message")
        elif current_state != UploadState.ERROR_STATE and has_error:
            warnings.append("Error message exists but state is not ERROR_STATE")
        
        # Check processing state consistency
        has_processing = bool(st.session_state.get('processing_results'))
        if current_state == UploadState.PROCESSING_FILES and not has_processing:
            warnings.append("State is PROCESSING_FILES but no processing results")
        
        # Check preview state consistency
        has_preview = bool(st.session_state.get('preview_data'))
        if current_state == UploadState.PREVIEW_MERGE and not has_preview:
            warnings.append("State is PREVIEW_MERGE but no preview data")
        
        return warnings


# Global instance for use by the upload interface
upload_state_manager = UploadStateManager()


# Convenience functions for easy access
def get_upload_state() -> UploadState:
    """Get current upload state."""
    return upload_state_manager.get_current_state()


def transition_upload_state(new_state: UploadState, action: str = "") -> bool:
    """Transition to new upload state."""
    return upload_state_manager.transition_to_state(new_state, action)


def get_upload_actions() -> List[str]:
    """Get available actions for current state."""
    return upload_state_manager.get_available_actions()


def reset_upload() -> None:
    """Reset upload state."""
    upload_state_manager.reset_upload_state()


def create_upload_rollback(description: str = "") -> None:
    """Create rollback point."""
    upload_state_manager.create_rollback_point(description)


def rollback_upload() -> bool:
    """Rollback to previous state."""
    return upload_state_manager.rollback_to_point()