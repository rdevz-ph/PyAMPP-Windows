# Changelog

All notable changes to PyAMPP will be documented in this file.

## [1.0.8] - 2026-06-12
### Added
* **Dynamic Theme Toggle**: Introduced a Light/Dark Mode switch in the application footer for instant theme switching.
* **Auto-Run on Startup**: Added a setting to automatically launch PyAMPP when Windows starts via registry integration.
* **Unified UI Theming**: Fixed unstyled tab backgrounds (Logs, PHP CLI, Global PHP, Settings) to seamlessly match the custom premium ocean-blue dashboard cards.
* **Readable Light Mode Tabs**: Fixed tab header text color contrast issues when using the Light Mode theme.
* **Automated SSL Setup**: The Setup Wizard and Updater now automatically execute the SSL Auto-Fix routine upon Apache extraction, generating self-signed certificates and enabling HTTPS to prevent first-time startup errors.

## [1.0.7] - 2026-05-30
### Added
* **Diagnostics & SSL Checker Tab**: Integrated a real-time HTTP reachability/latency scanner, MySQL database TCP tests, PHP CLI execution checks, and a detailed SSL certificate inspector.
* **One-Click SSL Auto-Fixer & Regenerator**: Automatically generates local development self-signed keys/certificates, registers virtual host SSL directives in Apache on port 443, and supports manual one-click regeneration, active SSL configuration file editing, and direct certificate directory exploration.
* **Htdocs Shortcut Button**: Added a dedicated `Htdocs 📁` button in the Apache Web Server control card footer, allowing one-click access to the Apache server root directory.

## [1.0.6] - 2026-05-27
### Added
* **Premium Card-Based Dashboard**: Revamped the row-based environment control panel into a high-end, visual control center with unified Slate 900 backgrounds and custom card frames.
* **Process-Level Resource Metrics**: Real-time tracking of PID, CPU utilization %, and RAM memory consumption (MB) dynamically aggregated for both Apache and MySQL servers.
* **System-Wide Health Monitor**: Dashboard cards displaying real-time System CPU, System RAM, and drive Disk Space usage with sleek progress-indicator bars.
* **Config Shortcuts**: One-click edit buttons inside the cards to instantly open `httpd.conf`, `my.ini`, or `php.ini` in the default text editor.
* **Dedicated Logs Tab**: Created a dedicated tab for logs, freeing up 250px of vertical space and enabling fully responsive dashboard auto-scaling in minimized/compact windows.

### Changed
* **Preset Overwrite Logic**: Remote preset downloads now completely overwrite the local cache instead of merging, ensuring removed or dead links are cleanly purged from selection dropdowns.
* **Latest Default Presets**: Upgraded default configuration fallback URLs to point to working PHP 8.5.6 and MySQL 8.4.4 LTS releases, resolving old dead URLs.

## [1.0.5] - 2026-04-27
### Added
* **PHP 8.5.5 Support**: Added support for the latest PHP 8.5.5 presets in the Setup Wizard and configuration engine.
* **Application Update Notifications**: Implemented an in-app notification system that detects newer versions of PyAMPP on GitHub and provides a direct link to the latest release page.
* **Manual Update Check Button**: Added a "Check for Updates" button to the application footer, allowing users to manually refresh presets and check for software updates at any time.
* **Metadata Support in Presets**: The preset system now supports optional metadata (like latest version info) without impacting component lists or breaking compatibility with older application versions.

### Changed
* **Improved Preset Merging Logic**: Refactored the merging engine to ensure that newly fetched versions from the server are prioritized and appear at the top of selection menus.
* **Consistent UI Arrangement**: Standardized the category order (PHP, Apache, MySQL, phpMyAdmin) in all configuration menus to ensure a consistent user experience.
* **Centralized Preset Management**: Consolidated preset update logic into a unified helper function to improve maintainability and ensure UI reactivity.

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
