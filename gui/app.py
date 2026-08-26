import customtkinter as ctk
import sys
import threading
import socket
from pathlib import Path
from PIL import Image
import pystray
from pystray import MenuItem as item
from gui.dashboard import DashboardFrame
from gui.settings import SettingsFrame
from gui.logs import Logger
from gui.php_cli import PHPCLIFrame
from gui.php_global import PHPGlobalFrame
from gui.wizard import SetupWizard
from gui.diagnostics import DiagnosticsFrame
from gui.php_extensions import PHPExtensionsFrame
from core.config import RESOURCE_DIR, config_manager, VERSION, COMPONENTS_PRESETS

class PyAMPP(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"PyAMPP {VERSION} - Apache & MySQL Manager")
        
        # Override the main window background color to a uniform premium dark blue/slate
        self.configure(fg_color=["#f1f5f9", "#0f172a"])
        
        # Center the main window on the screen
        window_width = 900
        window_height = 750
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        pos_x = (screen_width // 2) - (window_width // 2)
        pos_y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        
        # System Tray Setup
        self.tray_icon = None
        self.setup_tray()

        # Set Window Icon
        self.icon_path = RESOURCE_DIR / "app.ico"
        if not self.icon_path.exists():
             self.icon_path = Path(__file__).parent.parent / "app.ico"
             
        if self.icon_path.exists():
            self.iconbitmap(str(self.icon_path))

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.configure(
            fg_color=["#f8fafc", "#0f172a"],
            segmented_button_fg_color=["#cbd5e1", "#1e293b"],
            segmented_button_selected_color=["#3b8ed0", "#1f6aa5"],
            segmented_button_unselected_color=["#e2e8f0", "#0f172a"],
            text_color=["#0f172a", "#f8fafc"]
        )
        self.tabview.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.tabview.add("Dashboard")
        self.tabview.add("Logs")
        self.tabview.add("Diagnostics")
        self.tabview.add("PHP CLI")
        self.tabview.add("Global PHP")
        self.tabview.add("PHP Extensions")
        self.tabview.add("Settings")

        # Explicitly set background of individual tab frames to blend seamlessly
        for tab_name in ["Dashboard", "Logs", "Diagnostics", "PHP CLI", "Global PHP", "PHP Extensions", "Settings"]:
            self.tabview.tab(tab_name).configure(fg_color=["#f8fafc", "#0f172a"])

        # Footer
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.dev_label = ctk.CTkLabel(self.footer_frame, text="Developed by rdevz-ph | GitHub:", font=ctk.CTkFont(size=12))
        self.dev_label.pack(side="left", padx=(0, 5))
        
        self.github_link = ctk.CTkLabel(self.footer_frame, text="github.com/rdevz-ph", font=ctk.CTkFont(size=12, underline=True), text_color=["#1f6aa5", "#3b8ed0"], cursor="hand2")
        self.github_link.pack(side="left")
        self.github_link.bind("<Button-1>", lambda e: self.open_github())

        self.version_label = ctk.CTkLabel(self.footer_frame, text=VERSION, font=ctk.CTkFont(size=12))
        self.version_label.pack(side="right")

        self.update_btn = ctk.CTkButton(self.footer_frame, text="Check for Updates", font=ctk.CTkFont(size=11), height=24, width=100, command=lambda: self.check_for_updates(show_ui=True))
        self.update_btn.pack(side="right", padx=10)

        self.mode_switch = ctk.CTkSwitch(self.footer_frame, text="Dark Mode", command=self.toggle_mode)
        self.mode_switch.pack(side="right", padx=10)
        self.mode_switch.select()

        # Create Logger (Parent is now Logs tab)
        self.logger = Logger(self.tabview.tab("Logs"))
        self.logger.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Redirect stdout/stderr to logger
        sys.stdout = self.logger
        sys.stderr = self.logger

        # Dashboard Tab
        self.dashboard = DashboardFrame(self.tabview.tab("Dashboard"), self.logger)
        self.dashboard.pack(expand=True, fill="both", padx=10, pady=10)

        # Diagnostics Tab
        self.diagnostics = DiagnosticsFrame(self.tabview.tab("Diagnostics"), self.logger)
        self.diagnostics.pack(expand=True, fill="both", padx=10, pady=10)

        # PHP CLI Tab
        self.php_cli = PHPCLIFrame(self.tabview.tab("PHP CLI"), self.logger)
        self.php_cli.pack(expand=True, fill="both", padx=10, pady=10)

        # PHP Global Tab
        self.php_global = PHPGlobalFrame(self.tabview.tab("Global PHP"), self.logger)
        self.php_global.pack(expand=True, fill="both", padx=10, pady=10)

        # PHP Extensions Tab
        self.php_extensions = PHPExtensionsFrame(self.tabview.tab("PHP Extensions"), self.logger)
        self.php_extensions.pack(expand=True, fill="both", padx=10, pady=10)

        # Settings Tab
        self.settings = SettingsFrame(self.tabview.tab("Settings"), self.logger)
        self.settings.pack(expand=True, fill="both", padx=10, pady=10)

        self.logger.log("PyAMPP Initialized.")

        # Single Instance Listener
        self.start_instance_listener()

        # Check for updates in background
        self.check_for_updates()

        # Show Setup Wizard if not completed
        if not config_manager.get("wizard_completed"):
            self.after(100, self.show_wizard)

    def show_wizard(self):
        wizard = SetupWizard(self)
        wizard.focus()

    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/rdevz-ph")

    def toggle_mode(self):
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark" or current_mode == "System":
            ctk.set_appearance_mode("Light")
            self.mode_switch.configure(text="Light Mode")
            self.mode_switch.deselect()
        else:
            ctk.set_appearance_mode("Dark")
            self.mode_switch.configure(text="Dark Mode")
            self.mode_switch.select()

    def start_instance_listener(self):
        def listen():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Allow re-binding to the port if it's in TIME_WAIT
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', 49152))
                s.listen(1)
                while True:
                    conn, addr = s.accept()
                    try:
                        conn.settimeout(2.0)
                        data = conn.recv(1024).decode()
                        if data == "show":
                            self.after(0, self.show_window)
                    except:
                        pass
                    finally:
                        conn.close()
            except Exception as e:
                # If bind fails, another instance is probably listening
                pass
        
        threading.Thread(target=listen, daemon=True).start()

    def setup_tray(self):
        icon_path = RESOURCE_DIR / "app.ico"
        if not icon_path.exists():
            icon_path = Path(__file__).parent.parent / "app.ico"
            
        if icon_path.exists():
            image = Image.open(str(icon_path))
            menu = (
                item('Show', self.show_window),
                item('Exit PyAMPP', self.exit_app)
            )
            self.tray_icon = pystray.Icon("PyAMPP", image, "PyAMPP", menu)
            # Run tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """Robustly show and focus the window."""
        self.after(0, self._deiconify_and_focus)

    def _deiconify_and_focus(self):
        self.deiconify()
        self.state('normal')
        self.lift()
        self.attributes("-topmost", True)
        self.after(10, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def check_app_version(self, release_info, show_ui=False):
        """Compares current version with latest release and shows notification if update is available."""
        latest_version = release_info.get("version")
        update_url = release_info.get("url")
        
        if not latest_version or not update_url:
            if show_ui:
                from tkinter import messagebox
                messagebox.showwarning("Update Check", "Could not parse update details.")
            return
            
        from tkinter import messagebox
        # Basic version comparison (v1.0.4 vs v1.0.5)
        if latest_version != VERSION:
            import webbrowser
            
            if messagebox.askyesno("Update Available", 
                                   f"A new version of PyAMPP is available ({latest_version}).\n"
                                   f"Current version: {VERSION}\n\n"
                                   "Would you like to go to the download page?"):
                webbrowser.open(update_url)
        else:
            if show_ui:
                messagebox.showinfo("Up to Date", "You are using the latest version of PyAMPP.")

    def on_closing(self):
        # Create a custom dialog for closing behavior
        dialog = ctk.CTkToplevel(self)
        dialog.title("Exit PyAMPP")
        if hasattr(self, 'icon_path') and self.icon_path.exists():
            dialog.iconbitmap(str(self.icon_path))
        
        # Center the dialog on the main window
        dialog_width = 400
        dialog_height = 200
        
        # Get main window position and size
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        
        # Calculate centering coordinates
        pos_x = main_x + (main_width // 2) - (dialog_width // 2)
        pos_y = main_y + (main_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        dialog.resizable(False, False)
        dialog.transient(self) # Keep on top of main window
        dialog.attributes("-topmost", True)
        dialog.grab_set() # Modal

        label = ctk.CTkLabel(dialog, text="What would you like to do?", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=(20, 10))

        def stop_exit():
            dialog.destroy()
            self.exit_app()

        def minimize_to_tray():
            dialog.destroy()
            self.withdraw()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)

        exit_btn = ctk.CTkButton(btn_frame, text="Stop & Exit", command=stop_exit, fg_color="#d32f2f", hover_color="#b71c1c")
        exit_btn.pack(side="left", padx=5, expand=True)

        tray_btn = ctk.CTkButton(btn_frame, text="Minimize to Tray", command=minimize_to_tray)
        tray_btn.pack(side="left", padx=5, expand=True)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, fg_color="gray")
        cancel_btn.pack(side="left", padx=5, expand=True)

    def exit_app(self, icon=None, item=None):
        # Stop tray icon if it exists
        if self.tray_icon:
            self.tray_icon.stop()
            
        # Restore stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        # Stop all servers
        self.dashboard.stop_all()
        
        # Destroy window
        self.after(100, self.destroy)

    def check_for_updates(self, show_ui=False):
        """Starts a background thread to check for preset updates."""
        threading.Thread(target=self._run_update_check, args=(show_ui,), daemon=True).start()

    def _run_update_check(self, show_ui):
        """Internal method to fetch latest presets."""
        import requests
        import json
        from tkinter import messagebox
        url = config_manager.get("presets_url")
        if not url:
            if show_ui:
                self.after(0, lambda: messagebox.showerror("Update Error", "No presets URL configured in options."))
            return

        try:
            self.logger.log("Checking for latest component presets...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            new_presets = response.json()
            
            # Update global presets using the unified helper
            from core.config import update_presets
            update_presets(new_presets)

            # Check for application update
            if "latest_release" in new_presets:
                self.after(0, lambda: self.check_app_version(new_presets["latest_release"], show_ui))
            elif show_ui:
                self.after(0, lambda: messagebox.showwarning("Update Check", "Could not find update information in the presets file."))
            
            self.logger.log("Latest presets fetched and applied.")
            # Save these presets locally for future offline use
            presets_path = Path(config_manager.get("install_dir")).parent / "updated_config.json"
            presets_path.parent.mkdir(parents=True, exist_ok=True)
            with open(presets_path, "w") as f:
                json.dump(new_presets, f, indent=4)
            
            # Refresh settings UI if it exists
            if hasattr(self, "settings"):
                self.after(0, self.settings.refresh_settings)
                
        except Exception as e:
            self.logger.log(f"Offline: skipping presets update check. {e}", "INFO")
            if show_ui:
                self.after(0, lambda: messagebox.showinfo("Update Check failed", "The auto-update service is currently unavailable. Please check the official repository for the latest releases."))

if __name__ == "__main__":
    def is_already_running():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', 49152))
            s.sendall(b"show")
            s.close()
            return True
        except:
            return False

    if is_already_running():
        sys.exit(0)

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = PyAMPP()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
