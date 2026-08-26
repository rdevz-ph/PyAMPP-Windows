import customtkinter as ctk
from core.config import config_manager, COMPONENTS_PRESETS
from core.downloader import validate_url, download_file, extract_zip, configure_php, configure_pma, robust_rmtree, surgical_cleanup
from pathlib import Path
import threading
import os
import shutil

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, fg_color=["#ffffff", "#1a2333"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#2d3748"], **kwargs)
        self.logger = logger
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        
        # Apache Port
        self.apache_port_label = ctk.CTkLabel(self, text="Apache Port:")
        self.apache_port_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
        self.apache_port_entry = ctk.CTkEntry(self)
        self.apache_port_entry.insert(0, str(config_manager.get("apache_port")))
        self.apache_port_entry.grid(row=0, column=1, padx=20, pady=5, sticky="ew")

        # MySQL Port
        self.mysql_port_label = ctk.CTkLabel(self, text="MySQL Port:")
        self.mysql_port_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.mysql_port_entry = ctk.CTkEntry(self)
        self.mysql_port_entry.insert(0, str(config_manager.get("mysql_port")))
        self.mysql_port_entry.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        # --- Component Presets & URLs ---
        
        # PHP
        self.php_label = ctk.CTkLabel(self, text="PHP Version:")
        self.php_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.php_preset = ctk.CTkOptionMenu(self, values=list(COMPONENTS_PRESETS["PHP"].keys()), command=lambda v: self.update_url("php", v))
        self.php_preset.set("Custom")
        # Try to find which preset matches current URL
        current_php_url = config_manager.get("php_url")
        for k, v in COMPONENTS_PRESETS["PHP"].items():
            if v == current_php_url:
                self.php_preset.set(k)
                break
        self.php_preset.grid(row=2, column=1, padx=20, pady=5, sticky="ew")
        
        self.php_url_entry = ctk.CTkEntry(self)
        self.php_url_entry.insert(0, config_manager.get("php_url"))
        self.php_url_entry.grid(row=3, column=1, padx=20, pady=(0, 10), sticky="ew")

        # Apache
        self.apache_label = ctk.CTkLabel(self, text="Apache Version:")
        self.apache_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        self.apache_preset = ctk.CTkOptionMenu(self, values=list(COMPONENTS_PRESETS["Apache"].keys()), command=lambda v: self.update_url("apache", v))
        self.apache_preset.set("Custom")
        current_apache_url = config_manager.get("apache_url")
        for k, v in COMPONENTS_PRESETS["Apache"].items():
            if v == current_apache_url:
                self.apache_preset.set(k)
                break
        self.apache_preset.grid(row=4, column=1, padx=20, pady=5, sticky="ew")
        
        self.apache_url_entry = ctk.CTkEntry(self)
        self.apache_url_entry.insert(0, config_manager.get("apache_url"))
        self.apache_url_entry.grid(row=5, column=1, padx=20, pady=(0, 10), sticky="ew")

        # MySQL
        self.mysql_label = ctk.CTkLabel(self, text="MySQL Version:")
        self.mysql_label.grid(row=6, column=0, padx=20, pady=5, sticky="w")
        
        self.mysql_preset = ctk.CTkOptionMenu(self, values=list(COMPONENTS_PRESETS["MySQL"].keys()), command=lambda v: self.update_url("mysql", v))
        self.mysql_preset.set("Custom")
        current_mysql_url = config_manager.get("mysql_url")
        for k, v in COMPONENTS_PRESETS["MySQL"].items():
            if v == current_mysql_url:
                self.mysql_preset.set(k)
                break
        self.mysql_preset.grid(row=6, column=1, padx=20, pady=5, sticky="ew")
        
        self.mysql_url_entry = ctk.CTkEntry(self)
        self.mysql_url_entry.insert(0, config_manager.get("mysql_url"))
        self.mysql_url_entry.grid(row=7, column=1, padx=20, pady=(0, 10), sticky="ew")

        # phpMyAdmin
        self.pma_label = ctk.CTkLabel(self, text="phpMyAdmin Version:")
        self.pma_label.grid(row=8, column=0, padx=20, pady=5, sticky="w")
        
        self.pma_preset = ctk.CTkOptionMenu(self, values=list(COMPONENTS_PRESETS["phpMyAdmin"].keys()), command=lambda v: self.update_url("phpmyadmin", v))
        self.pma_preset.set("Custom")
        current_pma_url = config_manager.get("phpmyadmin_url")
        for k, v in COMPONENTS_PRESETS["phpMyAdmin"].items():
            if v == current_pma_url:
                self.pma_preset.set(k)
                break
        self.pma_preset.grid(row=8, column=1, padx=20, pady=5, sticky="ew")
        
        self.pma_url_entry = ctk.CTkEntry(self)
        self.pma_url_entry.insert(0, config_manager.get("phpmyadmin_url"))
        self.pma_url_entry.grid(row=9, column=1, padx=20, pady=(0, 10), sticky="ew")

        # LAN Access
        self.lan_access_label = ctk.CTkLabel(self, text="Enable LAN Access:")
        self.lan_access_label.grid(row=10, column=0, padx=20, pady=10, sticky="w")
        self.lan_access_switch = ctk.CTkSwitch(self, text="")
        if config_manager.get("lan_access"):
            self.lan_access_switch.select()
        self.lan_access_switch.grid(row=10, column=1, padx=20, pady=10, sticky="w")

        # Install Directory
        self.install_dir_label = ctk.CTkLabel(self, text="Install Directory:")
        self.install_dir_label.grid(row=11, column=0, padx=20, pady=10, sticky="w")
        
        self.install_dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.install_dir_frame.grid(row=11, column=1, padx=20, pady=10, sticky="ew")
        self.install_dir_frame.grid_columnconfigure(0, weight=1)

        self.install_dir_entry = ctk.CTkEntry(self.install_dir_frame)
        install_root = Path(config_manager.get("install_dir")).parent
        self.install_dir_entry.insert(0, str(install_root))
        self.install_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(self.install_dir_frame, text="Browse", width=60, command=self.browse_install_dir)
        self.browse_btn.grid(row=0, column=1)

        # Presets URL
        self.presets_url_label = ctk.CTkLabel(self, text="Presets URL (JSON):")
        self.presets_url_label.grid(row=12, column=0, padx=20, pady=5, sticky="w")
        
        self.presets_url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.presets_url_frame.grid(row=12, column=1, padx=20, pady=5, sticky="ew")
        self.presets_url_frame.grid_columnconfigure(0, weight=1)
        
        self.presets_url_entry = ctk.CTkEntry(self.presets_url_frame)
        self.presets_url_entry.insert(0, config_manager.get("presets_url"))
        self.presets_url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.download_presets_btn = ctk.CTkButton(self.presets_url_frame, text="Download", width=60, command=self.download_presets)
        self.download_presets_btn.grid(row=0, column=1)

        # Auto Run on Startup
        self.startup_label = ctk.CTkLabel(self, text="Auto Run on Startup:")
        self.startup_label.grid(row=13, column=0, padx=20, pady=10, sticky="w")
        self.startup_switch = ctk.CTkSwitch(self, text="", command=self.toggle_startup)
        if self.check_startup():
            self.startup_switch.select()
        self.startup_switch.grid(row=13, column=1, padx=20, pady=10, sticky="w")

        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=14, column=0, columnspan=2, padx=20, pady=20)
        
        # Save Button
        self.save_button = ctk.CTkButton(self.btn_frame, text="Save Config", command=self.save_settings)
        self.save_button.grid(row=0, column=0, padx=10)
        
        # Update Button
        self.update_button = ctk.CTkButton(self.btn_frame, text="Update/Reinstall Components", fg_color="#1f538d", hover_color="#14375e", command=self.confirm_update)
        self.update_button.grid(row=0, column=1, padx=10)

        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)

    def check_startup(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "PyAMPP")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def toggle_startup(self):
        import winreg
        import sys
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if self.startup_switch.get():
                executable = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                if getattr(sys, 'frozen', False):
                    command = f'"{executable}"'
                else:
                    command = f'"{executable}" "{script_path}"'
                    
                winreg.SetValueEx(key, "PyAMPP", 0, winreg.REG_SZ, command)
                self.logger.log("Added to Windows startup.")
            else:
                try:
                    winreg.DeleteValue(key, "PyAMPP")
                    self.logger.log("Removed from Windows startup.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.logger.log(f"Failed to toggle startup: {e}", "ERROR")

    def download_presets(self):
        url = self.presets_url_entry.get().strip()
        if not url:
            self.logger.log("Please enter a presets URL.", "ERROR")
            return
        
        def run_download():
            self.logger.log(f"Downloading presets from {url}...")
            try:
                import requests
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                new_presets = response.json()
                
                # Update global presets using the unified helper
                from core.config import update_presets
                update_presets(new_presets)
                
                # Check for application update
                if "latest_release" in new_presets:
                    # self.master is tab, self.master.master is tabview, self.master.master.master is PyAMPP
                    app = self.master.master.master
                    if hasattr(app, "check_app_version"):
                        self.after(0, lambda: app.check_app_version(new_presets["latest_release"]))

                self.after(0, self.refresh_settings)
                self.logger.log("Presets updated successfully.")
                
                # Save these presets locally for future offline use
                config_path = Path(config_manager.get("install_dir")).parent / "updated_config.json"
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, "w") as f:
                    import json
                    json.dump(new_presets, f, indent=4)
                
                from tkinter import messagebox
                self.after(0, lambda: messagebox.showinfo("Success", "Presets have been downloaded and merged."))
            except Exception as e:
                self.logger.log(f"Failed to download presets: {e}", "ERROR")
                from tkinter import messagebox
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to download presets: {e}"))

        threading.Thread(target=run_download, daemon=True).start()

    def refresh_settings(self):
        """Refreshes the UI components with the latest configuration values."""
        # Apache Port
        self.apache_port_entry.delete(0, "end")
        self.apache_port_entry.insert(0, str(config_manager.get("apache_port")))

        # MySQL Port
        self.mysql_port_entry.delete(0, "end")
        self.mysql_port_entry.insert(0, str(config_manager.get("mysql_port")))

        # --- Component URLs and Presets ---
        
        # Update OptionMenus with new presets
        self.php_preset.configure(values=list(COMPONENTS_PRESETS["PHP"].keys()))
        self.apache_preset.configure(values=list(COMPONENTS_PRESETS["Apache"].keys()))
        self.mysql_preset.configure(values=list(COMPONENTS_PRESETS["MySQL"].keys()))
        self.pma_preset.configure(values=list(COMPONENTS_PRESETS["phpMyAdmin"].keys()))

        # PHP
        self.php_url_entry.delete(0, "end")
        self.php_url_entry.insert(0, config_manager.get("php_url"))
        self.php_preset.set("Custom")
        for k, v in COMPONENTS_PRESETS["PHP"].items():
            if v == config_manager.get("php_url"):
                self.php_preset.set(k)
                break

        # Apache
        self.apache_url_entry.delete(0, "end")
        self.apache_url_entry.insert(0, config_manager.get("apache_url"))
        self.apache_preset.set("Custom")
        for k, v in COMPONENTS_PRESETS["Apache"].items():
            if v == config_manager.get("apache_url"):
                self.apache_preset.set(k)
                break

        # MySQL
        self.mysql_url_entry.delete(0, "end")
        self.mysql_url_entry.insert(0, config_manager.get("mysql_url"))
        self.mysql_preset.set("Custom")
        for k, v in COMPONENTS_PRESETS["MySQL"].items():
            if v == config_manager.get("mysql_url"):
                self.mysql_preset.set(k)
                break

        # phpMyAdmin
        self.pma_url_entry.delete(0, "end")
        self.pma_url_entry.insert(0, config_manager.get("phpmyadmin_url"))
        self.pma_preset.set("Custom")
        for k, v in COMPONENTS_PRESETS["phpMyAdmin"].items():
            if v == config_manager.get("phpmyadmin_url"):
                self.pma_preset.set(k)
                break

        # LAN Access
        if config_manager.get("lan_access"):
            self.lan_access_switch.select()
        else:
            self.lan_access_switch.deselect()

        # Install Directory
        self.install_dir_entry.delete(0, "end")
        install_root = Path(config_manager.get("install_dir")).parent
        self.install_dir_entry.insert(0, str(install_root))

        # Presets URL
        self.presets_url_entry.delete(0, "end")
        self.presets_url_entry.insert(0, config_manager.get("presets_url"))

    def update_url(self, component, version):

        if component == "php":
            self.php_url_entry.delete(0, "end")
            self.php_url_entry.insert(0, COMPONENTS_PRESETS["PHP"][version])
        elif component == "apache":
            self.apache_url_entry.delete(0, "end")
            self.apache_url_entry.insert(0, COMPONENTS_PRESETS["Apache"][version])
        elif component == "mysql":
            self.mysql_url_entry.delete(0, "end")
            self.mysql_url_entry.insert(0, COMPONENTS_PRESETS["MySQL"][version])
        elif component == "phpmyadmin":
            self.pma_url_entry.delete(0, "end")
            self.pma_url_entry.insert(0, COMPONENTS_PRESETS["phpMyAdmin"][version])

    def browse_install_dir(self):
        from tkinter import filedialog
        new_dir = filedialog.askdirectory(initialdir=self.install_dir_entry.get())
        if new_dir:
            self.install_dir_entry.delete(0, "end")
            self.install_dir_entry.insert(0, new_dir)

    def save_settings(self, show_msg=True, restart_if_running=True):
        try:
            config_manager.set("apache_port", int(self.apache_port_entry.get()))
            config_manager.set("mysql_port", int(self.mysql_port_entry.get()))
            config_manager.set("apache_url", self.apache_url_entry.get())
            config_manager.set("mysql_url", self.mysql_url_entry.get())
            config_manager.set("php_url", self.php_url_entry.get())
            config_manager.set("phpmyadmin_url", self.pma_url_entry.get())
            config_manager.set("lan_access", bool(self.lan_access_switch.get()))
            config_manager.set("presets_url", self.presets_url_entry.get().strip())
            
            new_root = Path(self.install_dir_entry.get())
            config_manager.set("install_dir", str(new_root / "bin"))
            config_manager.set("mysql_data_dir", str(new_root / "mysql_data"))
            
            # Refresh dashboard and restart servers if available
            try:
                # self.master is tab, self.master.master is tabview, self.master.master.master is PyAMPP
                app = self.master.master.master
                if hasattr(app, "dashboard"):
                    app.dashboard.refresh_dashboard()
                    
                    # If servers are running, restart them to apply new config (e.g. ports)
                    apache_running = app.dashboard.apache.is_running()
                    mysql_running = app.dashboard.mysql.is_running()
                    
                    if (apache_running or mysql_running) and restart_if_running:
                        self.logger.log("Restarting servers to apply new configuration...")
                        threading.Thread(target=app.dashboard.restart_all, daemon=True).start()
            except Exception as e:
                self.logger.log(f"Warning: Could not auto-restart servers: {e}", "WARNING")

            self.logger.log("Settings saved.")
            if show_msg:
                from tkinter import messagebox
                messagebox.showinfo("Success", "Settings saved successfully.")
            return True
        except ValueError:
            self.logger.log("Invalid port number.", "ERROR")
            return False
        except Exception as e:
            self.logger.log(f"Error saving settings: {e}", "ERROR")
            return False

    def confirm_update(self):
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Update", "This will download and reinstall the selected versions. Existing binaries will be replaced, but MySQL data should remain intact. Continue?"):
            self.save_settings(show_msg=False, restart_if_running=False)
            self.start_update_thread()

    def create_progress_dialog(self, title, message):
        from gui.dashboard import ProgressDialog
        self.progress_dialog = ProgressDialog(self.winfo_toplevel(), title, message)

    def update_progress_dialog(self, value, message=None):
        if hasattr(self, 'progress_dialog') and self.progress_dialog and self.progress_dialog.winfo_exists():
            self.progress_dialog.set_progress(value)
            if message:
                self.progress_dialog.set_message(message)

    def close_progress_dialog(self):
        if hasattr(self, 'progress_dialog') and self.progress_dialog and self.progress_dialog.winfo_exists():
            self.progress_dialog.grab_release()
            self.progress_dialog.destroy()
            self.progress_dialog = None

    def start_update_thread(self):
        self.update_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.progress_bar.grid(row=15, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        # Show custom progress dialog
        self.create_progress_dialog("Updating Components", "Starting update check...")
        
        threading.Thread(target=self.run_update, daemon=True).start()

    def run_update(self):
        # Stop servers before update to avoid file locks
        self.logger.log("Stopping servers before update...")
        try:
            # self.master is tab, self.master.master is tabview, self.master.master.master is PyAMPP app
            app = self.master.master.master
            if hasattr(app, "dashboard"):
                app.dashboard.stop_all()
        except Exception as e:
            self.logger.log(f"Warning: Could not stop servers: {e}", "WARNING")

        install_dir = Path(config_manager.get("install_dir"))
        install_dir.mkdir(parents=True, exist_ok=True)
        
        components = ["php", "apache", "mysql", "phpmyadmin"]
        
        for i, comp in enumerate(components):
            url = config_manager.get(f"{comp}_url")
            self.logger.log(f"Updating {comp}...")
            
            # Update dialog message
            display_name = "phpMyAdmin" if comp == "phpmyadmin" else comp.upper()
            self.after(0, lambda c=comp, d=display_name: self.update_progress_dialog((i / len(components)), f"Downloading {d}..."))
            
            zip_name = f"{comp}_update.zip"
            dest_zip = install_dir / zip_name
            
            def progress_cb(p):
                if p == -1:
                    if hasattr(self, 'progress_dialog') and self.progress_dialog:
                        current = self.progress_dialog.progress_bar.get()
                        new_val = (current + 0.02) % 1.0
                        self.after(0, lambda: self.update_progress_dialog(new_val))
                    
                    current = self.progress_bar.get()
                    new_val = (current + 0.02) % 1.0
                    self.after(0, lambda: self.progress_bar.set(new_val))
                else:
                    scaled_p = (i / len(components)) + (p / len(components))
                    self.after(0, lambda: self.update_progress_dialog(scaled_p))
                    self.after(0, lambda: self.progress_bar.set(scaled_p))

            if download_file(url, str(dest_zip), progress_cb):
                display_name = "phpMyAdmin" if comp == "phpmyadmin" else comp.upper()
                self.after(0, lambda d=display_name: self.update_progress_dialog((i + 1) / len(components), f"Extracting {d}..."))
                
                if comp == "phpmyadmin":
                    extract_to = install_dir / "pma_tmp"
                else:
                    extract_to = install_dir / comp
                
                # Clean up old binaries before extraction (except data)
                if extract_to.exists() and comp != "phpmyadmin":
                    self.logger.log(f"Cleaning old {comp} binaries...")
                    try:
                        # For safety, don't delete if it seems to be a root directory
                        if len(str(extract_to)) > 10: 
                            # Identify paths to keep
                            to_keep = []
                            if comp == "mysql":
                                data_dir = Path(config_manager.get("mysql_data_dir")).resolve()
                                if data_dir.is_relative_to(extract_to.resolve()):
                                    to_keep.append(data_dir)
                            elif comp == "apache":
                                htdocs_dir = (extract_to / "Apache24" / "htdocs").resolve()
                                if htdocs_dir.exists():
                                    to_keep.append(htdocs_dir)

                            if to_keep:
                                self.logger.log(f"{comp.capitalize()} requires surgical cleanup to preserve important data...", "INFO")
                                surgical_cleanup(extract_to, to_keep, self.logger)
                            else:
                                robust_rmtree(extract_to)
                    except Exception as e:
                        self.logger.log(f"Warning: Could not clean {comp} directory: {e}", "WARNING")

                extract_to.mkdir(parents=True, exist_ok=True)
                
                if extract_zip(str(dest_zip), str(extract_to)):
                    if comp == "php":
                        configure_php(extract_to, self.logger)
                    elif comp == "phpmyadmin":
                        configure_pma(extract_to, install_dir, self.logger)
                    elif comp == "apache":
                        self.logger.log("Running SSL Auto-Fix for Apache...")
                        try:
                            from core.apache_manager import ApacheManager
                            apache = ApacheManager()
                            success, msg = apache.enable_ssl(force=True)
                            if success:
                                self.logger.log(f"SSL Auto-Fix completed: {msg}")
                            else:
                                self.logger.log(f"SSL Auto-Fix failed: {msg}", "ERROR")
                        except Exception as e:
                            self.logger.log(f"Error during SSL Auto-Fix: {e}", "ERROR")
                    
                    self.logger.log(f"{comp.capitalize()} update complete.")
                    if dest_zip.exists():
                        os.remove(dest_zip)
                else:
                    self.logger.log(f"Failed to extract {comp}.", "ERROR")
            else:
                self.logger.log(f"Failed to download {comp}.", "ERROR")

        self.after(0, self.finish_update)

    def finish_update(self):
        self.progress_bar.grid_forget()
        self.update_button.configure(state="normal")
        self.save_button.configure(state="normal")
        
        # Close progress dialog
        self.close_progress_dialog()
        
        from tkinter import messagebox
        messagebox.showinfo("Update Complete", "All components have been updated. Please restart the application to ensure all changes take effect.")
        # self.master.master.master.on_closing() # Optional auto-restart
