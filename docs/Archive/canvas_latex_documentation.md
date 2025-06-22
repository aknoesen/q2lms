# Canvas LaTeX Requirements & Implementation Guide

## 📚 Overview

This document explains how to properly handle LaTeX mathematical notation when creating question databases for Canvas LMS. **This is a critical implementation detail that causes many QTI import failures.**

---

## 🚨 The Common Stumbling Block

### ❌ **What Breaks Canvas Imports**
Most QTI generators use standard LaTeX delimiters (`$...$` and `$$...$$`) directly in QTI packages, but **Canvas requires specific MathJax delimiters**. This mismatch causes:

- Questions import but math doesn't render
- Equations display as raw LaTeX text
- Silent failures during QTI processing
- Accessibility issues for screen readers

### ✅ **The Solution**
Our system maintains **strict LaTeX formatting** in the JSON database while **automatically converting** to Canvas-compatible delimiters during QTI export.

---

## 🎯 Canvas MathJax Requirements

### **Canvas MathJax Configuration**
- **Version**: MathJax 2.7.7 (not 3.x)
- **Configuration**: TeX-MML-AM_SVG
- **Accessibility**: Auto-converts to MathML for screen readers

### **Required Delimiters**
| Math Type | Canvas Requires | Standard LaTeX | 
|-----------|----------------|----------------|
| Inline equations | `\( ... \)` | `$ ... $` |
| Block/display equations | `$$ ... $$` | `$$ ... $$` |

### **❌ What Canvas Does NOT Support**
- `$ ... $` for inline math (renders as text)
- `\[ ... \]` for display math (not recognized)
- MathJax 3.x features or syntax

---

## 🏗️ Our Implementation Strategy

### **Three-Layer Architecture**

```
JSON Database    →    Web Interface    →    QTI Export
(Strict LaTeX)        (Browser Display)     (Canvas Format)
     ↓                      ↓                     ↓
  $x^2 + 1$            $x^2 + 1$            \(x^2 + 1\)
  $$\frac{a}{b}$$      $$\frac{a}{b}$$      $$\frac{a}{b}$$
```

### **Why This Approach Works**
1. **JSON Database**: Uses standard LaTeX (`$...$`) for portability and LLM compatibility
2. **Web Interface**: Browsers handle both `$...$` and `\(...\)` fine for preview
3. **QTI Export**: Automatically converts to Canvas requirements

---

## 📝 JSON Database Format

### **Strict LaTeX Requirements**
All mathematical content in JSON must use standard LaTeX delimiters:

```json
{
  "question_text": "Calculate the impedance $Z = R + j\\omega L$ for the circuit.",
  "choices": [
    "$Z = 100 + j314\\,\\Omega$",
    "$Z = 100 + j50\\,\\Omega$",
    "$Z = 314 + j100\\,\\Omega$"
  ],
  "feedback_correct": "Correct! Using $\\omega = 2\\pi f$, we get $Z = 100 + j314\\,\\Omega$."
}
```

### **LaTeX Best Practices**
- **Inline math**: `$variable = value$`
- **Block math**: `$$equation = complex$$`
- **Units**: `$10\\,\\text{Hz}$` (with spacing)
- **Greek letters**: `$\\omega$`, `$\\pi$`, `$\\Omega$`
- **Subscripts**: `$f_s$`, `$V_{rms}$`
- **Complex expressions**: `$Z = R + j\\omega L$`

---

## 🔄 Automatic Conversion Process

### **QTI Export Pipeline**
Our robust exporter performs automatic delimiter conversion:

```python
def convert_latex_for_canvas(text):
    """Convert LaTeX delimiters for Canvas MathJax compatibility"""
    
    # Convert inline math: $...$ → \(...\)
    if expr.startswith('$') and expr.endswith('$'):
        inner_content = expr[1:-1]  # Remove $ delimiters
        canvas_expr = f'\\({inner_content}\\)'
    
    # Keep block math: $$...$$ → $$...$$ (unchanged)
    elif expr.startswith('$$') and expr.endswith('$$'):
        canvas_expr = expr  # No change needed
```

### **Conversion Examples**

| JSON Database | QTI Export | Canvas Display |
|---------------|------------|----------------|
| `$A = 3\\,\\text{V}$` | `\(A = 3\,\text{V}\)` | A = 3 V |
| `$\\omega = 2\\pi f$` | `\(\omega = 2\pi f\)` | ω = 2π f |
| `$$Z = R + j\\omega L$$` | `$$Z = R + j\omega L$$` | Z = R + jωL (centered) |
| `$\\pm 0.3\\,\\text{V}$` | `\(\pm 0.3\,\text{V}\)` | ± 0.3 V |

---

## 🧪 Testing & Verification

### **Test Your Implementation**
Use our provided test script to verify Canvas compatibility:

```bash
python test_qti_exporter.py
```

### **Expected Results**
```
🔍 Verifying Canvas delimiter conversion...
📊 Canvas conversion rate: 100.0%
🎉 EXCELLENT! All delimiters converted for Canvas!

📋 Conversion examples:
  $A = 3\,\text{V}$ → \(A = 3\,\text{V}\)
  $f_s = 10\,\text{kHz}$ → \(f_s = 10\,\text{kHz}\)
  $Z = 100 + j314\,\Omega$ → \(Z = 100 + j314\,\Omega\)
```

### **Canvas Import Verification**
1. Import generated QTI package into Canvas
2. Create test quiz and preview questions
3. Verify mathematical expressions render properly:
   - Inline math appears within text flow
   - Greek letters display correctly (ω, π, Ω)
   - Units have proper spacing
   - Complex expressions maintain formatting

---

## 🚫 Common Pitfalls & Solutions

### **Pitfall 1: Using Canvas Delimiters in JSON**
```json
❌ WRONG: "question_text": "Calculate \\(x^2 + 1\\) for x = 5"
✅ CORRECT: "question_text": "Calculate $x^2 + 1$ for x = 5"
```
**Why**: JSON should use standard LaTeX for portability.

### **Pitfall 2: CSV Conversion Pipeline**
```python
❌ WRONG: JSON → CSV → QTI (corrupts LaTeX)
✅ CORRECT: JSON → DataFrame → JSON Sync → QTI (preserves LaTeX)
```
**Why**: CSV encoding mangles LaTeX backslashes and delimiters.

### **Pitfall 3: Manual Delimiter Conversion**
```python
❌ WRONG: text.replace('$', '\\(').replace('$', '\\)')  # Breaks $$
✅ CORRECT: Use regex with proper delimiter detection
```
**Why**: Simple string replacement breaks block math and nested expressions.

### **Pitfall 4: Not Testing Canvas Import**
```
❌ WRONG: Generate QTI → Assume it works
✅ CORRECT: Generate QTI → Test Canvas import → Verify rendering
```
**Why**: QTI may import successfully but math may not render.

---

## 🎓 LLM Integration Guidelines

### **Prompt Templates**
When generating questions with LLMs, enforce strict LaTeX formatting:

```markdown
**CRITICAL: Use standard LaTeX delimiters:**
- Inline math: $variable = value$
- Block math: $$equation = expression$$
- Never use \\(...\\) or \\[...\\] in JSON output
```

### **Content Validation**
Validate LLM-generated content for proper LaTeX formatting:

```python
def validate_latex_format(question_text):
    # Check for Canvas delimiters in JSON (incorrect)
    if '\\(' in question_text or '\\[' in question_text:
        raise ValueError("JSON should use $ delimiters, not Canvas delimiters")
    
    # Verify proper LaTeX structure
    dollar_count = question_text.count('$')
    if dollar_count % 2 != 0:
        raise ValueError("Unmatched $ delimiters in LaTeX")
```

---

## 📋 Implementation Checklist

### **For Developers**
- [ ] JSON database uses only `$...$` and `$$...$$` delimiters
- [ ] QTI exporter converts `$...$` → `\(...\)` for Canvas
- [ ] QTI exporter keeps `$$...$$` unchanged
- [ ] No CSV pipeline that corrupts LaTeX
- [ ] Test script verifies Canvas compatibility
- [ ] Canvas import testing included in workflow

### **For Instructors**
- [ ] Mathematical notation renders properly in Canvas previews
- [ ] Screen readers can access equations (MathML conversion)
- [ ] Students can right-click equations for LaTeX/MathML copy
- [ ] Equations scale properly with browser zoom
- [ ] All Greek letters and symbols display correctly

### **For Content Creators**
- [ ] Use `$variable$` for inline math in JSON
- [ ] Use `$$equation$$` for display math in JSON
- [ ] Include proper spacing: `$10\\,\\text{Hz}$`
- [ ] Test equations in Canvas before deploying to students
- [ ] Backup question databases regularly

---

## 🔗 Additional Resources

### **Canvas Documentation**
- [Canvas MathJax Support](https://community.canvaslms.com/docs/DOC-26701)
- [Canvas QTI Import Guide](https://community.canvaslms.com/docs/DOC-12947)

### **LaTeX References**
- [LaTeX Math Symbols](https://oeis.org/wiki/List_of_LaTeX_mathematical_symbols)
- [MathJax Documentation](https://docs.mathjax.org/en/latest/)

### **Accessibility**
- [MathML for Screen Readers](https://webaim.org/articles/mathml/)
- [Canvas Accessibility Features](https://community.canvaslms.com/docs/DOC-2061)

---

## 📞 Support & Troubleshooting

### **If Canvas Import Fails**
1. Run the test script to verify QTI format
2. Check Canvas error logs for specific issues
3. Verify mathematical expressions manually
4. Test with simplified questions first

### **If Math Doesn't Render**
1. Confirm Canvas MathJax is enabled
2. Check browser console for JavaScript errors
3. Verify delimiter conversion occurred properly
4. Test with different browsers

### **If Accessibility Issues Occur**
1. Verify MathML generation in browser inspector
2. Test with screen reader software
3. Confirm proper semantic structure
4. Check Canvas accessibility settings

---

**✅ Following these guidelines ensures reliable, accessible mathematical content in Canvas while maintaining clean, portable LaTeX in your question databases.**