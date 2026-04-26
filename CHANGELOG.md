# Changelog

All notable changes to PyAMPP will be documented in this file.

## [1.0.4] - 2026-04-26
### Added
* **Automated Preset Synchronization**: The application now automatically checks for and fetches the latest PHP, Apache, and MySQL version presets from GitHub on startup.
* **Self-Healing Path Validation**: Added a startup check that verifies the existence of configured binaries. PyAMPP automatically detects missing components and resets the Setup Wizard if needed.
* **Automatic Server Restart on Save**: Saving changes in the Settings tab now automatically restarts any active Apache or MySQL servers to apply changes immediately.

### Changed
* **Persistent AppData Configuration**: Migrated the configuration system to the Windows `AppData/Roaming` directory to ensure settings persist across updates and moves.
* **htdocs Data Preservation**: Implemented surgical cleanup logic that preserves the `Apache24/htdocs` folder during updates or re-installations.
* **Offline Graceful Handling**: Enhanced networking logic to detect offline states and skip update checks seamlessly.
* **Improved Update Safety**: Updated component re-installation logic to protect MySQL data and Apache web files.
* **Enhanced Progress Visibility**: Refactored the "Start All" sequence for better progress bar accuracy during sequential setups.

### Fixed
* **Stability & Import Fixes**: Resolved a critical `UnboundLocalError` during dashboard component installations and improved global import handling.

## [1.0.3] - 2026-04-25
### Added
* **GitHub-Managed Version Presets**: Synchronizes with a remote repository to fetch the latest verified component versions (PHP, Apache, MySQL) without requiring an application update.
* **Robust MySQL Port Configuration**: Resolved an issue where custom MySQL ports were not consistently applied. Automatically configures `my.ini` and synchronizes with phpMyAdmin.
* **Real-Time Settings Synchronization**: Changes to ports or paths are immediately reflected in the dashboard for accurate monitoring and control.
* **Setup Wizard Enhancements**: Introduced a loading state that prioritizes fetching the latest presets from GitHub on startup.

### Fixed
* **Known Issues (v1.0.3)**: Note that v1.0.3 had known issues with `htdocs` data loss and configuration volatility which were addressed in v1.0.4.

## [1.0.2] - 2026-04-25
### Added
* **Version Preset Selection**: The Setup Wizard now allows you to choose specific versions for each component from a curated list of presets (PHP 7.4 to 8.4).
* **Hardened Process Isolation**: Improved binary execution logic to prevent DLL conflicts (specifically `VCRUNTIME140.dll` mismatches) by running services in a strictly isolated environment.
* **Smart Reinstallation**: Cleanly updates or switches binaries while strictly preserving existing MySQL data directories.
* **Intelligent Module Mapping**: Automatically detects and maps the correct PHP module name based on the active version.

## [1.0.1] - 2026-04-25
### Added
* **Improved Global Actions**: "Start All", "Stop All", and "Restart All" buttons now intelligently enable/disable based on the service state.
* **Dynamic Progress Bar**: The progress bar is now hidden by default and only appears during active setup or download operations.
* **Version Branding**: Consistent version display in the application window title and footer.

## [1.0.0] - 2026-04-23
### Added
* **Initial Release**: Standalone Windows executable for automating portable Apache, MySQL, and PHP stacks.
* **Core Management**: Dashboard for controlling services, managing configurations, and viewing real-time logs.
* **Setup Wizard**: Automated retrieval and configuration of official component binaries.
