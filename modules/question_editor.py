# modules/question_editor.py

import streamlit as st
import streamlit.components.v1 as components  # NEW: Added for LaTeX fix
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import AppConfig for consistent button styling
try:
    from .app_config import AppConfig
except ImportError:
    from app_config import AppConfig

from .utils import render_latex_in_text
# RESTORED: Re-enable LaTeX converter for the fix
from .export.latex_converter import CanvasLaTeXConverter 

# RESTORED: Instantiate the LaTeX converter
_latex_converter_instance = CanvasLaTeXConverter() 

# Import from other modules
from .database_processor import save_question_changes, delete_question, validate_single_question

def determine_correct_answer_letter(correct_answer_text, choice_texts):
    """Determine the correct answer letter (A, B, C, D) from the correct answer text"""
    if not correct_answer_text:
        return 'A'
    
    answer_clean = str(correct_answer_text).strip()
    
    # Case 1: Already a letter (A, B, C, D)
    if answer_clean.upper() in ['A', 'B', 'C', 'D']:
        return answer_clean.upper()
    
    # Case 2: Exact text match (case insensitive)
    answer_lower = answer_clean.lower()
    for letter, choice_text in choice_texts.items():
        if choice_text.lower().strip() == answer_lower:
            return letter
    
    # Default fallback
    return 'A'

def display_live_question_preview(question_data):
    """
    Display with proper LaTeX handling using st.markdown for LaTeX content.
    """
    
    # Header with metadata (standard markdown)
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"**{question_data.get('title', 'Untitled')}**") 
    with col2:
        question_type = question_data.get('question_type', 'multiple_choice')
        st.markdown(f"🏷️ **{question_type.replace('_', ' ').title()}**") 
    with col3:
        difficulty = question_data.get('difficulty', 'Medium')
        difficulty_colors = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
        difficulty_icon = difficulty_colors.get(difficulty, '⚪')
        st.markdown(f"{difficulty_icon} **{difficulty}**") 
    with col4:
        points = question_data.get('points', 1)
        st.markdown(f"**{points} pts**") 
    
    topic = question_data.get('topic', 'General')
    subtopic = question_data.get('subtopic', '')
    topic_info = f"📚 {topic}"
    if subtopic and subtopic not in ['', 'N/A', 'empty']:
        topic_info += f" → {subtopic}"
    st.markdown(f"*{topic_info}*") 
    
    st.markdown("---")
    
    # Question text: Use st.markdown for LaTeX content
    question_text_html = render_latex_in_text(
        question_data.get('question_text', ''), 
        latex_converter=_latex_converter_instance
    )
    st.markdown(f"**Question:** {question_text_html}")
    
    # Handle different question types
    if question_data.get('question_type') == 'multiple_choice':
        st.markdown("**Choices:**")
        
        choices_list = ['A', 'B', 'C', 'D']
        correct_answer = question_data.get('correct_answer', 'A')
        
        choice_texts = {}
        for choice_letter in choices_list:
            choice_text = question_data.get(f'choice_{choice_letter.lower()}', '')
            if choice_text and str(choice_text).strip():
                choice_texts[choice_letter] = str(choice_text).strip()
        
        if correct_answer not in ['A', 'B', 'C', 'D']:
            correct_letter = determine_correct_answer_letter(correct_answer, choice_texts)
        else:
            correct_letter = correct_answer
        
        for choice_letter in choices_list:
            if choice_letter in choice_texts:
                choice_text_clean = choice_texts[choice_letter]
                choice_text_html = render_latex_in_text(
                    choice_text_clean, 
                    latex_converter=_latex_converter_instance
                )
                
                is_correct = (choice_letter == correct_letter)
                
                # Use st.markdown for choice content with LaTeX
                if is_correct:
                    st.markdown(f"• **{choice_letter}:** {choice_text_html} ✅ ← Correct Answer")
                else:
                    st.markdown(f"• **{choice_letter}:** {choice_text_html}")
    
    elif question_data.get('question_type') == 'numerical':
        correct_answer_html = render_latex_in_text(
            str(question_data.get('correct_answer', '')), 
            latex_converter=_latex_converter_instance
        )
        st.markdown(f"**Correct Answer:** {correct_answer_html} ✅")
        
        tolerance = question_data.get('tolerance', 0)
        if tolerance and float(tolerance) > 0:
            st.markdown(f"**Tolerance:** ±{tolerance}")
    
    elif question_data.get('question_type') == 'true_false':
        correct_answer = str(question_data.get('correct_answer', '')).strip()
        st.markdown(f"**Correct Answer:** {correct_answer} ✅")
    
    elif question_data.get('question_type') == 'fill_in_blank':
        correct_answer_html = render_latex_in_text(
            str(question_data.get('correct_answer', '')), 
            latex_converter=_latex_converter_instance
        )
        st.markdown(f"**Correct Answer:** {correct_answer_html} ✅")
    
    # Feedback
    correct_feedback = question_data.get('correct_feedback', '')
    incorrect_feedback = question_data.get('incorrect_feedback', '')
    
    if correct_feedback or incorrect_feedback:
        with st.expander("💡 View Feedback"):
            if correct_feedback:
                rendered_correct_html = render_latex_in_text(
                    str(correct_feedback), 
                    latex_converter=_latex_converter_instance
                )
                st.markdown(f"**Correct:** {rendered_correct_html}")
            
            if incorrect_feedback:
                rendered_incorrect_html = render_latex_in_text(
                    str(incorrect_feedback), 
                    latex_converter=_latex_converter_instance
                )
                st.markdown(f"**Incorrect:** {rendered_incorrect_html}")

def side_by_side_question_editor(filtered_df):
    """Enhanced Browse & Edit with side-by-side live preview"""
    
    st.markdown(f"### 📝 Browse & Edit Questions ({len(filtered_df)} results)")
    
    if len(filtered_df) > 0:
        st.info("💡 **Live Editor:** Edit questions on the right, see live preview on the left. Changes save in real-time!")
        
        # Pagination
        items_per_page = st.selectbox("Questions per page", [5, 10, 20], index=1)
        total_pages = (len(filtered_df) - 1) // items_per_page + 1
        
        if total_pages > 1:
            # Enhanced pagination
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            if 'current_page' not in st.session_state:
                st.session_state['current_page'] = 1
            
            with col1:
                if AppConfig.create_red_button("⬅️ Previous", button_type="secondary-action") and st.session_state['current_page'] > 1:
                    st.session_state['current_page'] -= 1
                    st.rerun()
            
            with col2:
                if AppConfig.create_red_button("⏪ First", button_type="secondary-action"):
                    st.session_state['current_page'] = 1
                    st.rerun()
            
            with col3:
                page = st.selectbox("Page", range(1, total_pages + 1), 
                                  index=st.session_state['current_page'] - 1, 
                                  key="page_selector")
                if page != st.session_state['current_page']:
                    st.session_state['current_page'] = page
                    st.rerun()
            
            with col4:
                if AppConfig.create_red_button("⏩ Last", button_type="secondary-action"):
                    st.session_state['current_page'] = total_pages
                    st.rerun()
            
            with col5:
                if AppConfig.create_red_button("Next ➡️", button_type="secondary-action") and st.session_state['current_page'] < total_pages:
                    st.session_state['current_page'] += 1
                    st.rerun()
            
            # Show page info
            st.info(f"Page {st.session_state['current_page']} of {total_pages} ({len(filtered_df)} total questions)")
            
            # Calculate indices
            start_idx = (st.session_state['current_page'] - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_df = filtered_df.iloc[start_idx:end_idx]
            page_offset = start_idx
        else:
            page_df = filtered_df
            page_offset = 0
        
        st.markdown("---")
        
        # Display questions with side-by-side edit
        for display_idx, (idx, question) in enumerate(page_df.iterrows()):
            actual_index = page_offset + display_idx
            
            st.markdown(f"### Question {actual_index + 1}")
            
            # Side-by-side layout: Preview | Edit
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### 👁️ Live Preview")
                
                # Get current edit values or defaults
                current_question_data = get_current_edit_values(actual_index, question)
                
                # Display live preview
                display_live_question_preview(current_question_data)
            
            with col2:
                st.markdown("#### ✏️ Edit Panel")
                
                # Edit form
                edit_question_form(actual_index, question)
            
            st.markdown("---")
            st.markdown("<br>")
        
        # Navigation at bottom
        if total_pages > 1:
            st.markdown("---")
            st.markdown("### 🔄 Page Navigation")
            
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if AppConfig.create_red_button("⬅️ Previous", key="bottom_prev", button_type="secondary-action") and st.session_state['current_page'] > 1:
                    st.session_state['current_page'] -= 1
                    st.rerun()
            
            with col2:
                if AppConfig.create_red_button("⏪ First", key="bottom_first", button_type="secondary-action"):
                    st.session_state['current_page'] = 1
                    st.rerun()
            
            with col3:
                st.info(f"Page {st.session_state['current_page']} of {total_pages}")
            
            with col4:
                if AppConfig.create_red_button("⏩ Last", key="bottom_last", button_type="secondary-action"):
                    st.session_state['current_page'] = total_pages
                    st.rerun()
            
            with col5:
                if AppConfig.create_red_button("Next ➡️", key="bottom_next", button_type="secondary-action") and st.session_state['current_page'] < total_pages:
                    st.session_state['current_page'] += 1
                    st.rerun()
    
    else:
        st.warning("🔍 No questions match the current filters.")

def get_current_edit_values(question_index, original_question):
    """Get current edit values from session state or return defaults"""
    
    # Build session state keys
    title_key = f"edit_title_{question_index}"
    question_text_key = f"edit_question_text_{question_index}"
    type_key = f"edit_type_{question_index}"
    difficulty_key = f"edit_difficulty_{question_index}"
    points_key = f"edit_points_{question_index}"
    topic_key = f"edit_topic_{question_index}"
    subtopic_key = f"edit_subtopic_{question_index}"
    
    # Get values from session state or defaults
    return {
        'title': st.session_state.get(title_key, original_question['Title']),
        'question_text': st.session_state.get(question_text_key, original_question['Question_Text']),
        'question_type': st.session_state.get(type_key, original_question['Type']),
        'difficulty': st.session_state.get(difficulty_key, original_question['Difficulty']),
        'points': st.session_state.get(points_key, float(original_question['Points'])),
        'topic': st.session_state.get(topic_key, original_question['Topic']),
        'subtopic': st.session_state.get(subtopic_key, original_question['Subtopic'] or ''),
        'choice_a': st.session_state.get(f"edit_choice_a_{question_index}", original_question.get('Choice_A', '')),
        'choice_b': st.session_state.get(f"edit_choice_b_{question_index}", original_question.get('Choice_B', '')),
        'choice_c': st.session_state.get(f"edit_choice_c_{question_index}", original_question.get('Choice_C', '')),
        'choice_d': st.session_state.get(f"edit_choice_d_{question_index}", original_question.get('Choice_D', '')),
        'correct_answer': st.session_state.get(f"edit_correct_answer_{question_index}", original_question['Correct_Answer']),
        'tolerance': st.session_state.get(f"edit_tolerance_{question_index}", float(original_question.get('Tolerance', 0.05))),
        'correct_feedback': st.session_state.get(f"edit_correct_feedback_{question_index}", original_question.get('Correct_Feedback', '')),
        'incorrect_feedback': st.session_state.get(f"edit_incorrect_feedback_{question_index}", original_question.get('Incorrect_Feedback', ''))
    }

def init_session_state(key: str, default: Any):
    if key not in st.session_state:
        st.session_state[key] = default

@dataclass
class QuestionFields:
    title: str
    question_text: str
    question_type: str
    difficulty: str
    points: float
    topic: str
    subtopic: str
    choice_a: str = ''
    choice_b: str = ''
    choice_c: str = ''
    choice_d: str = ''
    correct_answer: Any = ''
    tolerance: float = 0.05
    correct_feedback: str = ''
    incorrect_feedback: str = ''


def handle_multiple_choice_fields(question_index, original_question):
    choice_a_key = f"edit_choice_a_{question_index}"
    choice_b_key = f"edit_choice_b_{question_index}"
    choice_c_key = f"edit_choice_c_{question_index}"
    choice_d_key = f"edit_choice_d_{question_index}"
    correct_answer_key = f"edit_correct_answer_{question_index}"
    
    init_session_state(choice_a_key, original_question['Choice_A'] or '')
    init_session_state(choice_b_key, original_question['Choice_B'] or '')
    init_session_state(choice_c_key, original_question['Choice_C'] or '')
    init_session_state(choice_d_key, original_question['Choice_D'] or '')
    init_session_state(correct_answer_key, original_question['Correct_Answer'])
    
    choice_a = st.text_area("Choice A", key=choice_a_key, height=70)
    choice_b = st.text_area("Choice B", key=choice_b_key, height=70)
    choice_c = st.text_area("Choice C", key=choice_c_key, height=70)
    choice_d = st.text_area("Choice D", key=choice_d_key, height=70)
    
    # FIXED: Remove index parameter - let session state handle the value
    correct_answer = st.selectbox("Correct Answer", ['A', 'B', 'C', 'D'], key=correct_answer_key)
    
    return choice_a, choice_b, choice_c, choice_d, correct_answer

def handle_numerical_fields(question_index, original_question):
    correct_answer_key = f"edit_correct_answer_{question_index}"
    tolerance_key = f"edit_tolerance_{question_index}"
    
    init_session_state(correct_answer_key, str(original_question['Correct_Answer']))
    init_session_state(tolerance_key, float(original_question['Tolerance']) if original_question['Tolerance'] else 0.05)
    
    correct_answer = st.text_input("Correct Answer", key=correct_answer_key)
    tolerance = st.number_input("Tolerance", min_value=0.0, key=tolerance_key, step=0.01)
    
    return correct_answer, tolerance

def handle_true_false_fields(question_index, original_question):
    correct_answer_key = f"edit_correct_answer_{question_index}"
    
    init_session_state(correct_answer_key, original_question['Correct_Answer'])
    
    # FIXED: Remove index parameter - let session state handle the value
    correct_answer = st.selectbox("Correct Answer", ['True', 'False'], key=correct_answer_key)
    
    return correct_answer

def handle_fill_in_blank_fields(question_index, original_question):
    correct_answer_key = f"edit_correct_answer_{question_index}"
    
    init_session_state(correct_answer_key, str(original_question['Correct_Answer']))
    
    correct_answer = st.text_input("Correct Answer", key=correct_answer_key)
    
    return correct_answer

def handle_fill_in_blank_fields(question_index, original_question):
    correct_answer_key = f"edit_correct_answer_{question_index}"
    init_session_state(correct_answer_key, str(original_question['Correct_Answer']))
    correct_answer = st.text_input("Correct Answer", key=correct_answer_key)
    return correct_answer

def handle_feedback_fields(question_index, original_question):
    correct_feedback_key = f"edit_correct_feedback_{question_index}"
    incorrect_feedback_key = f"edit_incorrect_feedback_{question_index}"
    init_session_state(correct_feedback_key, original_question['Correct_Feedback'] or '')
    init_session_state(incorrect_feedback_key, original_question['Incorrect_Feedback'] or '')
    correct_feedback = st.text_area("Correct Feedback", key=correct_feedback_key, height=70)
    incorrect_feedback = st.text_area("Incorrect Feedback", key=incorrect_feedback_key, height=70)
    return correct_feedback, incorrect_feedback

def edit_question_form(question_index, original_question):
    """Display edit form for a single question"""
    # Initialize session state keys
    title_key = f"edit_title_{question_index}"
    question_text_key = f"edit_question_text_{question_index}"
    type_key = f"edit_type_{question_index}"
    difficulty_key = f"edit_difficulty_{question_index}"
    points_key = f"edit_points_{question_index}"
    topic_key = f"edit_topic_{question_index}"
    subtopic_key = f"edit_subtopic_{question_index}"
    init_session_state(title_key, original_question['Title'])
    init_session_state(question_text_key, original_question['Question_Text'])
    init_session_state(type_key, original_question['Type'])
    init_session_state(difficulty_key, original_question['Difficulty'])
    init_session_state(points_key, float(original_question['Points']))
    init_session_state(topic_key, original_question['Topic'])
    init_session_state(subtopic_key, original_question['Subtopic'] or '')
    # Edit fields with real-time updates
    title = st.text_input("Title", key=title_key, help="Question title or identifier")
    question_text = st.text_area("Question Text", key=question_text_key, height=100,
                               help="Use LaTeX notation like \\Omega, \\mu, etc.")
    col2a, col2b = st.columns(2)
    with col2a:
        question_type = st.selectbox("Type", 
                                   ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank'],
                                   key=type_key)
        difficulty = st.selectbox("Difficulty", ['Easy', 'Medium', 'Hard'], key=difficulty_key)
    with col2b:
        points = st.number_input("Points", min_value=0.1, key=points_key, step=0.1)
        topic = st.text_input("Topic", key=topic_key)
    subtopic = st.text_input("Subtopic", key=subtopic_key)
    # Handle different question types
    choice_a = choice_b = choice_c = choice_d = ''
    correct_answer = ''
    tolerance = 0.05
    if question_type == 'multiple_choice':
        st.markdown("**Choices:**")
        choice_a, choice_b, choice_c, choice_d, correct_answer = handle_multiple_choice_fields(question_index, original_question)
    elif question_type == 'numerical':
        correct_answer, tolerance = handle_numerical_fields(question_index, original_question)
    elif question_type == 'true_false':
        correct_answer = handle_true_false_fields(question_index, original_question)
    else:  # fill_in_blank
        correct_answer = handle_fill_in_blank_fields(question_index, original_question)
    # Feedback fields
    st.markdown("**Feedback:**")
    correct_feedback, incorrect_feedback = handle_feedback_fields(question_index, original_question)
    # Save and Delete buttons
    col_save, col_delete, col_reset = st.columns(3)
    with col_save:
        if AppConfig.create_red_button("💾 Save to Database", key=f"save_{question_index}", button_type="primary-action"):
            changes = {
                'title': title,
                'question_type': question_type,
                'difficulty': difficulty,
                'points': points,
                'topic': topic,
                'subtopic': subtopic,
                'question_text': question_text,
                'choice_a': choice_a if question_type == 'multiple_choice' else '',
                'choice_b': choice_b if question_type == 'multiple_choice' else '',
                'choice_c': choice_c if question_type == 'multiple_choice' else '',
                'choice_d': choice_d if question_type == 'multiple_choice' else '',
                'correct_answer': correct_answer,
                'tolerance': tolerance if question_type == 'numerical' else 0.05,
                'correct_feedback': correct_feedback,
                'incorrect_feedback': incorrect_feedback
            }
            save_success = save_question_changes(question_index, changes)
            if save_success:
                st.success("✅ Saved to database!")
                st.rerun()
    with col_delete:
        if AppConfig.create_red_button("🗑️ Delete Question", key=f"delete_{question_index}", button_type="destructive-action"):
            st.session_state[f"confirm_delete_{question_index}"] = True
    with col_reset:
        if AppConfig.create_red_button("🔄 Reset to Original", key=f"reset_{question_index}", button_type="secondary-action"):
            keys_to_reset = [key for key in st.session_state.keys() if key.endswith(f"_{question_index}")]
            for key in keys_to_reset:
                del st.session_state[key]
            st.success("✅ Reset to original values!")
            st.rerun()
    if st.session_state.get(f"confirm_delete_{question_index}", False):
        st.warning("⚠️ **Are you sure you want to delete this question?**")
        st.write("This action cannot be undone!")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if AppConfig.create_red_button("✅ Yes, Delete", key=f"confirm_yes_{question_index}", button_type="confirmation-action"):
                delete_success = delete_question(question_index)
                if delete_success:
                    st.success("🗑️ Question deleted successfully!")
                    st.session_state[f"confirm_delete_{question_index}"] = False
                    st.rerun()
        with col_no:
            if AppConfig.create_red_button("❌ Cancel", key=f"confirm_no_{question_index}", button_type="secondary-action"):
                st.session_state[f"confirm_delete_{question_index}"] = False
                st.rerun()