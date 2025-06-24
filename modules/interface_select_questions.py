# modules/interface_select_questions.py
"""
Select Questions Interface - Combines question editing with selection functionality
Allows users to choose specific questions for export while maintaining full editing capabilities
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import shared components - handle both relative and absolute imports
try:
    # Try relative imports first (when used as a module)
    from .question_flag_manager import QuestionFlagManager
    from .utils import render_latex_in_text
    from .export.latex_converter import CanvasLaTeXConverter
    from .database_processor import save_question_changes, delete_question, validate_single_question
except ImportError:
    # Fall back to absolute imports (when testing independently)
    try:
        from question_flag_manager import QuestionFlagManager
        from utils import render_latex_in_text
        from export.latex_converter import CanvasLaTeXConverter
        from database_processor import save_question_changes, delete_question, validate_single_question
    except ImportError as e:
        # If still failing, provide fallback functions for testing
        st.warning(f"⚠️ Some imports not available: {e}")
        st.info("Running in test mode with limited functionality")
        
        # Provide minimal fallback classes for testing
        from question_flag_manager import QuestionFlagManager
        
        # Mock functions for testing
        def render_latex_in_text(text, latex_converter=None):
            return text  # Simple fallback - just return text as-is
        
        class CanvasLaTeXConverter:
            pass
        
        def save_question_changes(index, changes):
            st.info(f"Mock save: Question {index} changes: {list(changes.keys())}")
            return True
        
        def delete_question(index):
            st.info(f"Mock delete: Question {index}")
            return True
        
        def validate_single_question(question):
            return True

class SelectQuestionsInterface:
    """
    Interface for Select Questions mode - combines editing with selection functionality.
    Users can flag questions for inclusion in export while editing them.
    """
    
    def __init__(self):
        self.flag_manager = QuestionFlagManager()
        self.latex_converter = CanvasLaTeXConverter()
        self.flag_type = 'selected'
        self.mode_context = 'select'
    
    def render_selection_interface(self, filtered_df: pd.DataFrame) -> None:
        """
        Render the complete Select Questions interface
        
        Args:
            filtered_df (pd.DataFrame): Filtered DataFrame from current filters
        """
        try:
            # Ensure flags are added to DataFrame
            if 'selected' not in filtered_df.columns:
                st.session_state.df = self.flag_manager.add_flags_to_dataframe(
                    st.session_state.df, 'selected'
                )
                # Re-apply filters to get updated filtered_df
                filtered_df = self._reapply_current_filters()
            
            # Header and description
            st.markdown("### 🎯 Select Questions to Export")
            st.info("""
            💡 **Select Mode**: Choose specific questions to include in your export. 
            You can edit questions and flag them for export at the same time.
            """)
            
            # Summary section
            self._render_selection_summary(filtered_df)
            
            st.markdown("---")
            
            # Bulk controls
            self._render_bulk_selection_controls(filtered_df)
            
            st.markdown("---")
            
            # Main question interface
            self._render_question_list_with_selection(filtered_df)
            
            # Export section
            st.markdown("---")
            self._render_export_section(filtered_df)
            
        except Exception as e:
            st.error(f"❌ Error rendering selection interface: {e}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
    
    def _reapply_current_filters(self) -> pd.DataFrame:
        """
        Reapply current topic filters to get updated filtered DataFrame
        
        Returns:
            pd.DataFrame: Filtered DataFrame with current topic selections
        """
        try:
            df = st.session_state.df
            
            # Get current topic filter from session state
            selected_topics = st.session_state.get('topic_filter_multi', [])
            
            if selected_topics and 'Topic' in df.columns:
                filtered_df = df[df['Topic'].isin(selected_topics)]
            else:
                filtered_df = df
            
            return filtered_df
            
        except Exception as e:
            st.error(f"❌ Error reapplying filters: {e}")
            return st.session_state.df
    
    def _render_selection_summary(self, filtered_df: pd.DataFrame) -> None:
        """
        Render selection summary with key metrics
        
        Args:
            filtered_df (pd.DataFrame): Current filtered DataFrame
        """
        try:
            # Get selection statistics
            summary = self.flag_manager.get_flag_status_summary(st.session_state.df)
            
            # Current view statistics  
            total_in_view = len(filtered_df)
            selected_in_view = self.flag_manager.get_flagged_count(filtered_df, 'selected')
            
            # Database-wide statistics
            total_questions = summary['total_questions']
            total_selected = summary['selected_count']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Questions",
                    total_questions,
                    help="Total questions in your database"
                )
            
            with col2:
                st.metric(
                    "In Current View", 
                    total_in_view,
                    help="Questions matching your current topic filters"
                )
            
            with col3:
                st.metric(
                    "Selected (View)",
                    f"{selected_in_view}/{total_in_view}",
                    help="Selected questions in current view"
                )
            
            with col4:
                st.metric(
                    "Selected (Total)",
                    total_selected,
                    help="Total selected questions across entire database"
                )
            
            # Export readiness indicator
            if total_selected > 0:
                # Calculate total points if available
                if 'Points' in st.session_state.df.columns:
                    selected_df = st.session_state.df[st.session_state.df['selected'] == True]
                    total_points = selected_df['Points'].sum()
                    st.success(f"✅ **Ready to export {total_selected} questions** ({total_points} total points)")
                else:
                    st.success(f"✅ **Ready to export {total_selected} questions**")
            else:
                st.warning("⚠️ **No questions selected for export** - Use checkboxes below to select questions")
                
        except Exception as e:
            st.error(f"❌ Error rendering selection summary: {e}")
    
    def _render_bulk_selection_controls(self, filtered_df: pd.DataFrame) -> None:
        """
        Render bulk selection controls specific to current view
        
        Args:
            filtered_df (pd.DataFrame): Current filtered DataFrame
        """
        try:
            st.subheader("🔧 Bulk Selection Controls")
            
            # Global bulk controls (affect entire database)
            st.markdown("**Database-wide controls:**")
            self.flag_manager.render_bulk_controls(
                st.session_state.df, 'selected', 'select'
            )
            
            # View-specific bulk controls
            if len(filtered_df) < len(st.session_state.df):
                st.markdown("**Current view controls:**")
                col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
                
                with col1:
                    if st.button("✅ Select View", key="select_view", use_container_width=True):
                        self._bulk_select_current_view(filtered_df, True)
                        st.success("✅ Selected all questions in current view")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Deselect View", key="deselect_view", use_container_width=True):
                        self._bulk_select_current_view(filtered_df, False)
                        st.success("✅ Deselected all questions in current view")
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Invert View", key="invert_view", use_container_width=True):
                        self._invert_selection_current_view(filtered_df)
                        st.success("✅ Inverted selection in current view")
                        st.rerun()
                
                with col4:
                    selected_in_view = self.flag_manager.get_flagged_count(filtered_df, 'selected')
                    st.markdown(f"**{selected_in_view} of {len(filtered_df)} selected in view**")
                    progress = selected_in_view / len(filtered_df) if len(filtered_df) > 0 else 0
                    st.progress(progress)
            
        except Exception as e:
            st.error(f"❌ Error rendering bulk controls: {e}")
    
    def _bulk_select_current_view(self, filtered_df: pd.DataFrame, select_state: bool) -> None:
        """
        Bulk select/deselect questions in current view only
        
        Args:
            filtered_df (pd.DataFrame): Current filtered DataFrame
            select_state (bool): True to select, False to deselect
        """
        try:
            # Get indices of questions in current view
            view_indices = filtered_df.index.tolist()
            
            # Update selection for only these questions
            for idx in view_indices:
                if idx < len(st.session_state.df):
                    st.session_state.df.loc[idx, 'selected'] = select_state
                    
        except Exception as e:
            st.error(f"❌ Error in bulk view selection: {e}")
    
    def _invert_selection_current_view(self, filtered_df: pd.DataFrame) -> None:
        """
        Invert selection for questions in current view only
        
        Args:
            filtered_df (pd.DataFrame): Current filtered DataFrame
        """
        try:
            # Get indices of questions in current view
            view_indices = filtered_df.index.tolist()
            
            # Invert selection for only these questions
            for idx in view_indices:
                if idx < len(st.session_state.df):
                    current_state = st.session_state.df.loc[idx, 'selected']
                    st.session_state.df.loc[idx, 'selected'] = not current_state
                    
        except Exception as e:
            st.error(f"❌ Error in view selection inversion: {e}")
    
    def _render_question_list_with_selection(self, filtered_df: pd.DataFrame) -> None:
        """
        Render paginated question list with selection checkboxes and editing capabilities
        
        Args:
            filtered_df (pd.DataFrame): Current filtered DataFrame
        """
        try:
            st.subheader(f"📝 Questions with Selection ({len(filtered_df)} questions)")
            
            if len(filtered_df) == 0:
                st.warning("🔍 No questions match your current filters.")
                return
            
            # Pagination controls
            items_per_page = st.selectbox(
                "Questions per page", 
                [5, 10, 20], 
                index=1,
                key="select_mode_pagination"
            )
            
            total_pages = (len(filtered_df) - 1) // items_per_page + 1
            
            if total_pages > 1:
                # Pagination UI
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                if 'select_current_page' not in st.session_state:
                    st.session_state['select_current_page'] = 1
                
                with col1:
                    if st.button("⬅️ Previous", key="select_prev") and st.session_state['select_current_page'] > 1:
                        st.session_state['select_current_page'] -= 1
                        st.rerun()
                
                with col2:
                    if st.button("⏪ First", key="select_first"):
                        st.session_state['select_current_page'] = 1
                        st.rerun()
                
                with col3:
                    page = st.selectbox(
                        "Page", 
                        range(1, total_pages + 1), 
                        index=st.session_state['select_current_page'] - 1, 
                        key="select_page_selector"
                    )
                    if page != st.session_state['select_current_page']:
                        st.session_state['select_current_page'] = page
                        st.rerun()
                
                with col4:
                    if st.button("⏩ Last", key="select_last"):
                        st.session_state['select_current_page'] = total_pages
                        st.rerun()
                
                with col5:
                    if st.button("Next ➡️", key="select_next") and st.session_state['select_current_page'] < total_pages:
                        st.session_state['select_current_page'] += 1
                        st.rerun()
                
                st.info(f"Page {st.session_state['select_current_page']} of {total_pages}")
                
                # Calculate page bounds
                start_idx = (st.session_state['select_current_page'] - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_df = filtered_df.iloc[start_idx:end_idx]
                page_offset = start_idx
            else:
                page_df = filtered_df
                page_offset = 0
            
            st.markdown("---")
            
            # Display questions with selection and editing
            for display_idx, (original_idx, question) in enumerate(page_df.iterrows()):
                actual_display_index = page_offset + display_idx
                self._render_single_question_with_selection(
                    question, original_idx, actual_display_index + 1
                )
                st.markdown("---")
                
        except Exception as e:
            st.error(f"❌ Error rendering question list: {e}")
    
    def _render_single_question_with_selection(self, 
                                             question: pd.Series, 
                                             question_index: int, 
                                             display_number: int) -> None:
        """
        Render a single question with selection checkbox and editing capabilities
        
        Args:
            question (pd.Series): Question data
            question_index (int): Original DataFrame index
            display_number (int): Display number for user
        """
        try:
            st.markdown(f"### Question {display_number}")
            
            # Top row: Selection checkbox and basic info
            col1, col2 = st.columns([1, 4])
            
            with col1:
                # Selection checkbox - prominent display
                current_selected = question.get('selected', False)
                new_selected = st.checkbox(
                    "✅ **Include in Export**",
                    value=current_selected,
                    key=f"select_checkbox_{question_index}",
                    help="Check to include this question in your export"
                )
                
                # Update flag if changed
                if new_selected != current_selected:
                    self.flag_manager.update_question_flag(question_index, 'selected', new_selected)
                
                # Visual feedback for selection state
                if new_selected:
                    st.success("✅ Selected")
                else:
                    st.info("⭕ Not Selected")
            
            with col2:
                # Question header info
                col2a, col2b, col2c, col2d = st.columns([2, 1, 1, 1])
                
                with col2a:
                    st.markdown(f"**{question.get('Title', 'Untitled')}**")
                
                with col2b:
                    question_type = question.get('Type', 'multiple_choice')
                    st.markdown(f"🏷️ **{question_type.replace('_', ' ').title()}**")
                
                with col2c:
                    difficulty = question.get('Difficulty', 'Medium')
                    difficulty_colors = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
                    difficulty_icon = difficulty_colors.get(difficulty, '⚪')
                    st.markdown(f"{difficulty_icon} **{difficulty}**")
                
                with col2d:
                    points = question.get('Points', 1)
                    st.markdown(f"**{points} pts**")
                
                # Topic info
                topic = question.get('Topic', 'General')
                subtopic = question.get('Subtopic', '')
                topic_info = f"📚 {topic}"
                if subtopic and subtopic not in ['', 'N/A', 'empty']:
                    topic_info += f" → {subtopic}"
                st.markdown(f"*{topic_info}*")
            
            # Main content: Preview and Edit side-by-side (like your existing editor)
            col_preview, col_edit = st.columns([1, 1])
            
            with col_preview:
                st.markdown("#### 👁️ Preview")
                self._render_question_preview(question, question_index)
            
            with col_edit:
                st.markdown("#### ✏️ Edit")
                self._render_question_edit_form(question, question_index)
                
        except Exception as e:
            st.error(f"❌ Error rendering question {display_number}: {e}")
    
    def _render_question_preview(self, question: pd.Series, question_index: int) -> None:
        """
        Render live question preview (reusing your existing preview logic)
        
        Args:
            question (pd.Series): Question data
            question_index (int): Question index for getting edit values
        """
        try:
            # Get current edit values or defaults (same logic as your question_editor.py)
            current_question_data = self._get_current_edit_values(question_index, question)
            
            # Question text with LaTeX rendering
            question_text_html = render_latex_in_text(
                current_question_data.get('question_text', ''),
                latex_converter=self.latex_converter
            )
            st.markdown(f"**Question:** {question_text_html}")
            
            # Handle different question types (same logic as your existing preview)
            question_type = current_question_data.get('question_type')
            
            if question_type == 'multiple_choice':
                self._render_multiple_choice_preview(current_question_data)
            elif question_type == 'numerical':
                self._render_numerical_preview(current_question_data)
            elif question_type == 'true_false':
                self._render_true_false_preview(current_question_data)
            elif question_type == 'fill_in_blank':
                self._render_fill_blank_preview(current_question_data)
            
            # Show feedback if available
            self._render_feedback_preview(current_question_data)
            
        except Exception as e:
            st.error(f"❌ Error in question preview: {e}")
    
    def _render_multiple_choice_preview(self, question_data: Dict) -> None:
        """Render multiple choice preview"""
        st.markdown("**Choices:**")
        
        choices_list = ['A', 'B', 'C', 'D']
        correct_answer = question_data.get('correct_answer', 'A')
        
        choice_texts = {}
        for choice_letter in choices_list:
            choice_text = question_data.get(f'choice_{choice_letter.lower()}', '')
            if choice_text and str(choice_text).strip():
                choice_texts[choice_letter] = str(choice_text).strip()
        
        # Determine correct letter if needed
        if correct_answer not in ['A', 'B', 'C', 'D']:
            correct_letter = self._determine_correct_answer_letter(correct_answer, choice_texts)
        else:
            correct_letter = correct_answer
        
        for choice_letter in choices_list:
            if choice_letter in choice_texts:
                choice_text_clean = choice_texts[choice_letter]
                choice_text_html = render_latex_in_text(
                    choice_text_clean,
                    latex_converter=self.latex_converter
                )
                
                is_correct = (choice_letter == correct_letter)
                
                if is_correct:
                    st.markdown(f"• **{choice_letter}:** {choice_text_html} ✅")
                else:
                    st.markdown(f"• **{choice_letter}:** {choice_text_html}")
    
    def _render_numerical_preview(self, question_data: Dict) -> None:
        """Render numerical preview"""
        correct_answer_html = render_latex_in_text(
            str(question_data.get('correct_answer', '')),
            latex_converter=self.latex_converter
        )
        st.markdown(f"**Correct Answer:** {correct_answer_html} ✅")
        
        tolerance = question_data.get('tolerance', 0)
        if tolerance and float(tolerance) > 0:
            st.markdown(f"**Tolerance:** ±{tolerance}")
    
    def _render_true_false_preview(self, question_data: Dict) -> None:
        """Render true/false preview"""
        correct_answer = str(question_data.get('correct_answer', '')).strip()
        st.markdown(f"**Correct Answer:** {correct_answer} ✅")
    
    def _render_fill_blank_preview(self, question_data: Dict) -> None:
        """Render fill-in-blank preview"""
        correct_answer_html = render_latex_in_text(
            str(question_data.get('correct_answer', '')),
            latex_converter=self.latex_converter
        )
        st.markdown(f"**Correct Answer:** {correct_answer_html} ✅")
    
    def _render_feedback_preview(self, question_data: Dict) -> None:
        """Render feedback preview"""
        correct_feedback = question_data.get('correct_feedback', '')
        incorrect_feedback = question_data.get('incorrect_feedback', '')
        
        if correct_feedback or incorrect_feedback:
            with st.expander("💡 View Feedback"):
                if correct_feedback:
                    rendered_correct_html = render_latex_in_text(
                        str(correct_feedback),
                        latex_converter=self.latex_converter
                    )
                    st.markdown(f"**Correct:** {rendered_correct_html}")
                
                if incorrect_feedback:
                    rendered_incorrect_html = render_latex_in_text(
                        str(incorrect_feedback),
                        latex_converter=self.latex_converter
                    )
                    st.markdown(f"**Incorrect:** {rendered_incorrect_html}")
    
    def _render_question_edit_form(self, question: pd.Series, question_index: int) -> None:
        """
        Render compact edit form (simplified version of your existing editor)
        
        Args:
            question (pd.Series): Question data
            question_index (int): Question index
        """
        try:
            # Initialize session state keys (same pattern as your existing editor)
            title_key = f"select_edit_title_{question_index}"
            question_text_key = f"select_edit_question_text_{question_index}"
            type_key = f"select_edit_type_{question_index}"
            
            # Initialize with current values
            if title_key not in st.session_state:
                st.session_state[title_key] = question.get('Title', '')
            if question_text_key not in st.session_state:
                st.session_state[question_text_key] = question.get('Question_Text', '')
            if type_key not in st.session_state:
                st.session_state[type_key] = question.get('Type', 'multiple_choice')
            
            # Compact edit form
            title = st.text_input("Title", key=title_key)
            question_text = st.text_area("Question Text", key=question_text_key, height=80)
            
            col_type, col_points = st.columns(2)
            with col_type:
                question_type = st.selectbox(
                    "Type", 
                    ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank'],
                    key=type_key
                )
            with col_points:
                points_key = f"select_edit_points_{question_index}"
                if points_key not in st.session_state:
                    st.session_state[points_key] = float(question.get('Points', 1))
                points = st.number_input("Points", min_value=0.1, key=points_key, step=0.1)
            
            # Quick save button
            if st.button(f"💾 Save Changes", key=f"select_save_{question_index}", type="secondary"):
                # Use your existing save logic
                changes = {
                    'title': title,
                    'question_text': question_text,
                    'question_type': question_type,
                    'points': points,
                    # Add other fields as needed
                }
                
                if save_question_changes(question_index, changes):
                    st.success("✅ Changes saved!")
                    st.rerun()
                else:
                    st.error("❌ Error saving changes")
                    
        except Exception as e:
            st.error(f"❌ Error in edit form: {e}")
    
    def _get_current_edit_values(self, question_index: int, original_question: pd.Series) -> Dict:
        """
        Get current edit values from session state or defaults (reusing your existing logic)
        
        Args:
            question_index (int): Question index
            original_question (pd.Series): Original question data
        
        Returns:
            Dict: Current values for preview
        """
        return {
            'title': st.session_state.get(f"select_edit_title_{question_index}", original_question.get('Title', '')),
            'question_text': st.session_state.get(f"select_edit_question_text_{question_index}", original_question.get('Question_Text', '')),
            'question_type': st.session_state.get(f"select_edit_type_{question_index}", original_question.get('Type', 'multiple_choice')),
            'points': st.session_state.get(f"select_edit_points_{question_index}", float(original_question.get('Points', 1))),
            'choice_a': st.session_state.get(f"select_edit_choice_a_{question_index}", original_question.get('Choice_A', '')),
            'choice_b': st.session_state.get(f"select_edit_choice_b_{question_index}", original_question.get('Choice_B', '')),
            'choice_c': st.session_state.get(f"select_edit_choice_c_{question_index}", original_question.get('Choice_C', '')),
            'choice_d': st.session_state.get(f"select_edit_choice_d_{question_index}", original_question.get('Choice_D', '')),
            'correct_answer': st.session_state.get(f"select_edit_correct_answer_{question_index}", original_question.get('Correct_Answer', 'A')),
            'tolerance': st.session_state.get(f"select_edit_tolerance_{question_index}", float(original_question.get('Tolerance', 0.05))),
            'correct_feedback': st.session_state.get(f"select_edit_correct_feedback_{question_index}", original_question.get('Correct_Feedback', '')),
            'incorrect_feedback': st.session_state.get(f"select_edit_incorrect_feedback_{question_index}", original_question.get('Incorrect_Feedback', ''))
        }
    
    def _determine_correct_answer_letter(self, correct_answer_text: str, choice_texts: Dict) -> str:
        """Determine correct answer letter from text (reusing your existing logic)"""
        if not correct_answer_text:
            return 'A'
        
        answer_clean = str(correct_answer_text).strip()
        
        # Case 1: Already a letter
        if answer_clean.upper() in ['A', 'B', 'C', 'D']:
            return answer_clean.upper()
        
        # Case 2: Exact text match
        answer_lower = answer_clean.lower()
        for letter, choice_text in choice_texts.items():
            if choice_text.lower().strip() == answer_lower:
                return letter
        
        return 'A'  # Default fallback
    
    def _render_export_section(self, filtered_df: pd.DataFrame) -> None:
        """
        Render export section for selected questions
        
        Args:
            filtered_df (pd.DataFrame): Current filtered DataFrame
        """
        try:
            st.subheader("📤 Export Selected Questions")
            
            # Get export statistics
            selected_df, selected_original = self.flag_manager.get_filtered_questions_for_export(
                st.session_state.df, 
                st.session_state.get('original_questions', []), 
                'select'
            )
            
            selected_count = len(selected_df)
            
            if selected_count > 0:
                # Export ready
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.success(f"✅ **{selected_count} questions selected and ready for export**")
                    
                    if 'Points' in selected_df.columns:
                        total_points = selected_df['Points'].sum()
                        st.info(f"📊 **Total Points:** {total_points}")
                    
                    # Show topic breakdown of selected questions
                    if 'Topic' in selected_df.columns and selected_count > 1:
                        topic_counts = selected_df['Topic'].value_counts()
                        with st.expander("📋 Selected Questions by Topic"):
                            for topic, count in topic_counts.items():
                                st.write(f"• **{topic}:** {count} questions")
                
                with col2:
                    st.metric("Questions to Export", selected_count)
                    if 'Type' in selected_df.columns:
                        unique_types = selected_df['Type'].nunique()
                        st.metric("Question Types", unique_types)
                
                # Export button (integrates with your existing export system)
                if st.button("📥 Go to Export Tab", type="primary", key="goto_export"):
                    st.info("💡 **Tip:** Switch to the Export tab to download your selected questions in CSV, QTI, or JSON format")
                    st.balloons()
                
            else:
                # No questions selected
                st.warning("⚠️ **No questions selected for export**")
                st.info("""
                **To export questions:**
                1. Use the checkboxes above to select questions
                2. Use bulk controls for faster selection
                3. Return here to export your selection
                """)
                
        except Exception as e:
            st.error(f"❌ Error rendering export section: {e}")


# Convenience function for easy integration
def get_select_questions_interface() -> SelectQuestionsInterface:
    """
    Get a configured SelectQuestionsInterface instance
    
    Returns:
        SelectQuestionsInterface: Configured instance
    """
    return SelectQuestionsInterface()


# Example usage and testing
if __name__ == "__main__":
    # This allows testing the interface independently
    st.title("Select Questions Interface Test")
    
    # Create sample data
    if 'df' not in st.session_state:
        sample_data = {
            'Title': [f'Question {i}' for i in range(1, 6)],
            'Type': ['multiple_choice', 'numerical', 'true_false', 'multiple_choice', 'numerical'],
            'Topic': ['Math', 'Science', 'Math', 'History', 'Science'],
            'Points': [1, 2, 1, 1, 2],
            'Question_Text': [f'This is question {i}?' for i in range(1, 6)],
            'Choice_A': ['Option A1', 'Answer 1', 'True', 'Choice A1', 'Value 1'],
            'Choice_B': ['Option B1', 'Answer 2', 'False', 'Choice B1', 'Value 2'],
            'Choice_C': ['Option C1', '', '', 'Choice C1', ''],
            'Choice_D': ['Option D1', '', '', 'Choice D1', ''],
            'Correct_Answer': ['A', '1', 'True', 'A', '1'],
            'Difficulty': ['Easy', 'Medium', 'Easy', 'Hard', 'Medium'],
            'Subtopic': ['Algebra', 'Physics', 'Logic', 'Events', 'Chemistry'],
            'Tolerance': [0, 0.1, 0, 0, 0.05],
            'Correct_Feedback': ['Good job!', 'Excellent!', 'Correct!', 'Well done!', 'Right!'],
            'Incorrect_Feedback': ['Try again', 'Check calculation', 'Review logic', 'Study more', 'Recalculate']
        }
        st.session_state.df = pd.DataFrame(sample_data)
        st.session_state.original_questions = [{'id': i, 'text': f'Question {i}'} for i in range(1, 6)]
    
    # Test the interface
    interface = SelectQuestionsInterface()
    interface.render_selection_interface(st.session_state.df)