#!/usr/bin/env python3

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import re
import threading
import subprocess
import platform

# Matches lines like:
# *PAR123: some text . code_code
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


def process_cha_file(input_file, output_text_widget, include_prompts=True):
    """Process a single .cha file and write output."""
    try:
        base_name = os.path.splitext(input_file)[0]
        output_file = base_name + '_CU.txt'
        
        output_text_widget.configure(state="normal")
        output_text_widget.insert("end", f"\nProcessing: {os.path.basename(input_file)}\n")
        output_text_widget.configure(state="disabled")
        output_text_widget.see("end")
        output_text_widget.update()
        
        # First pass: find which PAR contains "listen to each prompt" and get last timestamp
        prompt_par = None
        last_timestamp = 0
        with open(input_file, 'r', encoding='utf-8-sig') as infile:
            for line in infile:
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
        phrases_found_count = 0
        
        # Second pass: process the file
        with open(input_file, 'r', encoding='utf-8-sig') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
            # Write starting timestamp
            outfile.write("- 0:00\n")
            
            for line in infile:
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
                        outfile.write(f"{prefix} {cu}\n")
                        
                        # Only check for prompts if enabled
                        if include_prompts:
                            # Check if contains the phrase about excited/happy
                            if 'story about a time when you felt excited or really happy' in utterance_text:
                                outfile.write("+ happy\n")
                                prompts_found['happy'] = True
                                phrases_found_count += 1
                            
                            # Check if contains the phrase about annoyed/angry
                            if 'story about a time when you were really annoyed or angry' in utterance_text:
                                outfile.write("+ angry\n")
                                prompts_found['angry'] = True
                                phrases_found_count += 1
                            
                            # Check if contains the phrase about worried/confused
                            if 'story about a time when you felt worried or confused' in utterance_text:
                                outfile.write("+ confused\n")
                                prompts_found['confused'] = True
                                phrases_found_count += 1
                            
                            # Check if contains the phrase about proud
                            if 'story about a time when you felt proud of yourself' in utterance_text:
                                outfile.write("+ proud\n")
                                prompts_found['proud'] = True
                                phrases_found_count += 1
                            
                            # Check if contains the phrase about problem
                            if 'story about a time when you had a problem' in utterance_text:
                                outfile.write("+ problem\n")
                                prompts_found['problem'] = True
                                phrases_found_count += 1
                            
                            # Check if contains the phrase about important
                            if 'story about something that has happened to you that was very important to you' in utterance_text:
                                outfile.write("+ important\n")
                                prompts_found['important'] = True
                                phrases_found_count += 1
            
            # Convert last timestamp from milliseconds to min:seconds and write at end
            if last_timestamp > 0:
                total_seconds = last_timestamp // 1000
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                outfile.write(f"- {minutes}:{seconds:02d}\n")
        
        # Print status of prompts found
        output_text_widget.configure(state="normal")
        output_text_widget.insert("end", f"\nProcessed {os.path.basename(input_file)}.")
        
        if include_prompts:
            output_text_widget.insert("end", f" Prompts found:\n")
            for prompt, found in prompts_found.items():
                status = "✓ Found" if found else "✗ Not found"
                output_text_widget.insert("end", f"  {prompt}: {status}\n")
            
            not_found = [prompt for prompt, found in prompts_found.items() if not found]
            if not_found:
                output_text_widget.insert("end", f"\nWarning: The following prompts were not found: {', '.join(not_found)}\n")
        else:
            output_text_widget.insert("end", f" (Prompts excluded)\n")
        
        output_text_widget.insert("end", f"✓ Output saved to: {output_file}\n")
        output_text_widget.configure(state="disabled")
        output_text_widget.see("end")
        output_text_widget.update()
        
    except Exception as e:
        output_text_widget.configure(state="normal")
        output_text_widget.insert("end", f"✗ Error processing {input_file}: {str(e)}\n")
        output_text_widget.configure(state="disabled")
        output_text_widget.see("end")
        output_text_widget.update()


class ChatToTxtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat to TXT Converter")
        self.root.geometry("700x600")
        self.root.configure(fg_color="#f0f0f0")  # Light grey background
        
        # Title
        title_label = ctk.CTkLabel(root, text="Chat to TXT Converter", font=("Arial", 16, "bold"), text_color="black")
        title_label.pack(pady=10)
        
        # File/Folder selection frame
        selection_frame = ctk.CTkFrame(root, fg_color="#f0f0f0")
        selection_frame.pack(padx=10, pady=10, fill="x")
        
        self.file_label = ctk.CTkLabel(selection_frame, text="No file or folder selected", wraplength=400, justify="left", font=("Arial", 14, "bold"), text_color="red", fg_color="#f0f0f0")
        self.file_label.pack(anchor="w", pady=5)
        
        button_frame = ctk.CTkFrame(selection_frame, fg_color="#f0f0f0")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="SELECT .CHA FILE", command=self.select_file, width=200, text_color="white").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="SELECT FOLDER", command=self.select_folder, width=200, text_color="white").pack(side="left", padx=5)
        
        # Options frame
        options_frame = ctk.CTkFrame(root, fg_color="#f0f0f0")
        options_frame.pack(padx=10, pady=5, fill="x")
        
        self.include_prompts_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_frame, text="ADD GLOBAL TALES PROMPTS", variable=self.include_prompts_var, checkmark_color="white").pack(anchor="w")
        
        # Run and Open buttons frame
        run_frame = ctk.CTkFrame(root, fg_color="#f0f0f0")
        run_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkButton(run_frame, text="RUN CONVERSION", command=self.run_conversion, width=200, fg_color="#2dcc71", hover_color="#27ae60", text_color="white").pack(side="left", padx=5)
        self.open_button = ctk.CTkButton(run_frame, text="OPEN FILE LOCATION", command=self.open_output, width=200, fg_color="transparent", border_width=2, border_color="#3B8ED0", text_color="#3B8ED0", hover_color="#e0e0e0")
        self.open_button.pack(side="left", padx=5)
        
        # Output text area
        output_header_frame = ctk.CTkFrame(root, fg_color="#f0f0f0")
        output_header_frame.pack(anchor="w", padx=10, pady=(10, 0), fill="x")
        
        output_label = ctk.CTkLabel(output_header_frame, text="Output:", font=("Arial", 10, "bold"), text_color="black", fg_color="#f0f0f0")
        output_label.pack(side="left")
        
        clear_button = ctk.CTkButton(output_header_frame, text="CLEAR OUTPUT", command=self.clear_output, width=80, font=("Arial", 10), fg_color="transparent", border_width=2, border_color="#3B8ED0", text_color="#3B8ED0", hover_color="#e0e0e0")
        clear_button.pack(side="right", padx=5)
        
        self.output_text = ctk.CTkTextbox(root, height=20, width=80, wrap="word", state="disabled")
        self.output_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.selected_files = []
        self.output_folder = None
    
    def select_file(self):
        """Select a single .cha file."""
        file_path = filedialog.askopenfilename(
            title="Select a .cha file",
            filetypes=[("CHAT files", "*.cha"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_files = [file_path]
            self.output_folder = os.path.dirname(file_path)
            self.file_label.configure(text=f"Selected: {os.path.basename(file_path)}", text_color="black")
            self.open_button.configure(state="disabled")
    
    def select_folder(self):
        """Select a folder containing .cha files."""
        folder_path = filedialog.askdirectory(title="Select a folder containing .cha files")
        if folder_path:
            cha_files = [f for f in os.listdir(folder_path) if f.endswith('.cha')]
            if cha_files:
                self.selected_files = [os.path.join(folder_path, f) for f in cha_files]
                self.output_folder = folder_path
                self.file_label.configure(text=f"Selected folder: {os.path.basename(folder_path)} ({len(cha_files)} .cha files found)", text_color="black")
                self.open_button.configure(state="disabled")
            else:
                messagebox.showwarning("No Files", "No .cha files found in the selected folder.")
                self.selected_files = []
                self.output_folder = None
                self.file_label.configure(text_color="red")
    
    def open_output(self):
        """Open the output folder in file explorer."""
        if self.output_folder is None:
            messagebox.showwarning("No Output", "Please select a file or folder first.")
            return
        
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', self.output_folder])
            elif platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{self.output_folder}"')
            elif platform.system() == 'Linux':
                subprocess.Popen(['xdg-open', self.output_folder])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
    
    def clear_output(self):
        """Clear the output text box."""
        self.output_text.configure(state="normal")
        self.output_text.delete(1.0, "end")
        self.output_text.configure(state="disabled")
    
    def run_conversion(self):
        """Run the conversion on selected files."""
        if not self.selected_files:
            messagebox.showerror("Error", "Please select a file or folder first.")
            return
        
        self.output_text.configure(state="normal")
        self.output_text.insert("end", "\n" + "="*50 + "\nStarting conversion...\n")
        self.output_text.configure(state="disabled")
        
        # Run in a separate thread to avoid freezing the GUI
        thread = threading.Thread(target=self._process_files)
        thread.start()
    
    def _process_files(self):
        """Process all selected files."""
        include_prompts = self.include_prompts_var.get()
        for file_path in self.selected_files:
            process_cha_file(file_path, self.output_text, include_prompts=include_prompts)
        
        self.output_text.configure(state="normal")
        self.output_text.insert("end", "\n✓ All conversions completed!\n")
        self.output_text.configure(state="disabled")
        self.output_text.see("end")
        self.output_text.update()
        
        # Enable the open button after conversion
        self.open_button.configure(state="normal")


def main():
    """Entry point for the application."""
    ctk.set_appearance_mode("system")  # Follows system dark/light mode
    ctk.set_default_color_theme("blue")  # Modern blue theme
    root = ctk.CTk()
    gui = ChatToTxtGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
