import customtkinter as ctk
import threading
import os
import shutil
from pathlib import Path
from tkinter import messagebox
import psutil
from core.apache_manager import ApacheManager
from core.mysql_manager import MySQLManager
from core.downloader import validate_url, download_file, extract_zip, robust_rmtree
from core.config import config_manager, COMPONENTS_PRESETS

class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Installing Component", message="Downloading files...", **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        
        # Window dimensions
        window_width = 400
        window_height = 150
        
        # Center relative to parent window
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        pos_x = parent_x + (parent_width // 2) - (window_width // 2)
        pos_y = parent_y + (parent_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        
        # Modal setup
        self.transient(parent)
        self.attributes("-topmost", True)
        self.grab_set()
        
        # Set icon
        icon_path = Path(__file__).parent.parent / "app.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))
            
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        
        self.label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=13, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(25, 10), sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self, height=10)
        self.progress_bar.grid(row=1, column=0, padx=30, pady=(0, 25), sticky="ew")
        self.progress_bar.set(0)
        
        # Disable close button
        self.protocol("WM_DELETE_WINDOW", lambda: None)

    def set_progress(self, value):
        self.progress_bar.set(value)
        
    def set_message(self, text):
        self.label.configure(text=text)

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.logger = logger
        self.apache = ApacheManager()
        self.mysql = MySQLManager()
        
        # Ensure managers have latest paths from config
        self.apache.update_paths()
        self.mysql.update_paths()

        # Let's configure the frame's grid system
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Services grid expands

        # Dynamic Color Definitions
        self.card_bg = ["#ffffff", "#1a2333"]
        self.card_border = ["#e2e8f0", "#2d3748"]
        self.text_dim = ["#64748b", "#94a3b8"]
        
        # Premium Secondary Button Styling
        self.secondary_bg = ["#cbd5e1", "#334155"]
        self.secondary_hover = ["#94a3b8", "#475569"]
        self.secondary_fg = ["#0f172a", "#f8fafc"]

        # ==========================================
        # 1. HEADER CARD (Title + Global Actions)
        # ==========================================
        self.header_card = ctk.CTkFrame(self, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.header_card.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.header_card.grid_columnconfigure(0, weight=1)

        # Header Text Frame
        self.header_text_frame = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.header_text_frame.pack(side="left", padx=20, pady=15)
        
        self.title_label = ctk.CTkLabel(self.header_text_frame, text="ENVIRONMENT CONTROL PANEL", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(self.header_text_frame, text="Manage local services and monitor resource allocation in real-time.", font=ctk.CTkFont(size=11), text_color=self.text_dim)
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Header Buttons Frame (Global Actions)
        self.global_btn_frame = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.global_btn_frame.pack(side="right", padx=20, pady=15)

        self.start_all_btn = ctk.CTkButton(self.global_btn_frame, text="Start All", command=self.start_all, fg_color=["#2ecc71", "#27ae60"], hover_color=["#27ae60", "#218838"], width=100)
        self.start_all_btn.pack(side="left", padx=5)
        
        self.stop_all_btn = ctk.CTkButton(self.global_btn_frame, text="Stop All", command=self.stop_all, fg_color=["#e74c3c", "#c0392b"], hover_color=["#c0392b", "#c82333"], width=100)
        self.stop_all_btn.pack(side="left", padx=5)

        self.restart_all_btn = ctk.CTkButton(self.global_btn_frame, text="Restart All", command=self.restart_all, fg_color=["#3b8ed0", "#1f6aa5"], hover_color=["#1f6aa5", "#155a8a"], width=100)
        self.restart_all_btn.pack(side="left", padx=5)

        # ==========================================
        # 2. SYSTEM RESOURCE MONITOR CARD
        # ==========================================
        self.monitor_card = ctk.CTkFrame(self, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.monitor_card.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.monitor_card.grid_columnconfigure((0, 1, 2), weight=1)

        # Monitor - CPU
        self.cpu_frame = ctk.CTkFrame(self.monitor_card, fg_color="transparent")
        self.cpu_frame.grid(row=0, column=0, padx=15, pady=12, sticky="ew")
        self.cpu_lbl = ctk.CTkLabel(self.cpu_frame, text="SYSTEM CPU", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_dim)
        self.cpu_lbl.pack(anchor="w")
        self.cpu_val = ctk.CTkLabel(self.cpu_frame, text="0.0%", font=ctk.CTkFont(size=20, weight="bold"))
        self.cpu_val.pack(anchor="w", pady=2)
        self.cpu_bar = ctk.CTkProgressBar(self.cpu_frame, height=6)
        self.cpu_bar.pack(fill="x", pady=(2, 0))
        self.cpu_bar.set(0)

        # Monitor - RAM
        self.ram_frame = ctk.CTkFrame(self.monitor_card, fg_color="transparent")
        self.ram_frame.grid(row=0, column=1, padx=15, pady=12, sticky="ew")
        self.ram_lbl = ctk.CTkLabel(self.ram_frame, text="SYSTEM RAM", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_dim)
        self.ram_lbl.pack(anchor="w")
        self.ram_val = ctk.CTkLabel(self.ram_frame, text="0.0%", font=ctk.CTkFont(size=20, weight="bold"))
        self.ram_val.pack(anchor="w", pady=2)
        self.ram_bar = ctk.CTkProgressBar(self.ram_frame, height=6)
        self.ram_bar.pack(fill="x", pady=(2, 0))
        self.ram_bar.set(0)

        # Monitor - Disk Space
        self.disk_frame = ctk.CTkFrame(self.monitor_card, fg_color="transparent")
        self.disk_frame.grid(row=0, column=2, padx=15, pady=12, sticky="ew")
        self.disk_lbl = ctk.CTkLabel(self.disk_frame, text="DISK SPACE", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.text_dim)
        self.disk_lbl.pack(anchor="w")
        self.disk_val = ctk.CTkLabel(self.disk_frame, text="0.0%", font=ctk.CTkFont(size=20, weight="bold"))
        self.disk_val.pack(anchor="w", pady=2)
        self.disk_bar = ctk.CTkProgressBar(self.disk_frame, height=6)
        self.disk_bar.pack(fill="x", pady=(2, 0))
        self.disk_bar.set(0)

        # ==========================================
        # 3. SERVICE CARDS GRID (2x2)
        # ==========================================
        self.services_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.services_grid.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
        self.services_grid.grid_columnconfigure((0, 1), weight=1)
        self.services_grid.grid_rowconfigure((0, 1), weight=1)

        # --- A. APACHE CARD ---
        self.apache_card = ctk.CTkFrame(self.services_grid, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.apache_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.apache_card.grid_columnconfigure(0, weight=1)
        self.setup_apache_card_ui()

        # --- B. MYSQL CARD ---
        self.mysql_card = ctk.CTkFrame(self.services_grid, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.mysql_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.mysql_card.grid_columnconfigure(0, weight=1)
        self.setup_mysql_card_ui()

        # --- C. PHP CARD ---
        self.php_card = ctk.CTkFrame(self.services_grid, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.php_card.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.php_card.grid_columnconfigure(0, weight=1)
        self.setup_php_card_ui()

        # --- D. PHPMYADMIN CARD ---
        self.pma_card = ctk.CTkFrame(self.services_grid, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.pma_card.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.pma_card.grid_columnconfigure(0, weight=1)
        self.setup_pma_card_ui()

        # ==========================================
        # 4. PROGRESS BAR FOR SETUP
        # ==========================================
        self.progress_bar = ctk.CTkProgressBar(self, height=8)
        self.progress_bar.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.progress_bar.grid_remove()
        self.progress_bar.set(0)

        self.update_status()

    # =========================================================================
    # UI Setup Helpers for Service Cards
    # =========================================================================
    
    def create_badge(self, parent, text, type="running"):
        """Creates a modern styled pill badge for statuses."""
        if type == "running" or type == "installed":
            bg = ["#e6f4ea", "#14321a"]
            fg = ["#137333", "#34a853"]
        elif type == "stopped" or type == "not_installed":
            bg = ["#fce8e6", "#3c1e1a"]
            fg = ["#c5221f", "#ea4335"]
        else: # Warning / Other
            bg = ["#fef7e0", "#3c2e15"]
            fg = ["#b06000", "#fbbc04"]
            
        badge = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, border_width=0)
        label = ctk.CTkLabel(badge, text=text.upper(), text_color=fg, font=ctk.CTkFont(size=10, weight="bold"), height=20)
        label.pack(padx=8, pady=2)
        return badge

    def update_badge(self, badge_frame, text, type="running"):
        """Updates a badge frame color and text dynamically."""
        if type == "running" or type == "installed":
            bg = ["#e6f4ea", "#14321a"]
            fg = ["#137333", "#34a853"]
        elif type == "stopped" or type == "not_installed":
            bg = ["#fce8e6", "#3c1e1a"]
            fg = ["#c5221f", "#ea4335"]
        else: # Warning / Other
            bg = ["#fef7e0", "#3c2e15"]
            fg = ["#b06000", "#fbbc04"]
            
        badge_frame.configure(fg_color=bg)
        for child in badge_frame.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text=text.upper(), text_color=fg)

    def setup_apache_card_ui(self):
        # Card Header
        header = ctk.CTkFrame(self.apache_card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        lbl = ctk.CTkLabel(header, text="Apache Web Server", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(side="left")
        self.apache_badge = self.create_badge(header, "Stopped", "stopped")
        self.apache_badge.pack(side="right")

        # Card Content (Stats)
        content = ctk.CTkFrame(self.apache_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)
        content.grid_columnconfigure((0, 1), weight=1)

        self.apache_port_lbl = ctk.CTkLabel(content, text="Port: -", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.apache_port_lbl.grid(row=0, column=0, sticky="ew", pady=2)
        
        self.apache_pid_lbl = ctk.CTkLabel(content, text="PID: -", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.apache_pid_lbl.grid(row=0, column=1, sticky="ew", pady=2)

        self.apache_cpu_lbl = ctk.CTkLabel(content, text="CPU: 0.0%", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.apache_cpu_lbl.grid(row=1, column=0, sticky="ew", pady=2)

        self.apache_ram_lbl = ctk.CTkLabel(content, text="Memory: 0.0 MB", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.apache_ram_lbl.grid(row=1, column=1, sticky="ew", pady=2)

        # Card Footer (Buttons)
        footer = ctk.CTkFrame(self.apache_card, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=(5, 15))
        footer.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.apache_btn = ctk.CTkButton(footer, text="Start", command=self.toggle_apache, height=28)
        self.apache_btn.grid(row=0, column=0, padx=2, sticky="ew")

        self.apache_web_btn = ctk.CTkButton(footer, text="Preview", command=self.open_browser, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.apache_web_btn.grid(row=0, column=1, padx=2, sticky="ew")

        self.apache_htdocs_btn = ctk.CTkButton(footer, text="Htdocs 📁", command=self.open_htdocs, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.apache_htdocs_btn.grid(row=0, column=2, padx=2, sticky="ew")

        self.apache_conf_btn = ctk.CTkButton(footer, text="Config ⚙", command=self.open_apache_config, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.apache_conf_btn.grid(row=0, column=3, padx=2, sticky="ew")

    def setup_mysql_card_ui(self):
        # Card Header
        header = ctk.CTkFrame(self.mysql_card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        lbl = ctk.CTkLabel(header, text="MySQL Database", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(side="left")
        self.mysql_badge = self.create_badge(header, "Stopped", "stopped")
        self.mysql_badge.pack(side="right")

        # Card Content (Stats)
        content = ctk.CTkFrame(self.mysql_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)
        content.grid_columnconfigure((0, 1), weight=1)

        self.mysql_port_lbl = ctk.CTkLabel(content, text="Port: -", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.mysql_port_lbl.grid(row=0, column=0, sticky="ew", pady=2)
        
        self.mysql_pid_lbl = ctk.CTkLabel(content, text="PID: -", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.mysql_pid_lbl.grid(row=0, column=1, sticky="ew", pady=2)

        self.mysql_cpu_lbl = ctk.CTkLabel(content, text="CPU: 0.0%", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.mysql_cpu_lbl.grid(row=1, column=0, sticky="ew", pady=2)

        self.mysql_ram_lbl = ctk.CTkLabel(content, text="Memory: 0.0 MB", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.mysql_ram_lbl.grid(row=1, column=1, sticky="ew", pady=2)

        # Card Footer (Buttons)
        footer = ctk.CTkFrame(self.mysql_card, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=(5, 15))
        footer.grid_columnconfigure((0, 1, 2), weight=1)

        self.mysql_btn = ctk.CTkButton(footer, text="Start", command=self.toggle_mysql, height=28)
        self.mysql_btn.grid(row=0, column=0, padx=2, sticky="ew")

        self.mysql_admin_btn = ctk.CTkButton(footer, text="Admin (PMA)", command=self.open_pma, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.mysql_admin_btn.grid(row=0, column=1, padx=2, sticky="ew")

        self.mysql_conf_btn = ctk.CTkButton(footer, text="Config ⚙", command=self.open_mysql_config, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.mysql_conf_btn.grid(row=0, column=2, padx=2, sticky="ew")

    def setup_php_card_ui(self):
        # Card Header
        header = ctk.CTkFrame(self.php_card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        lbl = ctk.CTkLabel(header, text="PHP Engine Support", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(side="left")
        self.php_badge = self.create_badge(header, "Not Installed", "not_installed")
        self.php_badge.pack(side="right")

        # Card Content (Details)
        content = ctk.CTkFrame(self.php_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)

        self.php_version_lbl = ctk.CTkLabel(content, text="Version: Unknown", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.php_version_lbl.pack(fill="x", pady=2)
        
        self.php_path_lbl = ctk.CTkLabel(content, text="Path: Not installed", font=ctk.CTkFont(size=11), text_color=self.text_dim, anchor="w")
        self.php_path_lbl.pack(fill="x", pady=2)

        # Card Footer (Buttons)
        footer = ctk.CTkFrame(self.php_card, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=(5, 15))
        footer.grid_columnconfigure((0, 1), weight=1)

        self.php_btn = ctk.CTkButton(footer, text="Install", command=self.setup_php, height=28)
        self.php_btn.grid(row=0, column=0, padx=2, sticky="ew")

        self.php_conf_btn = ctk.CTkButton(footer, text="php.ini ⚙", command=self.open_php_config, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.php_conf_btn.grid(row=0, column=1, padx=2, sticky="ew")

    def setup_pma_card_ui(self):
        # Card Header
        header = ctk.CTkFrame(self.pma_card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        lbl = ctk.CTkLabel(header, text="phpMyAdmin Web Panel", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(side="left")
        self.pma_badge = self.create_badge(header, "Not Installed", "not_installed")
        self.pma_badge.pack(side="right")

        # Card Content (Details)
        content = ctk.CTkFrame(self.pma_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)

        self.pma_desc_lbl = ctk.CTkLabel(content, text="Web UI for managing MySQL databases.", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.pma_desc_lbl.pack(fill="x", pady=2)
        
        self.pma_url_lbl = ctk.CTkLabel(content, text="URL: Not available", font=ctk.CTkFont(size=11), text_color=self.text_dim, anchor="w")
        self.pma_url_lbl.pack(fill="x", pady=2)

        # Card Footer (Buttons)
        footer = ctk.CTkFrame(self.pma_card, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=(5, 15))
        footer.grid_columnconfigure((0, 1), weight=1)

        self.pma_btn = ctk.CTkButton(footer, text="Install", command=self.setup_pma, height=28)
        self.pma_btn.grid(row=0, column=0, padx=2, sticky="ew")

        self.pma_open_btn = ctk.CTkButton(footer, text="Open Panel", command=self.open_pma, fg_color=self.secondary_bg, hover_color=self.secondary_hover, text_color=self.secondary_fg, height=28)
        self.pma_open_btn.grid(row=0, column=1, padx=2, sticky="ew")

    # =========================================================================
    # Operation & Toggling Methods
    # =========================================================================

    def refresh_dashboard(self):
        """Refreshes the dashboard by updating paths in managers and status."""
        self.apache.update_paths()
        self.mysql.update_paths()
        self.update_status()

    def update_status(self):
        apache_running = self.apache.is_running()
        mysql_running = self.mysql.is_running()

        # 1. Update badges
        self.update_badge(self.apache_badge, "Running" if apache_running else "Stopped", "running" if apache_running else "stopped")
        self.update_badge(self.mysql_badge, "Running" if mysql_running else "Stopped", "running" if mysql_running else "stopped")

        # 2. Update service details & stats
        apache_stats = self.apache.get_stats() if apache_running else None
        mysql_stats = self.mysql.get_stats() if mysql_running else None

        self.apache_port_lbl.configure(text=f"Port: {self.apache.port}")
        self.apache_pid_lbl.configure(text=f"PID: {apache_stats['pid'] if apache_stats else '-'}")
        self.apache_cpu_lbl.configure(text=f"CPU: {apache_stats['cpu'] if apache_stats else '0.0'}%")
        self.apache_ram_lbl.configure(text=f"Memory: {apache_stats['ram'] if apache_stats else '0.0'} MB")

        self.mysql_port_lbl.configure(text=f"Port: {self.mysql.port}")
        self.mysql_pid_lbl.configure(text=f"PID: {mysql_stats['pid'] if mysql_stats else '-'}")
        self.mysql_cpu_lbl.configure(text=f"CPU: {mysql_stats['cpu'] if mysql_stats else '0.0'}%")
        self.mysql_ram_lbl.configure(text=f"Memory: {mysql_stats['ram'] if mysql_stats else '0.0'} MB")

        # Toggle Button Texts & Colors dynamically
        self.apache_btn.configure(text="Stop" if apache_running else "Start", fg_color=["#e74c3c", "#c0392b"] if apache_running else ["#3b8ed0", "#1f6aa5"])
        self.mysql_btn.configure(text="Stop" if mysql_running else "Start", fg_color=["#e74c3c", "#c0392b"] if mysql_running else ["#3b8ed0", "#1f6aa5"])

        # Update global buttons states
        if apache_running and mysql_running:
            self.start_all_btn.configure(state="disabled")
        else:
            self.start_all_btn.configure(state="normal")

        if not apache_running and not mysql_running:
            self.stop_all_btn.configure(state="disabled")
            self.restart_all_btn.configure(state="disabled")
        else:
            self.stop_all_btn.configure(state="normal")
            self.restart_all_btn.configure(state="normal")

        # PHP Info
        php_dir = Path(config_manager.get("install_dir")) / "php"
        php_installed = php_dir.exists() and any(php_dir.iterdir())
        
        self.update_badge(self.php_badge, "Installed" if php_installed else "Not Installed", "installed" if php_installed else "not_installed")
        self.php_btn.configure(text="Reinstall" if php_installed else "Install")
        
        if php_installed:
            current_php_url = config_manager.get("php_url")
            php_ver = "Installed"
            for k, v in COMPONENTS_PRESETS["PHP"].items():
                if v == current_php_url:
                    php_ver = k
                    break
            self.php_version_lbl.configure(text=f"Version: {php_ver}")
            self.php_path_lbl.configure(text=f"Path: {php_dir.name} ({php_dir.parent.name})")
        else:
            self.php_version_lbl.configure(text="Version: -")
            self.php_path_lbl.configure(text="Path: Not installed")

        # phpMyAdmin Info
        pma_dir = self.get_pma_dir()
        pma_installed = pma_dir.exists() and any(pma_dir.iterdir())

        self.update_badge(self.pma_badge, "Installed" if pma_installed else "Not Installed", "installed" if pma_installed else "not_installed")
        self.pma_btn.configure(text="Reinstall" if pma_installed else "Install")
        
        if pma_installed:
            self.pma_url_lbl.configure(text=f"URL: http://localhost:{self.apache.port}/phpmyadmin")
        else:
            self.pma_url_lbl.configure(text="URL: Not available")

        # 3. Update System Resource Monitors
        try:
            sys_cpu = psutil.cpu_percent()
            sys_ram = psutil.virtual_memory().percent
            
            # Disk space of installation dir
            install_dir = config_manager.get("install_dir")
            try:
                sys_disk = psutil.disk_usage(install_dir).percent
            except Exception:
                sys_disk = psutil.disk_usage("C:").percent
        except Exception:
            sys_cpu = 0.0
            sys_ram = 0.0
            sys_disk = 0.0

        self.cpu_val.configure(text=f"{sys_cpu:.1f}%")
        self.cpu_bar.set(sys_cpu / 100.0)

        self.ram_val.configure(text=f"{sys_ram:.1f}%")
        self.ram_bar.set(sys_ram / 100.0)

        self.disk_val.configure(text=f"{sys_disk:.1f}%")
        self.disk_bar.set(sys_disk / 100.0)

        # Loop the status update
        self.after(2000, self.update_status)

    def toggle_apache(self):
        if self.apache.is_running():
            success, msg = self.apache.stop()
            self.logger.log(msg, "INFO" if success else "ERROR")
        else:
            threading.Thread(target=self.run_setup_and_start, args=("apache", self.apache)).start()

    def toggle_mysql(self):
        if self.mysql.is_running():
            success, msg = self.mysql.stop()
            self.logger.log(msg, "INFO" if success else "ERROR")
        else:
            threading.Thread(target=self.run_setup_and_start, args=("mysql", self.mysql)).start()

    def setup_php(self):
        php_dir = Path(config_manager.get("install_dir")) / "php"
        is_installed = php_dir.exists() and any(php_dir.iterdir())
        
        if is_installed:
            if not messagebox.askyesno("Confirm Reinstall", "Are you sure you want to reinstall PHP? This will delete your current php.ini and all local PHP files."):
                return
        
        threading.Thread(target=self.run_setup_and_start, args=("php",), kwargs={"force": is_installed}).start()

    def get_htdocs_dir(self):
        htdocs_val = config_manager.get("htdocs_dir")
        if htdocs_val:
            return Path(htdocs_val)
        legacy_htdocs = Path(self.apache.install_dir) / "htdocs"
        if legacy_htdocs.exists():
            return legacy_htdocs
        return Path(config_manager.get("install_dir")).parent / "htdocs"

    def get_pma_dir(self):
        pma_dir = Path(self.apache.install_dir) / "htdocs" / "phpmyadmin"
        if pma_dir.exists() and any(pma_dir.iterdir()):
            return pma_dir
        htdocs_val = config_manager.get("htdocs_dir")
        if htdocs_val and (Path(htdocs_val) / "phpmyadmin").exists() and any((Path(htdocs_val) / "phpmyadmin").iterdir()):
            return Path(htdocs_val) / "phpmyadmin"
        return pma_dir

    def setup_pma(self):
        pma_dir = self.get_pma_dir()
        is_installed = pma_dir.exists() and any(pma_dir.iterdir())
        
        if is_installed:
            if not messagebox.askyesno("Confirm Reinstall", "Are you sure you want to reinstall phpMyAdmin? This will delete any custom configurations in the phpmyadmin folder."):
                return
                
        threading.Thread(target=self.run_setup_and_start, args=("phpmyadmin",), kwargs={"force": is_installed}).start()

    # =========================================================================
    # Config File Shortcut Open Methods
    # =========================================================================
    
    def open_apache_config(self):
        conf_path = self.apache.install_dir / "conf" / "httpd.conf"
        self.open_config_file(conf_path, "Apache (httpd.conf)")

    def open_mysql_config(self):
        mysql_dir = self.mysql.find_mysql_dir()
        if mysql_dir:
            conf_path = mysql_dir / "my.ini"
            self.open_config_file(conf_path, "MySQL (my.ini)")
        else:
            self.logger.log("MySQL folder not found. Please install MySQL first.", "ERROR")

    def open_php_config(self):
        php_dir = Path(config_manager.get("install_dir")) / "php"
        conf_path = php_dir / "php.ini"
        self.open_config_file(conf_path, "PHP (php.ini)")

    def open_config_file(self, path, name):
        if path and path.exists():
            try:
                self.logger.log(f"Opening config file: {path}")
                os.startfile(str(path))
            except Exception as e:
                self.logger.log(f"Failed to open {name} config file: {e}", "ERROR")
        else:
            self.logger.log(f"{name} config file not found. Is it installed?", "ERROR")

    # =========================================================================
    # Setup Download & Installation Workflow
    # =========================================================================

    def create_progress_dialog(self, title, message):
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

    def run_setup_and_start(self, service_name, manager=None, force=False, skip_ui_cleanup=False):
        if not skip_ui_cleanup:
            self.php_btn.configure(state="disabled")
            self.pma_btn.configure(state="disabled")
            self.after(0, lambda: self.progress_bar.grid())
        
        has_dialog = False
        try:
            was_apache_running = self.apache.is_running()
            was_mysql_running = self.mysql.is_running()

            if force:
                if was_apache_running or was_mysql_running:
                    self.logger.log(f"Stopping all servers before reinstalling {service_name}...")
                    self.stop_all()

            if manager:
                manager.update_paths()

            if service_name == "phpmyadmin":
                pma_dir = Path(self.apache.install_dir) / "htdocs" / "phpmyadmin"
                needs_setup = force or not pma_dir.exists() or not any(pma_dir.iterdir())
            else:
                needs_setup = force or not manager or not manager.exe_path or not manager.exe_path.exists()
            
            if needs_setup:
                has_dialog = True
                display_name = "phpMyAdmin" if service_name == "phpmyadmin" else service_name.upper()
                self.after(0, lambda: self.create_progress_dialog(f"Installing {display_name}", f"Downloading {display_name}..."))
                
                self.logger.log(f"{service_name.capitalize()} setup started (Force={force})...")
                url = config_manager.get(f"{service_name}_url")
                
                if not validate_url(url):
                    self.logger.log(f"Invalid URL for {service_name}: {url}", "ERROR")
                    return

                zip_name = f"{service_name}.zip"
                dest_zip = Path(config_manager.get("install_dir")) / zip_name
                dest_zip.parent.mkdir(parents=True, exist_ok=True)

                def progress_cb(p):
                    if p == -1:
                        if hasattr(self, 'progress_dialog') and self.progress_dialog:
                            current = self.progress_dialog.progress_bar.get()
                            new_val = (current + 0.05) % 1.0
                            self.after(0, lambda: self.update_progress_dialog(new_val))
                        
                        current_pb = self.progress_bar.get()
                        new_pb = (current_pb + 0.05) % 1.0
                        self.after(0, lambda: self.progress_bar.set(new_pb))
                    else:
                        self.after(0, lambda: self.update_progress_dialog(p))
                        self.after(0, lambda: self.progress_bar.set(p))

                if download_file(url, str(dest_zip), progress_cb):
                    self.logger.log(f"Download complete. Extracting {service_name}...")
                    display_name = "phpMyAdmin" if service_name == "phpmyadmin" else service_name.upper()
                    self.after(0, lambda: self.update_progress_dialog(1.0, f"Extracting {display_name}..."))
                    
                    if service_name == "phpmyadmin":
                        extract_to = Path(config_manager.get("install_dir")) / "pma_tmp"
                    else:
                        extract_to = Path(config_manager.get("install_dir")) / service_name
                    
                    if force and extract_to.exists():
                        robust_rmtree(extract_to)
                    
                    extract_to.mkdir(parents=True, exist_ok=True)
                    
                    if extract_zip(str(dest_zip), str(extract_to)):
                        # Configure PHP
                        if service_name == "php":
                            ini_dev = extract_to / "php.ini-development"
                            ini_target = extract_to / "php.ini"
                            if ini_dev.exists():
                                shutil.copy(ini_dev, ini_target)
                                
                                with open(ini_target, "r") as f:
                                    lines = f.readlines()
                                
                                new_ini_lines = []
                                ext_dir = str(extract_to / "ext").replace("\\", "/")
                                for line in lines:
                                    clean_line = line.strip()
                                    if clean_line in [";extension_dir = \"ext\"", "; extension_dir = \"ext\""]:
                                        new_ini_lines.append(f"extension_dir = \"{ext_dir}\"\n")
                                    elif clean_line in [";extension=mysqli", "; extension=mysqli"]:
                                        new_ini_lines.append("extension=mysqli\n")
                                    elif clean_line in [";extension=mbstring", "; extension=mbstring"]:
                                        new_ini_lines.append("extension=mbstring\n")
                                    elif clean_line in [";extension=openssl", "; extension=openssl"]:
                                        new_ini_lines.append("extension=openssl\n")
                                    elif clean_line in [";extension=curl", "; extension=curl"]:
                                        new_ini_lines.append("extension=curl\n")
                                    elif clean_line in [";extension=pdo_mysql", "; extension=pdo_mysql"]:
                                        new_ini_lines.append("extension=pdo_mysql\n")
                                    elif clean_line in [";extension=zip", "; extension=zip"]:
                                        new_ini_lines.append("extension=zip\n")
                                    elif clean_line in [";extension=gd", "; extension=gd"]:
                                        new_ini_lines.append("extension=gd\n")
                                    elif clean_line in [";extension=fileinfo", "; extension=fileinfo"]:
                                        new_ini_lines.append("extension=fileinfo\n")
                                    elif clean_line in [";extension=intl", "; extension=intl"]:
                                        new_ini_lines.append("extension=intl\n")
                                    elif clean_line in [";extension=exif", "; extension=exif"]:
                                        new_ini_lines.append("extension=exif\n")
                                    elif clean_line in [";extension=sqlite3", "; extension=sqlite3"]:
                                        new_ini_lines.append("extension=sqlite3\n")
                                    elif clean_line in [";extension=pdo_sqlite", "; extension=pdo_sqlite"]:
                                        new_ini_lines.append("extension=pdo_sqlite\n")
                                    elif clean_line in [";extension=bcmath", "; extension=bcmath"]:
                                        new_ini_lines.append("extension=bcmath\n")
                                    else:
                                        new_ini_lines.append(line)
                                
                                with open(ini_target, "w") as f:
                                    f.writelines(new_ini_lines)
                                self.logger.log("Configured php.ini with mysqli, zip, gd, and other essential extensions.")
                        
                        # Configure phpMyAdmin
                        if service_name == "phpmyadmin":
                            htdocs_pma = Path(self.apache.install_dir) / "htdocs" / "phpmyadmin"
                            htdocs_pma.parent.mkdir(parents=True, exist_ok=True)
                            
                            extracted_folder = next(extract_to.iterdir())
                            robust_rmtree(htdocs_pma)
                            
                            shutil.move(str(extracted_folder), str(htdocs_pma))
                            robust_rmtree(extract_to)
                            
                            sample_config = htdocs_pma / "config.sample.inc.php"
                            real_config = htdocs_pma / "config.inc.php"
                            if sample_config.exists() and not real_config.exists():
                                import secrets
                                secret = secrets.token_hex(16)
                                with open(sample_config, "r") as f:
                                    content = f.read()
                                content = content.replace("$cfg['blowfish_secret'] = '';", f"$cfg['blowfish_secret'] = '{secret}';")
                                content = content.replace("$cfg['Servers'][$i]['AllowNoPassword'] = false;", "$cfg['Servers'][$i]['AllowNoPassword'] = true;")
                                with open(real_config, "w") as f:
                                    f.write(content)
                                self.logger.log("Configured phpMyAdmin with blowfish secret and AllowNoPassword=true.")

                        self.logger.log(f"{service_name.capitalize()} setup successfully.")
                        
                        if manager:
                            manager.update_paths()
                        
                        if service_name == "php":
                            if was_apache_running or was_mysql_running:
                                self.logger.log("Auto-restarting servers to apply PHP changes...")
                                if was_apache_running:
                                    self.apache.stop()
                                    import time
                                    time.sleep(1)
                                    self.apache.start_server()
                                if was_mysql_running:
                                    self.mysql.stop()
                                    import time
                                    time.sleep(1)
                                    self.mysql.start_server()
                                self.logger.log("Servers restarted successfully.")

                        os.remove(dest_zip)
                    else:
                        self.logger.log(f"Failed to extract {service_name}.", "ERROR")
                        return
                else:
                    self.logger.log(f"Failed to download {service_name}.", "ERROR")
                    return

            if manager:
                self.logger.log(f"Starting {service_name.capitalize()}...")
                success, msg = manager.start_server()
                self.logger.log(msg, "INFO" if success else "ERROR")
        finally:
            if not skip_ui_cleanup:
                self.after(0, self.cleanup_ui)
            if has_dialog:
                self.after(0, self.close_progress_dialog)

    def start_all(self):
        """Starts all servers in a single sequential background thread to keep progress bar stable."""
        def run_start_all():
            self.after(0, lambda: self.progress_bar.grid())
            try:
                if not self.apache.is_running():
                    self.run_setup_and_start("apache", self.apache, skip_ui_cleanup=True)
                
                if not self.mysql.is_running():
                    self.run_setup_and_start("mysql", self.mysql, skip_ui_cleanup=True)
                
                self.logger.log("All servers checked/started.")
            finally:
                self.after(0, self.cleanup_ui)

        threading.Thread(target=run_start_all, daemon=True).start()

    def cleanup_ui(self):
        """Re-enables UI elements and hides progress bar."""
        self.php_btn.configure(state="normal")
        self.pma_btn.configure(state="normal")
        self.progress_bar.grid_remove()
        self.progress_bar.set(0)

    def stop_all(self):
        any_running = self.apache.is_running() or self.mysql.is_running()
        if self.apache.is_running():
            self.apache.stop()
        if self.mysql.is_running():
            self.mysql.stop()
        
        if any_running:
            self.logger.log("All servers stopped.")

    def restart_all(self):
        self.logger.log("Restarting all servers...")
        self.stop_all()
        import time
        time.sleep(1)
        self.start_all()

    def open_browser(self):
        import webbrowser
        port = config_manager.get("apache_port")
        url = f"http://localhost:{port}/index.php"
        
        htdocs = self.get_htdocs_dir()
        htdocs.mkdir(parents=True, exist_ok=True)
        index_file = htdocs / "index.php"
        if not index_file.exists():
            with open(index_file, "w") as f:
                f.write("<?php phpinfo(); ?>")
            self.logger.log("Created sample index.php in htdocs.")
        
        self.logger.log(f"Opening {url} in browser...")
        webbrowser.open(url)

    def open_htdocs(self):
        htdocs = self.get_htdocs_dir()
        htdocs.mkdir(parents=True, exist_ok=True)
        self.logger.log(f"Opening htdocs folder: {htdocs}")
        os.startfile(htdocs)

    def open_pma(self):
        import webbrowser
        port = config_manager.get("apache_port")
        url = f"http://localhost:{port}/phpmyadmin/index.php"
        pma_dir = self.get_pma_dir()
        if pma_dir.exists() and any(pma_dir.iterdir()):
            self.logger.log(f"Opening phpMyAdmin: {url}")
            webbrowser.open(url)
        else:
            self.logger.log("phpMyAdmin not installed. Please install it first.", "ERROR")
