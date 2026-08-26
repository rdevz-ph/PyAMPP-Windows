import customtkinter as ctk
import socket
import ssl
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import time
import threading
import os
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from core.config import config_manager
from core.apache_manager import ApacheManager

class DiagnosticsFrame(ctk.CTkFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.logger = logger
        
        # Grid configure: 2 equal-width columns for Diagnostics and SSL validation
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Aesthetics
        self.card_bg = ["#ffffff", "#1a2333"]
        self.card_border = ["#e2e8f0", "#2d3748"]
        self.text_dim = ["#64748b", "#94a3b8"]
        
        self.secondary_bg = ["#cbd5e1", "#334155"]
        self.secondary_hover = ["#94a3b8", "#475569"]
        self.secondary_fg = ["#0f172a", "#f8fafc"]

        # =====================================================================
        # CARD 1: SERVICE HEALTH DIAGNOSTICS
        # =====================================================================
        self.health_card = ctk.CTkFrame(self, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.health_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.health_card.grid_columnconfigure(0, weight=1)
        self.setup_health_ui()

        # =====================================================================
        # CARD 2: SSL CERTIFICATE CHECKER
        # =====================================================================
        self.ssl_card = ctk.CTkFrame(self, fg_color=self.card_bg, border_width=1, border_color=self.card_border, corner_radius=12)
        self.ssl_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.ssl_card.grid_columnconfigure(0, weight=1)
        self.setup_ssl_ui()

        # Run initial diagnostics in background
        self.run_diagnostics()

    # =========================================================================
    # Service Health UI Setup
    # =========================================================================
    def setup_health_ui(self):
        # Header
        header = ctk.CTkFrame(self.health_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        lbl = ctk.CTkLabel(header, text="Service Health Diagnostics", font=ctk.CTkFont(size=15, weight="bold"))
        lbl.pack(side="left")
        
        self.health_refresh_btn = ctk.CTkButton(header, text="Run Diagnostics", font=ctk.CTkFont(size=11), width=110, height=26, command=self.run_diagnostics)
        self.health_refresh_btn.pack(side="right")

        # Diagnostics Area
        self.health_content = ctk.CTkFrame(self.health_card, fg_color="transparent")
        self.health_content.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Apache Diagnostics Row
        self.apache_title = ctk.CTkLabel(self.health_content, text="Apache Web Server", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.apache_title.pack(fill="x", pady=(5, 0))
        
        self.apache_status_frame = ctk.CTkFrame(self.health_content, fg_color="transparent")
        self.apache_status_frame.pack(fill="x", pady=2)
        self.apache_badge = self.create_badge(self.apache_status_frame, "Pending", "warning")
        self.apache_badge.pack(side="left")
        self.apache_port_lbl = ctk.CTkLabel(self.apache_status_frame, text="Port check: -", font=ctk.CTkFont(size=12), text_color=self.text_dim)
        self.apache_port_lbl.pack(side="left", padx=10)
        
        self.apache_ping_lbl = ctk.CTkLabel(self.health_content, text="HTTP reachability: Pending", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.apache_ping_lbl.pack(fill="x", pady=(0, 10))

        # 2. MySQL Diagnostics Row
        self.mysql_title = ctk.CTkLabel(self.health_content, text="MySQL Database", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.mysql_title.pack(fill="x", pady=(5, 0))
        
        self.mysql_status_frame = ctk.CTkFrame(self.health_content, fg_color="transparent")
        self.mysql_status_frame.pack(fill="x", pady=2)
        self.mysql_badge = self.create_badge(self.mysql_status_frame, "Pending", "warning")
        self.mysql_badge.pack(side="left")
        self.mysql_port_lbl = ctk.CTkLabel(self.mysql_status_frame, text="Port check: -", font=ctk.CTkFont(size=12), text_color=self.text_dim)
        self.mysql_port_lbl.pack(side="left", padx=10)
        
        self.mysql_conn_lbl = ctk.CTkLabel(self.health_content, text="TCP connection latency: Pending", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.mysql_conn_lbl.pack(fill="x", pady=(0, 10))

        # 3. PHP CLI Diagnostics Row
        self.php_title = ctk.CTkLabel(self.health_content, text="PHP CLI Environment", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.php_title.pack(fill="x", pady=(5, 0))
        
        self.php_status_frame = ctk.CTkFrame(self.health_content, fg_color="transparent")
        self.php_status_frame.pack(fill="x", pady=2)
        self.php_badge = self.create_badge(self.php_status_frame, "Pending", "warning")
        self.php_badge.pack(side="left")
        
        self.php_cli_lbl = ctk.CTkLabel(self.health_content, text="PHP CLI execution: Pending", font=ctk.CTkFont(size=12), text_color=self.text_dim, anchor="w")
        self.php_cli_lbl.pack(fill="x", pady=(0, 10))

    # =========================================================================
    # SSL Checker UI Setup
    # =========================================================================
    def setup_ssl_ui(self):
        # Header
        header = ctk.CTkFrame(self.ssl_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        lbl = ctk.CTkLabel(header, text="SSL Certificate Inspector", font=ctk.CTkFont(size=15, weight="bold"))
        lbl.pack(side="left")

        # Input Frame
        input_frame = ctk.CTkFrame(self.ssl_card, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=5)
        
        self.ssl_entry = ctk.CTkEntry(input_frame, placeholder_text="localhost or url...")
        self.ssl_entry.insert(0, "localhost")
        self.ssl_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.ssl_check_btn = ctk.CTkButton(input_frame, text="Verify SSL", font=ctk.CTkFont(size=11), width=80, command=self.run_ssl_check)
        self.ssl_check_btn.pack(side="right")

        # Diagnostic Details Box
        self.ssl_content = ctk.CTkScrollableFrame(self.ssl_card, fg_color="transparent")
        self.ssl_content.pack(fill="both", expand=True, padx=20, pady=10)

        # SSL Checker Status Rows
        self.ssl_conn_title = ctk.CTkLabel(self.ssl_content, text="SSL Connection status", font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        self.ssl_conn_title.pack(fill="x", pady=(5, 0))
        
        self.ssl_conn_frame = ctk.CTkFrame(self.ssl_content, fg_color="transparent")
        self.ssl_conn_frame.pack(fill="x", pady=2)
        self.ssl_conn_badge = self.create_badge(self.ssl_conn_frame, "Idle", "warning")
        self.ssl_conn_badge.pack(side="left")
        
        self.ssl_trust_lbl = ctk.CTkLabel(self.ssl_conn_frame, text="Trust state: Unknown", font=ctk.CTkFont(size=12), text_color=self.text_dim)
        self.ssl_trust_lbl.pack(side="left", padx=10)

        # SSL Cert Properties Card
        self.cert_info_box = ctk.CTkFrame(self.ssl_content, fg_color=["#f8fafc", "#141c2b"], border_width=1, border_color=self.card_border, corner_radius=8)
        self.cert_info_box.pack(fill="both", expand=True, pady=10)
        self.cert_info_box.grid_columnconfigure(0, weight=1)

        self.cert_subject = ctk.CTkLabel(self.cert_info_box, text="Common Name (CN): -", font=ctk.CTkFont(size=11), anchor="w")
        self.cert_subject.grid(row=0, column=0, padx=15, pady=4, sticky="ew")

        self.cert_issuer = ctk.CTkLabel(self.cert_info_box, text="Issuer: -", font=ctk.CTkFont(size=11), anchor="w")
        self.cert_issuer.grid(row=1, column=0, padx=15, pady=4, sticky="ew")

        self.cert_dates = ctk.CTkLabel(self.cert_info_box, text="Expiry: -", font=ctk.CTkFont(size=11), anchor="w")
        self.cert_dates.grid(row=2, column=0, padx=15, pady=4, sticky="ew")

        self.cert_proto = ctk.CTkLabel(self.cert_info_box, text="Protocol / TLS version: -", font=ctk.CTkFont(size=11), anchor="w")
        self.cert_proto.grid(row=3, column=0, padx=15, pady=4, sticky="ew")

        # Auto-Fix SSL Button (Hidden by default, shown when certificate is missing or disabled)
        self.ssl_autofix_btn = ctk.CTkButton(
            self.ssl_card, 
            text="Auto-Fix SSL & Enable HTTPS 🛠", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            fg_color=["#e74c3c", "#c0392b"], 
            hover_color=["#c0392b", "#d32f2f"], 
            command=self.autofix_ssl
        )
        self.ssl_autofix_btn.pack(fill="x", padx=20, pady=(0, 20))
        self.ssl_autofix_btn.pack_forget()

        # SSL Tools Frame (Hidden by default, shown when SSL is configured & enabled)
        self.ssl_tools_frame = ctk.CTkFrame(self.ssl_card, fg_color="transparent")
        self.ssl_tools_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.ssl_tools_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.ssl_regenerate_btn = ctk.CTkButton(
            self.ssl_tools_frame, 
            text="Regenerate SSL 🔄", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            command=self.regenerate_ssl
        )
        self.ssl_regenerate_btn.grid(row=0, column=0, padx=(0, 2), sticky="ew")

        self.ssl_edit_btn = ctk.CTkButton(
            self.ssl_tools_frame, 
            text="Edit SSL Config 📝", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            fg_color=self.secondary_bg, 
            hover_color=self.secondary_hover, 
            text_color=self.secondary_fg, 
            command=self.edit_ssl_config
        )
        self.ssl_edit_btn.grid(row=0, column=1, padx=2, sticky="ew")

        self.ssl_folder_btn = ctk.CTkButton(
            self.ssl_tools_frame, 
            text="Open Certs Folder 📂", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            fg_color=self.secondary_bg, 
            hover_color=self.secondary_hover, 
            text_color=self.secondary_fg, 
            command=self.open_certs_folder
        )
        self.ssl_folder_btn.grid(row=0, column=2, padx=(2, 0), sticky="ew")
        self.ssl_tools_frame.pack_forget()

    # =========================================================================
    # Widget Helper Methods
    # =========================================================================
    def create_badge(self, parent, text, type="running"):
        """Creates a styled badge frame."""
        if type == "running" or type == "installed" or type == "trusted":
            bg = ["#e6f4ea", "#14321a"]
            fg = ["#137333", "#34a853"]
        elif type == "stopped" or type == "not_installed" or type == "untrusted" or type == "failed":
            bg = ["#fce8e6", "#3c1e1a"]
            fg = ["#c5221f", "#ea4335"]
        else: # Warning / Pending / Idle / Analyzing
            bg = ["#fef7e0", "#3c2e15"]
            fg = ["#b06000", "#fbbc04"]
            
        badge = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, border_width=0)
        label = ctk.CTkLabel(badge, text=text.upper(), text_color=fg, font=ctk.CTkFont(size=10, weight="bold"), height=20)
        label.pack(padx=8, pady=2)
        return badge

    def update_badge(self, badge_frame, text, type="running"):
        """Updates a badge frame color and text dynamically."""
        if type == "running" or type == "installed" or type == "trusted":
            bg = ["#e6f4ea", "#14321a"]
            fg = ["#137333", "#34a853"]
        elif type == "stopped" or type == "not_installed" or type == "untrusted" or type == "failed":
            bg = ["#fce8e6", "#3c1e1a"]
            fg = ["#c5221f", "#ea4335"]
        else: # Warning / Pending / Idle / Analyzing
            bg = ["#fef7e0", "#3c2e15"]
            fg = ["#b06000", "#fbbc04"]
            
        badge_frame.configure(fg_color=bg)
        for child in badge_frame.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text=text.upper(), text_color=fg)

    # =========================================================================
    # Health Diagnostics Task Executors
    # =========================================================================
    def run_diagnostics(self):
        self.health_refresh_btn.configure(state="disabled", text="Testing...")
        self.update_badge(self.apache_badge, "Testing", "warning")
        self.update_badge(self.mysql_badge, "Testing", "warning")
        self.update_badge(self.php_badge, "Testing", "warning")
        
        threading.Thread(target=self._exec_diagnostics_thread, daemon=True).start()

    def _exec_diagnostics_thread(self):
        # 1. Test Apache Web Server
        apache_port = config_manager.get("apache_port")
        apache_port_ok = False
        apache_http_ok = False
        apache_msg = ""
        apache_latency = 0.0

        # Port listening check
        try:
            with socket.create_connection(("127.0.0.1", apache_port), timeout=1) as sock:
                apache_port_ok = True
        except Exception:
            pass

        # HTTP Ping check
        if apache_port_ok:
            try:
                start = time.time()
                url = f"http://127.0.0.1:{apache_port}/"
                proxy_support = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy_support)
                with opener.open(url, timeout=2) as response:
                    apache_latency = (time.time() - start) * 1000
                    apache_http_ok = True
                    apache_msg = f"HTTP Reachable ({apache_latency:.1f}ms, status: {response.status})"
            except urllib.error.HTTPError as e:
                apache_latency = (time.time() - start) * 1000
                apache_http_ok = True
                apache_msg = f"HTTP Reachable ({apache_latency:.1f}ms, status: {e.code})"
            except Exception as e:
                apache_msg = f"HTTP unreachable: {str(e)}"
        else:
            apache_msg = "HTTP unreachable (Apache stopped)"

        # 2. Test MySQL Database
        mysql_port = config_manager.get("mysql_port")
        mysql_ok = False
        mysql_latency = 0.0
        try:
            start = time.time()
            with socket.create_connection(("127.0.0.1", mysql_port), timeout=1.5) as sock:
                mysql_latency = (time.time() - start) * 1000
                mysql_ok = True
        except Exception:
            pass

        # 3. Test PHP CLI Environment
        install_dir = Path(config_manager.get("install_dir"))
        php_exe = install_dir / "php" / "php.exe"
        php_ok = False
        php_version = "php.exe missing from installation directory"
        if php_exe.exists():
            try:
                res = subprocess.run(
                    [str(php_exe), "-v"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if res.returncode == 0:
                    php_ok = True
                    php_version = res.stdout.strip().split("\n")[0]
                else:
                    php_version = f"Execution returned error code: {res.returncode}"
            except Exception as e:
                php_version = f"PHP CLI failed to execute: {str(e)}"

        # 4. Synchronize UI Updates in main thread loop
        self.after(0, lambda: self._sync_diagnostics_ui(
            apache_port_ok, apache_http_ok, apache_msg, apache_port,
            mysql_ok, mysql_latency, mysql_port,
            php_ok, php_version
        ))

    def _sync_diagnostics_ui(self, ap_port_ok, ap_http_ok, ap_msg, ap_port, my_ok, my_lat, my_port, php_ok, php_ver):
        # Update Apache Indicators
        self.update_badge(self.apache_badge, "HEALTHY" if ap_http_ok else "OFFLINE", "running" if ap_http_ok else "stopped")
        self.apache_port_lbl.configure(text=f"Port {ap_port} check: {'LISTENING' if ap_port_ok else 'CLOSED'}", text_color="green" if ap_port_ok else self.text_dim)
        self.apache_ping_lbl.configure(text=ap_msg, text_color="green" if ap_http_ok else self.text_dim)

        # Update MySQL Indicators
        self.update_badge(self.mysql_badge, "HEALTHY" if my_ok else "OFFLINE", "running" if my_ok else "stopped")
        self.mysql_port_lbl.configure(text=f"Port {my_port} check: {'LISTENING' if my_ok else 'CLOSED'}", text_color="green" if my_ok else self.text_dim)
        self.mysql_conn_lbl.configure(text=f"TCP connection latency: {my_lat:.1f}ms" if my_ok else "TCP connection latency: Offline", text_color="green" if my_ok else self.text_dim)

        # Update PHP Indicators
        self.update_badge(self.php_badge, "OK" if php_ok else "FAIL", "running" if php_ok else "failed")
        self.php_cli_lbl.configure(text=php_ver, text_color="green" if php_ok else self.text_dim)

        # Reset button state
        self.health_refresh_btn.configure(state="normal", text="Run Diagnostics")

    # =========================================================================
    # SSL Checker Task Executors
    # =========================================================================
    def run_ssl_check(self):
        url_input = self.ssl_entry.get().strip()
        if not url_input:
            self.logger.log("SSL Checker: Please enter a hostname or URL.", "ERROR")
            return
            
        self.ssl_check_btn.configure(state="disabled", text="Inspecting...")
        self.update_badge(self.ssl_conn_badge, "Analyzing", "warning")
        self.ssl_trust_lbl.configure(text="Trust state: Connecting...")
        
        # Reset card
        self.cert_subject.configure(text="Common Name (CN): -")
        self.cert_issuer.configure(text="Issuer: -")
        self.cert_dates.configure(text="Expiry: -")
        self.cert_proto.configure(text="Protocol / TLS version: -")
        self.ssl_autofix_btn.pack_forget() # Hide auto-fixer during active checking
        self.ssl_tools_frame.pack_forget() # Hide tools during active checking

        threading.Thread(target=self._exec_ssl_check_thread, args=(url_input,), daemon=True).start()

    def _exec_ssl_check_thread(self, input_val):
        # 1. Parse host and port
        url = input_val
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname or "localhost"
            port = parsed.port or 443
        except Exception:
            self.after(0, lambda: self._sync_ssl_failure("Invalid hostname / URL structure", "failed"))
            return

        connected = False
        trusted = False
        ssl_version = "Unknown"
        pem_cert = None
        error_msg = ""

        # 2. Check if port is open first
        try:
            with socket.create_connection((hostname, port), timeout=3) as sock:
                connected = True
        except Exception as e:
            self.after(0, lambda err=str(e): self._sync_ssl_failure(f"Connection refused: {err}", "failed"))
            return

        # 3. Test trust status using built-in system CA verification
        if connected:
            context = ssl.create_default_context()
            try:
                with socket.create_connection((hostname, port), timeout=3) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        trusted = True
                        ssl_version = ssock.version()
            except ssl.SSLCertVerificationError as e:
                trusted = False
                error_msg = f"Untrusted Certificate (Self-signed or Local CA)"
            except Exception as e:
                trusted = False
                error_msg = f"Handshake Error: {str(e)}"

            # 4. Fetch the PEM certificate (ignores trust checking to ensure we can parse)
            try:
                pem_cert = ssl.get_server_certificate((hostname, port), timeout=3)
            except Exception as e:
                if not error_msg:
                    error_msg = f"Failed to retrieve certificate: {str(e)}"

        # 5. Parse certificate fields using Apache bundled OpenSSL
        cert_details = None
        if pem_cert:
            cert_details = self.parse_cert_with_openssl(pem_cert)

        # 6. Synchronize updates back to GUI main thread
        self.after(0, lambda: self._sync_ssl_success(connected, trusted, ssl_version, cert_details, error_msg))

    def _sync_ssl_failure(self, err_msg, badge_state="failed"):
        self.update_badge(self.ssl_conn_badge, "FAILED", badge_state)
        self.ssl_trust_lbl.configure(text=f"Trust state: {err_msg}", text_color="red")
        self.ssl_check_btn.configure(state="normal", text="Verify SSL")
        
        # Check if Apache is installed and certificate is missing to suggest auto-fix
        self._evaluate_autofix_prompt()

    def _sync_ssl_success(self, connected, trusted, version, cert_details, error_msg):
        # Update badge and trust state
        if trusted:
            self.update_badge(self.ssl_conn_badge, "TRUSTED", "trusted")
            self.ssl_trust_lbl.configure(text="Trust state: Trusted CA (Operating System verified)", text_color="green")
        else:
            self.update_badge(self.ssl_conn_badge, "UNTRUSTED", "untrusted")
            self.ssl_trust_lbl.configure(text=f"Trust state: {error_msg if error_msg else 'Local Self-signed Cert'}", text_color="orange")

        # Update Cert details card
        if cert_details:
            expiry_str = cert_details.get("notafter", "-")
            expiry_date = self.parse_openssl_date(expiry_str)
            
            if expiry_date:
                days_left = (expiry_date - datetime.utcnow()).days
                if days_left < 0:
                    days_text = f"EXPIRED ({abs(days_left)} days ago)"
                    self.cert_dates.configure(text=f"Expiry: {expiry_str} ({days_text})", text_color="red")
                else:
                    days_text = f"{days_left} days remaining"
                    self.cert_dates.configure(text=f"Expiry: {expiry_str} ({days_text})", text_color="green" if days_left > 30 else "orange")
            else:
                self.cert_dates.configure(text=f"Expiry: {expiry_str}", text_color=["#000000", "#ffffff"])

            self.cert_subject.configure(text=f"Common Name (CN): {cert_details.get('subject', '-')}")
            self.cert_issuer.configure(text=f"Issuer CA: {cert_details.get('issuer', '-')}")
            self.cert_proto.configure(text=f"TLS Connection Protocol: {version}")
        else:
            self.cert_subject.configure(text="Common Name (CN): Unable to parse (Self-signed or custom host)")
            self.cert_issuer.configure(text="Issuer CA: OpenSSL parser skipped")
            self.cert_proto.configure(text=f"TLS Connection Protocol: {version}")

        self.ssl_check_btn.configure(state="normal", text="Verify SSL")
        
        # Evaluate if we should offer Auto-Fix (e.g. if SSL configuration is disabled/missing on localhost)
        self._evaluate_autofix_prompt()

    def _evaluate_autofix_prompt(self):
        """Displays auto-fix option if Apache is installed but certificates or configurations are missing."""
        apache = ApacheManager()
        if not apache.exe_path.exists():
            self.ssl_autofix_btn.pack_forget()
            self.ssl_tools_frame.pack_forget()
            return
            
        key_file = apache.install_dir / "conf" / "ssl.key" / "server.key"
        crt_file = apache.install_dir / "conf" / "ssl.crt" / "server.crt"
        
        # Prompt auto-fix if files are missing or SSL configuration is not active
        if not key_file.exists() or not crt_file.exists() or not config_manager.get("ssl_enabled"):
            self.ssl_autofix_btn.pack(fill="x", padx=20, pady=(0, 20))
            self.ssl_tools_frame.pack_forget()
        else:
            self.ssl_autofix_btn.pack_forget()
            self.ssl_tools_frame.pack(fill="x", padx=20, pady=(0, 20))

    # =========================================================================
    # SSL Auto-Fix Logic
    # =========================================================================
    def autofix_ssl(self):
        self.ssl_autofix_btn.configure(state="disabled", text="Fixing SSL Configuration...")
        self.logger.log("SSL Auto-Fix: Checking Apache environment...")
        
        def run_fix():
            apache = ApacheManager()
            success, msg = apache.enable_ssl()
            
            if success:
                self.logger.log(f"SSL Auto-Fix Success: {msg}", "INFO")
                # Auto-restart Apache if it's currently running to bind SSL on port 443
                try:
                    if apache.is_running():
                        self.logger.log("SSL Auto-Fix: Restarting Apache to bind HTTPS on port 443...")
                        apache.stop()
                        time.sleep(1.5)
                        apache.start_server()
                        self.logger.log("SSL Auto-Fix: Apache restarted successfully.", "INFO")
                except Exception as e:
                    self.logger.log(f"Warning: Could not auto-restart Apache: {e}", "WARNING")
                
                self.after(0, lambda: self._autofix_complete(True, msg))
            else:
                self.logger.log(f"SSL Auto-Fix Failed: {msg}", "ERROR")
                self.after(0, lambda: self._autofix_complete(False, msg))
                
        threading.Thread(target=run_fix, daemon=True).start()

    def _autofix_complete(self, success, message):
        self.ssl_autofix_btn.configure(state="normal", text="Auto-Fix SSL & Enable HTTPS 🛠")
        if success:
            messagebox.showinfo("SSL Auto-Fixed", "Apache has been configured for SSL and a new self-signed certificate has been generated.\n\nHTTPS is now enabled on port 443!")
            self.ssl_autofix_btn.pack_forget()
            self.run_ssl_check() # Refresh SSL inspect
            self.run_diagnostics() # Refresh health diagnostics
        else:
            messagebox.showerror("SSL Fix Failed", f"Failed to auto-configure SSL:\n\n{message}")

    # =========================================================================
    # Openssl & Date Parsing Core Helpers
    # =========================================================================
    def parse_cert_with_openssl(self, pem_cert):
        install_dir = Path(config_manager.get("install_dir"))
        apache_dir = install_dir / "apache" / "Apache24"
        openssl_exe = apache_dir / "bin" / "openssl.exe"
        
        if not openssl_exe.exists():
            return None
            
        try:
            cmd = [str(openssl_exe), "x509", "-noout", "-subject", "-issuer", "-dates"]
            import os
            run_env = os.environ.copy()
            openssl_cnf = apache_dir / "conf" / "openssl.cnf"
            if openssl_cnf.exists():
                run_env["OPENSSL_CONF"] = str(openssl_cnf)
                
            result = subprocess.run(
                cmd,
                env=run_env,
                input=pem_cert,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                cert_info = {}
                for line in lines:
                    if "=" in line:
                        k, v = line.split("=", 1)
                        cert_info[k.strip().lower()] = v.strip()
                return cert_info
        except Exception:
            pass
        return None

    def parse_openssl_date(self, date_str):
        clean_str = date_str
        if "notAfter=" in date_str:
            clean_str = date_str.replace("notAfter=", "")
        clean_str = clean_str.replace("GMT", "").strip()
        
        try:
            return datetime.strptime(clean_str, "%b %d %H:%M:%S %Y")
        except Exception:
            try:
                return datetime.strptime(clean_str, "%b %d %H:%M:%S %Y %z")
            except Exception:
                pass
        return None

    # =========================================================================
    # SSL Tools Action Methods
    # =========================================================================
    def open_certs_folder(self):
        apache = ApacheManager()
        conf_dir = apache.install_dir / "conf"
        crt_dir = conf_dir / "ssl.crt"
        target_dir = crt_dir if crt_dir.exists() else conf_dir
        
        if target_dir.exists():
            try:
                self.logger.log(f"Opening SSL certificates folder: {target_dir}")
                import os
                os.startfile(str(target_dir))
            except Exception as e:
                self.logger.log(f"Failed to open certificates folder: {e}", "ERROR")
                messagebox.showerror("Error", f"Failed to open certificates folder:\n{e}")
        else:
            self.logger.log("SSL Certificates directory not found.", "ERROR")
            messagebox.showerror("Error", "SSL Certificates directory not found. Please run SSL Auto-Fix first.")

    def edit_ssl_config(self):
        apache = ApacheManager()
        conf_path = apache.install_dir / "conf" / "httpd.conf"
        if conf_path.exists():
            try:
                self.logger.log(f"Opening Apache SSL config: {conf_path}")
                import os
                os.startfile(str(conf_path))
            except Exception as e:
                self.logger.log(f"Failed to open config file: {e}", "ERROR")
                messagebox.showerror("Error", f"Failed to open Apache config file:\n{e}")
        else:
            self.logger.log("Apache httpd.conf not found.", "ERROR")
            messagebox.showerror("Error", "Apache configuration file (httpd.conf) not found.")

    def regenerate_ssl(self):
        if not messagebox.askyesno("Regenerate SSL", "Are you sure you want to regenerate the SSL certificate?\n\nThis will overwrite your existing self-signed certificate and key files."):
            return
            
        self.logger.log("SSL Regenerate: Starting certificate regeneration...")
        
        # Disable buttons during work
        for child in self.ssl_tools_frame.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(state="disabled")
                
        def run_reg():
            apache = ApacheManager()
            # Force regeneration by passing force=True
            success, msg = apache.enable_ssl(force=True)
            
            if success:
                self.logger.log(f"SSL Regeneration Success: {msg}", "INFO")
                # Auto-restart Apache if it's currently running to bind the new SSL cert
                try:
                    if apache.is_running():
                        self.logger.log("SSL Regenerate: Restarting Apache to load the new certificate...")
                        apache.stop()
                        time.sleep(1.5)
                        apache.start_server()
                        self.logger.log("SSL Regenerate: Apache restarted successfully.", "INFO")
                except Exception as e:
                    self.logger.log(f"Warning: Could not auto-restart Apache: {e}", "WARNING")
                
                self.after(0, lambda: self._regenerate_complete(True, msg))
            else:
                self.logger.log(f"SSL Regeneration Failed: {msg}", "ERROR")
                self.after(0, lambda: self._regenerate_complete(False, msg))
                
        threading.Thread(target=run_reg, daemon=True).start()

    def _regenerate_complete(self, success, message):
        for child in self.ssl_tools_frame.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(state="normal")
                
        if success:
            messagebox.showinfo("SSL Regenerated", "A new self-signed certificate and private key have been successfully generated and Apache has been reconfigured.")
            self.run_ssl_check() # Refresh SSL inspect
            self.run_diagnostics() # Refresh health diagnostics
        else:
            messagebox.showerror("SSL Regeneration Failed", f"Failed to regenerate SSL:\n\n{message}")
