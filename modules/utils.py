import re
import streamlit as st

def render_latex_in_text(text):
    """
    Enhanced LaTeX rendering for Streamlit with comprehensive mathematical notation support
    """
    if not text or not isinstance(text, str):
        return text
    unicode_preservations = {
        'π': '###PI###',
        'Ω': '###OMEGA###', 
        'μ': '###MU###',
        'α': '###ALPHA###',
        'β': '###BETA###',
        'γ': '###GAMMA###',
        'δ': '###DELTA###',
        'θ': '###THETA###',
        'λ': '###LAMBDA###',
        'σ': '###SIGMA###',
        'φ': '###PHI###',
        'τ': '###TAU###',
        '·': '###DOT###',
        '×': '###TIMES###',
        '±': '###PLUSMINUS###'
    }
    protected_text = text
    for unicode_char, placeholder in unicode_preservations.items():
        protected_text = protected_text.replace(unicode_char, placeholder)
    math_pattern = r'(\$\$.*?\$\$|\$.*?\$)'
    parts = re.split(math_pattern, protected_text)
    latex_to_unicode = {
        r'\\Omega': 'Ω', r'\\mu': 'μ', r'\\omega': 'ω', r'\\pi': 'π',
        r'\\alpha': 'α', r'\\beta': 'β', r'\\gamma': 'γ', r'\\delta': 'δ',
        r'\\theta': 'θ', r'\\lambda': 'λ', r'\\sigma': 'σ', r'\\phi': 'φ', r'\\tau': 'τ',
        r'\\infty': '∞', r'\\pm': '±', r'\\mp': '∓', r'\\times': '×', r'\\div': '÷',
        r'\\neq': '≠', r'\\leq': '≤', r'\\geq': '≥', r'\\approx': '≈', r'\\angle': '∠',
        r'\\sqrt': '√', r'\\partial': '∂', r'\\nabla': '∇', r'\\sum': '∑', r'\\int': '∫', r'\\prod': '∏',
    }
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = re.sub(r'\\mu([A-Z])', r'μ\1', part)
            part = re.sub(r'\^{?([0-9])}?', lambda m: {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}.get(m.group(1), f'^{m.group(1)}'), part)
            part = re.sub(r'_{?([0-9])}?', lambda m: {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'}.get(m.group(1), f'_{m.group(1)}'), part)
            for latex_cmd, unicode_char in latex_to_unicode.items():
                if latex_cmd.startswith(r'\\'):
                    clean_cmd = latex_cmd.replace(r'\\', '\\\\')
                    pattern = clean_cmd + r'(?![a-zA-Z])'
                    part = re.sub(pattern, unicode_char, part)
            part = re.sub(r'(\d+)(Ω|μ|ω|π|α|β|γ|δ|θ|λ|σ|φ|τ|∞|°)', r'\1 \2', part)
            part = re.sub(r'(\d+)(Hz|V|A|W|F|H|Ω|S|m|s|J)', r'\1 \2', part)
            part = re.sub(r'(\d+)\s*μ\s*([A-Z])', r'\1 μ\2', part)
            part = re.sub(r'(\d+)\s*m\s*([A-Z])', r'\1 m\2', part)
            part = re.sub(r'(\d+)\s*k\s*([A-Z])', r'\1 k\2', part)
            part = re.sub(r'\\,', ' ', part)
            part = re.sub(r'\\text\{([^}]+)\}', r'\1', part)
            part = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', part)
            part = re.sub(r'\s{3,}', ' ', part)
            part = part.strip()
        parts[i] = part
    result = ''.join(parts)
    for unicode_char, placeholder in unicode_preservations.items():
        result = result.replace(placeholder, unicode_char)
    return result

def determine_correct_answer_letter(correct_answer_text, choice_texts):
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
