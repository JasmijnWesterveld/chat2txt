#!/usr/bin/env python3

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess
import platform
from chat2txt.processor import process_cha_content

def process_cha_file(input_file, output_text_widget, include_prompts=True):
    """Process a single .cha file and write output to disk."""
    try:
        base_name = os.path.splitext(input_file)[0]
        output_file = base_name + '_CU.txt'
        
        output_text_widget.configure(state="normal")
        output_text_widget.insert("end", f"\nProcessing: {os.path.basename(input_file)}\n")
        output_text_widget.configure(state="disabled")
        output_text_widget.see("end")
        output_text_widget.update()
        
        # Read the input file
        with open(input_file, 'r', encoding='utf-8-sig') as infile:
            content = infile.read()
        
        # Process using shared processor
        output_content, prompts_found = process_cha_content(content, include_prompts)
        
        # Write output to disk
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(output_content)
        
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
