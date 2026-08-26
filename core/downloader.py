import requests
import zipfile
import os
import shutil
import secrets
from pathlib import Path

# Use minimal headers as they worked initially for MySQL
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def validate_url(url):
    """Simplified validation that was working for MySQL initially."""
    try:
        # Some servers (like MySQL) block HEAD requests with 403.
        # We use GET with stream=True to only fetch headers first.
        response = requests.get(url, timeout=10, headers=HEADERS, allow_redirects=True, stream=True)
        return response.status_code < 400
    except Exception:
        # If it fails, we still return True to let the actual download try,
        # as that is more robust than the validation check.
        return True

def download_file(url, dest_path, progress_callback=None):
    """Downloads a file with a progress callback."""
    try:
        # Verify=True ensures the connection is secure.
        response = requests.get(url, stream=True, timeout=30, headers=HEADERS)
        response.raise_for_status()
        try:
            total_size = int(response.headers.get('content-length', 0))
        except:
            total_size = 0
            
        downloaded_size = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if progress_callback:
                        if total_size > 0:
                            progress = downloaded_size / total_size
                            progress_callback(progress)
                        else:
                            # If size is unknown, send a negative value or counter to signal activity
                            # We'll use a simple oscillating value for the UI to show movement
                            progress_callback(-1) 
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def robust_rmtree(path):
    """Removes a directory tree robustly, handling read-only files on Windows."""
    import os
    import stat
    import shutil

    def remove_readonly(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if Path(path).exists():
        try:
            shutil.rmtree(path, onerror=remove_readonly)
            return True
        except Exception as e:
            print(f"Error removing {path}: {e}")
            return False
    return True

def surgical_cleanup(directory, keep_paths, logger=None):
    """
    Surgically cleans a directory by removing all items EXCEPT those in keep_paths.
    Handles nested keep paths.
    """
    directory = Path(directory)
    if not directory.exists():
        return

    # Convert keep_paths to set of resolved Path objects
    resolved_keeps = {Path(p).resolve() for p in keep_paths}
    
    for item in directory.iterdir():
        try:
            item_abs = item.resolve()
            should_keep = False
            is_parent_of_keep = False
            
            for keep_path in resolved_keeps:
                if item_abs == keep_path:
                    should_keep = True
                    break
                if keep_path.is_relative_to(item_abs):
                    is_parent_of_keep = True
                    break
            
            if should_keep:
                continue
            elif is_parent_of_keep:
                # Recursively clean the child directory if it's a directory
                if item.is_dir():
                    surgical_cleanup(item, keep_paths, logger)
                else:
                    # Should not happen as a file cannot be a parent of another path
                    item.unlink()
            else:
                # Not a keep path and not a parent of one, safe to delete
                robust_rmtree(item) if item.is_dir() else item.unlink()
        except Exception as e:
            if logger:
                msg = f"Could not remove {item}: {e}"
                if hasattr(logger, "log"):
                    logger.log(msg, "WARNING")
                else:
                    print(msg)
            else:
                print(f"Could not remove {item}: {e}")

def extract_zip(zip_path, extract_to):
    """Extracts a zip file to the specified directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print(f"Extraction error: {e}")
        return False

def configure_php(extract_to, logger=None):
    """Configures php.ini with basic extensions."""
    ini_dev = Path(extract_to) / "php.ini-development"
    ini_target = Path(extract_to) / "php.ini"
    if ini_dev.exists():
        shutil.copy(ini_dev, ini_target)
        with open(ini_target, "r") as f:
            lines = f.readlines()
        
        new_ini_lines = []
        ext_dir = str(Path(extract_to) / "ext").replace("\\", "/")
        for line in lines:
            clean_line = line.strip()
            if clean_line in [";extension_dir = \"ext\"", "; extension_dir = \"ext\""]:
                new_ini_lines.append(f"extension_dir = \"{ext_dir}\"\n")
            elif any(clean_line == f";extension={ext}" or clean_line == f"; extension={ext}" for ext in ["mysqli", "mbstring", "openssl", "curl", "pdo_mysql", "zip", "gd", "fileinfo", "intl", "exif", "sqlite3", "pdo_sqlite", "bcmath"]):
                new_ini_lines.append(line.lstrip("; ").lstrip(";"))
            else:
                new_ini_lines.append(line)
        
        with open(ini_target, "w") as f:
            f.writelines(new_ini_lines)
        if logger:
            logger.log("Configured php.ini.")
        return True
    return False

def configure_pma(extract_to, install_dir, logger=None):
    """Configures phpMyAdmin in Apache's htdocs."""
    apache_dir = Path(install_dir) / "apache" / "Apache24"
    htdocs_pma = apache_dir / "htdocs" / "phpmyadmin"
    htdocs_pma.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        extracted_folder = next(Path(extract_to).iterdir())
        if htdocs_pma.exists():
            shutil.rmtree(htdocs_pma)
        shutil.move(str(extracted_folder), str(htdocs_pma))
        shutil.rmtree(extract_to)
        
        sample_config = htdocs_pma / "config.sample.inc.php"
        real_config = htdocs_pma / "config.inc.php"
        if sample_config.exists():
            secret = secrets.token_hex(16)
            with open(sample_config, "r") as f:
                content = f.read()
            content = content.replace("$cfg['blowfish_secret'] = '';", f"$cfg['blowfish_secret'] = '{secret}';")
            content = content.replace("$cfg['Servers'][$i]['AllowNoPassword'] = false;", "$cfg['Servers'][$i]['AllowNoPassword'] = true;")
            with open(real_config, "w") as f:
                f.write(content)
            if logger:
                logger.log("Configured phpMyAdmin.")
        return True
    except Exception as e:
        if logger:
            logger.log(f"Failed to configure phpMyAdmin: {e}", "ERROR")
        return False
