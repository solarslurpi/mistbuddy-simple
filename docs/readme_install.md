# 🍓📦 Installing mistbuddy-simple on Raspberry Pi using Pipx and Git

This guide walks through installing the `mistbuddy-simple` application on a Raspberry Pi using `pipx` directly from its Git repository. `pipx` keeps the application isolated and makes updates easier.

## 📝✅ Prerequisites

1.  **Raspberry Pi with GrowBase Ecosystem:** A Raspberry Pi running Raspberry Pi OS (or similar). This guide assumes the Pi is part of a [`GrowBase` setup (solarslurpie/GrowBase)](https://github.com/solarslurpie/GrowBase). `mistbuddy-simple` is designed to interact with the MQTT broker managed or used by `GrowBase`. Ensure `GrowBase` or at least its MQTT broker (like Mosquitto) is installed, running, and accessible on the network from this Pi. Network connectivity is essential.
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

## 🐙✨ Step 3: Install `mistbuddy-simple` using Pipx from Git

Now, use `pipx` to install the application directly from the official Git repository on GitHub.

```bash
# Install directly from the solarslurpie/mistbuddy-simple repository using HTTPS
pipx install git+https://github.com/solarslurpi/mistbuddy-simple.git
```

*   `pipx` will perform the following steps:
    1.  **Temporarily Clone:** Download a copy of the `solarslurpie/mistbuddy-simple` repository to a temporary location on your Pi.
    2.  **Read Config:** Read the `pyproject.toml` file from this temporary copy.
    3.  **Create Environment:** Create an isolated virtual environment specifically for `mistbuddy-simple`.
    4.  **Install Dependencies:** Install the required libraries (`paho-mqtt`, `pydantic`, `pyyaml`, etc.) into this environment.
    5.  **Install Application:** Install the `mistbuddy-simple` package itself into the environment.
    6.  **Link Command:** Create the command `mistbuddy-simple` (as specified in `[project.scripts]`) and link it into `/home/pi/.local/bin/`, making it accessible from your terminal.
    7.  **Clean Up:** Delete the temporary copy of the repository code from your Pi, leaving only the installed application and its isolated environment.


## ✅👀 Step 4: Verify Installation

Check if the command was successfully installed and is accessible.

```bash
# Check if the command exists in the PATH
which mistbuddy-simple
```
*   You should see the output: `/home/pi/.local/bin/mistbuddy-simple` (or similar if your script name in `pyproject.toml` is different).
*   If the command isn't found, double-check the `pipx ensurepath` step and ensure you've opened a new terminal session. Also, review the output of the `pipx install` command for any errors.

## 🗑️ Uninstalling `mistbuddy-simple`

If you need to remove the application installed via `pipx`, follow these steps:

1.  **List Installed Packages (Optional):**
    To confirm the exact package name as registered by `pipx` (it should be `mistbuddy-simple` based on the `pyproject.toml`), you can run:
    ```bash
    pipx list
    ```
    This command shows all applications managed by `pipx` and their associated commands.

2.  **Uninstall the Package:**
    Use the `pipx uninstall` command followed by the package name:
    ```bash
    pipx uninstall mistbuddy-simple
    ```

3.  **What `pipx uninstall` Does:**
    *   **Removes Environment:** Deletes the isolated virtual environment created for `mistbuddy-simple`, including the installed application code and all its dependencies (`paho-mqtt`, `pydantic`, etc.). This environment is typically located under `/home/pi/.local/pipx/venvs/`.
    *   **Removes Command Link:** Deletes the command link (e.g., `mistbuddy-simple`) from the `pipx` binary directory (`/home/pi/.local/bin/`).

4.  **What is NOT Removed (Manual Cleanup):**
    `pipx uninstall` **only** removes the files it directly manages. You will need to manually remove other related files if desired:

    *   **Configuration File:** The `appconfig.yaml` file and its directory are *not* touched. To remove them:
        ```bash
        # WARNING: This permanently deletes your configuration!
        # Ensure the directory name matches what you used (e.g., mistbuddy_simple)
        rm -rf /home/pi/.config/mistbuddy-simple
        ```
    *   **Systemd Service File:** If you installed the system-wide service, the `.service` file remains in `/etc/systemd/system/`.
        *   First, stop and disable the service:
            ```bash
            sudo systemctl stop mistbuddy-simple.service
            sudo systemctl disable mistbuddy-simple.service
            ```
        *   Then, remove the file:
            ```bash
            # WARNING: Ensure you are deleting the correct service file!
            sudo rm /etc/systemd/system/mistbuddy-simple.service
            ```
        *   Finally, reload systemd:
            ```bash
            sudo systemctl daemon-reload
            ```
    *   **Log Files (Potentially):** If your application logs to specific files (check your `logger_setup`), these log files will also remain and need manual removal if desired. Systemd's journal logs related to the service will eventually be rotated out by the system.



## 📝⚙️ Step 5: Create External Configuration File

The configuration file, `appconfig.yaml`, is placed in a `mistbuddy-simple` subdirectory of  `~/.config/` because this is the standard Linux directory for user-specific application configuration data. Keeping it here ensures your settings are easily accessible by you and are not overwritten when the main application code is updated via `pipx`.

Follow these steps to create the directory and file:

```bash
# Define the configuration directory name (must match what's in app.py's get_config_path())
CONFIG_DIR_NAME="mistbuddy-simple"

# Create the configuration directory (e.g., /home/pi/.config/mistbuddy-simple)
mkdir -p "/home/pi/.config/${CONFIG_DIR_NAME}"

# Create and edit the configuration file using nano (or your preferred editor)
nano "/home/pi/.config/${CONFIG_DIR_NAME}/appconfig.yaml"
```

**Paste your complete and correctly structured `appconfig.yaml` content** into the `nano` editor. Ensure it matches the nested structure expected by the application (with `growbase_settings` and `tents_settings`).
*   Save the file (Ctrl+O, Enter in `nano`) and exit (Ctrl+X).
*   Verify permissions if needed (usually `pi` user will have correct permissions in their own home directory).

e.g.:
```
# The host_ip is validated as a v4 address.  With 127.0.0.1, we are saying it is running on the GrowBase.
growbase_settings:
  host_ip: 127.0.0.1

tents_settings:
  tent_one:
    MistBuddies:
      mistbuddy_1:
        mqtt_onoff_topic: cmnd/tent_one/mistbuddy_1/ONOFF
        mqtt_power_topics:
          - cmnd/tent_one/mistbuddy_1/fan/POWER
          - cmnd/tent_one/mistbuddy_1/mister/POWER
    # --- SIMPLIFIED LIGHT STATUS CHECK ---
    # Topic used to SEND the query command TO a snifferbuddy in the growtent to get Mem1 status
    # The code will ASSUME the response comes back on stat/.../RESULT with key "Mem1" == 1 for ON
    LightCheck:
      light_on_query_topic: cmnd/snifferbuddy/tent_one/sunshine/Mem1
      light_on_response_topic: stat/snifferbuddy/tent_one/sunshine/RESULT
      light_on_value: 1
      response_timeout: .5
```
## 🧪Step 6: Test Run (Manual)

Before setting up the background service, it's crucial to run the application directly from the command line to catch any immediate configuration, connection, or runtime errors.

```bash
# Run the installed command from your terminal
mistbuddy-simple
```

*   **Observe the output:** Watch the log messages printed to your terminal. Look for:
    *   Confirmation that the configuration file from `~/.config/mistbuddy-simple/appconfig.yaml` was loaded successfully.
    *   Messages indicating connection attempts to the MQTT broker specified in your config.
    *   Successful connection and subscription messages.
    *   Any error messages or Python tracebacks. Common initial errors might relate to incorrect MQTT broker IP, connection refused, or misconfigured topics in `appconfig.yaml`.
*   **Stop the application:** Let it run for a minute or two to ensure it doesn't crash immediately, then press `Ctrl+C` to stop it.

If the application starts, attempts to connect to MQTT, and doesn't produce obvious errors related to configuration or core functionality, the installation and basic setup are likely correct.

## ⚙️ Step 7: Install Systemd Service File

This step copies the pre-configured systemd service file from the GitHub repository directly to the correct system location. This requires `sudo`.

1.  **Download the Service File:**
    Use `wget` to download the `mistbuddy_simple.service` file directly into `/etc/systemd/system/`.
    ```bash
    sudo wget -O /etc/systemd/system/mistbuddy-simple.service https://raw.githubusercontent.com/solarslurpi/mistbuddy-simple/main/mistbuddy-simple.service
    ```
    *(Note: We use `-O` to specify the output path and filename. We name it `mistbuddy-simple.service` for consistency with the application name, even though the source filename might differ).*

2.  **Set Permissions:**
    Ensure the downloaded file has the standard permissions.
    ```bash
    sudo chmod 644 /etc/systemd/system/mistbuddy-simple.service
    ```

The service file is now in place. The next step is to use `systemctl` commands (with `sudo`) to enable and start the service.

sudo systemctl daemon-reload
sudo systemctl enable mistbuddy-simple
sudo systemctl start mistbuddy-simple