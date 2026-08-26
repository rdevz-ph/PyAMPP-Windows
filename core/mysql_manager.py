import os
import subprocess
from pathlib import Path
from core.server_manager import ServerManager
from core.config import config_manager

class MySQLManager(ServerManager):
    def __init__(self):
        self.update_paths()
        super().__init__("MySQL", self.exe_path, config_manager.get("mysql_port"))

    def update_paths(self):
        # MySQL zip typically has a folder like mysql-8.0.40-winx64
        # We'll need to find the bin folder after extraction.
        self.base_dir = Path(config_manager.get("install_dir")) / "mysql"
        self.mysql_dir = self.find_mysql_dir()
        self.exe_path = self.mysql_dir / "bin" / "mysqld.exe" if self.mysql_dir else None
        self.port = config_manager.get("mysql_port")

    def find_mysql_dir(self):
        if not self.base_dir.exists():
            return None
        # Check current dir
        if (self.base_dir / "bin" / "mysqld.exe").exists():
            return self.base_dir
        
        # Check one level deep
        candidates = []
        try:
            for item in self.base_dir.iterdir():
                if item.is_dir() and (item / "bin" / "mysqld.exe").exists():
                    candidates.append(item)
        except:
            pass
            
        if candidates:
            # Sort candidates by modification time descending so we get the most recently installed/extracted version
            candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return candidates[0]
            
        return None

    def configure(self):
        """Creates my.ini with correct paths and port."""
        if not self.mysql_dir:
            self.mysql_dir = self.find_mysql_dir()
            if not self.mysql_dir:
                return False, "MySQL directory not found."
            self.exe_path = self.mysql_dir / "bin" / "mysqld.exe"

        ini_path = self.mysql_dir / "my.ini"
        data_dir = Path(config_manager.get("mysql_data_dir"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        port = config_manager.get("mysql_port")
        
        # Paths in my.ini must use forward slashes
        basedir_str = str(self.mysql_dir).replace("\\", "/")
        datadir_str = str(data_dir).replace("\\", "/")

        content = f"""[mysqld]
port={port}
basedir="{basedir_str}"
datadir="{datadir_str}"
character-set-server=utf8mb4

[mysql]
port={port}
default-character-set=utf8mb4

[client]
port={port}
"""
        try:
            with open(ini_path, "w") as f:
                f.write(content)
            
            self.port = port
            
            # Sync phpMyAdmin port if installed
            self.sync_pma_port(port)

            # Initialize data directory if empty
            if not any(data_dir.iterdir()):
                init_cmd = [
                    str(self.exe_path),
                    f"--defaults-file={str(ini_path)}",
                    "--initialize-insecure",
                    "--console"
                ]
                subprocess.run(init_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            return True, "MySQL configured."
        except Exception as e:
            return False, f"Failed to configure MySQL: {e}"

    def sync_pma_port(self, port):
        """Updates phpMyAdmin's config.inc.php with the current MySQL port."""
        pma_config = Path(config_manager.get("install_dir")) / "apache" / "Apache24" / "htdocs" / "phpmyadmin" / "config.inc.php"
        if pma_config.exists():
            try:
                with open(pma_config, "r") as f:
                    lines = f.readlines()
                
                new_lines = []
                port_found = False
                for line in lines:
                    if "$cfg['Servers'][$i]['port'] =" in line:
                        new_lines.append(f"$cfg['Servers'][$i]['port'] = '{port}';\n")
                        port_found = True
                    else:
                        new_lines.append(line)
                
                if not port_found:
                    # Insert port after host or after the first Servers line
                    for i, line in enumerate(new_lines):
                        if "$cfg['Servers'][$i]['host'] =" in line:
                            new_lines.insert(i + 1, f"$cfg['Servers'][$i]['port'] = '{port}';\n")
                            port_found = True
                            break
                
                if port_found:
                    with open(pma_config, "w") as f:
                        f.writelines(new_lines)
            except Exception as e:
                print(f"Failed to sync phpMyAdmin port: {e}")


    def start_server(self):
        if not self.exe_path or not self.exe_path.exists():
            self.mysql_dir = self.find_mysql_dir()
            if not self.mysql_dir:
                return False, "MySQL binaries missing. Please download first."
            self.exe_path = self.mysql_dir / "bin" / "mysqld.exe"
        
        success, msg = self.configure()
        if not success:
            return False, msg

        ini_path = self.mysql_dir / "my.ini"
        cmd = [str(self.exe_path), f"--defaults-file={str(ini_path)}"]
        return self.start(cmd, cwd=str(self.mysql_dir))
