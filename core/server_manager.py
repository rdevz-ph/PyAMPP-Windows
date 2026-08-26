import psutil
import subprocess
import os
import signal
import sys
import time
from pathlib import Path

class ServerManager:
    def __init__(self, name, bin_path, port):
        self.name = name
        self.bin_path = Path(bin_path) if bin_path else None
        self.port = port
        self.process = None
        self._prev_cpu_data = {}

    def is_port_in_use(self):
        """Checks if the port is already in use and listening."""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return False

    def get_process_by_port(self):
        """Finds processes using the specified port with LISTEN status."""
        processes = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                    try:
                        processes.append(psutil.Process(conn.pid))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return processes[0] if processes else None

    def is_running(self):
        """Checks if the server process is currently running."""
        if self.process and self.process.poll() is None:
            return True
        return self.is_port_in_use()

    def start(self, cmd, cwd=None, env=None):
        """Starts the server process and verifies it stays running."""
        if self.is_running():
            return False, f"{self.name} is already running."
        
        # Check for port conflict (only LISTENING)
        if self.is_port_in_use():
            return False, f"Port {self.port} is already in use by another application."

        # Use a clean copy of the environment
        run_env = (env or os.environ).copy()
        
        # When running as a frozen EXE, PyInstaller sets some environment variables
        # that can occasionally cause issues with child processes. We strip them 
        # to ensure the child process runs in a more standard environment.
        for key in ["_MEIPASS2", "PYI_CHILD_PATH", "PYI_PARENT_ADDR"]:
            run_env.pop(key, None)

        try:
            # Use CREATE_NEW_PROCESS_GROUP (0x00000200) on Windows
            # This provides process isolation without opening a visible console window.
            creation_flags = subprocess.CREATE_NO_WINDOW
            if os.name == 'nt':
                creation_flags |= 0x00000200 # CREATE_NEW_PROCESS_GROUP
                
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=run_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags
            )
            
            import time
            time.sleep(1.5)
            
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                error_msg = stderr.strip() or stdout.strip() or "Process exited immediately."
                self.process = None
                return False, f"Failed to start {self.name}: {error_msg}"
            
            return True, f"{self.name} started."
        except Exception as e:
            return False, f"Failed to start {self.name}: {e}"

    def stop(self):
        """Stops the server process aggressively."""
        # 1. Try stopping by PID if we have it
        if self.process:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], 
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
            self.process = None

        # 2. Try stopping by Port
        p = self.get_process_by_port()
        if p:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], 
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

        # 3. Last resort: Kill by image name if it's our own binary
        img_name = "httpd.exe" if self.name == "Apache" else "mysqld.exe"
        try:
            subprocess.run(["taskkill", "/F", "/IM", img_name], 
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

        import time
        time.sleep(1) # Give OS time to release port
        
        if not self.is_port_in_use():
            return True, f"{self.name} stopped."
        return False, f"Failed to stop {self.name} completely."

    def get_stats(self):
        """Returns dict of stats: {'pid': pid, 'cpu': cpu%, 'ram': ram_mb} or None if not running."""
        try:
            p = None
            if self.process:
                try:
                    p = psutil.Process(self.process.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if not p:
                p = self.get_process_by_port()
            
            if p and p.is_running():
                cpu_percent = 0.0
                memory_bytes = 0
                try:
                    processes = [p] + p.children(recursive=True)
                except Exception:
                    processes = [p]
                
                current_pids = set()
                current_time = time.time()
                num_cores = os.cpu_count() or 1

                for proc in processes:
                    try:
                        pid = proc.pid
                        current_pids.add(pid)

                        # Memory usage
                        memory_bytes += proc.memory_info().rss

                        # CPU usage calculation matching C# logic
                        cpu_times = proc.cpu_times()
                        cpu_time = cpu_times.user + cpu_times.system

                        if pid in self._prev_cpu_data:
                            prev_time, prev_cpu_time = self._prev_cpu_data[pid]
                            time_delta = current_time - prev_time
                            cpu_delta = cpu_time - prev_cpu_time

                            if time_delta > 0 and cpu_delta >= 0:
                                percent = (cpu_delta / (time_delta * num_cores)) * 100
                                if percent > 0:
                                    cpu_percent += percent
                        
                        self._prev_cpu_data[pid] = (current_time, cpu_time)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Clean up dead PIDs from cache
                dead_pids = [pid for pid in self._prev_cpu_data if pid not in current_pids]
                for pid in dead_pids:
                    self._prev_cpu_data.pop(pid, None)

                return {
                    'pid': p.pid,
                    'cpu': round(cpu_percent, 1),
                    'ram': round(memory_bytes / (1024 * 1024), 1)  # in MB
                }
            else:
                self._prev_cpu_data.clear()
        except Exception:
            pass
        return None

