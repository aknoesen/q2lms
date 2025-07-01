# Q2LMS User Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Core Workflows](#core-workflows)
4. [Question Management](#question-management)
5. [Export and Deployment](#export-and-deployment)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Q2LMS (Question Database to Learning Management System) is a comprehensive web-based platform designed for educators to create, manage, and deploy question databases across multiple learning management systems. The platform streamlines the entire question lifecycle from creation to deployment.

### Key Capabilities
- **Smart Upload System**: Process single or multiple question files with intelligent conflict resolution
- **Instructor-Optimized Interface**: Clean, professional design focused on educational workflows
- **Flexible Question Management**: Choose between Select Mode (curate specific questions) or Delete Mode (remove unwanted questions)
- **Complete Question Overview**: "Show All" interface displays entire question banks for comprehensive course planning
- **Live Question Editor**: Real-time LaTeX preview and editing capabilities
- **Multi-Format Export**: Generate Canvas QTI packages, native JSON, and CSV exports with guided completion process
- **Analytics Dashboard**: Monitor question distribution and performance insights with immediate stats visibility
- **LaTeX Excellence**: Full mathematical notation support with automatic optimization
- **Version Control Integration**: Complete JSON export/import workflow for collaboration

### Target Users
- Course instructors creating assessments
- Academic departments managing question banks
- Educational content developers
- LMS administrators deploying assessments

### Interface Design Philosophy
Q2LMS prioritizes instructor efficiency with a clean, professional interface that eliminates visual clutter and provides clear guidance throughout the question management workflow. The platform displays essential information immediately and guides users seamlessly from upload to export completion.

---

## Getting Started

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for initial setup
- No additional software installation required for end users

### Companion Tools
**Q2Prompt**: For efficient question generation, consider using Q2Prompt (github.com/aknoesen/q2prompt), a companion tool that helps create AI prompts for generating Q2LMS-compatible JSON question banks. Q2Prompt is particularly useful for:
- Bulk question creation
- Structured prompt generation for LLMs
- Ensuring consistent JSON formatting
- Converting learning objectives into question prompts

### First Time Access

1. **Launch Q2LMS**
   - Navigate to your institution's Q2LMS deployment URL
   - Or run locally: `streamlit run streamlit_app.py`

2. **Interface Overview**
   The Q2LMS interface features a clean, instructor-focused design:
   - **Upload Panel**: Prominent file management and import tools
   - **Operation Mode Selection**: Choose between Select Questions or Delete Questions workflows
   - **Question Management Interface**: Complete question overview with "Show All" default view
   - **Export Completion Guidance**: Clear next-step instructions throughout the process
   - **Analytics Summary**: Key database statistics displayed immediately upon upload

3. **Initial Setup**
   - No user registration required
   - Session-based data management
   - Automatic backup recommendations will be displayed

4. **Try with Example Data**
   - Q2LMS includes sample question files in the `examples/` directory
   - Start by uploading `examples/sample_questions.json` to familiarize yourself with the interface
   - This provides a safe way to explore all features without affecting real data

---

## Core Workflows

### New in Q2LMS: 3-Step Workflow (Updated in Phase 14)

Phase 14 introduces a streamlined 3-step workflow for managing your question database:

**Step 1: Choose Your Path**
- Select between **Select Mode** (curate specific questions) or **Delete Mode** (remove unwanted questions)

**Step 2: Configure Categories**
- Use the new **Category Selection Interface** in the main area to filter by topic, subtopic, and difficulty
- Enjoy a full-width layout with multiselect controls and live question count preview

**Step 3: Select Questions**
- Browse the filtered results and proceed with selection or deletion as per your chosen mode


### Workflow 1: Creating Questions from Scratch

**Purpose**: Start a new question database or add questions to existing collections

**Method A: Direct Creation in Q2LMS**
1. Navigate to the **Question Editor** tab
2. Click "Add New Question"
3. Select question type (Multiple Choice, True/False, Short Answer, Essay, etc.)
4. Enter question content using the rich text editor
5. Add answer options and mark correct answers
6. Preview LaTeX rendering in real-time
7. Save question to active database

**Method B: AI-Assisted Creation with Q2Prompt (Recommended)**
1. Access **Q2Prompt** (companion tool for Q2LMS)
2. Input your learning objectives and topic requirements
3. Generate AI prompts tailored for educational question creation
4. Use generated prompts with your preferred LLM (ChatGPT, Claude, etc.)
5. Export results as Q2LMS-compatible JSON format
6. Import JSON file into Q2LMS using the Upload Interface
7. Review and refine questions in Q2LMS Question Editor

**Expected Outcome**: New question added to your working database with proper formatting

> **💡 Pro Tip**: Q2Prompt streamlines bulk question creation by generating structured prompts that produce Q2LMS-compatible JSON output. This approach is especially efficient for creating large question banks or when working with specific learning objectives.

### Workflow 2: Importing and Managing Question Banks

**Purpose**: Integrate existing question collections into Q2LMS with instructor-friendly management

**Steps**:
1. **Upload Questions**
   - Go to **Upload Interface**
   - Choose upload method (single file or multi-file upload)
   - Select supported file formats (JSON, CSV, QTI packages)
   - Review upload summary with automatic statistics display

2. **Choose Operation Mode**
   - **Select Questions Mode**: For curating specific questions
   - **Delete Questions Mode**: For removing unwanted content
   - Clear mode descriptions help you choose the right approach

3. **Review Complete Question Set**
   - Q2LMS displays **all questions by default** for comprehensive overview
   - Use topic filtering in main-area category selection interface to focus on specific subjects
   - No pagination barriers - see entire question bank at once

4. **Manage Questions**
   - Use checkboxes to select/mark questions according to chosen mode
   - Bulk controls available for efficient mass operations
   - Edit questions inline with live preview capabilities

5. **Complete Export Process**
   - Prominent **red completion notices** guide you to the Export tab
   - Clear statistics show exactly what will be exported
   - Multiple format options available (Canvas QTI, JSON, CSV)

**Expected Outcome**: Efficiently managed question database ready for deployment

> **📋 New Feature**: The instructor-optimized interface shows all questions by default, eliminating the need to navigate through pagination to see your complete question bank.

### Workflow 3: Editing and Refining Questions

**Purpose**: Modify existing questions with advanced editing features

**Steps**:
1. Access your chosen **Operation Mode** (Select or Delete)
2. Browse complete question set with **"Show All" default view**
3. Use main-area category selection interface to focus on specific content areas
4. Select questions for editing with inline preview capabilities
5. Modify question text, answers, or metadata with live LaTeX rendering
6. Apply bulk edits using efficient bulk control tools
7. Save changes and proceed to export with guided completion

**Expected Outcome**: Updated questions with improved formatting and content accuracy

> **🎯 Interface Enhancement**: All questions are displayed simultaneously by default, allowing instructors to see the complete scope of their question bank and make informed editing decisions.

### Workflow 4: Exporting for LMS Deployment

**Purpose**: Generate LMS-compatible question packages for deployment with clear guidance

**Steps**:
1. **Complete Question Management**
   - Finish selecting or marking questions in your chosen mode
   - Review **completion statistics** displayed throughout the interface

2. **Navigate to Export**
   - **Red completion notices** at the bottom of question lists provide clear guidance
   - "Complete Your Export" call-to-action directs you to the Export tab
   - No guesswork about next steps

3. **Configure Export Settings**
   - Choose export format (Canvas QTI, Generic QTI, JSON, CSV)
   - Review export preview showing exactly what will be included
   - Configure format-specific options as needed

4. **Generate and Download**
   - Download export package optimized for your target platform
   - Receive confirmation of successful export completion

**Expected Outcome**: LMS-ready question packages with clear completion guidance throughout the process

> **🚀 New Enhancement**: Prominent export completion guidance eliminates confusion about finishing the export process, ensuring instructors can confidently complete their question management workflow.

---

## Question Management

### Category Selection Interface (NEW in Phase 14)

Phase 14 introduces a redesigned category selection interface with the following features:

- **Full-width main area**: Replaces the old main-area category selection interface for better visibility and usability
- **Multiselect controls**: Filter questions by topic, subtopic, and difficulty using intuitive dropdowns
- **Live question count preview**: Instantly see how many questions match your selected filters
- **Spacious layout**: Provides a more comfortable and efficient filtering experience compared to the previous cramped main-area category selection interface

This interface appears in Step 2 of the new 3-step workflow and significantly improves the question selection process.


### Enhanced Question Interface

**Complete Question Visibility**
- **"Show All" Default**: See entire question bank without pagination barriers
- **Comprehensive Overview**: Make informed decisions about question selection
- **Topic Filtering**: Use main-area category selection interface to focus on specific subject areas
- **Instant Statistics**: Key metrics displayed immediately upon database load

**Streamlined Operation Modes**

**Select Questions Mode Interface**:
- ✅ Checkboxes to include questions in export
- 📊 Real-time selection statistics
- 🔧 Bulk selection controls for efficiency
- 📋 Clear export preview with selected question counts

**Delete Questions Mode Interface**:
- 🗑️ Checkboxes to mark questions for removal
- 📊 Statistics showing remaining question counts
- 🔧 Bulk deletion controls for mass operations
- ✅ Clear indication of questions that will be exported

### Question Types Supported

**Multiple Choice Questions**
- Single correct answer
- Multiple correct answers
- Configurable distractor options
- Automatic answer key generation

**True/False Questions**
- Binary response format
- Explanation field support
- Batch creation tools

**Short Answer Questions**
- Text-based responses
- Multiple acceptable answers
- Case-sensitive options

**Essay Questions**
- Long-form response format
- Rubric integration support
- Word count parameters

**Mathematical Questions**
- Full LaTeX support
- Formula rendering
- Variable substitution capabilities

### Question Attributes

Each question in Q2LMS includes comprehensive metadata:

- **Content Fields**
  - Question text (with LaTeX support)
  - Answer options and correct responses
  - Explanation and feedback text
  - Difficulty level classification

- **Administrative Fields**
  - Unique question ID
  - Creation and modification timestamps
  - Author information
  - Subject/topic categorization
  - Learning objective alignment

- **Technical Fields**
  - Export compatibility flags
  - LaTeX optimization status
  - Version control metadata

### Enhanced Search and Filter Capabilities

**Immediate Statistics Display**:
- Total question count, topics, points, and question types shown immediately
- Real-time updates as you apply filters
- Clear indication of database scope and content

**Advanced Filtering**:
- **Topic Filtering**: Sidebar multi-select with clear instructions
- **Subject Area Focus**: Easily include/exclude specific topics
- **Visual Feedback**: Clear indication of active filters and excluded content

**Bulk Operations**:
- **Database-wide Controls**: Affect entire question bank
- **View-specific Controls**: Target only currently filtered questions
- **Progress Indicators**: Visual feedback showing selection progress
- **Invert Operations**: Quickly reverse selection patterns

---

## Export and Deployment

### Enhanced Export Process

**Guided Export Completion**
- **Completion Notices**: Prominent red call-to-action boxes appear at the bottom of question lists
- **Clear Next Steps**: "Click the Export tab above to download your questions"
- **Export Statistics**: Real-time display of questions ready for export
- **Format Options**: Clear indication of available export formats (CSV, JSON, QTI)

**Export Preview and Statistics**
- **Select Mode**: Shows "X of Y selected questions" with export readiness
- **Delete Mode**: Shows "X remaining questions (Y excluded)" for clarity
- **Points Calculation**: Automatic total points calculation for selected questions
- **Topic Breakdown**: Expandable view of questions by topic area

### Export Formats

**Canvas QTI Packages**
- **Use Case**: Direct deployment to Canvas LMS
- **Features**: 
  - Complete question bank structure
  - Preserved LaTeX formatting
  - Answer key integration
  - Canvas-specific optimizations
- **Output**: ZIP package ready for Canvas import

**Generic QTI Packages**
- **Use Case**: Deployment to other QTI-compatible LMS platforms
- **Features**:
  - Standards-compliant QTI 2.1 format
  - Cross-platform compatibility
  - Metadata preservation
- **Output**: Standard QTI package

**Native JSON Format**
- **Use Case**: Backup, version control, and Q2LMS re-import
- **Features**:
  - Complete data fidelity
  - Human-readable format
  - Version control friendly
  - Full metadata preservation
- **Output**: Structured JSON file

**CSV Export**
- **Use Case**: Data analysis and reporting
- **Features**:
  - Tabular question data
  - Statistical analysis ready
  - Spreadsheet compatible
  - Customizable field selection
- **Output**: Comma-separated values file

### Deployment Process

**Pre-Deployment Checklist**:
- [ ] Questions reviewed using complete overview interface
- [ ] Operation mode chosen and questions selected/marked appropriately
- [ ] Export completion notice confirms readiness
- [ ] LaTeX formatting verified in preview
- [ ] Answer keys validated
- [ ] Export format selected
- [ ] Target LMS compatibility confirmed

**Canvas LMS Deployment**:
1. Complete question management in Q2LMS with guided export process
2. Export questions as Canvas QTI package following completion notices
3. Log into Canvas course
4. Navigate to Settings → Import Course Content
5. Select "QTI .zip file" as import type
6. Upload Q2LMS-generated package
7. Review import summary and confirm
8. Verify questions in Canvas question bank

**Other LMS Platforms**:
1. Export as Generic QTI package using guided completion process
2. Consult LMS-specific import documentation
3. Follow platform import procedures
4. Validate question rendering and functionality

---

## Advanced Features

### Enhanced Analytics Dashboard

**Immediate Statistics Display**:
- **Database Overview**: Total questions, topics, points, and question types displayed immediately upon upload
- **Real-time Updates**: Statistics update automatically as you apply filters or make selections
- **Export Readiness**: Clear indication of questions ready for export in chosen mode

**Question Database Insights**:
- Total question count by type
- Subject area distribution
- Difficulty level analysis
- Creation timeline visualization
- Author contribution statistics

**Performance Metrics**:
- Export frequency tracking
- Question usage statistics
- Popular question identification
- Database growth trends

### LaTeX Integration

**Mathematical Notation Support**:
- Inline math expressions: `$equation$`
- Display math blocks: `$$equation$$`
- Complex formulas and symbols
- Automatic optimization for web display
- Live preview in question editing interface

**Best Practices for LaTeX**:
- Use standard LaTeX mathematical notation
- Preview all equations before finalizing using built-in preview
- Test rendering across different export formats
- Utilize Q2LMS LaTeX validation tools

### Collaboration Features

**Version Control Integration**:
- JSON export for Git integration
- Collaborative editing workflows
- Change tracking and attribution
- Merge conflict resolution

**Team Management**:
- Multi-author question attribution
- Collaborative editing sessions
- Shared database management
- Access control recommendations

**Q2Prompt Team Workflows**:
- Share Q2Prompt templates across team members
- Standardize AI prompt generation for consistent question quality
- Coordinate large-scale question bank development projects
- Maintain institutional question creation standards

---

## Best Practices

### Instructor-Friendly Workflow Optimization

**Interface Usage**:
- **Take advantage of "Show All" default**: Review complete question sets for comprehensive course planning
- **Use topic filtering strategically**: Focus on specific subject areas when working with large databases
- **Leverage completion guidance**: Follow red completion notices to ensure successful export completion
- **Choose appropriate operation mode**: Use Select Mode for curation, Delete Mode for cleaning

**Question Development**:
- **Content Quality**:
  - Write clear, unambiguous question stems
  - Ensure single correct answers for objective questions
  - Provide meaningful distractors for multiple choice
  - Include explanatory feedback where appropriate

**AI-Assisted Development with Q2Prompt**:
- Use Q2Prompt to generate consistent, high-quality question prompts
- Leverage AI to create diverse question variations on similar topics
- Maintain pedagogical standards through structured prompt engineering
- Scale question creation while preserving educational quality

**Technical Optimization**:
- Test LaTeX rendering using live preview capabilities
- Validate question metadata completeness
- Use consistent formatting and style
- Implement regular backup procedures using JSON export

> **💡 Best Practice**: When using Q2Prompt for question generation, always review and refine AI-generated content in Q2LMS to ensure alignment with your specific learning objectives and institutional standards.

### Database Management

**Organization Strategies**:
- Implement consistent naming conventions
- Maintain detailed subject categorization using topic filters
- Document learning objective alignments
- Regular database cleanup using Delete Mode workflow

**Quality Assurance**:
- Use complete question overview for comprehensive peer review
- Leverage bulk controls for efficient quality assurance processes
- Regular validation using guided export previews
- Backup and recovery using JSON export format

### LMS Integration

**Deployment Planning**:
- Use export completion guidance to ensure thorough preparation
- Test imports in LMS development environments
- Coordinate with LMS administrators
- Plan deployment schedules
- Establish rollback procedures

**Post-Deployment Monitoring**:
- Verify question functionality in target LMS
- Monitor student interaction and performance
- Collect feedback for continuous improvement
- Document lessons learned

---

## Troubleshooting

### Common Issues and Solutions

**Interface and Navigation**
- **Issue**: Cannot see all questions in database
- **Solution**: Q2LMS now defaults to "Show All" - if you see pagination controls, select "Show All" from the dropdown
- **Prevention**: Use topic filtering to focus on specific content areas if working with very large databases

**Upload Problems**
- **Issue**: File format not recognized
- **Solution**: Verify file format compatibility; convert to supported format if necessary
- **Prevention**: Use recommended file formats (JSON, CSV, QTI)

**Mode Selection Confusion**
- **Issue**: Unsure which operation mode to choose
- **Solution**: Use Select Mode for building targeted question sets; use Delete Mode for cleaning and refining existing banks
- **Prevention**: Review mode descriptions in the interface and consider your end goal

**Export Process Issues**
- **Issue**: Unclear how to complete export process
- **Solution**: Look for red completion notices at the bottom of question lists providing clear guidance to Export tab
- **Prevention**: Follow the guided workflow and completion statistics throughout the process

**LaTeX Rendering Issues**
- **Issue**: Mathematical expressions not displaying correctly
- **Solution**: Check LaTeX syntax; use Q2LMS live preview feature for validation
- **Prevention**: Follow LaTeX best practices; test expressions using built-in preview before finalizing

**Export Failures**
- **Issue**: Export process fails or produces corrupted files
- **Solution**: Verify question data integrity; check for special characters or formatting issues
- **Prevention**: Regular database validation; use recommended export settings

**LMS Import Problems**
- **Issue**: Questions not importing correctly into target LMS
- **Solution**: Verify LMS compatibility; check export format settings
- **Prevention**: Test imports in development environment; follow LMS-specific guidelines

### Getting Help

**Self-Service Resources**:
- Built-in help system and tooltips throughout the interface
- Example question databases
- Video tutorials and documentation
- FAQ and knowledge base

**Interface Guidance**:
- Operation mode descriptions and guidance
- Export completion notices and next-step instructions
- Real-time statistics and progress indicators
- Clear visual feedback throughout all workflows

**Support Channels**:
- GitHub Issues for bug reports
- GitHub Discussions for community support
- Documentation updates and improvements
- Institution-specific support contacts

### Performance Optimization

**Large Database Management**:
- Utilize "Show All" default view for comprehensive overview
- Implement topic filtering for focused work sessions
- Use bulk controls for efficient mass operations
- Monitor export statistics for performance insights

**Browser Optimization**:
- Use modern, updated web browsers
- Clear browser cache if experiencing issues
- Disable unnecessary browser extensions
- Ensure adequate system memory

---

## Conclusion

Q2LMS provides a comprehensive, instructor-optimized solution for educational question database management and LMS integration. The enhanced interface prioritizes educator efficiency with clean design, complete question visibility, and guided workflows that eliminate confusion throughout the question management process.

By following the workflows and best practices outlined in this guide, instructors can efficiently create, manage, and deploy high-quality assessments across multiple platforms with confidence and clarity.

**Key Interface Advantages**:
- **Complete Visibility**: "Show All" default eliminates pagination barriers
- **Clear Guidance**: Export completion notices provide step-by-step direction
- **Flexible Workflows**: Choose between Select and Delete modes based on your needs
- **Professional Design**: Clean interface focuses attention on educational content
- **Immediate Feedback**: Real-time statistics and progress indicators throughout

For additional support and resources, consult the project documentation, community forums, and institutional support channels.

---

*This user guide reflects the enhanced Q2LMS interface with instructor-optimized design and workflows. For the most current version and updates, visit the project repository.*