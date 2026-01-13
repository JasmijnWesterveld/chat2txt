#!/usr/bin/env python3

import streamlit as st
import re
import os
from io import StringIO
import zipfile

# Matches lines like: *PAR123: some text . code_code
body_line_regex = re.compile(r'^\*PAR(\d+):\s+(.*) . (\S+_\S+)$')

def segment_into_c_units(text):
    """
    Splits text into communication units (C-units).
    A simple approach:
      1. Split on sentence-ending punctuation (.?!)
      2. Strip whitespace
      3. Discard empty units
      4. Add a final period to each unit
    """
    # Replace &-<word> patterns with (<word>)
    text = re.sub(r'&-(\w+)', r'(\1)', text)
    
    # Handle [/] marker for multi-word repetitions: <words> [/] words -> (words) words
    text = re.sub(r'<([^>]+)>\s*\[/\]\s*\1', r'(\1) \1', text)
    
    # Handle [/] marker for single-word repetitions: word [/] word -> (word) word
    text = re.sub(r'(\S+)\s*\[/\]\s*\1', r'(\1) \1', text)
    
    # Split on punctuation marks that can end a C-unit
    raw_units = re.split(r'[.?!]', text)

    c_units = []
    for unit in raw_units:
        unit = unit.strip()
        if unit:
            # Add final period if missing
            if not unit.endswith('.'):
                unit = unit + '.'
            c_units.append(unit)

    return c_units


def process_cha_file(file_content, include_prompts=True):
    """Process a single .cha file and return output as string."""
    output = StringIO()
    
    try:
        lines = file_content.split('\n')
        
        # First pass: find which PAR contains "listen to each prompt" and get last timestamp
        prompt_par = None
        last_timestamp = 0
        for line in lines:
            line = line.rstrip('\r\n\x15')
            utterance_match = body_line_regex.match(line)
            if utterance_match:
                par_num = utterance_match.group(1)
                utterance_text = utterance_match.group(2)
                timestamp_code = utterance_match.group(3).strip()
                
                # Extract timestamp
                try:
                    timestamp_ms = int(timestamp_code.split('_')[-1])
                    last_timestamp = timestamp_ms
                except (ValueError, IndexError):
                    pass
                
                if 'listen to each prompt' in utterance_text:
                    prompt_par = par_num
        
        # Track which prompts were found
        prompts_found = {
            'happy': False,
            'angry': False,
            'confused': False,
            'proud': False,
            'problem': False,
            'important': False
        }
        
        # Second pass: process the file
        output.write("- 0:00\n")
        
        for line in lines:
            line = line.rstrip('\r\n\x15')
            utterance_match = body_line_regex.match(line)
            if utterance_match:
                par_num = utterance_match.group(1)
                utterance_text = utterance_match.group(2)
                timestamp_code = utterance_match.group(3).strip()
                
                # Extract timestamp from the code (format: code_milliseconds)
                try:
                    timestamp_ms = int(timestamp_code.split('_')[-1])
                    last_timestamp = timestamp_ms
                except (ValueError, IndexError):
                    pass

                # Convert to C-units
                c_units = segment_into_c_units(utterance_text)

                # Determine prefix: 'E' for the PAR with "listen to each prompt", 'C' for the other
                if prompt_par and par_num == prompt_par:
                    prefix = 'E'
                else:
                    prefix = 'C'

                # Write each unit as a separate line with appropriate prefix
                for cu in c_units:
                    output.write(f"{prefix} {cu}\n")
                    
                    # Only check for prompts if enabled
                    if include_prompts:
                        # Check if contains the phrase about excited/happy
                        if 'story about a time when you felt excited or really happy' in utterance_text:
                            output.write("+ happy\n")
                            prompts_found['happy'] = True
                        
                        # Check if contains the phrase about annoyed/angry
                        if 'story about a time when you were really annoyed or angry' in utterance_text:
                            output.write("+ angry\n")
                            prompts_found['angry'] = True
                        
                        # Check if contains the phrase about worried/confused
                        if 'story about a time when you felt worried or confused' in utterance_text:
                            output.write("+ confused\n")
                            prompts_found['confused'] = True
                        
                        # Check if contains the phrase about proud
                        if 'story about a time when you felt proud of yourself' in utterance_text:
                            output.write("+ proud\n")
                            prompts_found['proud'] = True
                        
                        # Check if contains the phrase about problem
                        if 'story about a time when you had a problem' in utterance_text:
                            output.write("+ problem\n")
                            prompts_found['problem'] = True
                        
                        # Check if contains the phrase about important
                        if 'story about something that has happened to you that was very important to you' in utterance_text:
                            output.write("+ important\n")
                            prompts_found['important'] = True
        
        # Convert last timestamp from milliseconds to min:seconds and write at end
        if last_timestamp > 0:
            total_seconds = last_timestamp // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            output.write(f"- {minutes}:{seconds:02d}\n")
        
        return output.getvalue(), prompts_found
        
    except Exception as e:
        return f"Error processing file: {str(e)}", {}


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
        st.subheader("📤 Upload Files")
        uploaded_files = st.file_uploader(
            "Select .cha file(s) to convert",
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
                
                # Process the file
                output_content, prompts_found = process_cha_file(content, include_prompts)
                
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
