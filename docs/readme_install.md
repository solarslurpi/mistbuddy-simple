# 🍓📦 Installing MistBuddy-Lite on Raspberry Pi using Pipx and Git

This guide walks through installing the `mistbuddy-lite` application on a Raspberry Pi using `pipx` directly from its Git repository. `pipx` keeps the application isolated and makes updates easier.

## 📝✅ Prerequisites

1.  **Raspberry Pi with GrowBase Ecosystem:** A Raspberry Pi running Raspberry Pi OS (or similar). This guide assumes the Pi is part of a [`GrowBase` setup (solarslurpie/GrowBase)](https://github.com/solarslurpie/GrowBase). `MistBuddy-Lite` is designed to interact with the MQTT broker managed or used by `GrowBase`. Ensure `GrowBase` or at least its MQTT broker (like Mosquitto) is installed, running, and accessible on the network from this Pi. Network connectivity is essential.
2.  **SSH Access:** You should be able to SSH into your Raspberry Pi as the `pi` user (or your standard user). All commands below assume you are logged in as `pi`.

## ⬆️🛠️ Step 1: Update System and Install 
Ensure your system packages are up-to-date and essential tools are installed.

```bash
# Update package lists
sudo apt update
# Upgrade installed packages
sudo apt upgrade -y
# Ensure git is installed (pipx needs it to clone)
sudo apt install git -y
# Ensure Python 3.11 or higher is installed
python3 --version
```


## 🐍📦 Step 2: Install Pipx

`pipx` is used to install and run Python applications in isolated environments.

```bash
# Install pipx using apt
sudo apt install pipx -y

# Add pipx-managed directories to your user's PATH
# This ensures commands installed by pipx can be found
pipx ensurepath
```

*   **IMPORTANT:** After running `pipx ensurepath`, you might need to **log out and log back in** or open a **new terminal window** for the PATH changes to take effect. Verify by running `echo $PATH` and checking if `/home/pi/.local/bin` is included.

---

## 🐙✨ Step 3: Install `mistbuddy-lite` using Pipx from Git

Now, use `pipx` to install the application directly from the official Git repository on GitHub.

```bash
# Install directly from the solarslurpie/mistbuddy-lite repository using HTTPS
pipx install git+https://github.com/solarslurpie/mistbuddy-lite.git
```

*   `pipx` will perform the following steps:
    1.  **Temporarily Clone:** Download a copy of the `solarslurpie/mistbuddy-lite` repository to a temporary location on your Pi.
    2.  **Read Config:** Read the `pyproject.toml` file from this temporary copy.
    3.  **Create Environment:** Create an isolated virtual environment specifically for `mistbuddy-lite`.
    4.  **Install Dependencies:** Install the required libraries (`paho-mqtt`, `pydantic`, `pyyaml`, etc.) into this environment.
    5.  **Install Application:** Install the `mistbuddy-lite` package itself into the environment.
    6.  **Link Command:** Create the command `mistbuddy-lite` (as specified in `[project.scripts]`) and link it into `/home/pi/.local/bin/`, making it accessible from your terminal.
    7.  **Clean Up:** Delete the temporary copy of the repository code from your Pi, leaving only the installed application and its isolated environment.


## ✅👀 Step 4: Verify Installation

Check if the command was successfully installed and is accessible.

```bash
# Check if the command exists in the PATH
which mistbuddy-lite
```

*   You should see the output: `/home/pi/.local/bin/mistbuddy-lite` (or similar if your script name in `pyproject.toml` is different).
*   If the command isn't found, double-check the `pipx ensurepath` step and ensure you've opened a new terminal session. Also, review the output of the `pipx install` command for any errors.

---

## 📝⚙️ Step 5: Create External Configuration File

The application code expects its configuration file (`appconfig.yaml`) to be in a specific user directory, *outside* the `pipx` installation.

```bash
# Define the configuration directory name (must match what's in app.py's get_config_path())
CONFIG_DIR_NAME="mistbuddy_simple" # Or "mistbuddy-lite" if you changed it in app.py

# Create the configuration directory
mkdir -p "/home/pi/.config/${CONFIG_DIR_NAME}"

# Create and edit the configuration file using nano (or your preferred editor)
nano "/home/pi/.config/${CONFIG_DIR_NAME}/appconfig.yaml"
```

*   **Paste your complete and correctly structured `appconfig.yaml` content** into the `nano` editor. Ensure it matches the nested structure expected by your updated `