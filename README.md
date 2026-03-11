# ISTJ
### Integrated System Test Jig — Desktop Application

> **Beta Version 0.1** &nbsp;|&nbsp; Released: March 2026 &nbsp;|&nbsp; Platform: Windows &nbsp;|&nbsp; Python 3.8+

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [User Roles & Access](#user-roles--access)
- [Navigation Flow](#navigation-flow)
- [Test Modules](#test-modules)
- [Report Output](#report-output)
- [Release History](#release-history)
- [Known Issues](#known-issues)
- [Notes](#notes)

---

## Overview

**ISTJ** is a PyQt5-based desktop application designed for structured hardware testing and quality assurance workflows. It provides a role-based interface for test engineers, admins, and management to connect to hardware devices, execute automated test sequences, verify equipment health, and generate detailed test reports in PDF and Excel formats.

The application interfaces with physical lab equipment including digital multimeters (DMM), oscilloscopes, power supply units (PSU), APX analyzers, and ISTJ microcontrollers via VISA and serial communication protocols.

---

## Features

| Feature | Description |
|---|---|
| Role-based Authentication | Separate access levels for engineers, admins, and meta-admins |
| Device Auto-Detection | VISA-based automatic detection of connected instruments |
| Full Test Execution | End-to-end guided hardware test sequences |
| Unit Test Mode | Run individual test modules independently |
| Equipment Self-Check | Pre-test verification of all connected equipment |
| Test Reports | Auto-generated reports in both XLSX and PDF formats |
| Admin Dashboard | Management-level monitoring and configuration tools |
| Meta-Admin Dashboard | Top-level system administration and user management |
| Calibration Management | Calibration popup and database for instrument calibration records |
| Logging | Detailed connection and session logs with PDF export |

---

## Project Structure

```
mygui/
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
│
├── admin/                         # Admin dashboards & configurations
│   ├── admin_dashboard.py
│   ├── meta_admin_dashboard.py
│   └── admin_configs/
│
├── core/                          # Core utilities & helpers
│   ├── dmm_reader.py              # DMM data reading logic
│   ├── excel_logger.py            # Excel report logging
│   ├── exception_handler.py       # Global exception hook
│   ├── logger.py                  # Application logger
│   ├── paths.py                   # Centralised path constants
│   └── stm32_commands.py          # STM32 serial command interface
│
├── db/                            # Database layer
│   ├── admin_auth.py              # Admin authentication DB
│   ├── db_paths.py                # DB path constants
│   └── database/                  # SQLite database files
│       ├── admin_auth.db
│       ├── admin_dashboard.db
│       ├── calibration.db
│       └── employee_auth.db
│
├── devices/                       # Hardware device drivers
│   ├── apx_analyzer.py            # APX audio analyzer interface
│   ├── device_listeners.py        # Device event listeners
│   ├── device_types.py            # Device type definitions
│   ├── dmm.py                     # Digital multimeter driver
│   ├── microcontroller.py         # STM32 microcontroller interface
│   ├── oscilloscope.py            # Oscilloscope driver
│   ├── power_supply.py            # PSU driver
│   └── visa_auto_detector.py      # Auto-detect VISA instruments
│
├── dialogs/                       # Modal popup dialogs
│   ├── abort_test_dialog.py
│   ├── calibration_popup.py
│   ├── disconnect_result_dialog.py
│   ├── logs_viewer_dialog.py
│   ├── test_completion_dialog.py
│   └── OperatorInfoPopup.py
│
├── psu/                           # Power supply unit control
│   ├── automation.py
│   ├── psu_commands.py
│   ├── psu_helpers.py
│   └── psu_threads.py
│
├── screens/                       # Application UI screens
│   ├── login_screen.py
│   ├── connection_screen.py
│   ├── test_selection_screen.py
│   ├── full_test_screen.py
│   ├── equipment_self_check_screen.py
│   ├── test_reports_screen.py
│   ├── junction_box.py
│   ├── station_box.py
│   └── lru_selection.py
│
├── tests/                         # Individual hardware test modules
│   ├── lighting_test.py
│   ├── microphone_audio.py
│   ├── phones_audio.py
│   ├── power_supply.py
│   ├── resistance_measurement.py
│   ├── voltage_measurement.py
│   ├── transient.py
│   ├── vos_delay.py
│   └── ...
│
├── workers/                       # Background thread workers
│   └── connection_worker.py
│
├── resourses/                     # Application icons and images
└── test_reports/                  # Auto-generated test output
    ├── pdfs/                      # PDF format reports
    └── xl/                        # Excel format reports
```

---

## Requirements

- Python 3.8 or higher
- Windows OS (recommended for VISA instrument compatibility)
- NI-VISA or equivalent VISA runtime installed for instrument communication

### Python Dependencies

```
PyQt5
pyvisa
openpyxl
reportlab
pyserial
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mygui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure NI-VISA runtime is installed on your system for hardware communication.

4. Run the application:
```bash
python main.py
```

The `test_reports/` directory and required databases are initialised automatically on first launch.

---

## Running the Application

```bash
python main.py
```

On startup the application will:
- Initialise the admin authentication database
- Create the `test_reports/pdfs/` and `test_reports/xl/` directories if not present
- Launch the login screen

---

## User Roles & Access

| Role | Access Level |
|---|---|
| Test Engineer | Connection → Test Selection → Full / Unit Tests |
| Senior Test Engineer | Admin Dashboard |
| Manager | Admin Dashboard |
| General Manager | Admin Dashboard |
| META_ADMIN_SELF | Meta Admin Dashboard (full system control) |
| META_ADMIN_MASTER | Meta Admin Dashboard (full system control) |

---

## Navigation Flow

```
Login Screen
  │
  ├── META_ADMIN_SELF / META_ADMIN_MASTER
  │     └── MetaAdminDashboard
  │           └── [restart login]
  │
  ├── Senior Test Engineer / Manager / General Manager
  │     └── AdminDashboard
  │           └── [logout → login]
  │
  └── Test Engineer
        └── ConnectionScreen
              └── TestSelectionScreen
                    ├── FullTestScreen
                    │     └── [return to selection / disconnect]
                    ├── EquipmentSelfCheckScreen
                    │     └── [return to selection]
                    └── TestReportsScreen
                          └── [return to selection]
```

---

## Test Modules

The `tests/` directory contains modular, independently runnable test scripts:

| Module | Description |
|---|---|
| `lighting_test.py` | Panel and backlit lighting verification |
| `microphone_audio.py` | Microphone audio signal test |
| `phones_audio.py` | Headphone audio output test |
| `power_supply.py` | PSU voltage and current verification |
| `resistance_measurement.py` | Resistance measurement via DMM |
| `voltage_measurement.py` | Voltage measurement via DMM |
| `transient.py` | Transient response test |
| `vos_delay.py` | VOS delay measurement |
| `ground_crew_ics_volume.py` | Ground crew ICS volume test |
| `ground_crew_override.py` | Ground crew override function test |
| `user_primary_tx_ptt.py` | TX PTT functionality test |
| `user_transmit_tx_output.py` | Transmit output level test |
| `user_recieve_rx_select.py` | RX select functionality test |

---

## Report Output

Test reports are automatically saved in two formats after every test run:

- **Excel (`.xlsx`)** — Saved to `test_reports/xl/`
- **PDF** — Saved to `test_reports/pdfs/`

Report filenames follow the format:

```
{SerialNumber}_{HH-MM-SS}_{Pass|Fail}.xlsx
{SerialNumber}_{HH-MM-SS}_{Pass|Fail}.pdf
```

Example:
```
17ZY22W12345_15-59-08_Pass.xlsx
17ZY22W12345_15-59-08_Pass.pdf
```

---

## Release History

### v0.1.0-beta — March 2026 *(Initial Beta Release)*

**New in this release:**
- Initial beta release of the ISTJ application
- Role-based login with engineer, admin, and meta-admin access tiers
- VISA-based auto-detection of connected instruments (DMM, oscilloscope, PSU, APX analyzer)
- Full test sequence execution with pass/fail result tracking
- Equipment self-check screen for pre-test instrument verification
- Unit test mode for running individual test modules in isolation
- Auto-generated test reports in XLSX and PDF formats with serial number-based filenames
- Admin dashboard for Senior Test Engineers, Managers, and General Managers
- Meta-admin dashboard with full system administration and user management
- Calibration management with SQLite-backed calibration records
- Global exception handler with full console traceback logging
- Connection and session log viewer with PDF export capability
- STM32 microcontroller command interface via serial
- Operator info popup for session identification

---

## Known Issues

> The following are known limitations in this beta release and will be addressed in upcoming versions.

- Unit test screen is currently a placeholder — full implementation pending
- Log PDF export directory may need to be created manually on some systems
- VISA instrument detection may require a manual refresh on first connect on certain hardware configurations
- Application window is fixed size and does not support resizing or scaling

---

## Notes

- All SQLite databases are initialised automatically on first launch. Do not delete or modify files in `db/database/` manually.
- Device status captured on the Connection screen is passed downstream to the Equipment Self-Check screen.
- The `resourses/` folder name is intentional (matches internal codebase references) — do not rename.
- For best results, connect and power on all instruments before launching the application.

---

*ISTJ is an internal tool. For support or bug reports, contact the development team.*