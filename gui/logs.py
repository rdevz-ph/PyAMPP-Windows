import customtkinter as ctk
import sys
from datetime import datetime

class Logger(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=["#ffffff", "#1a2333"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#2d3748"], **kwargs)
        self.configure(state="disabled")

    def log(self, message, level="INFO"):
        try:
            if not self.winfo_exists():
                return
            self.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.insert("end", f"[{timestamp}] [{level}] {message}\n")
            self.configure(state="disabled")
            self.see("end")
        except Exception:
            # Fallback to console if widget is gone
            pass

    def write(self, message):
        if message.strip():
            try:
                if self.winfo_exists():
                    self.log(message.strip(), "SYS")
                else:
                    # If UI is gone, print to real stdout
                    sys.__stdout__.write(message + "\n")
            except:
                pass

    def flush(self):
        pass
