# Release Description
PyAMPP is a standalone Windows executable for automating the deployment and management of a portable Apache, MySQL, and PHP development stack.

## What's New in v1.1.0
* **Modern High-DPI App Icon**: Designed a sleek, minimalist 2-color application icon with full multi-resolution support (`16x16` up to `256x256` HD) for Windows taskbar and desktop shortcuts.
* **Automated CI/CD Release Pipeline**: Added GitHub Actions workflow (`release.yml`) for automated building, artifact archiving, and GitHub Release publishing on Windows runners.
* **Optimized Executable Size**: Streamlined PyInstaller build configuration in `build.py` to exclude unused heavy libraries, reducing the standalone executable size from ~30 MB down to ~17 MB.
* **Enhanced Documentation**: Updated project badges to modern shields.io specifications and improved layout in documentation.

> [!TIP]
> **Full Version History**: For a detailed list of all technical changes and fixes, please refer to the [CHANGELOG.md](https://github.com/rdevz-ph/PyAMPP-Windows/blob/main/CHANGELOG.md).

> [!IMPORTANT]
> **Still using or upgrading from older versions?**
> If you encounter an Apache SSL error, navigate to the **Diagnostics** tab, click **Verify SSL**, and then run the **Auto-Fix SSL & Enable HTTPS 🛠** tool to manually generate your missing certificates.

## MySQL Downgrade & Recovery Guide

> [!WARNING]
> **MySQL Downgrade Limitation**: While your MySQL data is strictly preserved during version changes, MySQL itself does not support downgrading data directories (e.g., moving from 8.4 back to 8.0). 

If you downgrade and MySQL fails to start:
1. **Back up** your existing `mysql_data` folder.
2. **Clear** the contents of the `mysql_data` folder.
3. **Restart** the application to allow the older version to initialize a compatible database.

Alternatively, go to the **Settings** tab and upgrade back to the last version you used to restore functionality without data loss.

## Key Features
* **Standalone Executable**: Portable application requiring no external dependencies.
* **Automated Setup**: Integrated wizard for retrieving and configuring official components.
* **Service Management**: Centralized control for Apache and MySQL with real-time monitoring.
* **Diagnostics**: Real-time log aggregation, LAN toggle, and SSL certification automation.

## Installation
1. Download and run the standalone PyAMPP.exe.
2. Follow the Setup Wizard to provision and configure your stack.
