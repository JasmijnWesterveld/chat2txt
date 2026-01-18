#!/usr/bin/env python3

import streamlit as st
import os
import zipfile
from io import StringIO
from chat2txt.processor import process_cha_content


def main():
    st.set_page_config(page_title="Chat to TXT Converter", layout="wide")
    st.title("🎙️ Chat to TXT Converter")
    st.markdown("Convert CHAT format files (.cha) to TXT format with communication unit segmentation.")
    
    # Sidebar for options
    with st.sidebar:
        st.header("Settings")
        include_prompts = st.checkbox("Add Global Tales Prompts", value=False)
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool converts CHAT format files to TXT with:
        - Communication unit (C-unit) segmentation
        - Optional Global Tales prompt detection
        - Timestamp tracking
        """)
    
    # Main content area with columns
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.subheader("📤 Select Files")
        uploaded_files = st.file_uploader(
            "Select .cha file(s) to convert. Note. These files are not uploaded anywhere but stored in memory.",
            type=["cha"],
            accept_multiple_files=True
        )
    
    # Process files and display on the right
    with col2:
        st.subheader("📥 Results")
        
        if uploaded_files:
            results = []
            download_files = {}
            
            for uploaded_file in uploaded_files:
                # Read the uploaded file
                content = uploaded_file.read().decode('utf-8-sig')
                base_name = os.path.splitext(uploaded_file.name)[0]
                output_name = f"{base_name}_CU.txt"
                
                # Process the file using shared processor
                output_content, prompts_found = process_cha_content(content, include_prompts)
                
                # Store results
                results.append({
                    'name': uploaded_file.name,
                    'output_name': output_name,
                    'content': output_content,
                    'prompts': prompts_found
                })
                download_files[output_name] = output_content
                
                # Display results for this file
                st.success(f"✓ {uploaded_file.name}")
                
                if include_prompts and prompts_found:
                    with st.expander("View Prompts"):
                        for prompt, found in prompts_found.items():
                            status = "✅" if found else "❌"
                            st.write(f"{status} {prompt.capitalize()}")
                
                st.markdown("---")
            
            # Download section
            st.subheader("Download")
            
            if len(download_files) == 1:
                # Single file - direct download
                output_name = list(download_files.keys())[0]
                content = download_files[output_name]
                st.download_button(
                    label=f"📄 {output_name}",
                    data=content,
                    file_name=output_name,
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                # Multiple files - zip download
                zip_buffer = StringIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_name, content in download_files.items():
                        zip_file.writestr(file_name, content)
                
                st.download_button(
                    label=f"📦 Download All ({len(download_files)} files)",
                    data=zip_buffer.getvalue(),
                    file_name="converted_files.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        else:
            st.info("Upload files to see results here")


if __name__ == "__main__":
    main()
