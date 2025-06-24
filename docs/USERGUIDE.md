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
- **Live Question Editor**: Real-time LaTeX preview and editing capabilities
- **Multi-Format Export**: Generate Canvas QTI packages, native JSON, and CSV exports
- **Analytics Dashboard**: Monitor question distribution and performance insights
- **LaTeX Excellence**: Full mathematical notation support with automatic optimization
- **Version Control Integration**: Complete JSON export/import workflow for collaboration

### Target Users
- Course instructors creating assessments
- Academic departments managing question banks
- Educational content developers
- LMS administrators deploying assessments

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
   The main interface consists of four primary sections:
   - **Upload Panel**: File management and import tools
   - **Question Editor**: Real-time editing workspace
   - **Export Center**: Multi-format export options
   - **Analytics Dashboard**: Question database insights

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

### Workflow 2: Importing Existing Question Banks

**Purpose**: Integrate existing question collections into Q2LMS

**Steps**:
1. Go to **Upload Interface**
2. Choose upload method:
   - Single file upload for individual question banks
   - Multi-file upload for batch processing
3. Select supported file formats:
   - **JSON** (native Q2LMS format - recommended)
   - **CSV** (requires format conversion)
   - **QTI packages** (imported from other LMS platforms)
4. Review conflict resolution options if duplicate questions detected
5. Confirm import settings and process files
6. Verify imported questions in the Question Editor

**Expected Outcome**: Existing questions integrated into Q2LMS with preserved formatting and metadata

> **📋 Note**: Q2LMS works best with JSON-formatted input files. If you have questions in other formats, consider using Q2Prompt to help convert and structure them properly, or use the built-in format conversion tools in the Upload Interface.

> **🎯 Quick Start**: Try uploading `examples/sample_questions.json` first to familiarize yourself with the import process before working with your own data.

### Workflow 3: Editing and Refining Questions

**Purpose**: Modify existing questions with advanced editing features

**Steps**:
1. Access **Question Editor**
2. Browse or search existing questions using filters
3. Select question for editing
4. Use live preview to see LaTeX rendering
5. Modify question text, answers, or metadata
6. Apply bulk edits if working with multiple questions
7. Save changes to database

**Expected Outcome**: Updated questions with improved formatting and content accuracy

### Workflow 4: Exporting for LMS Deployment

**Purpose**: Generate LMS-compatible question packages for deployment

**Steps**:
1. Navigate to **Export Center**
2. Select questions for export (individual, filtered set, or entire database)
3. Choose export format:
   - **Canvas QTI**: For Canvas LMS deployment
   - **Generic QTI**: For other QTI-compatible systems
   - **Native JSON**: For backup and version control
   - **CSV**: For data analysis and reporting
4. Configure export settings (question randomization, answer shuffling, etc.)
5. Generate and download export package
6. Deploy to target LMS following platform-specific instructions

**Expected Outcome**: LMS-ready question packages optimized for your target platform

---

## Question Management

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

### Search and Filter Capabilities

**Advanced Search Features**:
- Full-text search across question content
- Metadata filtering (author, date, difficulty)
- Topic and subject area filtering
- Question type filtering
- Export status filtering

**Bulk Operations**:
- Mass editing of question attributes
- Batch export selection
- Bulk categorization updates
- Group deletion with confirmation

---

## Export and Deployment

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
- [ ] Questions reviewed and finalized
- [ ] LaTeX formatting verified
- [ ] Answer keys validated
- [ ] Export format selected
- [ ] Target LMS compatibility confirmed

**Canvas LMS Deployment**:
1. Export questions as Canvas QTI package
2. Log into Canvas course
3. Navigate to Settings → Import Course Content
4. Select "QTI .zip file" as import type
5. Upload Q2LMS-generated package
6. Review import summary and confirm
7. Verify questions in Canvas question bank

**Other LMS Platforms**:
1. Export as Generic QTI package
2. Consult LMS-specific import documentation
3. Follow platform import procedures
4. Validate question rendering and functionality

---

## Advanced Features

### LaTeX Integration

**Mathematical Notation Support**:
- Inline math expressions: `$equation$`
- Display math blocks: `$$equation$$`
- Complex formulas and symbols
- Automatic optimization for web display

**Best Practices for LaTeX**:
- Use standard LaTeX mathematical notation
- Preview all equations before finalizing
- Test rendering across different export formats
- Utilize Q2LMS LaTeX validation tools

### Analytics Dashboard

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

### Question Development

**Content Quality**:
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
- Test LaTeX rendering across all export formats
- Validate question metadata completeness
- Use consistent formatting and style
- Implement regular backup procedures

> **💡 Best Practice**: When using Q2Prompt for question generation, always review and refine AI-generated content in Q2LMS to ensure alignment with your specific learning objectives and institutional standards.

### Database Management

**Organization Strategies**:
- Implement consistent naming conventions
- Maintain detailed subject categorization
- Document learning objective alignments
- Regular database cleanup and maintenance

**Quality Assurance**:
- Peer review processes for new questions
- Regular validation of existing content
- Performance monitoring and optimization
- Backup and recovery procedures

### LMS Integration

**Deployment Planning**:
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

**Upload Problems**
- **Issue**: File format not recognized
- **Solution**: Verify file format compatibility; convert to supported format if necessary
- **Prevention**: Use recommended file formats (JSON, CSV, QTI)

**LaTeX Rendering Issues**
- **Issue**: Mathematical expressions not displaying correctly
- **Solution**: Check LaTeX syntax; use Q2LMS preview feature for validation
- **Prevention**: Follow LaTeX best practices; test expressions before finalizing

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
- Built-in help system and tooltips
- Example question databases
- Video tutorials and documentation
- FAQ and knowledge base

**Support Channels**:
- GitHub Issues for bug reports
- GitHub Discussions for community support
- Documentation updates and improvements
- Institution-specific support contacts

### Performance Optimization

**Large Database Management**:
- Implement database segmentation strategies
- Use filtering to work with question subsets
- Optimize export operations for large datasets
- Monitor system performance metrics

**Browser Optimization**:
- Use modern, updated web browsers
- Clear browser cache if experiencing issues
- Disable unnecessary browser extensions
- Ensure adequate system memory

---

## Conclusion

Q2LMS provides a comprehensive solution for educational question database management and LMS integration. By following the workflows and best practices outlined in this guide, instructors can efficiently create, manage, and deploy high-quality assessments across multiple platforms.

For additional support and resources, consult the project documentation, community forums, and institutional support channels.

---

*This user guide is maintained as part of the Q2LMS project. For the most current version and updates, visit the project repository.*