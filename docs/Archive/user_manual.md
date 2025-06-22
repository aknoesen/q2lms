# Question Database Manager - User Manual

## 📚 Table of Contents
1. [Getting Started](#getting-started)
2. [System Overview](#system-overview)
3. [Creating Questions](#creating-questions)
4. [Managing Your Database](#managing-your-database)
5. [Exporting to Canvas](#exporting-to-canvas)
6. [LaTeX Mathematical Notation](#latex-mathematical-notation)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Advanced Features](#advanced-features)

---

## 🚀 Getting Started

### System Requirements
- **Web Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Canvas LMS**: Any recent version with QTI import capability
- **File Access**: Ability to upload/download files from your computer

### First Launch
1. **Start the Application**: Open your web browser and navigate to the application URL
2. **Upload Your Question Database**: Use the file uploader to select your JSON question file
3. **Review Questions**: Browse through your questions using the interface
4. **Export When Ready**: Generate Canvas-compatible QTI packages

### Quick Start Checklist ✅
- [ ] Question database file is in JSON format
- [ ] Mathematical expressions use proper LaTeX syntax (`$...$` for inline, `$$...$$` for display)
- [ ] Canvas course is ready to receive QTI imports
- [ ] You have instructor permissions in Canvas

---

## 🏗️ System Overview

### Core Components

#### **Question Database (JSON)**
- **Purpose**: Central repository for all questions
- **Format**: Structured JSON with standardized fields
- **LaTeX Support**: Full mathematical notation support
- **Portability**: Compatible with other systems and LLMs

#### **Web Interface**
- **Purpose**: Browse, filter, edit, and export questions
- **Features**: Real-time preview, search/filter, bulk operations
- **User-Friendly**: No technical knowledge required
- **Responsive**: Works on desktop and tablet devices

#### **QTI Exporter**
- **Purpose**: Generate Canvas-compatible quiz packages
- **Canvas Integration**: Automatic LaTeX conversion for Canvas MathJax
- **Quality Assurance**: Built-in validation and error checking
- **Standards Compliant**: Follows IMS QTI 1.2 specification

### Architecture Flow
```
JSON Database → Web Interface → Canvas QTI Export
     ↓              ↓               ↓
   Storage      Edit/Filter      Import to Canvas
```

---

## 📝 Creating Questions

### Supported Question Types

#### **Multiple Choice**
Perfect for concept testing and quick assessments.

**Example:**
```json
{
  "type": "multiple_choice",
  "title": "Ohm's Law Application",
  "question_text": "For a circuit with $R = 100\\,\\Omega$ and $I = 2\\,\\text{A}$, what is the voltage?",
  "choices": [
    "$V = 200\\,\\text{V}$",
    "$V = 50\\,\\text{V}$", 
    "$V = 100\\,\\text{V}$",
    "$V = 300\\,\\text{V}$"
  ],
  "correct_answer": "$V = 200\\,\\text{V}$",
  "points": 2
}
```

#### **Numerical Answer**
Ideal for calculations with tolerance ranges.

**Example:**
```json
{
  "type": "numerical",
  "title": "Frequency Calculation",
  "question_text": "Calculate frequency in Hz using $f = \\frac{\\omega}{2\\pi}$ where $\\omega = 628\\,\\text{rad/s}$",
  "correct_answer": "100",
  "tolerance": 1,
  "points": 3
}
```

#### **True/False**
Simple binary questions for quick concept checks.

**Example:**
```json
{
  "type": "true_false",
  "title": "Phase Relationship",
  "question_text": "A phase difference of $\\pi/2$ radians equals $90°$",
  "correct_answer": "True",
  "points": 1
}
```

#### **Fill in the Blank**
Text-based answers for definitions and short responses.

**Example:**
```json
{
  "type": "fill_in_blank",
  "title": "Unit Definition",
  "question_text": "The SI unit for electrical resistance is the _____",
  "correct_answer": "ohm",
  "points": 1
}
```

### Required Fields
- **`id`**: Unique identifier (e.g., "Q_00001")
- **`type`**: Question type (see above)
- **`title`**: Brief descriptive title
- **`question_text`**: The actual question content
- **`correct_answer`**: Correct response
- **`points`**: Point value for scoring

### Optional Fields
- **`choices`**: Array of answer options (for multiple choice)
- **`tolerance`**: Acceptable range for numerical answers
- **`feedback_correct`**: Message shown for correct answers
- **`feedback_incorrect`**: Message shown for incorrect answers
- **`topic`**: Subject area classification
- **`subtopic`**: More specific classification
- **`difficulty`**: Easy, Medium, Hard
- **`image_file`**: Associated image files (future feature)

---

## 🗂️ Managing Your Database

### Uploading Your Question File
1. **Click the Upload Button**: Look for "Upload Question Database" or similar
2. **Select Your JSON File**: Browse to your question database file
3. **Wait for Processing**: The system will validate and load your questions
4. **Review Results**: Check for any validation errors or warnings

### Browsing Questions
- **Navigation**: Use pagination controls to browse through questions
- **Search**: Find specific questions using the search box
- **Filter**: Narrow down by topic, difficulty, or question type
- **Preview**: See how questions will appear to students

### Editing Questions
- **In-Place Editing**: Click on question fields to edit directly
- **LaTeX Preview**: Mathematical expressions update in real-time
- **Auto-Save**: Changes are preserved automatically
- **Validation**: System checks for errors as you edit

### Quality Control
- **Duplicate Detection**: System identifies potential duplicate questions
- **Validation Checks**: Ensures all required fields are complete
- **LaTeX Verification**: Confirms mathematical notation is properly formatted
- **Point Totals**: Calculates total points for exported quizzes

---

## 🎯 Exporting to Canvas

### Pre-Export Checklist
- [ ] All desired questions are selected
- [ ] Mathematical expressions are properly formatted
- [ ] Point values are assigned
- [ ] Feedback messages are complete

### Export Process
1. **Select Questions**: Use filters or checkboxes to choose questions
2. **Choose Export Options**: Set quiz title and preferences
3. **Generate QTI Package**: Click "Create QTI Package" button
4. **Download File**: Save the generated .zip file to your computer
5. **Import to Canvas**: Upload the QTI package to your Canvas course

### Canvas Import Steps
1. **Navigate to Quizzes**: In your Canvas course, go to Quizzes section
2. **Import Quiz**: Click "Import Quiz" or similar option
3. **Upload File**: Select your downloaded QTI .zip file
4. **Review Import**: Check Canvas import results
5. **Publish Quiz**: Make the quiz available to students when ready

### Expected Results
- ✅ **Clean Import**: No errors or warnings in Canvas
- ✅ **Proper Math Rendering**: LaTeX expressions display correctly
- ✅ **Correct Scoring**: Point values and answer keys work properly
- ✅ **Accessibility**: Screen readers can access mathematical content

---

## 🧮 LaTeX Mathematical Notation

### Why LaTeX Matters
Mathematical notation is essential for STEM courses. Our system uses LaTeX, the gold standard for mathematical typesetting, ensuring:
- **Professional Appearance**: Equations look publication-quality
- **Accessibility**: Screen readers can interpret mathematical content
- **Portability**: Content works across different platforms
- **Precision**: Complex expressions are clearly communicated

### Basic LaTeX Syntax

#### **Inline Math** (within text)
Use single dollar signs: `$expression$`

**Examples:**
- Variables: `$x$`, `$y$`, `$z$`
- Simple equations: `$E = mc^2$`
- With units: `$f = 60\\,\\text{Hz}$`

#### **Display Math** (centered, standalone)
Use double dollar signs: `$$expression$$`

**Examples:**
- `$$V = IR$$`
- `$$f = \\frac{1}{2\\pi\\sqrt{LC}}$$`

#### **Common Mathematical Elements**

| Element | LaTeX Code | Displays As |
|---------|------------|-------------|
| Subscript | `$V_{rms}$` | V_rms |
| Superscript | `$x^2$` | x² |
| Fraction | `$\\frac{a}{b}$` | a/b |
| Square root | `$\\sqrt{x}$` | √x |
| Greek letters | `$\\omega, \\pi, \\Omega$` | ω, π, Ω |
| Infinity | `$\\infty$` | ∞ |
| Plus/minus | `$\\pm$` | ± |
| Multiplication | `$\\times$` | × |
| Degrees | `$90^\\circ$` | 90° |

#### **Units and Spacing**
Always include proper spacing before units:
- ✅ Correct: `$10\\,\\text{Hz}$`
- ❌ Wrong: `$10Hz$`

#### **Complex Expressions**
```latex
$Z = R + j\\omega L$               // Complex impedance
$P = \\frac{V^2}{R}$              // Power calculation  
$\\sin(\\omega t + \\phi)$         // Sinusoidal function
$\\vec{F} = m\\vec{a}$            // Vector notation
```

### LaTeX Best Practices
1. **Always use dollar signs** in your JSON database
2. **Include spacing** with `\\,` before units
3. **Test complex expressions** in the preview
4. **Use descriptive variable names** when possible
5. **Double-check** Greek letters and special symbols

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### **File Upload Problems**
**Symptom**: "Invalid file format" or upload fails
**Solutions**:
- Ensure file is valid JSON format
- Check file isn't corrupted
- Verify file size isn't too large
- Use a JSON validator to check syntax

#### **Math Not Rendering**
**Symptom**: LaTeX code appears as text instead of equations
**Solutions**:
- Check for unmatched dollar signs (`$`)
- Verify proper LaTeX syntax
- Use `\\` for backslashes in JSON
- Test in preview mode before exporting

#### **Canvas Import Errors**
**Symptom**: "1 issues" or import warnings in Canvas
**Solutions**:
- Check for missing required fields
- Verify point values are numbers, not text
- Ensure choice options are complete
- Review feedback messages for completeness

#### **Questions Not Appearing**
**Symptom**: Exported quiz has fewer questions than expected
**Solutions**:
- Check filter settings aren't excluding questions
- Verify all questions have required fields
- Review selection criteria
- Check for duplicate IDs

### Diagnostic Tools
The system includes built-in diagnostic tools:
- **Validation Checker**: Identifies missing or invalid fields
- **LaTeX Validator**: Confirms mathematical expressions are correct
- **Export Preview**: Shows exactly what will be sent to Canvas
- **Error Logger**: Detailed error messages for troubleshooting

---

## 💡 Best Practices

### Question Writing Guidelines

#### **Clear and Concise**
- Keep question text focused and unambiguous
- Avoid unnecessary complexity
- Use consistent terminology throughout

#### **Appropriate Difficulty**
- Match question difficulty to learning objectives
- Provide scaffolding for complex concepts
- Include a range of difficulty levels

#### **Effective Distractors** (for multiple choice)
- Create plausible incorrect answers
- Base distractors on common student errors
- Avoid obviously incorrect options

#### **Meaningful Feedback**
- Explain why answers are correct or incorrect
- Reference relevant concepts or formulas
- Provide hints for further learning

### Database Organization

#### **Consistent Naming**
- Use descriptive, consistent question IDs
- Organize by topic and subtopic
- Include difficulty levels in metadata

#### **Version Control**
- Keep backup copies of your database
- Document major changes
- Use clear file naming conventions

#### **Regular Maintenance**
- Review and update questions regularly
- Remove outdated or problematic questions
- Add new questions as curriculum evolves

### Canvas Integration

#### **Test Before Deployment**
- Always test import in a sandbox course first
- Verify mathematical expressions render correctly
- Check that scoring works as expected
- Review accessibility features

#### **Student Experience**
- Consider question order and flow
- Provide clear instructions
- Set appropriate time limits
- Include helpful feedback

---

## 🎓 Advanced Features

### Bulk Operations
- **Mass Edit**: Update multiple questions simultaneously
- **Batch Export**: Create multiple quiz versions
- **Template Application**: Apply consistent formatting across questions

### Integration Options
- **LLM Compatibility**: Question format works with AI content generation
- **Export Formats**: Support for multiple LMS platforms (future)
- **Analytics Integration**: Track question performance over time

### Customization
- **Themes**: Adjust interface appearance
- **Workflows**: Customize export processes
- **Validation Rules**: Set institution-specific requirements

### Quality Assurance
- **Automated Testing**: Built-in checks for common issues
- **Performance Metrics**: Track system usage and efficiency
- **Update Notifications**: Stay informed about new features

---

## 📞 Support and Resources

### Getting Help
- **Built-in Help**: Hover tooltips and contextual guidance
- **Documentation**: This manual and additional resources
- **Community**: User forums and discussion groups
- **Technical Support**: Contact information for urgent issues

### Additional Resources
- **Canvas Documentation**: Official Canvas QTI import guides
- **LaTeX References**: Mathematical notation resources
- **Best Practices**: Educational assessment guidelines
- **Updates**: System changelog and new features

### Training and Development
- **Video Tutorials**: Step-by-step walkthroughs
- **Workshops**: Institution-specific training sessions
- **Certification**: Proficiency validation programs
- **Advanced Training**: Power-user techniques and tips

---

## 📋 Quick Reference

### Keyboard Shortcuts
- **Ctrl+S**: Save current changes
- **Ctrl+F**: Search questions
- **Ctrl+E**: Export selected questions
- **Esc**: Cancel current operation

### File Formats
- **Input**: JSON (.json)
- **Output**: QTI Package (.zip)
- **Backup**: JSON (.json.bak)

### System Limits
- **Questions per database**: 10,000+
- **File size**: 100MB maximum
- **Export batch size**: 500 questions
- **Mathematical complexity**: No practical limits

---

**🎯 This manual covers the essential information for effective use of the Question Database Manager. For additional support or advanced topics, consult the supplementary documentation or contact your system administrator.**