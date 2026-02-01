# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the project structure, purpose, and development conventions.

## Project Overview

This is a Python application designed to monitor a list of web pages for content changes. When a change is detected, it sends a notification via Telegram.

The project is architected to run automatically at regular intervals, using a GitHub Actions workflow for scheduling.

### Key Technologies

*   **Language:** Python 3
*   **Core Libraries:**
    *   `requests`: For making HTTP requests to fetch web pages.
    *   `beautifulsoup4`: For parsing HTML and extracting meaningful text content.
*   **Data Storage:**
    *   `data/pages.json`: A user-configured JSON file listing the web pages to monitor.
    *   `data/snapshots.json`: An automatically generated and updated file that stores the latest content snapshot and a history of changes for each page.
*   **CI/CD:** GitHub Actions are used for automated, hourly checks.

### Architecture

The application is composed of several modules:

*   `main.py`: The main entry point that orchestrates the monitoring process.
*   `src/config.py`: Loads configuration from `data/pages.json` and environment variables (for Telegram credentials).
*   `src/monitor.py`: Contains the core logic for fetching a web page, extracting its text content, and computing a diff against the last known version.
*   `src/storage.py`: Manages the reading and writing of the `data/snapshots.json` file.
*   `src/notify.py`: Responsible for formatting and sending notifications to Telegram.
*   `tests/`: Contains the unit tests for the application.
    *   `conftest.py`: Test fixtures and setup.
    *   `test_monitor.py`: Tests for the core monitoring logic.
    *   `test_storage.py`: Tests for the storage layer.
    *   `test_notify.py`: Tests for the notification system.
    *   `test_config.py`: Tests for configuration loading.
*   `.github/workflows/monitor.yml`: A GitHub Actions workflow that automates the execution of the monitor on an hourly schedule and commits the results.

## Building and Running

### Prerequisites

*   Python 3
*   A Telegram Bot Token and Chat ID.
*   `pytest` (for running tests)

### Installation

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### Running Locally

1.  **Configure Environment Variables:**
    Set your Telegram credentials as environment variables.

    ```bash
    export TELEGRAM_BOT_TOKEN="your_bot_token"
    export TELEGRAM_CHAT_ID="your_chat_id"
    ```

2.  **Run the Monitor:**
    Execute the main script.

    ```bash
    python main.py
    ```

3.  **Dry Run (without notifications):**
    To test the application without sending notifications, use the `--dry-run` flag.

    ```bash
    python main.py --dry-run
    ```

### Running Tests

To run the automated tests, install `pytest` and execute:

```bash
pip install pytest pytest-mock
python -m pytest tests
```

### Running with GitHub Actions

The primary method of execution is via the included GitHub Actions workflow.

*   **Trigger:** The workflow runs automatically every hour. It can also be triggered manually from the "Actions" tab in the GitHub repository.
*   **Configuration:** The `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` must be configured as secrets in the GitHub repository settings.
*   **Operation:** The workflow checks out the code, installs dependencies, runs the monitor, and then commits and pushes the updated `data/snapshots.json` file back to the repository.

## Development Conventions

*   **Configuration:** All user-facing configuration is done in `data/pages.json`. Sensitive information like API keys is handled through environment variables.
*   **Code Style:** The code follows standard Python conventions (PEP 8).
*   **Modularity:** The application is divided into single-responsibility modules (config, storage, monitor, notify).
*   **Data Flow:**
    1.  `main.py` loads pages from `src/config.py`.
    2.  For each page, it retrieves the last known snapshot from `src/storage.py`.
    3.  It calls `src/monitor.py` to check for changes.
    4.  If a change is detected, `src/notify.py` sends a notification, and `src/storage.py` updates the snapshot.
*   **Error Handling:** The application includes basic error handling for network requests and gracefully skips pages that fail to load.
