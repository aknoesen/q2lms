import streamlit as st
import io
import os
import json
import tempfile
from datetime import datetime

def export_to_csv(df, filename="filtered_questions.csv"):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )

def create_qti_package(df, original_questions, quiz_title, transform_json_to_csv, csv_to_qti):
    if df is None or len(df) == 0:
        st.error("❌ No questions to export.")
        return
    try:
        with st.spinner("🔄 Creating QTI package..."):
            filtered_question_ids = df['ID'].tolist()
            filtered_questions = []
            for i, q in enumerate(original_questions):
                question_id = f"Q_{i+1:05d}"
                if question_id in filtered_question_ids:
                    filtered_questions.append(q)
            temp_json = {
                "questions": filtered_questions,
                "metadata": {
                    "generated_by": "Streamlit Question Database Manager",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "total_questions": len(filtered_questions),
                    "filter_applied": True
                }
            }
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(temp_json, temp_file, indent=2)
                temp_json_path = temp_file.name
            temp_csv_path = temp_json_path.replace('.json', '.csv')
            success = transform_json_to_csv(temp_json_path, temp_csv_path)
            if success:
                qti_success = csv_to_qti(temp_csv_path, quiz_title)
                if qti_success:
                    zip_filename = f"{quiz_title}.zip"
                    if os.path.exists(zip_filename):
                        with open(zip_filename, 'rb') as f:
                            zip_data = f.read()
                        st.success(f"✅ QTI package created successfully!")
                        st.download_button(
                            label="📦 Download QTI Package",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip"
                        )
                        os.unlink(zip_filename)
                    else:
                        st.error("❌ QTI package file not found")
                else:
                    st.error("❌ Failed to create QTI package")
            else:
                st.error("❌ Failed to convert JSON to CSV")
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)
            if os.path.exists(temp_csv_path):
                os.unlink(temp_csv_path)
    except Exception as e:
        st.error(f"❌ Error creating QTI package: {str(e)}")
