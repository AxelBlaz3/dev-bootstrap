# Dev Bootstrap 🚀

A collection of automated scripts to set up development environments quickly and consistently across Windows, macOS, and Linux.

## 📂 Repository Structure

```text
dev-bootstrap/
├── flutter/
│   └── setup_flutter.py   # OS-agnostic Flutter SDK installer
├── backend/               # (Coming Soon) Node/Express setup
├── docker/                # (Coming Soon) Container tools
└── README.md

```

---

## 📱 Flutter Setup

The `setup_flutter.py` script automates the installation of the Flutter SDK. It is designed to be **idempotent**—you can run it safely at any time.

### Features

* **OS Agnostic:** Works on Windows 11, macOS, and Linux.
* **Smart Detection:** Checks your current installed version against the latest stable release.
* *Already up to date?* It skips the download to save time.
* *Outdated?* It performs an upgrade.
* *Not installed?* It does a fresh install.

* **Robust:** Handles Windows file permission issues (like Read-Only git files) automatically.
* **Visuals:** Includes progress bars and colorful status updates.

### Prerequisites

* **Python 3.x** must be installed.

### How to Run

1. Clone this repository:

```bash
git clone https://github.com/AxelBlaz3/dev-bootstrap.git
cd dev-bootstrap

```

1. Run the script:

```bash
python flutter/setup_flutter.py

```

1. **Post-Install:**

* The script will tell you if you need to manually add Flutter to your `PATH`.
* Once finished, restart your terminal and run:

```bash
flutter doctor

```

---

## 🛠 Troubleshooting

**Windows: `Access is denied` errors**
The script includes a handler to force-delete Read-Only files (common with Git pack files). However, if you still see permission errors:

1. Ensure no other terminals or IDEs (like VS Code) are open in the `C:\flutter` directory.
2. Try running your terminal as **Administrator**.

**Windows: "Flutter is not recognized"**
If `flutter doctor` fails after installation:

1. Search for **"Edit environment variables for your account"** in Windows.
2. Edit the `Path` variable.
3. Add the full path to `C:\flutter\bin`.

---

## 🗺️ Roadmap

* [x] Flutter SDK Setup
* [ ] Backend Environment (Node.js/Express)
* [ ] Docker & Container Utilities
* [ ] Android Studio Command Line Tools
