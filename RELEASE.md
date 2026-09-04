# Release Description
PyAMPP is a standalone Windows executable for automating the deployment and management of a portable Apache, MySQL, and PHP development stack.

## What's New in v1.1.1
* **Custom Document Root (`htdocs`) Path Configuration**: Added options in both the **Settings** tab and the **Setup Wizard** to configure a custom web root directory (defaulting to `C:\PyAMPP\htdocs`).
* **Full Backward Compatibility for Legacy Document Roots**: Automatically preserves existing `htdocs` folders if previously located at `<install_dir>\bin\apache\Apache24\htdocs` so existing users aren't forced to move or migrate files.
* **Seamless phpMyAdmin Alias Integration**: Configured Apache `Alias /phpmyadmin` to allow full phpMyAdmin access without polluting custom web root folders.
* **Collapsible Download URLs in Settings**: Component download URL entry fields are now tucked into an expandable container and collapsed by default, saving vertical space and providing a much cleaner configuration interface.

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
