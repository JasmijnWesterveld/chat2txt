#!/usr/bin/env python3
"""Shared CHAT file processing logic used by both GUI and web app."""

import re
from io import StringIO

# Matches lines like: *PAR123: some text . code_code
BODY_LINE_REGEX = re.compile(r'^\*PAR(\d+):\s+(.*) . (\S+_\S+)$')

PROMPTS = {
    'happy': 'story about a time when you felt excited or really happy',
    'angry': 'story about a time when you were really annoyed or angry',
    'confused': 'story about a time when you felt worried or confused',
    'proud': 'story about a time when you felt proud of yourself',
    'problem': 'story about a time when you had a problem',
    'important': 'story about something that has happened to you that was very important to you'
}


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


def process_cha_content(content, include_prompts=True):
    """
    Process CHAT format content and return converted text with prompt metadata.
    
    Args:
        content: String content of the .cha file
        include_prompts: Whether to detect and tag Global Tales prompts
    
    Returns:
        Tuple of (output_text, prompts_found_dict)
    """
    output = StringIO()
    
    lines = content.split('\n')
    
    # First pass: find which PAR contains "listen to each prompt" and get last timestamp
    prompt_par = None
    last_timestamp = 0
    for line in lines:
        line = line.rstrip('\r\n\x15')
        utterance_match = BODY_LINE_REGEX.match(line)
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
    prompts_found = {prompt: False for prompt in PROMPTS.keys()}
    
    # Second pass: process the file
    output.write("- 0:00\n")
    
    for line in lines:
        line = line.rstrip('\r\n\x15')
        utterance_match = BODY_LINE_REGEX.match(line)
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
                    for prompt_name, prompt_phrase in PROMPTS.items():
                        if prompt_phrase in utterance_text:
                            output.write(f"+ {prompt_name}\n")
                            prompts_found[prompt_name] = True
    
    # Convert last timestamp from milliseconds to min:seconds and write at end
    if last_timestamp > 0:
        total_seconds = last_timestamp // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        output.write(f"- {minutes}:{seconds:02d}\n")
    
    return output.getvalue(), prompts_found
