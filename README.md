# WorkItems - Advanced Developer Tracking App

**WorkItems** is a high-performance, local-first Python desktop application built with PySide6. It is designed to track tasks, incidents, and chronological notes with seamless file-based synchronization to GitHub.

## ✨ Key Features
*   **Dual UI Modes**: Toggle between a beautiful, modern **Classic Mode** and an efficient **Analogue Mode**.
*   **Offline First**: Powered by a local SQLite database (using Peewee ORM with WAL mode) for lightning-fast performance, even without an internet connection.
*   **GitHub File-Based Sync**: Repos are cleanly categorized into "Online" and "Offline". WorkItems sync to your GitHub repository as `.wi` files automatically via PyGithub.
*   **Incident Management**: Native support for "Incident" type WorkItems, featuring a one-click "Declare Outage / Mitigated" toggle and specialized note status trackers (Active, Service Degradation, On Deps).
*   **Recycle Bin**: Soft-delete system prevents accidental data loss, funneling deleted items into a dedicated Recycle Bin.
*   **Built-in E2E Testing**: Robust UI testing and telemetry via a non-interactive `--ni` state-machine test runner.

---

## 🚀 Getting Started

### 1. Download the Standalone Executable
If you just want to run the app without touching code, simply download the pre-compiled executable directly from the repository!
*   **Linux**: Run `./dist/WorkItems`

*(Windows `.exe` cross-compilation is supported via the included build script!)*

### 2. Developer Setup (From Source)

#### Prerequisites
*   Python 3.10+
*   Git

#### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ralph7789/WorkItem.git
    cd WorkItem
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install PySide6 peewee PyGithub keyring pyinstaller
    ```

---

## ⚙️ Configuration & GitHub Access

To sync WorkItems with GitHub, the app requires a **GitHub Personal Access Token (PAT)** with repository permissions.

### How to generate your GitHub PAT:
1. Go to your GitHub account **Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**.
   *(Or click this direct link: [Generate new token](https://github.com/settings/tokens/new))*
2. Add a Note (e.g., "WorkItems Desktop App").
3. Set the expiration to your preference.
4. Under **Select scopes**, check the box for **`repo`** (Full control of private repositories).
5. Click **Generate token** and copy the resulting string (it starts with `ghp_...`).

### Adding the token to the app:
1.  Launch the app.
2.  Click the **🔑 PAT** button in the top toolbar.
3.  Paste your generated token into the dialog and click Save.
4.  **Security**: Your token is stored securely using the OS-level credential manager (via the `keyring` library).
    *   *Linux Headless Fallback*: If D-Bus / SecretService is unavailable, the app falls back to a securely chmodded `~/.workitems/token.json` file.

---

## 🛠️ Usage & Development

### Running the App
Run the app using the built-in monitor for full logging and telemetry:
```bash
python3 monitor.py
```

### Running the Test Suite
Trigger the headless End-to-End (E2E) testing state machine. This will evaluate all UI transitions and generate an HTML/JSON report:
```bash
python3 monitor.py --ni
```
*Reports are saved locally as `e2e_report.json` and `e2e_report.html`.*

### Building Executables
Use the included build script to compile the Python source code into a single, standalone binary.

**For Linux:**
```bash
./build.sh --linux
```

**For Windows (Cross-compiling from Linux via Wine):**
```bash
./build.sh --win
```
*(This automatically downloads a Windows Python environment, installs dependencies inside a local `.wine_env`, and compiles the `.exe` using Wine.)*

---
*Developed by ralph7789.*
