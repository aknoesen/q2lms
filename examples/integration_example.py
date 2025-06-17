#!/usr/bin/env python3
"""
LaTeX Processor Integration Example
Shows how to integrate the LaTeX processor with the existing Streamlit app
"""

import json
import streamlit as st
from latex_processor import LaTeXProcessor, process_question_list
from typing import Dict, List, Tuple

def integrate_latex_processing_to_streamlit():
    """
    Example of how to integrate LaTeX processing into the existing Streamlit app
    This would be added to your load_database_from_json function
    """
    
    # Initialize the processor (you'd do this once at module level)
    latex_processor = LaTeXProcessor()
    
    def enhanced_load_database_from_json(json_content: str, auto_cleanup: bool = True):
        """
        Enhanced version of your existing function with LaTeX processing
        """
        try:
            data = json.loads(json_content)
            
            # Handle both formats: {"questions": [...]} or direct [...]
            if isinstance(data, dict) and 'questions' in data:
                questions = data['questions']
                metadata = data.get('metadata', {})
            elif isinstance(data, list):
                questions = data
                metadata = {}
            else:
                st.error("❌ Unexpected JSON structure")
                return None, None, None, None
            
            # NEW: LaTeX Processing Step
            cleanup_reports = []
            if auto_cleanup:
                with st.spinner("🔄 Processing LaTeX notation..."):
                    cleaned_questions, cleanup_reports = latex_processor.process_question_database(questions)
                    questions = cleaned_questions
                    
                    # Show cleanup summary
                    if cleanup_reports:
                        total_unicode = sum(r.unicode_conversions for r in cleanup_reports)
                        total_fixes = sum(len(r.changes_made) for r in cleanup_reports)
                        
                        st.success(f"✅ LaTeX Processing Complete!")
                        st.info(f"""**Cleanup Summary:**
- Questions processed: {len(cleanup_reports)}
- Unicode symbols converted: {total_unicode}
- Total formatting fixes: {total_fixes}
""")
                        
                        # Option to show detailed reports
                        if st.expander("📋 View Detailed Cleanup Reports"):
                            for i, report in enumerate(cleanup_reports):
                                if report.changes_made:
                                    st.write(f"**Question {i+1}:**")
                                    for change in report.changes_made:
                                        st.write(f"  • {change}")
            
            # Continue with existing DataFrame conversion logic...
            rows = []
            for i, q in enumerate(questions):
                # Your existing logic here
                question_id = f"Q_{i+1:05d}"
                # ... rest of your existing conversion code
                pass
            
            # Return the processed data
            return df, metadata, questions, cleanup_reports
            
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")
            return None, None, None, None
        except Exception as e:
            st.error(f"❌ Error processing database: {e}")
            return None, None, None, None

def add_latex_processing_tab():
    """
    Example of adding a dedicated LaTeX processing tab to your Streamlit app
    """
    
    st.markdown("### 🧮 LaTeX Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Processing Options:**")
        
        # Option to reprocess with different settings
        if st.button("🔄 Reprocess LaTeX"):
            if 'original_questions' in st.session_state:
                processor = LaTeXProcessor()
                cleaned_questions, reports = processor.process_question_database(
                    st.session_state['original_questions']
                )
                st.session_state['processed_questions'] = cleaned_questions
                st.session_state['cleanup_reports'] = reports
                st.success("✅ LaTeX reprocessing complete!")
        
        # Option to validate all LaTeX
        if st.button("✅ Validate All LaTeX"):
            if 'df' in st.session_state:
                processor = LaTeXProcessor()
                validation_results = []
                
                for idx, row in st.session_state['df'].iterrows():
                    for field in ['Question_Text', 'Correct_Answer', 'Feedback']:
                        if row[field]:
                            is_valid, errors = processor.validate_latex_syntax(row[field])
                            if not is_valid:
                                validation_results.append({
                                    'question_id': row['ID'],
                                    'field': field,
                                    'errors': errors
                                })
                
                if validation_results:
                    st.warning(f"⚠️ Found {len(validation_results)} validation issues")
                    for result in validation_results[:10]:  # Show first 10
                        st.write(f"**{result['question_id']} - {result['field']}:** {result['errors']}")
                else:
                    st.success("✅ All LaTeX notation is valid!")
    
    with col2:
        st.markdown("**Processing Statistics:**")
        
        if 'cleanup_reports' in st.session_state:
            reports = st.session_state['cleanup_reports']
            
            # Statistics
            total_questions = len(reports)
            questions_changed = len([r for r in reports if r.changes_made])
            total_unicode = sum(r.unicode_conversions for r in reports)
            total_syntax_fixes = sum(r.syntax_errors_fixed for r in reports)
            mixed_notation_count = len([r for r in reports if r.mixed_notation_detected])
            
            st.metric("Questions Processed", total_questions)
            st.metric("Questions Modified", questions_changed)
            st.metric("Unicode Conversions", total_unicode)
            st.metric("Syntax Fixes", total_syntax_fixes)
            st.metric("Mixed Notation Detected", mixed_notation_count)

def add_latex_preview_enhancement():
    """
    Enhanced preview function that shows before/after LaTeX processing
    """
    
    def enhanced_display_question_preview(question_row, show_original=False):
        """
        Enhanced version of your display_question_preview function
        """
        
        # Your existing preview code...
        st.markdown('<div class="question-preview">', unsafe_allow_html=True)
        
        # Header with metadata (existing code)
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"**{question_row['Title']}**")
        # ... rest of existing header code
        
        # NEW: LaTeX processing indicator
        if 'cleanup_reports' in st.session_state:
            question_num = int(question_row['ID'].split('_')[1]) - 1
            if question_num < len(st.session_state['cleanup_reports']):
                report = st.session_state['cleanup_reports'][question_num]
                if report.changes_made:
                    st.info(f"🧮 LaTeX processed: {len(report.changes_made)} changes made")
        
        # Question text with enhanced LaTeX rendering
        question_text = render_latex_in_text(question_row['Question_Text'])
        st.markdown(f"**Question:** {question_text}")
        
        # NEW: Option to show original vs processed
        if show_original and 'original_questions' in st.session_state:
            with st.expander("👁️ Show Original vs Processed"):
                question_num = int(question_row['ID'].split('_')[1]) - 1
                if question_num < len(st.session_state['original_questions']):
                    original = st.session_state['original_questions'][question_num]
                    st.markdown("**Original:**")
                    st.code(original.get('question_text', ''), language='text')
                    st.markdown("**Processed:**")
                    st.code(question_row['Question_Text'], language='text')
        
        # ... rest of existing preview code
        st.markdown('</div>', unsafe_allow_html=True)

def demo_latex_processing():
    """
    Standalone demo of LaTeX processing capabilities
    """
    
    st.markdown("# 🧮 LaTeX Processor Demo")
    
    # Initialize processor
    processor = LaTeXProcessor()
    
    # Input section
    st.markdown("## 📝 Input Text")
    sample_texts = [
        "Circuit with R = 50Ω, C = 10μF at frequency f = 1000Hz",
        "The impedance Z = R + jXₗ where Xₗ = ωL and ω = 2πf",
        "Phase angle ∠45° with magnitude |Z| = √(R² + X²)",
        "RMS voltage$V_{RMS} = \\frac{V_m}{\\sqrt{2}}$for sinusoidal signals"
    ]
    
    selected_sample = st.selectbox("Choose a sample or enter custom text:", 
                                   ["Custom"] + sample_texts)
    
    if selected_sample == "Custom":
        input_text = st.text_area("Enter text with mathematical notation:", 
                                  height=100)
    else:
        input_text = selected_sample
        st.text_area("Selected text:", value=input_text, height=100, disabled=True)
    
    if input_text:
        # Processing section
        st.markdown("## 🔄 Processing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Process LaTeX"):
                # Process the text
                cleaned_text = processor.clean_mathematical_notation(input_text)
                report = processor.generate_cleanup_report(input_text, cleaned_text)
                
                # Store results
                st.session_state['demo_original'] = input_text
                st.session_state['demo_cleaned'] = cleaned_text
                st.session_state['demo_report'] = report
        
        with col2:
            if st.button("✅ Validate LaTeX"):
                if 'demo_cleaned' in st.session_state:
                    is_valid, errors = processor.validate_latex_syntax(
                        st.session_state['demo_cleaned']
                    )
                    st.session_state['demo_validation'] = (is_valid, errors)
        
        # Results section
        if 'demo_cleaned' in st.session_state:
            st.markdown("## 📊 Results")
            
            # Before/After comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Original:**")
                st.code(st.session_state['demo_original'], language='text')
            
            with col2:
                st.markdown("**Processed:**")
                st.code(st.session_state['demo_cleaned'], language='text')
            
            # Rendered preview
            st.markdown("**Rendered Preview:**")
            st.markdown(st.session_state['demo_cleaned'])
            
            # Cleanup report
            if 'demo_report' in st.session_state:
                report = st.session_state['demo_report']
                st.markdown("**Cleanup Report:**")
                st.info(str(report))
            
            # Validation results
            if 'demo_validation' in st.session_state:
                is_valid, errors = st.session_state['demo_validation']
                if is_valid:
                    st.success("✅ LaTeX syntax is valid!")
                else:
                    st.error("❌ LaTeX syntax errors found:")
                    for error in errors:
                        st.write(f"  • {error}")

def create_latex_settings_sidebar():
    """
    Add LaTeX processing settings to the sidebar
    """
    
    st.sidebar.markdown("## 🧮 LaTeX Processing")
    
    # Auto-processing option
    auto_process = st.sidebar.checkbox("Auto-process LaTeX on upload", value=True)
    
    # Processing options
    st.sidebar.markdown("**Processing Options:**")
    convert_unicode = st.sidebar.checkbox("Convert Unicode symbols", value=True)
    fix_equations = st.sidebar.checkbox("Fix equation formatting", value=True)
    fix_syntax = st.sidebar.checkbox("Fix syntax errors", value=True)
    
    # Validation options
    st.sidebar.markdown("**Validation:**")
    validate_after_processing = st.sidebar.checkbox("Validate after processing", value=True)
    show_warnings = st.sidebar.checkbox("Show validation warnings", value=True)
    
    # Advanced options
    with st.sidebar.expander("⚙️ Advanced Options"):
        preserve_original = st.checkbox("Preserve original text", value=True)
        detailed_reports = st.checkbox("Generate detailed reports", value=False)
        electrical_mode = st.checkbox("Electrical engineering mode", value=True)
    
    return {
        'auto_process': auto_process,
        'convert_unicode': convert_unicode,
        'fix_equations': fix_equations,
        'fix_syntax': fix_syntax,
        'validate_after_processing': validate_after_processing,
        'show_warnings': show_warnings,
        'preserve_original': preserve_original,
        'detailed_reports': detailed_reports,
        'electrical_mode': electrical_mode
    }

# Example of how to modify your existing Streamlit app's main function
def enhanced_main():
    """
    Example of enhanced main function with LaTeX processing integration
    """
    
    # Page configuration (existing)
    st.set_page_config(
        page_title="Question Database Manager with LaTeX Processing",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header (existing)
    st.markdown("# 📊 Question Database Manager")
    st.markdown("**Web-based interface with advanced LaTeX processing**")
    
    # NEW: LaTeX settings in sidebar
    latex_settings = create_latex_settings_sidebar()
    
    # File upload (existing logic with enhancement)
    uploaded_file = st.file_uploader(
        "📁 Upload Question Database (JSON)",
        type=['json'],
        help="Upload a Phase 3 or Phase 4 JSON question database file"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        
        with st.spinner("🔄 Processing database..."):
            # Use enhanced function with LaTeX processing
            df, metadata, original_questions, cleanup_reports = enhanced_load_database_from_json(
                content, 
                auto_cleanup=latex_settings['auto_process']
            )
        
        if df is not None:
            # Store in session state (including new LaTeX data)
            st.session_state['df'] = df
            st.session_state['metadata'] = metadata
            st.session_state['original_questions'] = original_questions
            st.session_state['cleanup_reports'] = cleanup_reports
            st.session_state['filename'] = uploaded_file.name
            
            st.success(f"✅ Database loaded and processed! {len(df)} questions ready.")
    
    # Main interface with LaTeX processing tab
    if 'df' in st.session_state:
        df = st.session_state['df']
        
        # Enhanced tabs with LaTeX processing
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🔍 Browse Questions", 
            "🧮 LaTeX Processing",  # NEW TAB
            "🎯 Quiz Builder", 
            "📥 Export"
        ])
        
        with tab1:
            # Existing overview code
            pass
        
        with tab2:
            # Existing browse code with enhanced preview
            pass
        
        with tab3:
            # NEW: LaTeX processing tab
            add_latex_processing_tab()
        
        with tab4:
            # Existing quiz builder code
            pass
        
        with tab5:
            # Existing export code
            pass
    
    else:
        # Landing page with LaTeX demo
        st.markdown("## 🚀 Getting Started")
        st.markdown("Upload a JSON question database to begin, or try the LaTeX processor:")
        
        if st.button("🧮 Try LaTeX Processor Demo"):
            demo_latex_processing()

if __name__ == "__main__":
    # Run the demo
    demo_latex_processing()
