import customtkinter as ctk
import re
import threading
import time
from pathlib import Path
from tkinter import messagebox
from core.config import config_manager
from core.apache_manager import ApacheManager

class PHPExtensionsFrame(ctk.CTkFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, fg_color=["#ffffff", "#1a2333"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#2d3748"], **kwargs)
        self.logger = logger
        
        # Grid layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # Extensions list container expands

        # Dynamic Color Definitions consistent with other frames
        self.secondary_bg = ["#cbd5e1", "#334155"]
        self.secondary_hover = ["#94a3b8", "#475569"]
        self.secondary_fg = ["#0f172a", "#f8fafc"]

        # Track loaded extensions and their widgets
        self.extensions_list = []
        self.checkbox_vars = {}
        self.checkbox_widgets = {}
        self.php_ini_path = None
        self.php_ini_lines = []

        # 1. Header Title
        self.label = ctk.CTkLabel(self, text="PHP Extensions Manager", font=ctk.CTkFont(size=18, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        # 2. Header Description
        self.desc = ctk.CTkLabel(
            self, 
            text="Configure PHP extensions by checking or unchecking them below. Toggling these options edits your php.ini file and restarts the Apache server if it is running.", 
            wraplength=700, 
            justify="left", 
            font=ctk.CTkFont(size=12), 
            text_color=["#64748b", "#94a3b8"]
        )
        self.desc.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # 3. Search Box Frame/Card
        self.search_frame = ctk.CTkFrame(self, fg_color=["#f1f5f9", "#0f172a"], border_width=1, border_color=["#e2e8f0", "#2d3748"], corner_radius=8)
        self.search_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search extensions...", border_width=0, fg_color="transparent")
        self.search_entry.grid(row=0, column=0, padx=15, pady=8, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        # 4. Status Message Label
        self.status_label = ctk.CTkLabel(self, text="Loading extensions...", font=ctk.CTkFont(slant="italic"), text_color=["#64748b", "#94a3b8"])
        self.status_label.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="w")

        # 5. Extensions List Frame (Scrollable)
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color=["#f8fafc", "#111827"], border_width=1, border_color=["#e2e8f0", "#2d3748"], corner_radius=8)
        self.scroll_container.grid(row=4, column=0, padx=20, pady=(5, 10), sticky="nsew")
        
        # Configure columns for grid inside scroll container (4 columns)
        for col_idx in range(4):
            self.scroll_container.grid_columnconfigure(col_idx, weight=1)

        # 6. Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        self.save_btn = ctk.CTkButton(self.action_frame, text="Save Changes", command=self.save_changes, width=140)
        self.save_btn.pack(side="right")

        self.refresh_btn = ctk.CTkButton(
            self.action_frame, 
            text="Refresh", 
            command=self.load_extensions, 
            width=100, 
            fg_color=self.secondary_bg, 
            hover_color=self.secondary_hover, 
            text_color=self.secondary_fg
        )
        self.refresh_btn.pack(side="right", padx=(0, 10))

        # Initial Load
        self.load_extensions()

    def load_extensions(self):
        install_dir = config_manager.get("install_dir") or ""
        self.php_ini_path = Path(install_dir) / "php" / "php.ini"

        if not self.php_ini_path.exists():
            self.status_label.configure(text="php.ini not found. Please make sure PHP is installed.", text_color="red")
            # Clear existing checkboxes if any
            for widget in self.checkbox_widgets.values():
                widget.destroy()
            self.checkbox_widgets.clear()
            self.checkbox_vars.clear()
            self.extensions_list.clear()
            return

        try:
            with open(self.php_ini_path, "r") as f:
                self.php_ini_lines = f.readlines()
            
            # Clear current widgets
            for widget in self.checkbox_widgets.values():
                widget.destroy()
            self.checkbox_widgets.clear()
            self.checkbox_vars.clear()
            self.extensions_list.clear()

            # Regex for extension=... and zend_extension=... lines (allowing comments)
            pattern = re.compile(r'^\s*(;)?\s*(zend_)?extension\s*=\s*([^;]+?)(?:\s*;.*)?$', re.IGNORECASE)

            parsed_extensions = {}
            for i, line in enumerate(self.php_ini_lines):
                match = pattern.match(line)
                if match:
                    is_commented = match.group(1) is not None
                    is_zend = match.group(2) is not None
                    
                    # Clean extension name by stripping whitespace (\r, \n, spaces) and quotes
                    name = match.group(3).strip()
                    name = name.strip('\'"')
                    name = name.strip()

                    # Skip empty/invalid names or example configurations
                    if (not name or
                        name.lower() == "modulename" or 
                        "<ext>" in name or 
                        "/" in name or 
                        "\\" in name or 
                        name.lower().endswith(".so")):
                        continue

                    lower_name = name.lower()
                    # If duplicate, prioritize the enabled (uncommented) one
                    if lower_name in parsed_extensions:
                        existing_item = parsed_extensions[lower_name]
                        if not existing_item["enabled"] and not is_commented:
                            parsed_extensions[lower_name] = {
                                "name": name,
                                "enabled": True,
                                "is_zend": is_zend,
                                "original_line": line,
                                "line_index": i
                            }
                    else:
                        parsed_extensions[lower_name] = {
                            "name": name,
                            "enabled": not is_commented,
                            "is_zend": is_zend,
                            "original_line": line,
                            "line_index": i
                        }

            self.extensions_list = list(parsed_extensions.values())

            # Sort extensions alphabetically
            self.extensions_list.sort(key=lambda x: x["name"].lower())

            # Create checkbox widgets
            for item in self.extensions_list:
                name = item["name"]
                var = ctk.BooleanVar(value=item["enabled"])
                self.checkbox_vars[name] = var

                display_name = f"{name} (Zend)" if item["is_zend"] else name
                cb = ctk.CTkCheckBox(self.scroll_container, text=display_name, variable=var)
                self.checkbox_widgets[name] = cb

            self.apply_filter()

        except Exception as e:
            self.status_label.configure(text=f"Error reading php.ini: {e}", text_color="red")
            self.logger.log(f"Error loading php extensions: {e}", "ERROR")

    def apply_filter(self):
        query = self.search_entry.get().strip().lower()
        num_cols = 4

        # Clear existing grid layouts
        for widget in self.checkbox_widgets.values():
            widget.grid_forget()

        visible_count = 0
        for item in self.extensions_list:
            name = item["name"]
            if not query or query in name.lower():
                col = visible_count % num_cols
                row = visible_count // num_cols
                cb = self.checkbox_widgets[name]
                cb.grid(row=row, column=col, padx=15, pady=8, sticky="w")
                visible_count += 1

        self.status_label.configure(text=f"Found {visible_count} extension(s) in php.ini.", text_color=["gray", "#94a3b8"])

    def save_changes(self):
        if not self.php_ini_path or not self.php_ini_path.exists():
            messagebox.showerror("Error", "No active php.ini loaded to save changes.")
            return

        try:
            # Load the lines fresh from the file to ensure we don't overwrite external edits
            with open(self.php_ini_path, "r") as f:
                lines = f.readlines()

            for item in self.extensions_list:
                name = item["name"]
                is_enabled = self.checkbox_vars[name].get()
                line_idx = item["line_index"]
                original_line = lines[line_idx]

                trimmed = original_line.strip()
                is_currently_commented = trimmed.startswith(";")

                if is_enabled and is_currently_commented:
                    # Remove first semicolon
                    semi_idx = original_line.find(";")
                    if semi_idx >= 0:
                        new_line = original_line[:semi_idx] + original_line[semi_idx+1:]
                    else:
                        new_line = original_line
                elif not is_enabled and not is_currently_commented:
                    # Prepend semicolon
                    new_line = ";" + original_line
                else:
                    new_line = original_line

                lines[line_idx] = new_line

            # Save lines to file
            with open(self.php_ini_path, "w") as f:
                f.writelines(lines)

            messagebox.showinfo("Success", "PHP extensions configuration saved successfully to php.ini.")

            # Reload extensions to sync states and original line contents
            self.load_extensions()

            # Restart Apache if it is running
            self.restart_apache_if_running()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {e}")
            self.logger.log(f"Failed to save php.ini: {e}", "ERROR")

    def restart_apache_if_running(self):
        apache = ApacheManager()
        if apache.is_running():
            self.status_label.configure(text="Restarting Apache server to apply changes...", text_color="orange")
            
            def do_restart():
                try:
                    apache.stop()
                    time.sleep(1.5)
                    apache.update_paths()
                    success, msg = apache.start_server()
                    if success:
                        self.after(0, lambda: self.status_label.configure(text="Apache restarted successfully. Extensions loaded!", text_color="green"))
                    else:
                        self.after(0, lambda: self.status_label.configure(text=f"Apache restart failed: {msg}", text_color="red"))
                        self.after(0, lambda: messagebox.showwarning("Restart Error", f"Apache failed to restart:\n\n{msg}"))
                except Exception as e:
                    self.after(0, lambda: self.status_label.configure(text=f"Warning: Could not auto-restart Apache: {e}", text_color="red"))
                    self.logger.log(f"Warning: Could not auto-restart Apache: {e}", "WARNING")

            threading.Thread(target=do_restart, daemon=True).start()
        else:
            self.status_label.configure(text="Configuration saved. (Apache is not running; no restart required)", text_color="green")
