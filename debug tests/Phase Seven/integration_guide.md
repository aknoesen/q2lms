# Refactored QTI Export System Integration Guide

## Overview

The QTI export system has been completely refactored from a monolithic `exporter.py` file into a modular, maintainable architecture. This guide shows how to integrate the new system with your existing Question Database Manager.

## New Module Structure

```
modules/
├── export/
│   ├── __init__.py
│   ├── data_processor.py       # Question data filtering and processing
│   ├── latex_converter.py      # LaTeX conversion for different systems
│   ├── qti_generator.py        # Core QTI XML generation
│   ├── canvas_adapter.py       # Canvas-specific optimizations
│   ├── export_ui.py           # Streamlit UI components
│   └── filename_utils.py       # Filename handling and validation
└── exporter.py                # Main interface (simplified)
```

## Key Benefits

1. **Custom Filename Support** ✅ - Users can now name their export files
2. **Modular Architecture** - Easy to debug and enhance individual components
3. **Better Error Handling** - Clear error messages and validation
4. **Canvas Optimization** - Specific adaptations for Canvas LMS
5. **Backward Compatibility** - Existing code continues to work

## Integration Steps

### Step 1: Update Your Import in `streamlit_app.py`

**Before:**
```python
from modules.exporter import create_qti_package, export_to_csv
```

**After (Recommended):**
```python
from modules.exporter import integrate_with_existing_ui
```

### Step 2: Replace Export Tab Content

**Before:**
```python
with tab_export:
    if st.session_state.df is not None:
        # Old export code...
        create_qti_package(df, original_questions, quiz_title)
    else:
        st.info("Please load a database first")
```

**After:**
```python
with tab_export:
    integrate_with_existing_ui(
        st.session_state.get('df'), 
        st.session_state.get('original_questions', [])
    )
```

### Step 3: Add New Export Directory

Create the new module structure:

```bash
mkdir -p modules/export
touch modules/export/__init__.py
```

Copy the refactored modules into the `modules/export/` directory.

## Usage Examples

### Basic Integration (Easiest)

```python
# In your streamlit_app.py export tab:
from modules.exporter import integrate_with_existing_ui

integrate_with_existing_ui(df, original_questions)
```

### Custom Export Interface

```python
from modules.exporter import render_export_interface

# More control over the interface
render_export_interface(filtered_df, original_questions)
```

### Quick Exports

```python
from modules.exporter import quick_csv_export, quick_qti_export

# Simple CSV export with custom naming
quick_csv_export(df, "midterm_questions")

# Simple QTI export with custom naming  
quick_qti_export(df, original_questions, "Midterm Exam")
```

### Legacy Compatibility

```python
# Existing code continues to work unchanged
from modules.exporter import create_qti_package, export_to_csv

create_qti_package(df, original_questions, "Quiz Title")
export_to_csv(df, "questions.csv")
```

## New Features

### 1. Custom Filename Input

Users can now specify their own filenames for exports:

- **Automatic validation** - Checks for invalid characters, length, reserved names
- **Smart suggestions** - Suggests filenames based on quiz title and question count
- **Cross-platform safety** - Ensures filenames work on Windows, Mac, and Linux

### 2. Enhanced Progress Indication

- **Step-by-step progress** - Shows what's happening during export
- **Better error messages** - Clear feedback when something goes wrong
- **Success confirmation** - Detailed information about successful exports

### 3. Canvas Optimization

- **LaTeX conversion** - Automatic conversion for Canvas MathJax compatibility
- **Question validation** - Checks for Canvas-specific requirements
- **Metadata enhancement** - Adds Canvas-specific package metadata

### 4. Export Preview

- **Data preview** - Shows what will be exported before creating files
- **Statistics display** - Question counts, points, LaTeX usage
- **Validation warnings** - Alerts about potential issues

## Troubleshooting

### Module Import Errors

If you get import errors, ensure:

1. The `modules/export/` directory exists
2. All `.py` files are in the correct location
3. `modules/export/__init__.py` exists (can be empty)

### Legacy Function Not Found

Some functions have been reorganized:

**Old Location → New Location:**
- `sanitize_filename` → `modules.export.filename_utils.sanitize_filename`
- `count_latex_questions` → `modules.export.latex_converter.count_latex_questions`
- `filter_and_sync_questions` → Now handled internally by `ExportDataManager`

### Canvas Import Issues

If Canvas imports fail:

1. Check that LaTeX expressions use proper delimiters (`$...$` or `$$...$$`)
2. Ensure question types are supported (`multiple_choice`, `numerical`, `true_false`, `fill_in_blank`)
3. Verify that correct answers are properly formatted

## Configuration Options

### Export Settings

Users can configure export behavior:

```python
from modules.export.export_ui import ExportConfigManager

config = ExportConfigManager()
settings = config.get_export_settings()

# Available settings:
# - add_timestamp: Add date/time to filenames
# - include_feedback: Include correct/incorrect feedback
# - canvas_compatibility: Optimize for Canvas LMS
# - preserve_latex: Convert LaTeX expressions
```

### Custom LaTeX Conversion

```python
from modules.export.latex_converter import LaTeXConverterFactory

# Create converter for specific target
converter = LaTeXConverterFactory.create_converter('canvas')
converted_text = converter.convert_for_canvas(latex_text)
```

## Testing the New System

### 1. Test CSV Export with Custom Filename

1. Load a question database
2. Go to Export tab
3. Choose "CSV Export"
4. Enter a custom filename
5. Verify validation feedback
6. Download and check the file

### 2. Test QTI Export with Custom Naming

1. Load questions with LaTeX
2. Choose "QTI Package for Canvas"
3. Enter quiz title and package name
4. Verify LaTeX analysis appears
5. Create package and test in Canvas

### 3. Test Error Handling

1. Try invalid filenames (test validation)
2. Export with no questions loaded
3. Export questions with missing data

## Migration Checklist

- [ ] Create `modules/export/` directory structure
- [ ] Copy new module files
- [ ] Update imports in `streamlit_app.py`
- [ ] Replace export tab content
- [ ] Test CSV export functionality
- [ ] Test QTI export functionality  
- [ ] Test filename validation
- [ ] Test Canvas import compatibility
- [ ] Verify backward compatibility
- [ ] Update any custom export code

## Support

If you encounter issues during migration:

1. Check the console for detailed error messages
2. Verify all module files are correctly placed
3. Test with the provided sample data first
4. Use the legacy compatibility functions if needed

The refactored system is designed to be drop-in compatible with your existing code while providing significant new functionality and improved maintainability.
