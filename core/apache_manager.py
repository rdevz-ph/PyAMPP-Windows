import os
import subprocess
import sys
from pathlib import Path
from core.server_manager import ServerManager
from core.config import config_manager

class ApacheManager(ServerManager):
    def __init__(self):
        self.update_paths()
        super().__init__("Apache", self.exe_path, config_manager.get("apache_port"))

    def update_paths(self):
        self.install_dir = Path(config_manager.get("install_dir")) / "apache" / "Apache24"
        self.exe_path = self.install_dir / "bin" / "httpd.exe"
        self.port = config_manager.get("apache_port")

    def get_subnet(self):
        """Detects the local IPv4 subnet."""
        import socket
        try:
            # Create a dummy connection to a public IP to find the local interface IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            
            if ip.startswith("127."):
                return None
                
            parts = ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        except Exception:
            return None

    def configure(self):
        """Updates httpd.conf with the correct paths and port."""
        conf_path = self.install_dir / "conf" / "httpd.conf"
        if not conf_path.exists():
            return False, "httpd.conf not found."

        try:
            with open(conf_path, "r") as f:
                lines = f.readlines()

            new_lines = []
            # Ensure the path is absolute and uses forward slashes
            server_root = str(self.install_dir.absolute()).replace("\\", "/")
            port = config_manager.get("apache_port")
            
            # PHP Integration
            php_dir = Path(config_manager.get("install_dir")) / "php"
            php_module_path = None
            if php_dir.exists():
                # Search for any apache module dll
                for item in php_dir.iterdir():
                    if item.name.startswith("php") and item.name.endswith(".dll") and "apache" in item.name:
                        php_module_path = str(item.absolute()).replace("\\", "/")
                        break
                
                # If not found by pattern, try common names
                if not php_module_path:
                    for common_name in ["php8apache2_4.dll", "php7apache2_4.dll"]:
                        possible = php_dir / common_name
                        if possible.exists():
                            php_module_path = str(possible.absolute()).replace("\\", "/")
                            break

            # Filter out all PHP, stability, and phpMyAdmin related lines to prevent duplication
            # We use lowercase comparisons for more robust matching
            skip_keywords = [
                "loadmodule php", 
                "addhandler application/x-httpd-php", 
                "phpinidir", 
                "# php support", 
                "# windows performance fixes", 
                "acceptfilter", 
                "enablesendfile", 
                "enablemmap", 
                "phpmyadmin access control",
                "# ssl support",
                "loadmodule ssl_module",
                "loadmodule socache_shmcb_module",
                "listen 443",
                "<virtualhost _default_:443>"
            ]   

            # Temporary storage to catch block start/end for phpmyadmin and ssl virtualhost
            in_pma_block = False
            in_ssl_block = False

            for line in lines:
                lower_line = line.lower()

                # Check for the start of a phpmyadmin directory block
                if "<directory" in lower_line and "phpmyadmin" in lower_line:
                    in_pma_block = True
                    continue

                if in_pma_block:
                    if "</directory>" in lower_line:
                        in_pma_block = False
                    continue

                # Check for the start of an SSL virtualhost block
                if "<virtualhost" in lower_line and "443" in lower_line:
                    in_ssl_block = True
                    continue

                if in_ssl_block:
                    if "</virtualhost>" in lower_line:
                        in_ssl_block = False
                    continue

                if any(kw in lower_line for kw in skip_keywords):
                    continue                
                if line.startswith("Define SRVROOT"):
                    new_lines.append(f'Define SRVROOT "{server_root}"\n')
                elif line.startswith('ServerRoot "'):
                    new_lines.append(f'ServerRoot "{server_root}"\n')
                elif line.startswith('DocumentRoot "'):
                    new_lines.append(f'DocumentRoot "{server_root}/htdocs"\n')
                elif line.startswith('<Directory "'):
                    if "Apache24-64" in line or "htdocs" in line:
                        new_lines.append(f'<Directory "{server_root}/htdocs">\n')
                    else:
                        new_lines.append(line)
                elif line.startswith("Listen "):
                    new_lines.append(f"Listen {port}\n")
                elif line.strip().startswith("ServerName ") or line.strip().startswith("#ServerName "):
                    new_lines.append(f"ServerName localhost:{port}\n")
                else:
                    new_lines.append(line)

            # Trim trailing empty lines to prevent massive gaps from previous duplications
            while new_lines and not new_lines[-1].strip():
                new_lines.pop()

            # Append Performance/Stability fixes for Windows
            new_lines.append("\n# Windows Performance Fixes\n")
            new_lines.append("AcceptFilter http none\n")
            new_lines.append("AcceptFilter https none\n")
            new_lines.append("EnableSendfile off\n")
            new_lines.append("EnableMMAP off\n")

            # Append PHP config at the end if found
            if php_module_path:
                # Detect correct module name based on the DLL filename
                # PHP 7 uses php7_module, PHP 8+ uses php_module
                module_name = "php_module"
                if "php7" in php_module_path.lower():
                    module_name = "php7_module"
                
                php_dir_str = str(php_dir.absolute()).replace("\\", "/")
                new_lines.append(f'\n# PHP Support\n')
                new_lines.append(f'LoadModule {module_name} "{php_module_path}"\n')
                new_lines.append(f'AddHandler application/x-httpd-php .php\n')
                new_lines.append(f'PHPIniDir "{php_dir_str}"\n')
                
                # Update DirectoryIndex to include index.php
                for i, line in enumerate(new_lines):
                    if line.strip().startswith("DirectoryIndex "):
                        if "index.php" not in line:
                            new_lines[i] = line.replace("DirectoryIndex ", "DirectoryIndex index.php ")

            # Add phpMyAdmin LAN access configuration
            new_lines.append(f'\n# phpMyAdmin Access Control\n')
            new_lines.append(f'<Directory "{server_root}/htdocs/phpmyadmin">\n')
            new_lines.append(f'    Options Indexes FollowSymLinks MultiViews\n')
            new_lines.append(f'    AllowOverride all\n')
            new_lines.append(f'    <RequireAny>\n')
            new_lines.append(f'        Require local\n')
            
            if config_manager.get("lan_access"):
                subnet = self.get_subnet()
                if subnet:
                    new_lines.append(f'        Require ip {subnet}\n')
                else:
                    # Fallback to allow all if subnet detection fails but LAN access is requested
                    new_lines.append(f'        Require all granted\n')
            
            new_lines.append(f'    </RequireAny>\n')
            new_lines.append(f'</Directory>\n')

            # Add SSL Support if enabled
            if config_manager.get("ssl_enabled"):
                new_lines.append(f'\n# SSL Support\n')
                new_lines.append(f'LoadModule ssl_module modules/mod_ssl.so\n')
                new_lines.append(f'LoadModule socache_shmcb_module modules/mod_socache_shmcb.so\n')
                new_lines.append(f'Listen 443\n')
                new_lines.append(f'<VirtualHost _default_:443>\n')
                new_lines.append(f'    DocumentRoot "{server_root}/htdocs"\n')
                new_lines.append(f'    ServerName localhost:443\n')
                new_lines.append(f'    SSLEngine on\n')
                new_lines.append(f'    SSLCertificateFile "{server_root}/conf/ssl.crt/server.crt"\n')
                new_lines.append(f'    SSLCertificateKeyFile "{server_root}/conf/ssl.key/server.key"\n')
                new_lines.append(f'</VirtualHost>\n')

            with open(conf_path, "w") as f:
                f.writelines(new_lines)
            
            self.port = port
            return True, "Apache configured."
        except Exception as e:
            return False, f"Failed to configure Apache: {e}"

    def start_server(self):
        if not self.exe_path.exists():
            return False, "Apache binaries missing. Please download first."
        
        # When running as a built EXE, PyInstaller's VCRUNTIME140.dll (v14.29) 
        # often conflicts with PHP 8.4's requirement (v14.44+).
        # We fix this by copying the system's modern DLLs to the Apache/PHP folders.
        if getattr(sys, "frozen", False):
            try:
                import shutil
                system32 = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"
                runtimes = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]
                
                targets = [
                    self.install_dir / "bin",
                    Path(config_manager.get("install_dir")) / "php"
                ]
                
                for target in targets:
                    if target.exists():
                        for dll in runtimes:
                            src = system32 / dll
                            dst = target / dll
                            if src.exists() and not dst.exists():
                                shutil.copy2(src, dst)
            except Exception as e:
                print(f"Note: Could not copy system runtimes: {e}")

        success, msg = self.configure()
        if not success:
            return False, msg

        # Run config test first to catch errors early
        try:
            test_cmd = [str(self.exe_path), "-t"]
            result = subprocess.run(
                test_cmd, 
                cwd=str(self.install_dir), 
                capture_output=True, 
                text=True, 
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode != 0:
                # Get the last few lines of the error message as it's usually the most relevant
                error_lines = result.stderr.strip().split("\n")
                relevant_error = error_lines[-1] if error_lines else "Unknown syntax error"
                return False, f"Apache configuration error: {relevant_error}"
        except Exception as e:
            # If we can't even run the test, it's likely a missing Redistributable
            return False, f"Failed to run Apache check (Missing VC++ Redistributable?): {e}"

        cmd = [str(self.exe_path)]
        return self.start(cmd, cwd=str(self.install_dir))

    def enable_ssl(self, force=False):
        """Generates self-signed SSL certificate and configures httpd.conf for SSL."""
        if not self.exe_path.exists():
            return False, "Apache binaries missing. Please install Apache first."

        openssl_exe = self.install_dir / "bin" / "openssl.exe"
        if not openssl_exe.exists():
            return False, "openssl.exe missing from Apache installation."

        key_dir = self.install_dir / "conf" / "ssl.key"
        crt_dir = self.install_dir / "conf" / "ssl.crt"
        key_dir.mkdir(parents=True, exist_ok=True)
        crt_dir.mkdir(parents=True, exist_ok=True)

        key_file = key_dir / "server.key"
        crt_file = crt_dir / "server.crt"

        if force:
            if key_file.exists():
                try:
                    key_file.unlink()
                except Exception:
                    pass
            if crt_file.exists():
                try:
                    crt_file.unlink()
                except Exception:
                    pass

        # 1. Generate SSL certificate and key if they don't exist
        if not key_file.exists() or not crt_file.exists():
            cmd = [
                str(openssl_exe), "req", "-x509", "-nodes", "-days", "1095", "-newkey", "rsa:2048",
                "-keyout", str(key_file), "-out", str(crt_file),
                "-subj", "/CN=localhost"
            ]
            import subprocess
            import os
            
            # Set OPENSSL_CONF env var to point to the portable openssl.cnf location
            run_env = os.environ.copy()
            openssl_cnf = self.install_dir / "conf" / "openssl.cnf"
            if openssl_cnf.exists():
                run_env["OPENSSL_CONF"] = str(openssl_cnf)
                
            try:
                res = subprocess.run(
                    cmd, 
                    env=run_env,
                    capture_output=True, 
                    text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if res.returncode != 0:
                    return False, f"OpenSSL certificate generation failed: {res.stderr}"
            except Exception as e:
                return False, f"Failed to run OpenSSL: {e}"

        # 2. Update config to enable SSL
        config_manager.set("ssl_enabled", True)
        success, msg = self.configure() # Reconfigure httpd.conf with SSL enabled!
        if not success:
            return False, msg
            
        return True, "SSL successfully configured and self-signed certificate generated."
