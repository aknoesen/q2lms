# modules/utils.py

import re
import streamlit as st
# REMOVE CanvasLaTeXConverter import as it's not used by render_latex_in_text directly anymore
# from .export.latex_converter import CanvasLaTeXConverter # <-- REMOVE THIS LINE

def render_latex_in_text(text, latex_converter=None): # Keep latex_converter parameter for QTI compatibility
    """
    LaTeX rendering with space protection for basic Streamlit markdown display.
    This function simply processes '$' delimiters.
    """
    if not text or not isinstance(text, str):
        return text

    # For display purposes in Streamlit, we rely on st.markdown's default behavior for '$' and '$$'
    # The latex_converter is explicitly set to None for display calls in question_editor/simple_browse.
    # It will be used for QTI export.
    processed_text = text

    # Apply space protection (converts ' $' to '&nbsp;$')
    final_result = _protect_latex_spaces(processed_text)
    
    # Diagnostic for display - check original problem case
    if "Current leads voltage by" in text and "$90" in text:
        print(f"🔍 DIAGNOSTIC (render_latex_in_text - DISPLAY MODE): Input '{text}' -> Output '{final_result}'")
        print(f"   Output has '&nbsp;': {'&nbsp;' in final_result}")
        print("=" * 60)

    return final_result

def _protect_latex_spaces(text):
    """
    Protect spaces before '$' LaTeX expressions by inserting &nbsp;.
    This version adds NO div or span wrappers for general text.
    """
    if not text:
        return text
    
    # Diagnostic for _protect_latex_spaces
    # print(f"🚨 _protect_latex_spaces called with: '{text}'") # Uncomment for more verbose diagnostics
    
    # The original "corner case" logic for ` $`
    if ' $' in text:
        result = text.replace(' $', '&nbsp;$')
        # print(f"🔧 _protect_latex_spaces result: '{result}'") # Uncomment for more verbose diagnostics
        return result
    
    # print(f"🔧 _protect_latex_spaces result: '{text}' (no change)") # Uncomment for more verbose diagnostics
    return text


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
    
    # Case 3: Partial match for long answers
    if len(answer_clean) > 10:
        for letter, choice_text in choice_texts.items():
            if (len(choice_text) > 10 and answer_lower in choice_text.lower()):
                return letter
    
    # Default fallback
    return 'A'
