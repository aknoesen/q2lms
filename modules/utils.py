# modules/utils.py

import re
import streamlit as st

def normalize_latex_for_display(text):
    """
    Fix common LLM LaTeX formatting issues for consistent display.
    """
    if not text or not isinstance(text, str):
        return text
    
    # Fix degree symbols using simple string replacement
    text = text.replace('\\,^\\circ', '^{\\circ}')
    text = text.replace('^\\circ', '^{\\circ}')
    text = text.replace('\\,^\\degree', '^{\\circ}')
    text = text.replace('^\\degree', '^{\\circ}')
    
    # Fix degree symbols in numeric patterns
    text = re.sub(r'(\d+\.?\d*)\^\\circ', r'\1^{\\circ}', text)
    
    # Fix angle notation patterns - comprehensive handling
    text = text.replace('\\\\angle', '\\angle')
    
    # Fix angle notation in plain text (not wrapped in $...$) - add proper LaTeX wrapping
    # Handle positive and negative angles
    text = re.sub(r'(\d+\.?\d*)\s*\\angle\s*(-?\d+\.?\d*)\^{\\circ}', r'$\1 \\angle \2^{\\circ}$', text)
    
    # Fix angle notation already inside $...$ delimiters  
    text = re.sub(r'\$([\d.]+)\s*\\angle\s*([-\d.]+)\^{\\circ}\$', r'$\1 \\angle \2^{\\circ}$', text)
    
    # Handle cases where angle has no spaces (including negative angles)
    text = re.sub(r'(\d+\.?\d*)\\angle(-?\d+\.?\d*)\^{\\circ}', r'$\1 \\angle \2^{\\circ}$', text)
    
    # Fix Unicode degree inside LaTeX
    if '$' in text and '°' in text:
        parts = text.split('$')
        for i in range(1, len(parts), 2):
            parts[i] = parts[i].replace('°', '^{\\circ}')
        text = '$'.join(parts)
    
    # Fix subscripts and superscripts - add braces if missing
    text = re.sub(r'_([a-zA-Z0-9])(?![{])', r'_{\1}', text)
    text = re.sub(r'\^([a-zA-Z0-9])(?![{])', r'^{\1}', text)
    
    # Fix spacing issues carefully
    text = re.sub(r'\s{2,}\$', r' $', text)
    text = re.sub(r'\$\s+', r'$', text)
    
    # Only fix spacing after Omega symbols specifically
    text = re.sub(r'\$([^$]*\\Omega[^$]*)\$([a-zA-Z])', r'$\1$ \2', text)
    
    # Fix common symbols
    text = text.replace('\\ohm', '\\Omega')
    text = text.replace('\\micro', '\\mu')
    
    return text

def render_latex_in_text(text, latex_converter=None):
    """
    LaTeX rendering with automatic formatting fixes.
    """
    if not text or not isinstance(text, str):
        return text

    # Normalize LaTeX formatting
    normalized_text = normalize_latex_for_display(text)
    
    # Apply space protection
    final_result = _protect_latex_spaces(normalized_text)
    
    # Debug output removed - LaTeX normalization working correctly
    # if text != normalized_text:
    #     print(f"🔧 LATEX NORMALIZED: '{text}' → '{normalized_text}'")
    
    return final_result

def _protect_latex_spaces(text):
    """
    Add proper spacing around LaTeX expressions for Streamlit compatibility.
    """
    if not text:
        return text
    
    # Add space after LaTeX expressions that are followed by letters
    # This handles cases like "$0.707$times" -> "$0.707$ times"
    text = re.sub(r'\$([^$]+)\$([a-zA-Z])', r'$\1$ \2', text)
    
    # Add space before LaTeX expressions that are preceded by letters  
    # This handles cases like "frequency$f_c$" -> "frequency $f_c$"
    text = re.sub(r'([a-zA-Z])\$([^$]+)\$', r'\1 $\2$', text)
    
    return text

def determine_correct_answer_letter(correct_answer_text, choice_texts):
    """Determine the correct answer letter (A, B, C, D) from the correct answer text"""
    if not correct_answer_text:
        return 'A'
    
    answer_clean = str(correct_answer_text).strip()
    
    if answer_clean.upper() in ['A', 'B', 'C', 'D']:
        return answer_clean.upper()
    
    answer_lower = answer_clean.lower()
    for letter, choice_text in choice_texts.items():
        if choice_text.lower().strip() == answer_lower:
            return letter
    
    if len(answer_clean) > 10:
        for letter, choice_text in choice_texts.items():
            if (len(choice_text) > 10 and answer_lower in choice_text.lower()):
                return letter
    
    return 'A'