# PyAMPP: Portable Web Development Stack Manager

[![Downloads](https://my-release-badge-api.vercel.app/api/badge?owner=rdevz-ph&repo=PyAMPP-Windows&mode=downloads&color=blue&v=1.0.1)](https://github.com/rdevz-ph/PyAMPP-Windows/releases)
[![Version](https://my-release-badge-api.vercel.app/api/badge?owner=rdevz-ph&repo=PyAMPP-Windows&mode=version&color=brightgreen&v=1.0.1)](https://github.com/rdevz-ph/PyAMPP-Windows/releases/latest)
[![Release](https://my-release-badge-api.vercel.app/api/badge?owner=rdevz-ph&repo=PyAMPP-Windows&mode=name&color=blue&v=1.0.1)](https://github.com/rdevz-ph/PyAMPP-Windows/releases/latest)

## Project Overview

PyAMPP is an advanced Windows-based orchestration utility designed to automate the deployment and management of a local web development environment. It provides a centralized graphical interface for the integrated management of Apache HTTP Server, MySQL Database, PHP, and phpMyAdmin.

> [!NOTE]
> This software is developed for personal use and internal development purposes. The source code is not available for public distribution or external contribution.

## Core Objectives

1.  **True Portability:** Consolidates all binaries, configuration templates, and data directories into a single root directory, ensuring the environment remains independent of the host system.
2.  **Zero-Configuration Logic:** Dynamically calculates paths, ports, and module mappings at runtime, eliminating the need for manual edits to `httpd.conf`, `my.ini`, or `php.ini`.
3.  **Automated Lifecycle:** A built-in wizard handles the retrieval, validation, and extraction of official binaries, keeping the stack current with zero administrative overhead.

## Advanced Features

### Intelligent Service Orchestration
- **Detached Execution:** Services run as independent process trees, ensuring stability even if the GUI is closed.
- **Real-Time Monitoring:** Continuous tracking of Process IDs (PIDs) and port availability with an integrated log aggregator.
- **Unified Controls:** One-click "Start All", "Stop All", and "Restart All" functionality.

### Dynamic Environment Mapping
- **PHP Extension Automation:** Automatically enables and maps essential extensions (`mysqli`, `mbstring`, `openssl`, `curl`, `pdo_mysql`, `zip`, `gd`, `fileinfo`, `intl`, `exif`, etc.) using absolute local paths.
- **Global CLI Integration:** Built-in PowerShell automation to register the portable PHP binary in the System PATH, enabling CLI tools like Composer or Artisan.
- **phpMyAdmin Security:** Automated deployment with dynamic `blowfish_secret` generation and restricted local-only access controls.
- **LAN Toggle:** Rapidly switch between local-loopback and network-exposed states with automatic subnet detection for Apache access control.

## Technical Specifications

- **Engine:** Python 3.x
- **GUI:** CustomTkinter (Modern, High-DPI aware)
- **Networking:** Synchronous socket validation and subnet discovery.
- **Components:**
    - **Apache:** VS17 Win64 (Apache Lounge) with Windows performance optimizations.
    - **MySQL:** 8.0.x Community Server with automated `--initialize-insecure` routine.
    - **PHP:** Thread Safe 8.3.x distributions.
    - **phpMyAdmin:** Multi-language web interface.

## System Architecture

- **Core Layer:** Management of binaries, configuration templating, and low-level process control.
- **GUI Layer:** Modular dashboard, setup wizard, log aggregator, and global settings.
- **Automation Layer:** PowerShell integration for system-wide environment pathing.

## Documentation

For more detailed information, technical guides, and visual overviews, visit our documentation site:
**[View Detailed Documentation](https://rdevz-ph.github.io/PyAMPP-Windows/)**

## Legal

Copyright (c) 2026 Romel Brosas. All Rights Reserved.
Provided under a proprietary license. See the [LICENSE](LICENSE) file for details.

## Disclaimer

PyAMPP is intended exclusively for local development and testing. Default configurations prioritize development speed over production-grade security hardening. Do not use for hosting public-facing services.
