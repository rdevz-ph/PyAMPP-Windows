import customtkinter as ctk
import subprocess
import os
import sys
import threading
from pathlib import Path
from core.config import config_manager, RESOURCE_DIR

class PHPGlobalFrame(ctk.CTkFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, fg_color=["#ffffff", "#1a2333"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#2d3748"], **kwargs)
        self.logger = logger

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Global PHP Setup", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.desc = ctk.CTkLabel(self, text="Set the PyAMPP PHP version as your system's global PHP. This allows you to run 'php' from any terminal.", wraplength=500, justify="left")
        self.desc.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        # Current PHP Detection
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.status_frame.grid_columnconfigure(1, weight=1)

        self.curr_label = ctk.CTkLabel(self.status_frame, text="Current System PHP:", font=ctk.CTkFont(weight="bold"))
        self.curr_label.grid(row=0, column=0, padx=10, pady=10)

        self.curr_val = ctk.CTkLabel(self.status_frame, text="Checking...", text_color="gray")
        self.curr_val.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Setup Button
        self.setup_btn = ctk.CTkButton(self, text="Set PyAMPP PHP as Global", command=self.start_setup_thread)
        self.setup_btn.grid(row=3, column=0, padx=20, pady=20)

        self.warning_label = ctk.CTkLabel(self, text="* Requires Administrator privileges. A PowerShell window will prompt for permission.", text_color="orange", font=ctk.CTkFont(size=12))
        self.warning_label.grid(row=4, column=0, padx=20, pady=5)

        self.refresh_status()

    def get_pyampp_php_path(self):
        php_dir = Path(config_manager.get("install_dir")) / "php"
        if (php_dir / "php.exe").exists():
            return php_dir
        return None

    def refresh_status(self):
        try:
            result = subprocess.run(["where", "php"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                path = result.stdout.splitlines()[0]
                self.curr_val.configure(text=path, text_color="green")
            else:
                self.curr_val.configure(text="Not found in PATH", text_color="red")
        except Exception:
            self.curr_val.configure(text="Error checking status", text_color="red")
        
        self.after(5000, self.refresh_status)

    def start_setup_thread(self):
        self.setup_btn.configure(state="disabled", text="Setup in Progress...")
        threading.Thread(target=self.set_global_php, daemon=True).start()

    def set_global_php(self):
        try:
            pyampp_php = self.get_pyampp_php_path()
            if not pyampp_php:
                self.logger.log("Error: PyAMPP PHP not installed. Please install it first from the Dashboard.", "ERROR")
                return

            ps_script = RESOURCE_DIR / "core" / "setup_global_php.ps1"
            if not ps_script.exists():
                self.logger.log(f"Error: {ps_script} not found.", "ERROR")
                return

            self.logger.log(f"Setting global PHP to: {pyampp_php}...")
            
            # Build command to run PowerShell as Admin
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f"Start-Process powershell.exe -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{ps_script}\" -TargetPhpPath \"{pyampp_php}\"' -Verb RunAs -Wait"
            ]

            # Run the command. This will pop up a UAC prompt.
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self.logger.log("Global PHP setup process finished.")

            # Ask to restart
            from tkinter import messagebox
            messagebox.showinfo("Restart Required", "Global PHP has been set successfully. The application will now close. Please reopen it manually to recognize the new system PATH.")
            
            # Trigger main app closing logic (stops servers and exits)
            self.master.master.master.on_closing() 
            
        except Exception as e:
            self.logger.log(f"Failed to trigger global PHP setup: {e}", "ERROR")
        finally:
            # UI updates must happen in main thread or via after()
            self.after(0, lambda: self.setup_btn.configure(state="normal", text="Set PyAMPP PHP as Global"))
            self.after(0, self.refresh_status)
