# Release Description
PyAMPP is a standalone Windows executable for automating the deployment and management of a portable Apache, MySQL, and PHP development stack.

## What's New in v1.0.9
* **PHP Extensions Manager Tab**: Added a dedicated "PHP Extensions" tab to the PyAMPP GUI. Users can search and toggle PHP extensions, editing `php.ini` in-place. Saving changes will automatically restart the Apache server (if running) in a background thread to apply settings.
* **Fixed Service CPU Usage**: Resolved an issue where service CPU usage for Apache and MySQL always showed `0.0%` by replacing the stateless `proc.cpu_percent()` calls with a stateful calculation of user+system CPU time delta divided by wall-clock time delta, normalized by the processor core count.
* **Manual Update Check Feedback**: Clicking "Check for Updates" in the footer now shows clear, user-friendly dialogs if the app is already up to date, if parsing fails, or if the updater service is offline, while startup checks remain silent.
* **Custom Dialog Progress Loader**: Introduced a modal `ProgressDialog` window for component downloading/extracting on both the Dashboard and Settings tab, preventing progress indicators from being cut off or hidden in smaller/non-maximized views.
* **Unified Custom Dialog Icons**: Set all custom top-level dialogs (such as the Exit Confirmation and Setup Wizard windows) to display the application's native icon (`app.ico`) instead of the default Tkinter feather icon.

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
