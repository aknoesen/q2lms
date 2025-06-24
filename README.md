# Q2LMS - Question Database Manager

**Professional question database management and LMS integration platform for educational institutions.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)

## 🚀 Quick Start

```bash
# Clone and run
git clone https://github.com/aknoesen/q2lms.git
cd q2lms
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[User Guide](docs/USERGUIDE.md)** | Complete installation and usage guide | Instructors & End Users |
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

- **Documentation**: [Complete guides](USERGUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/aknoesen/q2lms/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aknoesen/q2lms/discussions)

---

**Built for educators by educators**