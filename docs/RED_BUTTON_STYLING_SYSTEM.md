# Q2LMS Red Button Styling System

## Overview
This document describes the centralized red button styling system implemented for Q2LMS to provide consistent, visually appealing action buttons throughout the application.

## Button Types and Usage

### 1. Primary Action (`primary-action`)
**Purpose**: Main workflow actions that users are expected to take
**Styling**: Solid red background with gradient (#dc3545 to #c82333)
**Examples**:
- Export buttons
- Save operations
- Continue/Next actions
- Active tab navigation

```python
AppConfig.create_red_button("📦 Create QTI Package", "primary-action", "export_btn")
```

### 2. Secondary Action (`secondary-action`)
**Purpose**: Supporting actions that complement primary actions
**Styling**: White background with red outline (#dc3545 border)
**Examples**:
- Change mode buttons
- Alternative options
- Inactive tab navigation
- Edit/Modify actions

```python
AppConfig.create_red_button("🔄 Change Mode", "secondary-action", "change_mode_btn")
```

### 3. Destructive Action (`destructive-action`)
**Purpose**: Actions that remove, delete, or exit
**Styling**: Dark red gradient (#a71e2a to #8b1a1a)
**Examples**:
- Exit application
- Delete operations
- Clear/Reset actions

```python
AppConfig.create_red_button("🚪 Exit Application", "destructive-action", "exit_btn")
```

### 4. Confirmation Action (`confirmation-action`)
**Purpose**: Critical actions requiring user confirmation
**Styling**: Bright red with emphasis (#ff1744 to #d50000), larger size
**Examples**:
- Final confirmations
- Critical save operations
- Irreversible actions

```python
AppConfig.create_red_button("✅ Confirm Export", "confirmation-action", "confirm_btn")
```

## Implementation Details

### CSS Classes
The styling system uses CSS attribute selectors to target buttons with specific `data-q2lms-type` attributes:

```css
.stButton > button[data-q2lms-type="primary-action"] {
    background: linear-gradient(135deg, #dc3545, #c82333) !important;
    color: white !important;
    font-weight: bold !important;
    /* Additional styling... */
}
```

### JavaScript Integration
Buttons are styled using JavaScript that runs after Streamlit renders the button:

```javascript
setTimeout(function() {
    const button = document.querySelector('[data-testid="baseButton-{key}"]');
    if (button) {
        button.setAttribute('data-q2lms-type', '{button_type}');
    }
}, 100);
```

### Usage in Code

#### Method 1: Using AppConfig.create_red_button() (Recommended)
```python
from .app_config import AppConfig

# Primary action button
if AppConfig.create_red_button("Save Changes", "primary-action", "save_btn", use_container_width=True):
    # Handle button click
    save_changes()
```

#### Method 2: Using AppConfig.apply_red_button_styling() (Manual)
```python
# Create standard Streamlit button
if st.button("Save Changes", key="save_btn", use_container_width=True):
    save_changes()

# Apply red styling
styling_script = AppConfig.apply_red_button_styling("primary-action", "save_btn")
st.markdown(styling_script, unsafe_allow_html=True)
```

## Color Palette

| Button Type | Primary Color | Hover Color | Border | Purpose |
|-------------|---------------|-------------|---------|---------|
| Primary Action | #dc3545 | #c82333 | #bd2130 | Main actions |
| Secondary Action | #dc3545 (border) | #ffeaea (bg) | #dc3545 | Supporting actions |
| Destructive Action | #a71e2a | #8b1a1a | #721c24 | Delete/Exit actions |
| Confirmation Action | #ff1744 | #d50000 | #b71c1c | Critical confirmations |

## Features

### Hover Effects
- **Elevation**: Buttons lift up on hover (`translateY(-2px)`)
- **Shadow**: Enhanced box shadows for depth
- **Color Shift**: Gradient transitions for visual feedback

### Responsive Design
- **Container Width**: All buttons support `use_container_width=True`
- **Minimum Height**: Consistent 45-50px height for touch accessibility
- **Font Scaling**: Responsive font sizes

### Accessibility
- **High Contrast**: Red colors meet WCAG contrast requirements
- **Focus States**: Clear focus indicators for keyboard navigation
- **Disabled States**: Proper disabled styling with reduced opacity

## Implementation Status

### ✅ Completed Files
- `modules/app_config.py` - Core styling system
- `modules/ui_manager.py` - Main interface buttons

### 🔄 Pending Files
- `modules/upload_interface_v2.py`
- `modules/exporter.py`
- `modules/interface_select_questions.py`
- `modules/interface_delete_questions.py`
- `modules/operation_mode_manager.py`
- `modules/question_editor.py`

## Migration Guide

### Converting Existing Buttons

#### Before (Standard Streamlit)
```python
if st.button("Save Changes", type="primary", key="save_btn"):
    save_changes()
```

#### After (Red Styling System)
```python
if AppConfig.create_red_button("Save Changes", "primary-action", "save_btn"):
    save_changes()
```

### Button Type Mapping
- `type="primary"` → `"primary-action"`
- `type="secondary"` → `"secondary-action"`
- Exit/Delete buttons → `"destructive-action"`
- Critical confirmations → `"confirmation-action"`

## Best Practices

1. **Consistent Naming**: Use descriptive button keys (`save_changes_btn` not `btn1`)
2. **Appropriate Types**: Match button type to action semantics
3. **Container Width**: Use `use_container_width=True` for layout consistency
4. **Error Handling**: Always handle button click events properly
5. **Visual Hierarchy**: Use primary-action sparingly to maintain emphasis

## Troubleshooting

### Common Issues

#### Styling Not Applied
- **Cause**: JavaScript timing issue
- **Solution**: Increase timeout in `apply_red_button_styling()`

#### Button Not Responding
- **Cause**: Duplicate keys or session state conflicts
- **Solution**: Use unique keys and check session state

#### Layout Issues
- **Cause**: Missing container width or column structure
- **Solution**: Use proper Streamlit layout components

### Debug Mode
Enable debug mode to see styling application:

```python
# In streamlit_app.py
if st.checkbox("Debug Red Buttons"):
    st.write("Button styling debug info...")
```

## Future Enhancements

1. **Theme Support**: Light/Dark theme variations
2. **Size Variants**: Small, medium, large button sizes
3. **Icon Integration**: Better emoji/icon positioning
4. **Animation**: More sophisticated hover animations
5. **Custom Colors**: Per-module color customization
