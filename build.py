import os
import subprocess
import shutil
import customtkinter
from pathlib import Path
from core.config import VERSION

def build():
    # Application settings
    app_name = f"PyAMPP_{VERSION}"
    main_script = "main.py"
    icon_path = "app.ico" 

    # Get CustomTkinter path
    ctk_path = os.path.dirname(customtkinter.__file__)

    # Ensure we are in the PyAMPP directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print(f"--- Starting Build for {app_name} ---")

    # Clean previous builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # PyInstaller command
    cmd = [
        "py", "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--clean", # Always clean cache
        f"--add-data={ctk_path};customtkinter/",
        "--collect-all", "customtkinter",
        f"--add-data=core;core/",
        f"--add-data=gui;gui/",
        f"--add-data=app.ico;.",
        f"--name={app_name}",
        "--hidden-import=psutil",
        "--hidden-import=requests",
        "--hidden-import=customtkinter",
        # Exclude common VC++ runtimes to force the app to use system ones
        # and prevent conflicts with PHP's required versions.
        "--exclude-module", "vcruntime140",
        "--exclude-module", "vcruntime140_1",
        "--exclude-module", "msvcp140",
        # Explicitly exclude internal testing tools
        "--exclude-module", "tester_server",
        "--version-file=version.txt",
        main_script
    ]

    if icon_path and os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, shell=True)
        print(f"\n--- Build Successful! ---")
        print(f"Executable is located in: {os.path.abspath('dist')}")
    except subprocess.CalledProcessError as e:
        print(f"\n--- Build Failed! ---")
        print(e)

if __name__ == "__main__":
    build()
