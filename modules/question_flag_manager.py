# modules/question_flag_manager.py
"""
Question Flag Manager - Shared functionality for flagging questions
Handles checkbox operations, bulk actions, and flag statistics for both Select and Delete modes
"""

import streamlit as st
import pandas as pd
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime

class QuestionFlagManager:
    """
    Manages question flags for both Select and Delete operation modes.
    Provides shared functionality for checkbox operations, bulk actions, and statistics.
    """
    
    def __init__(self):
        self.supported_flags = ['selected', 'deleted']
    
    def add_flags_to_dataframe(self, df: pd.DataFrame, flag_type: str = 'both') -> pd.DataFrame:
        """
        Add flag columns to DataFrame if they don't exist
        
        Args:
            df (pd.DataFrame): The questions DataFrame
            flag_type (str): 'selected', 'deleted', or 'both'
        
        Returns:
            pd.DataFrame: DataFrame with flag columns added
        """
        try:
            df_copy = df.copy()
            
            if flag_type in ['selected', 'both']:
                if 'selected' not in df_copy.columns:
                    df_copy['selected'] = False
            
            if flag_type in ['deleted', 'both']:
                if 'deleted' not in df_copy.columns:
                    df_copy['deleted'] = False
            
            return df_copy
            
        except Exception as e:
            st.error(f"❌ Error adding flag columns: {e}")
            return df
    
    def update_question_flag(self, question_index: int, flag_type: str, value: bool) -> bool:
        """
        Update a flag for a specific question
        
        Args:
            question_index (int): Index of the question in the DataFrame
            flag_type (str): 'selected' or 'deleted'
            value (bool): New flag value
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if 'df' not in st.session_state or st.session_state.df is None:
                st.error("❌ No DataFrame available")
                return False
            
            if flag_type not in self.supported_flags:
                st.error(f"❌ Unsupported flag type: {flag_type}")
                return False
            
            df = st.session_state.df
            
            # Ensure flag column exists
            if flag_type not in df.columns:
                df[flag_type] = False
            
            # Validate index
            if question_index < 0 or question_index >= len(df):
                st.error(f"❌ Invalid question index: {question_index}")
                return False
            
            # Update the flag
            st.session_state.df.loc[question_index, flag_type] = value
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error updating question flag: {e}")
            return False
    
    def get_flagged_count(self, df: pd.DataFrame, flag_type: str) -> int:
        """
        Get count of questions with specified flag set to True
        
        Args:
            df (pd.DataFrame): The questions DataFrame
            flag_type (str): 'selected' or 'deleted'
        
        Returns:
            int: Number of flagged questions
        """
        try:
            if flag_type not in df.columns:
                return 0
            
            return int(df[flag_type].sum())
            
        except Exception as e:
            st.error(f"❌ Error counting flagged questions: {e}")
            return 0
    
    def bulk_flag_operation(self, df: pd.DataFrame, flag_type: str, operation: str) -> bool:
        """
        Perform bulk flag operations
        
        Args:
            df (pd.DataFrame): The questions DataFrame
            flag_type (str): 'selected' or 'deleted'
            operation (str): 'all', 'none', 'invert'
        
        Returns:
            bool: True if operation successful, False otherwise
        """
        try:
            if 'df' not in st.session_state or st.session_state.df is None:
                return False
            
            if flag_type not in self.supported_flags:
                return False
            
            # Ensure flag column exists
            if flag_type not in st.session_state.df.columns:
                st.session_state.df[flag_type] = False
            
            if operation == 'all':
                st.session_state.df[flag_type] = True
            elif operation == 'none':
                st.session_state.df[flag_type] = False
            elif operation == 'invert':
                st.session_state.df[flag_type] = ~st.session_state.df[flag_type]
            else:
                st.error(f"❌ Unknown bulk operation: {operation}")
                return False
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error in bulk flag operation: {e}")
            return False
    
    def render_bulk_controls(self, df: pd.DataFrame, flag_type: str, mode_context: str = '') -> None:
        """
        Render bulk control buttons for flag operations
        
        Args:
            df (pd.DataFrame): The questions DataFrame
            flag_type (str): 'selected' or 'deleted'
            mode_context (str): Context for button labels ('select' or 'delete')
        """
        try:
            # Get current counts
            flagged_count = self.get_flagged_count(df, flag_type)
            total_count = len(df)
            
            # Configure labels based on mode
            if mode_context == 'select':
                all_label = "✅ Select All"
                none_label = "❌ Select None"
                invert_label = "🔄 Invert Selection"
                status_text = f"**{flagged_count} of {total_count} questions selected**"
            elif mode_context == 'delete':
                all_label = "🗑️ Mark All for Deletion"
                none_label = "✅ Clear All Deletions"
                invert_label = "🔄 Invert Deletions"
                status_text = f"**{flagged_count} of {total_count} questions marked for deletion**"
            else:
                all_label = f"Flag All"
                none_label = f"Clear All"
                invert_label = f"Invert Flags"
                status_text = f"**{flagged_count} of {total_count} questions flagged**"
            
            # Controls row
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            
            with col1:
                if st.button(all_label, key=f"bulk_all_{flag_type}", use_container_width=True):
                    if self.bulk_flag_operation(df, flag_type, 'all'):
                        st.success(f"✅ All questions {flag_type}")
                        st.rerun()
            
            with col2:
                if st.button(none_label, key=f"bulk_none_{flag_type}", use_container_width=True):
                    if self.bulk_flag_operation(df, flag_type, 'none'):
                        st.success(f"✅ Cleared all {flag_type} flags")
                        st.rerun()
            
            with col3:
                if st.button(invert_label, key=f"bulk_invert_{flag_type}", use_container_width=True):
                    if self.bulk_flag_operation(df, flag_type, 'invert'):
                        st.success(f"✅ Inverted {flag_type} flags")
                        st.rerun()
            
            with col4:
                st.markdown(status_text)
                
                # Progress bar
                if total_count > 0:
                    progress = flagged_count / total_count
                    st.progress(progress)
            
        except Exception as e:
            st.error(f"❌ Error rendering bulk controls: {e}")
    
    def render_question_with_checkbox(self, 
                                    question: pd.Series, 
                                    question_index: int, 
                                    flag_type: str,
                                    mode_context: str = '') -> bool:
        """
        Render a question with a checkbox for flagging
        
        Args:
            question (pd.Series): Question data from DataFrame row
            question_index (int): Index of the question
            flag_type (str): 'selected' or 'deleted'
            mode_context (str): Context for checkbox label
        
        Returns:
            bool: Current flag state
        """
        try:
            # Get current flag state
            current_flag = question.get(flag_type, False)
            
            # Configure checkbox label based on mode
            if mode_context == 'select':
                checkbox_label = "Include in export"
            elif mode_context == 'delete':
                checkbox_label = "Mark for deletion"
            else:
                checkbox_label = f"Flag as {flag_type}"
            
            # Render checkbox
            checkbox_key = f"flag_{flag_type}_{question_index}"
            new_flag_state = st.checkbox(
                checkbox_label,
                value=current_flag,
                key=checkbox_key,
                help=f"Toggle {flag_type} flag for this question"
            )
            
            # Update flag if changed
            if new_flag_state != current_flag:
                self.update_question_flag(question_index, flag_type, new_flag_state)
            
            return new_flag_state
            
        except Exception as e:
            st.error(f"❌ Error rendering question checkbox: {e}")
            return False
    
    def get_flag_status_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive summary of flag status
        
        Args:
            df (pd.DataFrame): The questions DataFrame
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        try:
            summary = {
                'total_questions': len(df),
                'selected_count': 0,
                'deleted_count': 0,
                'unselected_count': 0,
                'remaining_count': 0,
                'selected_percentage': 0,
                'deleted_percentage': 0
            }
            
            if 'selected' in df.columns:
                summary['selected_count'] = self.get_flagged_count(df, 'selected')
                summary['unselected_count'] = summary['total_questions'] - summary['selected_count']
                
                if summary['total_questions'] > 0:
                    summary['selected_percentage'] = (summary['selected_count'] / summary['total_questions']) * 100
            
            if 'deleted' in df.columns:
                summary['deleted_count'] = self.get_flagged_count(df, 'deleted')
                summary['remaining_count'] = summary['total_questions'] - summary['deleted_count']
                
                if summary['total_questions'] > 0:
                    summary['deleted_percentage'] = (summary['deleted_count'] / summary['total_questions']) * 100
            
            return summary
            
        except Exception as e:
            st.error(f"❌ Error generating flag summary: {e}")
            return {'total_questions': 0}
    
    def render_flag_summary(self, df: pd.DataFrame, mode_context: str = '') -> None:
        """
        Render flag status summary with metrics
        
        Args:
            df (pd.DataFrame): The questions DataFrame
            mode_context (str): Context for display ('select' or 'delete')
        """
        try:
            summary = self.get_flag_status_summary(df)
            
            if mode_context == 'select':
                # Show selection statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total Questions", 
                        summary['total_questions'],
                        help="Total questions in database"
                    )
                
                with col2:
                    st.metric(
                        "Selected", 
                        summary['selected_count'],
                        help="Questions selected for export"
                    )
                
                with col3:
                    st.metric(
                        "Selection %", 
                        f"{summary['selected_percentage']:.1f}%",
                        help="Percentage of questions selected"
                    )
                
                # Export readiness indicator
                if summary['selected_count'] > 0:
                    st.success(f"✅ Ready to export {summary['selected_count']} selected questions")
                else:
                    st.warning("⚠️ No questions selected for export")
            
            elif mode_context == 'delete':
                # Show deletion statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total Questions", 
                        summary['total_questions'],
                        help="Total questions in database"
                    )
                
                with col2:
                    st.metric(
                        "Marked for Deletion", 
                        summary['deleted_count'],
                        help="Questions marked for deletion"
                    )
                
                with col3:
                    st.metric(
                        "Remaining", 
                        summary['remaining_count'],
                        help="Questions that will be exported"
                    )
                
                # Export readiness indicator
                if summary['remaining_count'] > 0:
                    st.success(f"✅ Ready to export {summary['remaining_count']} remaining questions")
                else:
                    st.warning("⚠️ All questions marked for deletion - nothing to export")
            
        except Exception as e:
            st.error(f"❌ Error rendering flag summary: {e}")
    
    def get_filtered_questions_for_export(self, 
                                        df: pd.DataFrame, 
                                        original_questions: List[Dict[str, Any]], 
                                        mode: str) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Filter questions based on flags for export
        
        Args:
            df (pd.DataFrame): Questions DataFrame with flags
            original_questions (List[Dict]): Original question data
            mode (str): 'select' or 'delete'
        
        Returns:
            Tuple[pd.DataFrame, List[Dict]]: Filtered DataFrame and original questions
        """
        try:
            if mode == 'select':
                # Export only selected questions
                if 'selected' in df.columns:
                    mask = df['selected'] == True
                    filtered_df = df[mask].copy()
                    
                    # Filter original questions by index
                    selected_indices = df[mask].index.tolist()
                    filtered_original = [original_questions[i] for i in selected_indices 
                                       if i < len(original_questions)]
                else:
                    # No selection column, return empty
                    filtered_df = df.iloc[0:0].copy()  # Empty DataFrame with same structure
                    filtered_original = []
            
            elif mode == 'delete':
                # Export questions NOT marked for deletion
                if 'deleted' in df.columns:
                    mask = df['deleted'] == False
                    filtered_df = df[mask].copy()
                    
                    # Filter original questions by index
                    remaining_indices = df[mask].index.tolist()
                    filtered_original = [original_questions[i] for i in remaining_indices 
                                       if i < len(original_questions)]
                else:
                    # No deletion column, return all questions
                    filtered_df = df.copy()
                    filtered_original = original_questions.copy()
            
            else:
                st.error(f"❌ Unknown export mode: {mode}")
                return df.iloc[0:0].copy(), []
            
            # Remove flag columns from export DataFrame
            flag_columns = ['selected', 'deleted']
            for col in flag_columns:
                if col in filtered_df.columns:
                    filtered_df = filtered_df.drop(columns=[col])
            
            return filtered_df, filtered_original
            
        except Exception as e:
            st.error(f"❌ Error filtering questions for export: {e}")
            return df.iloc[0:0].copy(), []
    
    def validate_flags(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate flag columns and data integrity
        
        Args:
            df (pd.DataFrame): DataFrame to validate
        
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'info': []
        }
        
        try:
            # Check for flag columns
            has_selected = 'selected' in df.columns
            has_deleted = 'deleted' in df.columns
            
            if not has_selected and not has_deleted:
                validation['warnings'].append("No flag columns found in DataFrame")
            
            # Validate flag data types
            if has_selected:
                if not df['selected'].dtype == bool:
                    validation['errors'].append("'selected' column is not boolean type")
                    validation['valid'] = False
                else:
                    selected_count = df['selected'].sum()
                    validation['info'].append(f"Selected questions: {selected_count}")
            
            if has_deleted:
                if not df['deleted'].dtype == bool:
                    validation['errors'].append("'deleted' column is not boolean type")
                    validation['valid'] = False
                else:
                    deleted_count = df['deleted'].sum()
                    validation['info'].append(f"Deleted questions: {deleted_count}")
            
            # Check for conflicts (selected AND deleted)
            if has_selected and has_deleted:
                conflicts = df['selected'] & df['deleted']
                conflict_count = conflicts.sum()
                if conflict_count > 0:
                    validation['warnings'].append(f"{conflict_count} questions are both selected and deleted")
            
            return validation
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {e}")
            return validation


# Convenience functions for easy integration
def get_question_flag_manager() -> QuestionFlagManager:
    """
    Get a configured QuestionFlagManager instance
    
    Returns:
        QuestionFlagManager: Configured instance
    """
    return QuestionFlagManager()


def add_flags_to_current_dataframe(flag_type: str = 'both') -> bool:
    """
    Add flag columns to the current session DataFrame
    
    Args:
        flag_type (str): 'selected', 'deleted', or 'both'
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if 'df' not in st.session_state or st.session_state.df is None:
            return False
        
        flag_manager = QuestionFlagManager()
        st.session_state.df = flag_manager.add_flags_to_dataframe(
            st.session_state.df, flag_type
        )
        return True
        
    except Exception:
        return False


# Example usage and testing
if __name__ == "__main__":
    # This code runs when the module is executed directly
    # Useful for testing the module independently
    
    st.title("Question Flag Manager Test")
    
    # Create sample data for testing
    if 'df' not in st.session_state:
        sample_data = {
            'Title': [f'Question {i}' for i in range(1, 6)],
            'Type': ['multiple_choice'] * 5,
            'Topic': ['Math', 'Science', 'Math', 'History', 'Science'],
            'Points': [1, 2, 1, 1, 2],
            'Question_Text': [f'This is question {i}?' for i in range(1, 6)]
        }
        st.session_state.df = pd.DataFrame(sample_data)
        st.session_state.original_questions = [{'id': i, 'text': f'Question {i}'} for i in range(1, 6)]
    
    flag_manager = QuestionFlagManager()
    
    # Add flags to DataFrame
    st.session_state.df = flag_manager.add_flags_to_dataframe(st.session_state.df)
    
    # Test interface
    st.subheader("Test Flag Operations")
    
    # Mode selection for testing
    test_mode = st.radio("Test Mode", ['select', 'delete'])
    flag_type = 'selected' if test_mode == 'select' else 'deleted'
    
    # Bulk controls
    st.subheader("Bulk Controls")
    flag_manager.render_bulk_controls(st.session_state.df, flag_type, test_mode)
    
    # Individual question checkboxes
    st.subheader("Individual Questions")
    for idx, question in st.session_state.df.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                flag_manager.render_question_with_checkbox(
                    question, idx, flag_type, test_mode
                )
            
            with col2:
                st.write(f"**{question['Title']}** - {question['Topic']} ({question['Points']} pts)")
                st.caption(question['Question_Text'])
    
    # Summary
    st.subheader("Flag Summary")
    flag_manager.render_flag_summary(st.session_state.df, test_mode)
    
    # Validation
    st.subheader("Validation Results")
    validation = flag_manager.validate_flags(st.session_state.df)
    
    if validation['valid']:
        st.success("✅ All validations passed")
    else:
        st.error("❌ Validation errors found")
    
    for error in validation['errors']:
        st.error(f"Error: {error}")
    
    for warning in validation['warnings']:
        st.warning(f"Warning: {warning}")
    
    for info in validation['info']:
        st.info(f"Info: {info}")
