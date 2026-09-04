import json
import os
import sys
from pathlib import Path


def get_base_dir():
    """Returns the base directory of the application."""
    if getattr(sys, "frozen", False):
        # Running as a built .exe
        return Path(sys.executable).parent
    else:
        # Running as a script
        return Path(__file__).parent.parent


def get_appdata_dir():
    """Returns the AppData directory for the application."""
    appdata = os.getenv("APPDATA")
    if appdata:
        path = Path(appdata) / "PyAMPP"
    else:
        # Fallback to home directory if APPDATA is not set
        path = Path.home() / ".pyampp"
    
    path.mkdir(parents=True, exist_ok=True)
    return path


BASE_DIR = get_base_dir()
APPDATA_DIR = get_appdata_dir()
DATA_DIR = BASE_DIR / "data"
VERSION = "v1.1.1"

# Internal resource directory (where .ps1 and other bundled files live)
if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)
else:
    RESOURCE_DIR = Path(__file__).parent.parent

DEFAULT_CONFIG = {
    "apache_port": 80,
    "mysql_port": 3306,
    "apache_url": "https://www.apachelounge.com/download/VS17/binaries/httpd-2.4.66-251206-Win64-VS17.zip",
    "mysql_url": "https://downloads.mysql.com/archives/get/p/23/file/mysql-8.4.4-winx64.zip",
    "php_url": "https://windows.php.net/downloads/releases/php-8.5.6-Win32-vs17-x64.zip",
    "phpmyadmin_url": "https://files.phpmyadmin.net/phpMyAdmin/5.2.3/phpMyAdmin-5.2.3-all-languages.zip",
    "install_dir": "C:\\PyAMPP\\bin",
    "mysql_data_dir": "C:\\PyAMPP\\mysql_data",
    "htdocs_dir": "C:\\PyAMPP\\htdocs",
    "presets_url": "https://raw.githubusercontent.com/rdevz-ph/PyAMPP-Windows/main/presets.json",
    "lan_access": False,
    "wizard_completed": False,
}

COMPONENTS_PRESETS = {
    "PHP": {
        "8.5.6": "https://windows.php.net/downloads/releases/php-8.5.6-Win32-vs17-x64.zip",
        "8.4.21": "https://windows.php.net/downloads/releases/php-8.4.21-Win32-vs17-x64.zip",
        "8.3.31": "https://windows.php.net/downloads/releases/php-8.3.31-Win32-vs16-x64.zip",
        "8.2.31": "https://windows.php.net/downloads/releases/php-8.2.31-Win32-vs16-x64.zip",
        "8.1.34": "https://windows.php.net/downloads/releases/php-8.1.34-Win32-vs16-x64.zip",
        "8.0.30 (Archive)": "https://windows.php.net/downloads/releases/archives/php-8.0.30-Win32-vs16-x64.zip",
        "7.4.33 (Archive)": "https://windows.php.net/downloads/releases/archives/php-7.4.33-Win32-vc15-x64.zip",
    },
    "Apache": {
        "2.4.66": "https://www.apachelounge.com/download/VS17/binaries/httpd-2.4.66-251206-Win64-VS17.zip",
    },
    "MySQL": {
        "8.4.4": "https://downloads.mysql.com/archives/get/p/23/file/mysql-8.4.4-winx64.zip",
        "8.0.40": "https://downloads.mysql.com/archives/get/p/23/file/mysql-8.0.40-winx64.zip",
        "5.7.44": "https://downloads.mysql.com/archives/get/p/23/file/mysql-5.7.44-winx64.zip",
    },
    "phpMyAdmin": {
        "5.2.3": "https://files.phpmyadmin.net/phpMyAdmin/5.2.3/phpMyAdmin-5.2.3-all-languages.zip",
        "5.2.2": "https://files.phpmyadmin.net/phpMyAdmin/5.2.2/phpMyAdmin-5.2.2-all-languages.zip",
        "5.2.1": "https://files.phpmyadmin.net/phpMyAdmin/5.2.1/phpMyAdmin-5.2.1-all-languages.zip",
    },
}


def update_presets(new_presets):
    """Updates the global COMPONENTS_PRESETS with new data, ensuring proper arrangement."""
    global COMPONENTS_PRESETS
    
    # 1. Clean the new presets to remove special metadata keys (like latest_release)
    cleaned_presets = {}
    for category, versions in new_presets.items():
        if category == "latest_release":
            continue
        cleaned_presets[category] = versions
            
    # 2. Ensure category order: PHP, Apache, MySQL, phpMyAdmin, then others
    standard_order = ["PHP", "Apache", "MySQL", "phpMyAdmin"]
    ordered_presets = {}
    
    # First, add standard categories in order if they exist
    for cat in standard_order:
        if cat in cleaned_presets:
            ordered_presets[cat] = cleaned_presets[cat]
            
    # Then add any other categories
    for cat in cleaned_presets:
        if cat not in ordered_presets:
            ordered_presets[cat] = cleaned_presets[cat]
            
    # Update the global dictionary in-place to preserve references across modules
    COMPONENTS_PRESETS.clear()
    COMPONENTS_PRESETS.update(ordered_presets)



class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def get_config_path(self):
        # Always use AppData for the primary configuration
        return APPDATA_DIR / "config.json"

    def load(self):
        config_path = self.get_config_path()
        saved_config = {}
        
        # 1. Load from AppData first
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except Exception as e:
                print(f"Error loading config from AppData: {e}")
        else:
            # 2. Migration: Check for legacy config in BASE_DIR or install_dir
            legacy_paths = [
                BASE_DIR / "config.json",
                Path(self.config["install_dir"]) / "config.json"
            ]
            for path in legacy_paths:
                if path.exists():
                    try:
                        with open(path, "r") as f:
                            saved_config = json.load(f)
                            self.config.update(saved_config)
                        self.save() # Migrate to AppData immediately
                        break
                    except:
                        continue

        # Force update broken Apache URL if detected
        if "httpd-2.4.62-win64-VS17.zip" in self.config.get("apache_url", ""):
            self.config["apache_url"] = DEFAULT_CONFIG["apache_url"]

        # Backward compatibility for htdocs_dir:
        # If legacy htdocs exists on disk, preserve it so users aren't forced to migrate files
        legacy_htdocs = Path(self.config["install_dir"]) / "apache" / "Apache24" / "htdocs"
        if legacy_htdocs.exists():
            # If not explicitly configured or the configured path doesn't exist, preserve legacy
            if "htdocs_dir" not in saved_config or not saved_config.get("htdocs_dir") or not Path(saved_config.get("htdocs_dir", "")).exists():
                self.config["htdocs_dir"] = os.path.normpath(str(legacy_htdocs))
            else:
                self.config["htdocs_dir"] = os.path.normpath(str(self.config["htdocs_dir"]))
        else:
            if "htdocs_dir" not in saved_config or not saved_config.get("htdocs_dir"):
                self.config["htdocs_dir"] = os.path.normpath(str(Path(self.config["install_dir"]).parent / "htdocs"))
            else:
                self.config["htdocs_dir"] = os.path.normpath(str(self.config["htdocs_dir"]))

        # Load presets after main config to use correct install_dir
        updated_presets_path = Path(self.config["install_dir"]).parent / "updated_config.json"
        if updated_presets_path.exists():
            try:
                with open(updated_presets_path, "r") as f:
                    new_presets = json.load(f)
                    update_presets(new_presets)
            except Exception as e:
                print(f"Error loading local presets: {e}")

        # Validation: If path changes or binaries are missing, reset wizard
        self.validate_binaries()

    def validate_binaries(self):
        """Checks if configured binaries exist. If not, resets wizard status."""
        if not self.config.get("wizard_completed"):
            return

        install_dir = Path(self.config["install_dir"])
        apache_exe = install_dir / "apache" / "Apache24" / "bin" / "httpd.exe"
        mysql_exe = install_dir / "mysql" / "bin" / "mysqld.exe"
        php_exe = install_dir / "php" / "php.exe"

        # If the directory doesn't exist or main binaries are missing, force re-setup
        if not install_dir.exists() or not (apache_exe.exists() or mysql_exe.exists() or php_exe.exists()):
            print("Configured binaries missing. Resetting wizard...")
            self.config["wizard_completed"] = False
            # We don't call save() here to avoid overwriting the user's path immediately, 
            # but the runtime state will trigger the wizard.


    def save(self):
        # 1. Always save to AppData
        config_path = self.get_config_path()
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config to AppData: {e}")

        # 2. Also save to the current install_dir for portability/backup
        install_config_path = Path(self.config["install_dir"]) / "config.json"
        if install_config_path.resolve() != config_path.resolve():
            install_config_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(install_config_path, "w") as f:
                    json.dump(self.config, f, indent=4)
            except Exception as e:
                print(f"Error saving backup config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()


def restart_app():
    """Restarts the current application cleanly."""
    import subprocess
    import sys
    import os

    # Clean the environment of PyInstaller variables
    # This is critical! If we don't clear these, the new process will try to
    # use the old temp folder (_MEIPASS) which is about to be deleted.
    env = os.environ.copy()
    for key in ["_MEIPASS2", "PYI_CHILD_PATH", "PYI_PARENT_ADDR"]:
        env.pop(key, None)

    if getattr(sys, "frozen", False):
        # Running as a built .exe
        try:
            # On Windows, using Popen with a detached flag is more reliable than startfile
            # for ensuring the old process can exit and clean up its temp folder.
            subprocess.Popen(
                [sys.executable],
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE
                | subprocess.DETACHED_PROCESS,
            )
            os._exit(0)
        except Exception as e:
            print(f"Restart failed: {e}")
    else:
        # Running as a script
        executable = sys.executable
        args = sys.argv
        try:
            subprocess.Popen(
                [executable] + args,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            os._exit(0)
        except Exception as e:
            print(f"Restart failed: {e}")

    os._exit(0)


config_manager = ConfigManager()
