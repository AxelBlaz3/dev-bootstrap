import os
import sys
import platform
import json
import urllib.request
import zipfile
import tarfile
import shutil
import subprocess
import re
import stat

# --- Configuration ---
INSTALL_DIR_NAME = "flutter"
BASE_URL = "https://storage.googleapis.com/flutter_infra_release/releases"
PATHS = {
    "Windows": r"C:\flutter",
    "Darwin": os.path.expanduser("~/development/flutter"),
    "Linux": os.path.expanduser("~/development/flutter")
}
METADATA_URLS = {
    "Windows": "https://storage.googleapis.com/flutter_infra_release/releases/releases_windows.json",
    "Darwin": "https://storage.googleapis.com/flutter_infra_release/releases/releases_macos.json",
    "Linux": "https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json"
}

# --- Visual Utilities ---
if os.name == 'nt':
    os.system('')  # Enable ANSI colors on Windows


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_step(emoji, text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{emoji}  {text}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.BOLD}{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.BOLD}{Colors.RED}✖ {text}{Colors.RESET}")


def draw_progress_bar(current, total, prefix='', suffix='', decimals=1, length=40, fill='█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (current / float(total)))
    filled_length = int(length * current // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(
        f'\r{prefix} |{Colors.BLUE}{bar}{Colors.RESET}| {percent}% {suffix}')
    sys.stdout.flush()
    if current == total:
        sys.stdout.write('\n')

# --- Logic ---


def get_os():
    return platform.system()


def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read only file),
    it attempts to add write permission and then retries.
    """
    # Check if the file is read-only
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise


def get_installed_version():
    """Tries to run 'flutter --version' and parse the version string."""
    try:
        # shell=True is required on Windows to find 'flutter.bat'
        use_shell = (os.name == 'nt')

        result = subprocess.run(
            ["flutter", "--version"],
            capture_output=True,
            text=True,
            check=True,
            shell=use_shell
        )
        # Output example: "Flutter 3.38.5 • channel stable..."
        match = re.search(r"Flutter\s+(\d+\.\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return None
    except Exception:
        return None
    return None


def download_reporthook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if downloaded < total_size:
        draw_progress_bar(downloaded, total_size,
                          prefix='Downloading:', suffix='', length=30)
    else:
        draw_progress_bar(total_size, total_size,
                          prefix='Downloading:', suffix='Complete', length=30)


def install_flutter():
    current_os = get_os()

    print(f"{Colors.HEADER}========================================{Colors.RESET}")
    print(f"{Colors.HEADER}    FLUTTER ENVIRONMENT SETUP           {Colors.RESET}")
    print(f"{Colors.HEADER}========================================{Colors.RESET}")

    if current_os not in PATHS:
        print_error(f"Unsupported OS: {current_os}")
        return

    install_path = PATHS[current_os]
    print(f"Detected System: {Colors.BOLD}{current_os}{Colors.RESET}")

    # 1. Fetch Metadata
    print_step("🔍", "Checking for latest stable release...")
    latest_version = None
    download_url = None

    try:
        with urllib.request.urlopen(METADATA_URLS[current_os]) as url:
            data = json.loads(url.read().decode())
            current_hash = data['current_release']['stable']
            release = next(
                (item for item in data['releases'] if item['hash'] == current_hash), None)

            if not release:
                raise Exception("Could not match hash to release.")

            archive_path = release['archive']
            download_url = f"{BASE_URL}/{archive_path}"
            latest_version = release['version']
            print_success(
                f"Latest Stable Version: {Colors.BOLD}{latest_version}{Colors.RESET}")
    except Exception as e:
        print_error(f"Failed to fetch metadata: {e}")
        return

    # 2. Check Installed Version
    installed_version = get_installed_version()

    if installed_version:
        print(
            f"   Local Version:         {Colors.BOLD}{installed_version}{Colors.RESET}")

        if installed_version == latest_version:
            print(
                f"\n{Colors.GREEN}Great news! You are already on the latest version.{Colors.RESET}")
            print("Skipping installation to save time.")
            return
        else:
            print_warning(
                f"Version mismatch. Upgrading {installed_version} -> {latest_version}...")
    else:
        print_warning(
            "Flutter not found in PATH. Proceeding with fresh install...")

    # 3. Download
    filename = f"flutter_{latest_version}_archive" + \
        (".zip" if current_os == "Windows" else ".tar.xz")
    print_step("⬇️", f"Downloading Flutter SDK...")

    try:
        urllib.request.urlretrieve(download_url, filename, download_reporthook)
        print_success("Download finished.")
    except Exception as e:
        print_error(f"Download failed: {e}")
        return

    # 4. Extract
    print_step("📦", f"Extracting to {install_path}...")

    # Clean old install
    if os.path.exists(install_path):
        print_warning("Removing old installation directory...")
        try:
            # Use the custom error handler for Read-Only Git files
            shutil.rmtree(install_path, onerror=on_rm_error)
        except OSError as e:
            print_error(f"Could not remove old directory: {e}")
            print("Check if any Flutter files are open or locked.")
            return

    parent_dir = os.path.dirname(install_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    # Extraction
    try:
        if filename.endswith(".zip"):
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)
                for i, file in enumerate(file_list):
                    zip_ref.extract(file, parent_dir)
                    if i % 100 == 0 or i == total_files - 1:
                        draw_progress_bar(i + 1, total_files,
                                          prefix='Extracting: ', length=30)
        else:
            with tarfile.open(filename, "r:xz") as tar:
                members = tar.getmembers()
                total_files = len(members)
                for i, member in enumerate(members):
                    tar.extract(member, path=parent_dir)
                    if i % 100 == 0 or i == total_files - 1:
                        draw_progress_bar(i + 1, total_files,
                                          prefix='Extracting: ', length=30)

        print_success("Extraction complete.")
    except Exception as e:
        print_error(f"Extraction failed: {e}")
        return
    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

    # 5. PATH Handling
    bin_path = os.path.join(install_path, "bin")
    print_step("⚙️", "Final Configuration")

    if current_os == "Windows":
        user_path = os.environ.get('PATH', '')
        if bin_path.lower() in user_path.lower():
            print_success("Flutter is already in your PATH.")
        else:
            print_warning("Action Required: Update your PATH.")
            print(f"Run this in PowerShell (Admin) to finish:")
            print(
                f"  [Environment]::SetEnvironmentVariable('Path', $env:Path + ';{bin_path}', 'User')")
    else:
        print_success("Installation done.")
        print(
            f"Add this to your .zshrc/.bashrc: export PATH=\"$PATH:{bin_path}\"")

    print(f"\n{Colors.HEADER}========================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}   READY TO CODE! 🚀{Colors.RESET}")
    print(
        f"   Run '{Colors.CYAN}flutter doctor{Colors.RESET}' to verify setup.")
    print(f"{Colors.HEADER}========================================{Colors.RESET}")


if __name__ == "__main__":
    install_flutter()
