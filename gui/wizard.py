import customtkinter as ctk
import os
import threading
import shutil
import secrets
from pathlib import Path
from tkinter import filedialog, messagebox
from core.config import config_manager, COMPONENTS_PRESETS
from core.downloader import validate_url, download_file, extract_zip, configure_php, configure_pma, robust_rmtree, surgical_cleanup
from core.apache_manager import ApacheManager
from core.mysql_manager import MySQLManager

class SetupWizard(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("PyAMPP Setup Wizard")
        
        # Set icon
        icon_path = Path(parent.icon_path) if hasattr(parent, 'icon_path') else Path(__file__).parent.parent / "app.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))
        
        # Center the wizard on the screen
        window_width = 650
        window_height = 550 # Increased height for version selection
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        pos_x = (screen_width // 2) - (window_width // 2)
        pos_y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()  # Modal
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.current_step = 0
        self.is_loading_presets = True
        
        self.selected_services = {
            "apache": ctk.BooleanVar(value=True),
            "mysql": ctk.BooleanVar(value=True),
            "php": ctk.BooleanVar(value=True),
            "phpmyadmin": ctk.BooleanVar(value=True)
        }

        # Initialize selected versions with dummy values, will be updated after download
        self.selected_versions = {
            "apache": ctk.StringVar(value=""),
            "mysql": ctk.StringVar(value=""),
            "php": ctk.StringVar(value=""),
            "phpmyadmin": ctk.StringVar(value="")
        }
        
        # Use default from config as initial value
        current_root = Path(config_manager.get("install_dir")).parent
        if not current_root.exists() and Path("C:/PyAMPP").exists():
            current_root = Path("C:/PyAMPP")
        self.install_root_var = ctk.StringVar(value=str(current_root))
        
        legacy_htdocs = Path(current_root) / "bin" / "apache" / "Apache24" / "htdocs"
        if not legacy_htdocs.exists():
            legacy_htdocs = Path(config_manager.get("install_dir")) / "apache" / "Apache24" / "htdocs"

        if legacy_htdocs.exists():
            default_htdocs = str(legacy_htdocs)
        elif config_manager.get("htdocs_dir") and Path(config_manager.get("htdocs_dir")).exists():
            default_htdocs = config_manager.get("htdocs_dir")
        else:
            default_htdocs = str(current_root / "htdocs")

        self.htdocs_dir_var = ctk.StringVar(value=default_htdocs)
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=30)
        
        # Start presets download
        self.show_loading_presets()
        threading.Thread(target=self.download_initial_presets, daemon=True).start()

    def show_loading_presets(self):
        self.clear_frame()
        label = ctk.CTkLabel(self.main_frame, text="Fetching latest presets...", font=ctk.CTkFont(size=18))
        label.pack(pady=50)
        self.loading_bar = ctk.CTkProgressBar(self.main_frame)
        self.loading_bar.pack(fill="x", padx=100)
        self.loading_bar.configure(mode="indeterminate")
        self.loading_bar.start()

    def download_initial_presets(self):
        import requests
        url = config_manager.get("presets_url")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            new_presets = response.json()
            
            # Update global presets using the unified helper
            from core.config import update_presets
            update_presets(new_presets)
            
            # Save these presets locally for future offline use
            config_path = Path(config_manager.get("install_dir")).parent / "updated_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                import json
                json.dump(new_presets, f, indent=4)
                
        except Exception as e:
            print(f"Wizard: Failed to download latest presets: {e}")
            # Continue with hardcoded defaults if download fails
        
        finally:
            self.is_loading_presets = False
            # Update default versions from newly downloaded presets
            self.selected_versions["apache"].set(list(COMPONENTS_PRESETS["Apache"].keys())[0])
            self.selected_versions["mysql"].set(list(COMPONENTS_PRESETS["MySQL"].keys())[0])
            self.selected_versions["php"].set(list(COMPONENTS_PRESETS["PHP"].keys())[0])
            self.selected_versions["phpmyadmin"].set(list(COMPONENTS_PRESETS["phpMyAdmin"].keys())[0])
            
            self.after(0, lambda: self.show_step(0))

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_step(self, step):
        self.current_step = step
        self.clear_frame()
        
        if step == 0:
            self.step_welcome()
        elif step == 1:
            self.step_path()
        elif step == 2:
            self.step_services()
        elif step == 3:
            self.step_install()
        elif step == 4:
            self.step_finish()

    def step_welcome(self):
        label = ctk.CTkLabel(self.main_frame, text="Welcome to PyAMPP!", font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(pady=(20, 10))
        
        desc = ctk.CTkLabel(self.main_frame, text="This wizard will help you set up your local development environment\nwith Apache, MySQL, and PHP in just a few steps.", justify="center")
        desc.pack(pady=20)
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        next_btn = ctk.CTkButton(btn_frame, text="Get Started", command=lambda: self.show_step(1))
        next_btn.pack(side="right", padx=10)
        
        skip_btn = ctk.CTkButton(btn_frame, text="Skip for now", fg_color="gray", command=self.skip_wizard)
        skip_btn.pack(side="right", padx=10)

    def step_path(self):
        label = ctk.CTkLabel(self.main_frame, text="Choose Installation Paths", font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=(0, 15))
        
        desc = ctk.CTkLabel(self.main_frame, text="Select where you want PyAMPP to install binaries, MySQL data, and web root.\nWe recommend using paths without spaces.", justify="left")
        desc.pack(pady=(0, 15), anchor="w")
        
        # 1. Install Directory (Binaries & MySQL Data)
        inst_label = ctk.CTkLabel(self.main_frame, text="Installation Directory (Binaries & MySQL Data):", font=ctk.CTkFont(size=12, weight="bold"))
        inst_label.pack(anchor="w", pady=(5, 2))

        path_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 10))
        
        entry = ctk.CTkEntry(path_frame, textvariable=self.install_root_var, width=400)
        entry.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        browse_btn = ctk.CTkButton(path_frame, text="Browse", width=80, command=self.browse_path)
        browse_btn.pack(side="left")

        # 2. Document Root (htdocs)
        htdocs_label = ctk.CTkLabel(self.main_frame, text="Document Root (htdocs / Web Files):", font=ctk.CTkFont(size=12, weight="bold"))
        htdocs_label.pack(anchor="w", pady=(5, 2))

        htdocs_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        htdocs_frame.pack(fill="x", pady=(0, 10))

        htdocs_entry = ctk.CTkEntry(htdocs_frame, textvariable=self.htdocs_dir_var, width=400)
        htdocs_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")

        htdocs_browse_btn = ctk.CTkButton(htdocs_frame, text="Browse", width=80, command=self.browse_htdocs_path)
        htdocs_browse_btn.pack(side="left")
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        next_btn = ctk.CTkButton(btn_frame, text="Next", command=self.save_path_and_next)
        next_btn.pack(side="right", padx=10)
        
        back_btn = ctk.CTkButton(btn_frame, text="Back", fg_color="gray", command=lambda: self.show_step(0))
        back_btn.pack(side="right", padx=10)

    def browse_path(self):
        old_root = self.install_root_var.get()
        self.attributes("-topmost", False)
        new_dir = filedialog.askdirectory(initialdir=old_root, parent=self)
        self.attributes("-topmost", True)
        if new_dir:
            norm_dir = os.path.normpath(new_dir)
            self.install_root_var.set(norm_dir)
            # Auto-update htdocs_dir if it was default matching old_root/htdocs
            current_htdocs = self.htdocs_dir_var.get()
            if not current_htdocs or current_htdocs == os.path.normpath(str(Path(old_root) / "htdocs")):
                self.htdocs_dir_var.set(os.path.normpath(str(Path(norm_dir) / "htdocs")))

    def browse_htdocs_path(self):
        self.attributes("-topmost", False)
        new_dir = filedialog.askdirectory(initialdir=self.htdocs_dir_var.get(), parent=self)
        self.attributes("-topmost", True)
        if new_dir:
            self.htdocs_dir_var.set(os.path.normpath(new_dir))

    def save_path_and_next(self):
        new_root = Path(self.install_root_var.get().strip())
        new_htdocs = Path(self.htdocs_dir_var.get().strip())
        try:
            new_root.mkdir(parents=True, exist_ok=True)
            new_htdocs.mkdir(parents=True, exist_ok=True)
            config_manager.set("install_dir", os.path.normpath(str(new_root / "bin")))
            config_manager.set("mysql_data_dir", os.path.normpath(str(new_root / "mysql_data")))
            config_manager.set("htdocs_dir", os.path.normpath(str(new_htdocs)))
            self.show_step(2)
        except Exception as e:
            self.attributes("-topmost", False)
            messagebox.showerror("Error", f"Could not create directory: {e}", parent=self)
            self.attributes("-topmost", True)

    def step_services(self):
        label = ctk.CTkLabel(self.main_frame, text="Select Services & Versions", font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=(0, 20))
        
        desc = ctk.CTkLabel(self.main_frame, text="Choose which components and versions you want to install.")
        desc.pack(pady=(0, 20), anchor="w")
        
        services_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        services_frame.pack(fill="both", expand=True)

        def create_service_row(name, key, preset_key):
            row = ctk.CTkFrame(services_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            cb = ctk.CTkCheckBox(row, text=name, variable=self.selected_services[key])
            cb.pack(side="left", anchor="w")
            
            # Version dropdown
            versions = list(COMPONENTS_PRESETS[preset_key].keys())
            menu = ctk.CTkOptionMenu(row, values=versions, variable=self.selected_versions[key], width=150)
            menu.pack(side="right", padx=10)
            
            # Disable menu if checkbox is unchecked
            def toggle_menu(*args):
                if self.selected_services[key].get():
                    menu.configure(state="normal")
                else:
                    menu.configure(state="disabled")
            
            self.selected_services[key].trace_add("write", toggle_menu)
            toggle_menu() # Initial state

        create_service_row("Apache HTTP Server", "apache", "Apache")
        create_service_row("MySQL Database Server", "mysql", "MySQL")
        create_service_row("PHP Interpreter", "php", "PHP")
        create_service_row("phpMyAdmin (Web Interface)", "phpmyadmin", "phpMyAdmin")
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        next_btn = ctk.CTkButton(btn_frame, text="Install Now", command=self.prepare_and_install)
        next_btn.pack(side="right", padx=10)
        
        back_btn = ctk.CTkButton(btn_frame, text="Back", fg_color="gray", command=lambda: self.show_step(1))
        back_btn.pack(side="right", padx=10)

    def prepare_and_install(self):
        # Update config with selected versions before running installation
        config_manager.set("apache_url", COMPONENTS_PRESETS["Apache"][self.selected_versions["apache"].get()])
        config_manager.set("mysql_url", COMPONENTS_PRESETS["MySQL"][self.selected_versions["mysql"].get()])
        config_manager.set("php_url", COMPONENTS_PRESETS["PHP"][self.selected_versions["php"].get()])
        config_manager.set("phpmyadmin_url", COMPONENTS_PRESETS["phpMyAdmin"][self.selected_versions["phpmyadmin"].get()])
        
        self.show_step(3)

    def step_install(self):
        label = ctk.CTkLabel(self.main_frame, text="Installing Components", font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(self.main_frame, text="Preparing installation...")
        self.status_label.pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        
        self.log_text = ctk.CTkTextbox(self.main_frame, height=150)
        self.log_text.pack(fill="both", expand=True, pady=10)
        
        threading.Thread(target=self.run_installation, daemon=True).start()

    def log(self, message, level="INFO"):
        self.log_text.insert("end", f"[{level}] {message}\n")
        self.log_text.see("end")

    def run_installation(self):
        services_to_install = [s for s, var in self.selected_services.items() if var.get()]
        
        if not services_to_install:
            self.after(0, lambda: self.show_step(4))
            return

        install_dir = Path(config_manager.get("install_dir"))
        install_dir.mkdir(parents=True, exist_ok=True)

        for i, service in enumerate(services_to_install):
            self.after(0, lambda s=service: self.status_label.configure(text=f"Installing {s.capitalize()}..."))
            self.log(f"Starting setup for {service}...")
            
            url = config_manager.get(f"{service}_url")
            if not validate_url(url):
                self.log(f"Error: Invalid URL for {service}")
                continue

            zip_name = f"{service}.zip"
            dest_zip = install_dir / zip_name
            
            def progress_cb(p):
                if p == -1:
                    current = self.progress_bar.get()
                    new_val = (current + 0.02) % 1.0
                    self.after(0, lambda: self.progress_bar.set(new_val))
                else:
                    # Scale progress for each service
                    scaled_p = (i / len(services_to_install)) + (p / len(services_to_install))
                    self.after(0, lambda: self.progress_bar.set(scaled_p))

            if download_file(url, str(dest_zip), progress_cb):
                self.log(f"Downloaded {service}.")
                
                if service == "phpmyadmin":
                    extract_to = install_dir / "pma_tmp"
                else:
                    extract_to = install_dir / service
                
                # Clean up old binaries before extraction (except data)
                if extract_to.exists() and service != "phpmyadmin":
                    self.log(f"Cleaning old {service} binaries...")
                    try:
                        if len(str(extract_to)) > 10: 
                            # Identify paths to keep
                            to_keep = []
                            if service == "mysql":
                                data_dir = Path(config_manager.get("mysql_data_dir")).resolve()
                                if data_dir.is_relative_to(extract_to.resolve()):
                                    to_keep.append(data_dir)
                            elif service == "apache":
                                htdocs_dir = (extract_to / "Apache24" / "htdocs").resolve()
                                if htdocs_dir.exists():
                                    to_keep.append(htdocs_dir)
                                cfg_htdocs = Path(config_manager.get("htdocs_dir", "")).resolve()
                                if cfg_htdocs.exists() and cfg_htdocs.is_relative_to(extract_to.resolve()):
                                    to_keep.append(cfg_htdocs)

                            if to_keep:
                                self.log(f"{service.capitalize()} requires surgical cleanup to preserve important data...", "INFO")
                                surgical_cleanup(extract_to, to_keep, self)
                            else:
                                robust_rmtree(extract_to)
                    except Exception as e:
                        self.log(f"Warning: Could not clean {service} directory: {e}", "WARNING")

                extract_to.mkdir(parents=True, exist_ok=True)
                
                if extract_zip(str(dest_zip), str(extract_to)):
                    self.log(f"Extracted {service}.")
                    
                    # Post-extraction logic
                    if service == "php":
                        configure_php(extract_to, self)
                    elif service == "phpmyadmin":
                        configure_pma(extract_to, config_manager.get("install_dir"), self)
                    elif service == "apache":
                        self.log("Running SSL Auto-Fix for Apache...")
                        try:
                            apache = ApacheManager()
                            success, msg = apache.enable_ssl(force=True)
                            if success:
                                self.log(f"SSL Auto-Fix completed: {msg}")
                            else:
                                self.log(f"SSL Auto-Fix failed: {msg}", "ERROR")
                        except Exception as e:
                            self.log(f"Error during SSL Auto-Fix: {e}", "ERROR")
                    
                    self.log(f"{service.capitalize()} setup complete.")
                    if dest_zip.exists():
                        os.remove(dest_zip)
                else:
                    self.log(f"Failed to extract {service}.")
            else:
                self.log(f"Failed to download {service}.")

        self.after(0, lambda: self.show_step(4))

    # Removed configure_php and configure_pma as they are now in core.downloader

    def step_finish(self):
        label = ctk.CTkLabel(self.main_frame, text="Setup Complete!", font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(pady=(20, 10))
        
        desc = ctk.CTkLabel(self.main_frame, text="PyAMPP is now configured and ready to use.\nYou can start your servers from the dashboard.")
        desc.pack(pady=20)
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        finish_btn = ctk.CTkButton(btn_frame, text="Finish", command=self.complete_wizard)
        finish_btn.pack(side="right", padx=10)

    def complete_wizard(self):
        config_manager.set("wizard_completed", True)
        self.destroy()
        
        # Refresh other frames to use latest config
        if hasattr(self.parent, "dashboard"):
            self.parent.dashboard.refresh_dashboard()
            
        if hasattr(self.parent, "settings"):
            self.parent.settings.refresh_settings()

    def skip_wizard(self):
        self.attributes("-topmost", False)
        if messagebox.askyesno("Skip Setup", "Are you sure you want to skip the setup wizard?\nYou can still configure and install everything manually from the dashboard.", parent=self):
            config_manager.set("wizard_completed", True)
            self.destroy()
        else:
            self.attributes("-topmost", True)

    def on_closing(self):
        if self.current_step == 3: # Installing
             self.attributes("-topmost", False)
             if not messagebox.askyesno("Abort Installation", "Installation is in progress. Are you sure you want to abort?", parent=self):
                 self.attributes("-topmost", True)
                 return
        self.destroy()
