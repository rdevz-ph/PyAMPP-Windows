import customtkinter as ctk
import subprocess
import os
from pathlib import Path
from core.config import config_manager

class PHPCLIFrame(ctk.CTkFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, fg_color=["#ffffff", "#1a2333"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#2d3748"], **kwargs)
        self.logger = logger

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Instruction Label
        self.label = ctk.CTkLabel(self, text="PHP CLI Tester", font=ctk.CTkFont(size=18, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Command Entry
        self.cmd_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cmd_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.cmd_frame.grid_columnconfigure(0, weight=1)

        self.cmd_entry = ctk.CTkEntry(self.cmd_frame, placeholder_text="e.g. php -v  or  echo 'Hello World';")
        self.cmd_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.cmd_entry.bind("<Return>", lambda e: self.run_command())

        self.run_btn = ctk.CTkButton(self.cmd_frame, text="Run PHP", width=100, command=self.run_command)
        self.run_btn.grid(row=0, column=1)

        # Output Area
        self.output_area = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12), fg_color=["#f1f5f9", "#0f172a"], border_width=1, border_color=["#e2e8f0", "#2d3748"], corner_radius=8)
        self.output_area.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.output_area.configure(state="disabled")

        self.log("PHP CLI initialized. Type code or commands above.")

    def log(self, message):
        self.output_area.configure(state="normal")
        self.output_area.insert("end", f"{message}\n")
        self.output_area.see("end")
        self.output_area.configure(state="disabled")

    def clear_output(self):
        self.output_area.configure(state="normal")
        self.output_area.delete("1.0", "end")
        self.output_area.configure(state="disabled")

    def run_command(self):
        raw_cmd = self.cmd_entry.get().strip()
        if not raw_cmd:
            return

        php_dir = Path(config_manager.get("install_dir")) / "php"
        php_exe = php_dir / "php.exe"

        if not php_exe.exists():
            self.log(f"Error: PHP binaries not found at {php_exe}. Please install PHP first.")
            return

        # Prepare the command
        # If the user typed 'php something', replace 'php' with the full path
        if raw_cmd.startswith("php "):
            cmd_parts = raw_cmd.split(" ", 1)
            cmd = [str(php_exe)] + cmd_parts[1].split()
        else:
            # Assume it's code and run via php -r
            cmd = [str(php_exe), "-r", raw_cmd]

        self.log(f"\n> {raw_cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.stdout:
                self.log(result.stdout)
            if result.stderr:
                self.log(f"STDERR: {result.stderr}")
            
            if not result.stdout and not result.stderr:
                self.log("(No output)")
                
        except subprocess.TimeoutExpired:
            self.log("Error: Command timed out after 10 seconds.")
        except Exception as e:
            self.log(f"Error executing command: {e}")
