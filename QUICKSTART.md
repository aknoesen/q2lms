# Q2LMS Developer Quick Start Guide

Get up and running with Q2LMS development in under 10 minutes.

## 🚀 Quick Setup (5 minutes)

### Prerequisites Check
```bash
# Verify you have the essentials
python --version  # Should be 3.8+
git --version     # Any recent version
```

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/aknoesen/q2lms.git
cd q2lms

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application
```bash
# Start Q2LMS
streamlit run streamlit_app.py

# Should open http://localhost:8501 automatically
# If not, navigate there manually
```

### 3. Verify Installation
- ✅ Upload Interface loads
- ✅ Question Editor accessible
- ✅ Export Center functional
- ✅ No error messages in terminal

### 4. Test with Example Data
```bash
# Q2LMS includes sample data for testing
# Navigate to Upload Interface in the browser
# Upload: examples/sample_questions.json

# You should see sample questions load successfully
# Try editing a question in Question Editor
# Test export functionality with the sample data
```

**Quick Test Workflow:**
1. Go to **Upload Interface** tab
2. Click "Browse files" and select `examples/sample_questions.json`
3. Upload and verify questions appear
4. Switch to **Question Editor** to see loaded questions
5. Try **Export Center** to generate a test export

---

## 🛠️ Development Setup (Additional 5 minutes)

### Install Development Tools
```bash
# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Or if requirements-dev.txt exists:
pip install -r requirements-dev.txt
```

### Configure Your IDE

**VS Code (Recommended)**
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

**PyCharm**
- Set interpreter to `./venv/bin/python`
- Enable Black formatter
- Configure pytest as test runner

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov=utilities

# Should see all tests passing ✅
```

---

## 🎯 Your First Contribution (15 minutes)

### Option 1: Fix a Simple Bug
1. Check [GitHub Issues](https://github.com/aknoesen/q2lms/issues) for "good first issue" labels
2. Create branch: `git checkout -b fix/issue-description`
3. Make changes and test
4. Submit pull request

### Option 2: Add a New Question Type
Follow this pattern for a simple True/False question variant:

```python
# 1. Create question type (utilities/question_types.py)
class YesNoQuestion(Question):
    """Yes/No question (True/False variant)"""
    
    def __init__(self, question_data: Dict):
        super().__init__(question_data)
        self.type = "yes_no"
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if len(self.answers) != 2:
            errors.append("Yes/No questions must have exactly 2 answers")
        return errors

# 2. Add UI component (modules/question_editor.py)
def render_yes_no_editor(question: YesNoQuestion):
    """Render Yes/No question editor"""
    question.text = st.text_area("Question Text", value=question.text)
    
    # Yes/No answers
    col1, col2 = st.columns(2)
    with col1:
        yes_correct = st.checkbox("Yes is correct", value=question.answers[0].correct if question.answers else False)
    with col2:
        no_correct = st.checkbox("No is correct", value=question.answers[1].correct if question.answers else False)
    
    # Update answers
    question.answers = [
        Answer({"text": "Yes", "correct": yes_correct}),
        Answer({"text": "No", "correct": no_correct})
    ]

# 3. Register in question_manager.py
QUESTION_TYPES = {
    "multiple_choice": MultipleChoiceQuestion,
    "true_false": TrueFalseQuestion,
    "yes_no": YesNoQuestion,  # Add this line
    # ... other types
}
```

### Option 3: Improve Documentation
1. Pick a function missing docstrings
2. Add comprehensive documentation
3. Include usage examples

---

## 📁 Key Files to Know

### Core Application
- `streamlit_app.py` - Main entry point
- `modules/upload_interface_v2.py` - File upload handling
- `modules/question_editor.py` - Question editing UI
- `modules/export/` - Export system

### Example Data & Testing
- `examples/sample_questions.json` - Sample question database for testing
- `examples/templates/` - Export templates (if available)
- `examples/test_data/` - Additional test datasets

### Utilities
- `utilities/json_handler.py` - JSON processing
- `utilities/latex_processor.py` - LaTeX handling
- `utilities/validation.py` - Data validation

### Configuration
- `requirements.txt` - Dependencies

---

## 🧪 Testing Your Changes

### Quick Test Commands
```bash
# Format code
black modules/ utilities/ tests/

# Check style
flake8 modules/ utilities/ tests/

# Run specific test
pytest tests/test_questions.py -v

# Test upload functionality
pytest tests/test_upload.py -v

# Manual testing
streamlit run streamlit_app.py
```

### Test Your Changes Checklist
- [ ] Code follows style guidelines (`black` and `flake8` pass)
- [ ] All existing tests still pass
- [ ] New functionality has tests
- [ ] Manual testing in browser works
- [ ] No console errors when running

---

## 🚀 Common Development Tasks

### Adding a New Export Format

**Quick Template:**
```python
# 1. Create exporter (modules/export/my_format_exporter.py)
from .export_base import ExportBase

class MyFormatExporter(ExportBase):
    def export(self, questions: List[Question], options: Dict) -> bytes:
        # Your export logic here
        return exported_data.encode('utf-8')
    
    def get_file_extension(self) -> str:
        return ".myformat"
    
    def validate_questions(self, questions: List[Question]) -> List[str]:
        return []  # Add validation logic

# 2. Register in modules/export/__init__.py
from .my_format_exporter import MyFormatExporter

AVAILABLE_EXPORTERS = {
    'qti': QTIExporter,
    'json': JSONExporter,
    'csv': CSVExporter,
    'myformat': MyFormatExporter,  # Add this
}

# 3. Add to UI (modules/export_center.py)
export_formats = ['QTI Package', 'JSON', 'CSV', 'My Format']  # Add to list
```

### Debugging Common Issues

**Streamlit Rerun Issues:**
```python
# Use st.rerun() instead of st.experimental_rerun()
if st.button("Refresh"):
    st.rerun()
```

**Session State Problems:**
```python
# Always initialize before use
if 'my_data' not in st.session_state:
    st.session_state.my_data = []
```

**LaTeX Not Rendering:**
```python
# Enable LaTeX in Streamlit
st.markdown("$x^2 + y^2 = z^2$")  # Inline math
st.latex("x^2 + y^2 = z^2")      # Display math
```

---

## 📝 Development Workflow

### Daily Development
```bash
# 1. Start your day
git pull origin main
source venv/bin/activate

# 2. Create feature branch
git checkout -b feature/my-awesome-feature

# 3. Develop with live reload
streamlit run streamlit_app.py --server.runOnSave true

# 4. Test frequently
pytest tests/

# 5. Format and check
black . && flake8

# 6. Commit and push
git add .
git commit -m "feat: add awesome feature"
git push origin feature/my-awesome-feature
```

### Before Submitting PR
```bash
# Final checklist
pytest --cov=modules --cov=utilities  # All tests pass
black modules/ utilities/ tests/       # Code formatted
flake8 modules/ utilities/ tests/      # Style check passes
python -m streamlit run streamlit_app.py  # Manual test
```

---

## 🔧 Useful Development Tools

### VS Code Extensions
- Python (Microsoft)
- Black Formatter
- Streamlit Snippets
- GitLens

### Browser Tools
- **Streamlit Developer Tools**: Enable in browser dev tools
- **Console Debugging**: Check browser console for JavaScript errors
- **Network Tab**: Monitor file upload/download

### Command Line Helpers
```bash
# Watch for file changes
pip install watchdog
watchmedo auto-restart --patterns="*.py" --recursive -- streamlit run streamlit_app.py

# Database inspection (if using SQLite)
sqlite3 database.db ".tables"

# Performance monitoring
pip install memory-profiler
python -m memory_profiler your_script.py
```

---

## 🆘 Getting Help

### Quick References
- **Full Developer Docs**: See `DEVELOPER.md` for comprehensive guide
- **User Guide**: `USERGUIDE.md` for understanding user workflows
- **API Reference**: `API.md` for function documentation

### Debugging Steps
1. **Check Console**: Look for Python errors in terminal
2. **Browser Console**: Check for JavaScript errors
3. **Session State**: Use debug utilities to inspect state
4. **Restart**: Sometimes `Ctrl+C` and restart fixes issues

### Community Support
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community help
- **Code Review**: Submit draft PRs for early feedback

---

## 🎉 You're Ready!

You now have:
- ✅ Working Q2LMS development environment
- ✅ Understanding of key files and structure
- ✅ Knowledge of common development tasks
- ✅ Testing and debugging tools
- ✅ Clear workflow for contributions

### Next Steps
1. **Explore the codebase**: Read through key modules
2. **Try the example tasks**: Add a question type or export format
3. **Pick your first issue**: Check GitHub for beginner-friendly tasks
4. **Join the community**: Engage in discussions and code reviews

**Happy coding! 🚀**

---

*Need more detailed information? Check the full [Developer Documentation](DEVELOPER.md) for comprehensive guides on architecture, testing, and advanced development topics.*