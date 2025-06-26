# Q2LMS Quick Start Guide

<div align="center">
  <img src="https://raw.githubusercontent.com/aknoesen/q2lms/main/assets/q2lms-logo.svg" alt="Q2LMS Logo" width="80" height="80">
  <br>
  <strong>Phase 10 Enhanced - Instructor-Optimized Interface</strong>
  <br>
  <em>Get Q2LMS running in 5 minutes with professional educational workflows</em>
</div>

---

## 🚀 **What is Q2LMS Phase 10?**

Q2LMS is a **professional question database management platform** designed specifically for instructors. **Phase 10** represents the evolution from a development tool into a **production-ready instructor platform** with:

- ✨ **Clean, Professional Interface** - No visual clutter, focused on educational content
- 📊 **Immediate Statistics Display** - Database insights shown instantly upon upload
- 🎯 **Complete Question Visibility** - "Show All" default eliminates pagination barriers
- 🚀 **Guided Export Process** - Clear completion guidance with step-by-step instructions
- 🔧 **Smart Operation Modes** - Choose Select Questions or Delete Questions workflows

---

## ⚡ **5-Minute Setup**

### **Option 1: Try the Live Demo** *(Fastest)*
**👉 [Launch Q2LMS Demo](https://aknoesen.github.io/q2lms/)** - Experience Phase 10 immediately

### **Option 2: Local Installation** *(Recommended for Regular Use)*

**Step 1: Prerequisites**
```bash
# Ensure you have Python 3.8 or higher
python --version

# Install Git if not already installed
git --version
```

**Step 2: Quick Install**
```bash
# Clone and setup (takes 2-3 minutes)
git clone https://github.com/aknoesen/q2lms.git
cd q2lms

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Step 3: Launch Q2LMS**
```bash
# Start the Phase 10 enhanced interface
streamlit run streamlit_app.py
```

**🎉 That's it!** Q2LMS will open in your browser at `http://localhost:8501`

---

## 🎯 **Phase 10 Interface Overview**

When Q2LMS launches, you'll see the **Phase 10 instructor-optimized interface**:

### **Clean Professional Header**
- Q2LMS title with Phase 10 enhancement indicator
- No visual clutter or distracting elements
- Clear navigation tabs

### **Immediate Statistics Display** *(When questions are loaded)*
- **Questions**: Total count in your database
- **Points**: Sum of all question point values  
- **Types**: Number of different question types
- **Topics**: Number of subject areas covered

### **Four Main Tabs**
1. **📤 Upload** - Import your question databases
2. **🎯 Browse & Manage** - Phase 10 operation modes for question curation
3. **📊 Analytics** - Enhanced dashboard with instructor insights
4. **🚀 Export** - Guided export process with completion notices

---

## 📤 **Quick Upload Guide**

### **Step 1: Prepare Your Questions**

**Option A: Use Sample Data** *(Fastest way to explore)*
- Q2LMS includes sample questions in `examples/sample_questions.json`
- Perfect for testing Phase 10 features

**Option B: Create with Q2Prompt** *(Recommended for new content)*
- Visit **[Q2Prompt](https://github.com/aknoesen/q2prompt)** - AI prompt generator
- Generate structured prompts for LLMs to create Q2LMS-compatible questions
- Export as JSON and import into Q2LMS

**Option C: Convert Existing Questions**
- CSV files with question data
- Existing QTI packages from other systems
- JSON files from other question banks

### **Step 2: Upload Process**

1. **Click the Upload Tab**
2. **Choose Upload Method**:
   - **Single File**: Upload one question database
   - **Multiple Files**: Batch import with intelligent merging
3. **Select Your File**: Drag and drop or browse
4. **Review Upload Summary**: Phase 10 shows immediate statistics
5. **Confirm Import**: Questions are processed instantly

### **Step 3: Phase 10 Enhancement**
- **Statistics Display**: See total questions, points, types, and topics immediately
- **Upload Guidance**: Clear next-step instructions appear
- **Database Overview**: Complete summary before you begin working

---

## 🎯 **Phase 10 Operation Modes**

After uploading questions, Phase 10 presents **two instructor-optimized workflows**:

### **🎯 Select Questions Mode**
**Perfect for**: Building targeted assessments, focused quizzes, topic-specific exams

**How it works**:
1. Choose "Select Questions" from the clean interface
2. **See ALL questions** by default (no pagination barriers)
3. Use **topic filtering** to focus on specific subject areas
4. **Check boxes** to select questions for export
5. **Export completion notice** appears when ready

**Best practices**:
- Review complete question set for informed selection
- Use topic filters for large databases
- Select questions that align with learning objectives

### **🗑️ Delete Questions Mode**
**Perfect for**: Cleaning question banks, removing outdated content, filtering large databases

**How it works**:
1. Choose "Delete Questions" from the clean interface
2. **See ALL questions** by default for comprehensive review
3. Use **topic filtering** to focus review efforts
4. **Check boxes** to mark questions for removal
5. **Export completion notice** shows remaining questions

**Best practices**:
- Review entire database before marking deletions
- Use filters to systematically review content areas
- Consider archiving rather than permanent deletion

---

## 🚀 **Export Process**

Phase 10 provides **guided export completion** with clear next-step instructions:

### **Export Completion Guidance**
When you've selected or marked questions, **prominent red notices** appear:

```
🚀 Complete Your Export
✅ X questions selected for export
📊 Total Points: Y
Click the Export tab above to download your questions
📁 Available formats: CSV, JSON, Canvas QTI
```

### **Export Formats**

**Canvas QTI Package** *(Most Popular)*
- Direct import to Canvas LMS
- Optimized compatibility and formatting
- Preserves LaTeX math notation
- **File**: `.zip` package ready for Canvas

**Native JSON Format**
- Complete data fidelity
- Perfect for backup and version control
- Re-importable to Q2LMS
- **File**: `.json` with full metadata

**CSV Data Export**
- Analysis-ready tabular format
- Spreadsheet compatible
- Statistical analysis friendly
- **File**: `.csv` with comprehensive data

### **Export Steps**
1. **Complete Question Management**: Finish selecting or marking questions
2. **Follow Guidance Notice**: Click Export tab when prompted
3. **Choose Format**: Select target LMS or analysis format
4. **Configure Options**: Set package name and preferences
5. **Download**: Get your export package instantly

---

## 📊 **Understanding the Analytics**

Phase 10 provides **immediate instructor insights**:

### **Database Overview** *(Displayed Before Tabs)*
- **Quick Metrics**: Essential statistics at a glance
- **Real-time Updates**: Statistics update as you filter and select
- **Expandable Details**: Click for comprehensive breakdowns

### **Detailed Analytics** *(Analytics Tab)*
- **Question Type Distribution**: Visual breakdown of question variety
- **Topic Coverage Analysis**: Subject area representation
- **Difficulty Level Balance**: Assessment challenge distribution
- **Point Value Analysis**: Score distribution insights
- **Export Readiness Indicators**: Clear status for deployment

### **Instructor Insights**
- **Content Balance Recommendations**: Suggestions for improved assessments
- **Coverage Gap Analysis**: Identification of missing topic areas
- **Quality Indicators**: Metadata completeness and question standards
- **Performance Metrics**: Database size and optimization suggestions

---

## 🧮 **LaTeX Math Support**

Q2LMS Phase 10 includes **enhanced LaTeX rendering** for mathematical content:

### **Supported Notation**
- **Inline Math**: `$equation$` for math within text
- **Display Math**: `$$equation$$` for centered mathematical expressions
- **Complex Formulas**: Full LaTeX mathematical notation support
- **Live Preview**: Real-time rendering during question editing

### **Common Examples**
```latex
# Inline math example
The quadratic formula is $x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$.

# Display math example  
$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

# Fractions and symbols
$$P(A|B) = \frac{P(B|A)P(A)}{P(B)}$$
```

### **Phase 10 Enhancement**
- **Live Preview**: See rendered math as you type
- **Validation**: Automatic LaTeX syntax checking
- **Optimization**: Enhanced rendering for web display
- **Export Preservation**: Math notation maintained across all export formats

---

## 🔧 **Troubleshooting**

### **Common Quick Start Issues**

**Q: Interface looks different from screenshots**
A: Ensure you're running the latest version with Phase 10 enhancements:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

**Q: "Show All" not displaying all questions**
A: Phase 10 defaults to "Show All" but check the pagination dropdown:
- Look for pagination controls above question list
- Select "Show All" from dropdown if not already selected
- For very large databases (1000+ questions), consider using topic filters

**Q: Export completion guidance not appearing**
A: Ensure you've selected/marked questions in operation mode:
- Choose Select Questions or Delete Questions mode
- Use checkboxes to select/mark questions
- Red completion notices appear when questions are ready for export

**Q: Upload failing with file format errors**
A: Check supported formats and file structure:
- **Supported**: `.json`, `.csv`, `.zip` (QTI packages)
- **JSON Structure**: Must include `questions` array with valid question objects
- **CSV Format**: Headers must match Q2LMS field names
- Try the sample data in `examples/` folder first

**Q: Statistics not displaying immediately**
A: Phase 10 shows stats before tabs when questions are loaded:
- Ensure questions uploaded successfully (check Upload tab status)
- Refresh browser if statistics don't appear
- Check browser console for JavaScript errors

**Q: LaTeX math not rendering**
A: Verify LaTeX syntax and browser compatibility:
- Check for unmatched braces `{}` or dollar signs `$$`
- Use Q2LMS live preview to test equations
- Ensure modern browser (Chrome, Firefox, Safari, Edge)

### **Performance Optimization**

**Large Database Handling**:
- **Topic Filtering**: Use sidebar filters to focus on specific content areas
- **Batch Operations**: Use bulk select/delete controls for efficiency
- **Memory Management**: Close other browser tabs if interface becomes slow
- **Chunked Processing**: Phase 10 automatically optimizes large dataset handling

**Browser Optimization**:
- **Modern Browser**: Use updated Chrome, Firefox, Safari, or Edge
- **JavaScript Enabled**: Required for Phase 10 interactive features
- **Clear Cache**: Refresh browser cache if experiencing issues
- **Extensions**: Disable ad blockers or script blockers if interface problems occur

---

## 🎓 **Best Practices for Instructors**

### **Question Database Organization**

**Topic Structure**:
- Use consistent topic naming (e.g., "Chapter 1", "Unit 2", "Functions")
- Group related concepts under broader topics
- Consider hierarchical organization for large courses

**Point Values**:
- Assign points reflecting question difficulty and importance
- Use consistent scale across similar question types
- Consider total exam/quiz point targets when selecting

**Metadata Completeness**:
- Add difficulty levels (Easy, Medium, Hard) for balanced assessments
- Include learning objectives or standards alignment
- Use author fields for collaborative question banking

### **Assessment Creation Workflow**

**Phase 10 Recommended Process**:
1. **Upload and Review**: Import questions and review complete database overview
2. **Analyze Coverage**: Use Analytics tab to assess content balance
3. **Filter and Select**: Use topic filters and Select Questions mode for targeted curation
4. **Validate Selection**: Review statistics and point totals before export
5. **Export with Guidance**: Follow completion notices to generate LMS packages

**Quality Assurance**:
- Preview questions in Q2LMS before export
- Test LaTeX rendering for mathematical content
- Validate answer keys and correct responses
- Review point values and difficulty balance

### **Collaborative Question Banking**

**Team Workflows**:
- Use JSON export/import for version control and sharing
- Establish consistent metadata standards across team members
- Regular database cleanup using Delete Questions mode
- Shared topic taxonomies for consistent organization

**Version Control**:
- Export to JSON for Git repository management
- Tag releases for major question bank updates
- Document changes and additions in commit messages
- Regular backups using JSON export format

---

## 📚 **Next Steps**

### **Explore Advanced Features**
- **[User Guide](USERGUIDE.md)**: Complete workflows and detailed feature explanations
- **[Features Overview](FEATURES.md)**: Comprehensive platform capabilities
- **[Developer Documentation](DEVELOPER.md)**: Technical details and customization

### **Expand Your Question Banking**
- **[Q2Prompt](https://github.com/aknoesen/q2prompt)**: AI-assisted question generation
- **Sample Databases**: Explore `examples/` folder for question templates
- **Import Existing Content**: Convert from other LMS question banks

### **Join the Community**
- **[GitHub Repository](https://github.com/aknoesen/q2lms)**: Source code and development
- **[GitHub Discussions](https://github.com/aknoesen/q2lms/discussions)**: Community support and ideas
- **[Issue Tracking](https://github.com/aknoesen/q2lms/issues)**: Bug reports and feature requests

### **Production Deployment**
- **[Deployment Guide](DEPLOYMENT.md)**: Production setup for institutions
- **[API Documentation](API.md)**: Integration with existing systems
- **Institutional Licensing**: Multi-user deployment considerations

---

## 🎉 **You're Ready!**

**Congratulations!** You now have Q2LMS Phase 10 running with the instructor-optimized interface. The platform is ready for:

✅ **Professional Question Management** - Clean interface focused on educational workflows  
✅ **Complete Database Visibility** - "Show All" defaults for comprehensive course planning  
✅ **Guided Export Processes** - Clear completion guidance eliminates confusion  
✅ **Enhanced Analytics** - Immediate insights for informed decision-making  
✅ **LaTeX Mathematical Content** - Full support for STEM assessments  

### **Quick Success Checklist**
- [ ] Q2LMS launched successfully in browser
- [ ] Sample questions uploaded and statistics displayed
- [ ] Operation mode selected (Select or Delete Questions)
- [ ] Questions filtered and selected using "Show All" interface
- [ ] Export completion guidance appeared with clear next steps
- [ ] Questions exported in preferred format (QTI, JSON, or CSV)

### **Ready for Production Use**
Phase 10 Q2LMS is designed for immediate professional use. The instructor-optimized interface, complete question visibility, and guided workflows make it suitable for:

- **Course Assessment Creation** - Build exams, quizzes, and assignments
- **Question Bank Management** - Organize and maintain institutional question libraries  
- **LMS Integration** - Seamless export to Canvas and other learning management systems
- **Collaborative Development** - Team-based question creation and review workflows
- **Educational Research** - Data analysis and assessment effectiveness studies

**Welcome to Q2LMS Phase 10 - Professional Question Database Management for Educators!**

---

<div align="center">
  <strong>Questions? Need Help?</strong>
  <br>
  <a href="https://github.com/aknoesen/q2lms/discussions">Community Support</a> | 
  <a href="https://github.com/aknoesen/q2lms/issues">Report Issues</a> | 
  <a href="USERGUIDE.md">Complete User Guide</a>
  <br><br>
  <em>Built for educators by educators</em>
</div>