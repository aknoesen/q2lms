# Q2LMS - Question Database Manager

**Professional question database management and LMS integration platform for educational institutions.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.20+-red.svg)](https://streamlit.io)


## 🚀 Quick Start

```bash
# Clone and run
git clone https://github.com/your-username/q2lms.git
cd q2lms
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[User Guide](docs/README.md)** | Complete installation and usage guide | Instructors & End Users |
| **[API Reference](docs/API.md)** | Developer integration guide | Developers & IT Staff |
| **[Deployment Guide](docs/DEPLOYMENT.md)** | Production deployment manual | System Administrators |

## ✨ Key Features

- **📤 Smart Upload System**: Single and multi-file processing with conflict resolution
- **🔧 Live Question Editor**: Real-time LaTeX preview and editing
- **📊 Analytics Dashboard**: Question distribution and performance insights  
- **🎯 Multi-Format Export**: Canvas QTI, native JSON, and CSV with LaTeX preservation
- **🧮 LaTeX Excellence**: Full mathematical notation with automatic optimization
- **🔄 Complete Workflow**: JSON export/import for version control and collaboration

## 🏗️ Architecture

Q2LMS follows a modular design:

```
streamlit_app.py          # Main application
├── modules/              # Core functionality
│   ├── upload_interface_v2.py    # File processing
│   ├── question_editor.py        # Question editing
│   ├── export/                   # Multi-format export system
│   │   ├── qti_generator.py      # Canvas QTI packages
│   │   ├── json_exporter.py      # Native JSON format
│   │   └── csv_exporter.py       # Data analysis exports
│   └── ...
├── utilities/            # Helper functions
├── examples/             # Sample data
└── docs/                 # Complete documentation
```

## 🎓 For Educators

Transform your question creation workflow:
1. **Upload** JSON question databases (single or multiple files)
2. **Edit** questions with live LaTeX preview
3. **Export** in multiple formats:
   - **Canvas QTI** packages for LMS deployment
   - **Native JSON** for backup and version control  
   - **CSV files** for data analysis
4. **Deploy** to any QTI-compatible LMS or re-import for collaboration

## 🔧 For Developers

Extend Q2LMS capabilities:
- **Modular Architecture**: Clean separation of concerns
- **API Documentation**: Complete function references
- **Extension Points**: Custom question types and export formats
- **Testing Framework**: Comprehensive test suite
- **JSON API**: Full-fidelity data export and import

## 🚀 Deployment Options

- **Development**: Local Python environment
- **Department**: Streamlit Cloud or Docker
- **Enterprise**: Kubernetes with full monitoring
- **Institution**: Cloud platforms (AWS, Azure, GCP)

## 📋 Requirements

- Python 3.8+
- Modern web browser
- 2GB RAM (4GB recommended for production)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! See our documentation for:
- Development setup instructions
- Code style guidelines  
- Testing procedures
- Submission process

## 📞 Support

- **Documentation**: [Complete guides](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/q2lms/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/q2lms/discussions)

---

**Built for educators by educators** 

# Updates from docs_readme_updates.md

# docs/README.md Update Instructions

## 1. Update Table of Contents

**Location**: Update the existing table of contents to include Phase 8 sections:

```markdown
### Table of Contents
1. [Overview](#overview)
2. [Quick Start Guide](#quick-start-guide)
3. [Installation](#installation)
4. [Core Features](#core-features)
5. [Upload System](#upload-system)
6. [Question Management](#question-management)
7. [Advanced Filtering Features](#advanced-filtering-features) <!-- NEW -->
8. [Professional Session Management](#professional-session-management) <!-- NEW -->
9. [Export System](#export-system)
10. [LaTeX Support](#latex-support)
11. [LMS Integration](#lms-integration)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)
14. [Advanced Features](#advanced-features)
```

## 2. Update "Quick Start Guide" Section

**Location**: In the "First-Time User Workflow", update Step 3:

```markdown
**Step 3: Quality Control and Advanced Filtering**
- Browse questions using the "Browse & Edit" tab
- **NEW: Use multi-topic filtering** to select questions from multiple topics simultaneously
- Filter by combinations like "Circuit Analysis" + "MATLAB Programming" for cross-disciplinary content
- Use enhanced filtering for comprehensive course planning
- Verify LaTeX rendering appears correctly
- Make any necessary edits using the live editor
- **NEW: Use professional exit** when planning sessions are complete to safely preserve work
```

## 3. Update "Core Features" Section

**Location**: Add new subsection after "Database Analytics":

```markdown
### Enhanced Multi-Topic Filtering (Phase 8)

Q2LMS now supports sophisticated multi-topic question filtering for comprehensive course planning:

**Advanced Topic Selection**:
- Select multiple topics simultaneously using OR logic
- Cross-disciplinary question curation (e.g., "MATLAB Programming" + "Numerical Methods" + "Circuit Analysis")
- Visual feedback showing "X of Y topics selected"
- Easy topic management with selection/deselection controls

**Course Planning Applications**:
- **Comprehensive Exams**: Combine multiple engineering topics for broad assessments
- **Cross-Topic Labs**: Mix "MATLAB Programming" + "Numerical Methods" for coding exercises
- **Modular Course Design**: Build topic-specific question banks efficiently
- **Integrated Learning**: Combine theory + practical topics for comprehensive coverage

### Professional Session Management (Phase 8)

**Graceful Exit System**:
- Prominent "Exit Q2LMS" button in sidebar for clean application shutdown
- Comprehensive exit interface showing current work and session information
- Data backup options before exit to prevent loss of filtered question sets
- Session cleanup and resource management for long planning sessions
- Professional confirmation dialogs and clear next-step guidance
```

## 4. Add New Major Section: "Advanced Filtering Features"

**Location**: Add as new section after "Question Management":

```markdown
## Advanced Filtering Features

### Multi-Topic Question Selection

Q2LMS Phase 8 introduces powerful multi-topic filtering capabilities designed for comprehensive course planning and cross-disciplinary assessments.

#### Accessing Multi-Topic Filtering

1. **Location**: Find the topic filter in the left sidebar, positioned above difficulty and type filters
2. **Interface**: Use the multi-select dropdown labeled "Select Topics"
3. **Feedback**: See "X of Y topics selected" confirmation message with color-coded status

#### Using Multi-Topic Filters

**Basic Multi-Topic Selection**:
1. Click the topic dropdown in the sidebar
2. Select multiple topics by clicking each desired option
3. Questions from ANY selected topic will appear (OR logic)
4. Use existing difficulty/type filters for further refinement
5. Clear selections by deselecting topics or using "Clear All" option

**Advanced Filtering Combinations**:
- **Topic + Difficulty**: Select "Circuit Analysis" + "Numerical Methods" + filter by "Medium" difficulty
- **Topic + Type**: Choose multiple topics + filter by "multiple_choice" questions only
- **Complete Filtering**: Combine topic, difficulty, and type filters for precise question sets

#### Practical Course Planning Examples

**Comprehensive Electrical Engineering Exam**:
- Select: "Circuit Analysis" + "Complex Numbers" + "Phasors" + "Impedance"
- Result: Questions covering all fundamental EE concepts for comprehensive assessment
- Use Case: Final exam spanning multiple course modules

**MATLAB Programming Lab**:
- Select: "MATLAB Programming" + "Numerical Methods" + "Linear Algebra"
- Result: Questions combining programming skills with mathematical applications
- Use Case: Hands-on lab assessment integrating coding and math

**Cross-Disciplinary Assessment**:
- Select: "Theory" + "Applications" + "Problem Solving"
- Result: Questions spanning theoretical knowledge and practical application
- Use Case: Assessment measuring both understanding and application skills

**Modular Quiz Creation**:
- Select: "Circuit Analysis" + "MATLAB Programming" for Week 5 quiz
- Select: "Linear Algebra" + "Numerical Methods" for Week 8 quiz
- Result: Topic-specific assessments aligned with course schedule

#### Benefits for Instructors

- **Efficient Course Planning**: Quickly curate questions for specific learning objectives
- **Comprehensive Coverage**: Ensure balanced representation across course topics
- **Flexible Assessment**: Create exams tailored to specific needs without manual sorting
- **Time Savings**: Eliminate manual question-by-question selection
- **Cross-Disciplinary Integration**: Build assessments that span multiple knowledge areas

#### Visual Feedback and Status

**Selection Indicators**:
- Topic count display: "3 of 12 topics selected"
- Color-coded status messages (green for successful selection)
- Real-time question count updates as selections change
- Clear indication of active filter combinations

**Filter Management**:
- Easy deselection of individual topics
- "Clear All" option for quick reset
- Persistent selections during browsing session
- Integration with existing filter controls
```

## 5. Add New Major Section: "Professional Session Management"

**Location**: Add as new section after "Advanced Filtering Features":

```markdown
## Professional Session Management

### Graceful Exit System

Q2LMS includes a professional exit system designed for educational environments requiring clean session management and data preservation.

#### Understanding Session Management

**Session Tracking**:
- Automatic session start time recording
- Duration tracking for planning activities
- Current work state monitoring
- Resource usage awareness

**Professional Environment Needs**:
- Clean application shutdown for shared computers
- Data preservation for interrupted sessions
- Resource cleanup for system performance
- Professional user experience in educational settings

#### Accessing the Exit Interface

1. **Location**: Find "Exit Q2LMS" button at the bottom of the left sidebar
2. **Section**: Located under "Application" heading for clear organization
3. **Availability**: Always accessible during active sessions
4. **Styling**: Prominent button design for easy identification

#### Complete Exit Process

**Step 1: Initiate Exit**
- Click the "Exit Q2LMS" button in the sidebar
- System immediately transitions to comprehensive exit interface
- Previous interface is replaced with exit workflow

**Step 2: Review Session Information**
The exit interface displays comprehensive session details:
- **Session Duration**: Total time spent in current session
- **Start Time**: When the current session began
- **Questions Loaded**: Number of questions in current database
- **Active Filters**: Current multi-topic and other filter selections
- **Recent Activity**: Summary of work completed during session

**Step 3: Data Preservation Options**
- **Quick JSON Export**: Download current filtered question set as backup
- **Filter Settings Summary**: Review current filter configurations for future reference
- **Session Summary**: Complete overview of work completed
- **Backup Recommendations**: Suggestions for preserving important work

**Step 4: Session Cleanup and Confirmation**
- **Resource Cleanup**: Clear temporary data and release system resources
- **Memory Management**: Free up RAM used during session
- **State Reset**: Prepare application for next user (shared environments)
- **Confirmation Dialog**: Final confirmation before completing exit

**Step 5: Professional Closure**
- **Success Confirmation**: Clear message confirming successful exit
- **Next Steps**: Guidance for future Q2LMS sessions
- **Professional Messaging**: Appropriate closure for educational environments

#### When to Use Graceful Exit

**Recommended Scenarios**:
- **End of Planning Sessions**: Complete long course planning work sessions
- **Before Major Changes**: Exit before making significant database modifications
- **Course Switching**: When moving between different course preparations
- **Shared Computer Use**: Clean shutdown when others need to use the system
- **Break Periods**: Professional pause during extended planning sessions

**Benefits for Educational Environments**:
- **Data Safety**: Never lose filtered question sets or current work
- **System Performance**: Prevents memory leaks during extended use in labs/offices
- **Professional Experience**: Clean, institutional-appropriate application shutdown
- **Resource Management**: Proper cleanup for shared computing environments
- **Session Awareness**: Track time spent on course planning activities

#### Troubleshooting Exit Issues

**If Exit Button Not Visible**:
- Scroll to bottom of left sidebar
- Look under "Application" section header
- Refresh browser if sidebar appears incomplete

**If Exit Interface Doesn't Load**:
- Try clicking exit button again
- Refresh browser and re-access Q2LMS
- Manually save current work before closing browser

**Data Preservation Tips**:
- Use JSON export option during exit for complete backup
- Note current filter settings for easy reproduction
- Save any important filtered question sets before exit
```

## 6. Update "Question Management" Section

**Location**: In the "Browse Interface" subsection, replace with:

```markdown
### Enhanced Browse Interface

The Browse Questions tab now includes advanced filtering capabilities for efficient navigation through large question databases:

**Multi-Topic Navigation (Phase 8)**:
- **Cross-Disciplinary Browsing**: Select multiple topics simultaneously for comprehensive viewing
- **Topic Combinations**: Combine related topics (e.g., "Circuit Analysis" + "MATLAB Programming")
- **Visual Feedback**: Clear indication of selected topic combinations with count display
- **OR Logic Display**: Questions from ANY selected topics appear in browsing results

**Integrated Filtering System**:
- **Seamless Integration**: Multi-topic selection works with existing difficulty and type filters
- **Real-Time Updates**: Question count updates instantly as filters are applied/removed
- **Filter Status Display**: Clear indication of all active filter combinations
- **Persistent Selections**: Filter choices maintained during browsing session

**Enhanced Navigation Controls**:
- **Pagination Controls**: Navigate through filtered questions in manageable chunks
- **Real-Time Search**: Find questions by text, topic, or metadata within filtered results
- **Advanced Filtering**: Multiple criteria filtering with live updates and visual feedback
- **LaTeX Preview**: Mathematical expressions render in real-time during browsing

**Professional Session Control**:
- **Exit Access**: Graceful exit system available while browsing
- **Session Preservation**: Current filter settings preserved during exit process
- **Work Continuity**: Resume filtered views in future sessions
- **Data Backup**: Export current filtered selections before ending session
```

## 7. Update "Best Practices" Section

**Location**: Add to "Workflow Optimization" subsection:

```markdown
#### Enhanced Course Planning Workflow (Phase 8)

**Multi-Topic Assessment Strategy**:
- Use multi-topic filtering to create comprehensive exams covering multiple learning objectives
- Combine theoretical topics with practical applications (e.g., "Linear Algebra" + "MATLAB Programming")
- Build modular question banks for different course components
- Create cross-disciplinary assessments that integrate multiple subject areas

**Session Management Best Practices**:
- Use the graceful exit feature to end long planning sessions professionally
- Export current work as JSON before major changes or when ending sessions
- Take advantage of session information display to track planning progress
- Utilize data backup options during exit to preserve filtered question sets

**Advanced Filtering Workflow**:
- Start with broad topic selection, then narrow with difficulty/type filters
- Use multi-topic combinations to create comprehensive assessment coverage
- Save filtered question sets as JSON exports for reuse in similar courses
- Document successful topic combinations for future course planning
```

## 8. Update "Troubleshooting" Section

**Location**: Add new subsection:

```markdown
### Phase 8 Feature Issues

#### Multi-Topic Filtering Problems

**Issue**: Multi-topic dropdown not appearing
**Solution**:
- Refresh the browser page
- Ensure questions are loaded successfully
- Check that database contains multiple topics
- Verify sidebar is fully expanded

**Issue**: Topic selections not filtering correctly
**Solution**:
- Verify topics exist in the current database
- Check that question data includes 'Topic' field
- Clear and reselect topics if filtering seems stuck
- Ensure other filters aren't conflicting

**Issue**: "X of Y topics selected" not updating
**Solution**:
- Click directly on topic names in dropdown
- Wait for selection confirmation before proceeding
- Refresh if counter appears frozen
- Check browser console for JavaScript errors

#### Graceful Exit Issues

**Issue**: Exit button not responding
**Solution**:
- Ensure no other operations are in progress
- Try scrolling sidebar to locate button
- Refresh browser if button appears inactive
- Save work manually before troubleshooting

**Issue**: Exit interface shows incorrect session information
**Solution**:
- Session timing based on browser session
- Refresh may reset session start time
- Export current work regardless of displayed time
- Focus on data preservation rather than timing accuracy

**Issue**: Session cleanup appears incomplete
**Solution**:
- Complete exit process fully before restarting
- Clear browser cache if issues persist
- Restart browser for complete cleanup
- Contact support if problems continue
```

## Summary of docs/README.md Changes
- Added Phase 8 sections to table of contents
- Updated Quick Start workflow with Phase 8 features
- Enhanced Core Features with new Phase 8 capabilities
- Added comprehensive "Advanced Filtering Features" section
- Added complete "Professional Session Management" section
- Updated existing Question Management section
- Enhanced Best Practices with Phase 8 workflows
- Added Phase 8 troubleshooting information
- Maintained comprehensive documentation style and depth