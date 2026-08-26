import os
import sys
import socket

# Add the project root to sys.path to allow imports from core and gui
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from gui.app import PyAMPP
import customtkinter as ctk

def is_already_running():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 49152))
        s.sendall(b"show")
        s.close()
        return True
    except:
        return False

def main():
    if is_already_running():
        sys.exit(0)

    log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else project_root, "startup_error.log")
    try:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        app = PyAMPP()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except Exception as e:
        with open(log_path, "a") as f:
            import traceback
            f.write(f"\n--- {os.path.basename(sys.executable)} Error ---\n")
            f.write(str(e) + "\n")
            f.write(traceback.format_exc())
        print(f"Critical error: {e}")

if __name__ == "__main__":
    main()
