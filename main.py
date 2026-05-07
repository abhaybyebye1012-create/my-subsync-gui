#!/usr/bin/env python3
import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

class SubSyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FFSubsync Standalone")
        self.root.geometry("600x500")
        
        # Detect if running inside an AppImage to fix binary paths
        app_dir = None
        if 'APPIMAGE' in os.environ:
            app_path = os.path.abspath(os.environ.get('APPIMAGE', ''))
            app_dir = str(Path(app_path).parent)
            # Add the AppImage internal bin folder to system PATH so subprocess finds ffmpeg
            if os.path.isdir(os.path.join(app_dir, 'usr', 'bin')):
                original_path = os.environ.get('PATH', '')
                os.environ['PATH'] = os.path.join(app_dir, 'usr', 'bin') + ':' + original_path
        
        # UI Elements
        frame_input = ttk.LabelFrame(root, text="Input Files")
        frame_input.pack(fill="x", padx=10, pady=5)

        self.video_var = tk.StringVar()
        tk.Button(frame_input, text="Select Video", command=self.select_video).pack(side="left", padx=5)
        self.video_entry = tk.Entry(frame_input, textvariable=self.video_var, state='readonly')
        self.video_entry.pack(fill="x", expand=True, padx=5)

        self.subtitle_var = tk.StringVar()
        tk.Button(frame_input, text="Select Subtitle (.srt)", command=self.select_subtitle).pack(side="left", padx=5)
        self.subtitle_entry = tk.Entry(frame_input, textvariable=self.subtitle_var, state='readonly')
        self.subtitle_entry.pack(fill="x", expand=True, padx=5)

        frame_output = ttk.LabelFrame(root, text="Output")
        frame_output.pack(fill="x", padx=10, pady=5)
        
        self.output_var = tk.StringVar()
        tk.Button(frame_output, text="Select Output Folder", command=self.select_output_dir).pack(side="left", padx=5)
        self.output_entry = tk.Entry(frame_output, textvariable=self.output_var)
        self.output_entry.pack(fill="x", expand=True, padx=5)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="START SYNC", command=self.run_sync, style="Accent.TButton")
        self.start_btn.pack(padx=20)

        self.log_text = scrolledtext.ScrolledText(root, height=15, width=70)
        self.log_text.pack(padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def select_video(self):
        path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov"), ("All", "*.*")])
        if path:
            self.video_var.set(path)
            # Auto-set output sub-name based on video name
            out_name = os.path.splitext(os.path.basename(path))[0] + ".srt"
            # We don't set the full path immediately as it depends on output dir selection

    def select_subtitle(self):
        path = filedialog.askopenfilename(title="Select Source Subtitle", filetypes=[("Subtitles", "*.srt *.ass *.ssa"), ("All", "*.*")])
        if path:
            self.subtitle_var.set(path)

    def select_output_dir(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_var.set(path)

    def run_sync(self):
        video_path = self.video_var.get()
        sub_path = self.subtitle_var.get()
        out_dir = self.output_var.get()

        if not video_path or not sub_path or not out_dir:
            messagebox.showerror("Error", "Please select video, subtitle, and output directory.")
            return

        outfile = os.path.join(out_dir, os.path.basename(sub_path.replace('.srt', '_synced.srt')))
        
        cmd = [
            "subsync", 
            "-i", video_path, 
            "-s", sub_path, 
            "-o", outfile
        ]

        self.log(f"Running command: {' '.join(cmd)}")
        self.start_btn.config(state=tk.DISABLED)

        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                universal_newlines=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self.log(line.rstrip())
                
            process.wait()
            
            if process.returncode == 0:
                self.log("SUCCESS: Sync completed.")
                messagebox.showinfo("Success", f"Synced subtitle saved to:\n{outfile}")
            else:
                self.log("ERROR: Sync failed.")
                messagebox.showerror("Failed", "Synchronization failed. Check logs above.")
                
        except FileNotFoundError:
            self.log("FATAL ERROR: Could not find 'subsync' command.")
            self.log("Is ffmpeg installed on this system or bundled correctly?")
        except Exception as e:
            self.log(f"UNEXPECTED ERROR: {str(e)}")
        finally:
            self.start_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = SubSyncGUI(root)
    root.mainloop()
