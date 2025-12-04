# M3 Agent RPA Host Setup Guide

This guide explains how to set up a host machine to be controlled by the M3 Agent's RPA tool.

## 1. Required Dependencies

The host machine must have the following dependencies installed:

- **Python 3**
- **pyautogui**
- **sshpass** (for password-based authentication)

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3
brew install sshpass
pip3 install pyautogui
```

### Linux (Debian/Ubuntu)

```bash
# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install -y python3 python3-pip sshpass scrot python3-tk python3-dev
pip3 install pyautogui
```

### Windows

1.  **Install Python 3**:
    -   Download and install from [python.org](https://python.org)
    -   **Important**: Check the box "Add Python to PATH" during installation.

2.  **Install pyautogui**:
    ```bash
    pip install pyautogui
    ```

3.  **Install sshpass**:
    -   `sshpass` is not natively available on Windows.
    -   You can use **WSL (Windows Subsystem for Linux)** to run a Linux environment with `sshpass`.
    -   Alternatively, rely on **SSH key-based authentication (recommended for Windows)**.

## 2. Authentication Methods

The RPA tool supports two authentication methods:

### Method 1: SSH Key-based (Recommended)

**How it works**:
- The agent's SSH key is added to the host's `~/.ssh/authorized_keys` file.
- The agent can then log in without a password.

**Setup**:
1.  Ensure the agent's `.ssh` directory is mounted to the container:
    ```bash
    -v /path/to/your/.ssh:/root/.ssh:ro
    ```

2.  Add the agent's public key (`id_rsa.pub`) to the host's `~/.ssh/authorized_keys` file.

**Docker Environment**:
- `RPA_HOST_STRING`: `user@host`
- `RPA_HOST_PASSWORD`: (not set)

### Method 2: Password-based

**How it works**:
- The agent uses `sshpass` to provide the password during SSH connection.
- **Less secure** as the password is stored in an environment variable.

**Setup**:
1.  Install `sshpass` on the host machine (see above).

**Docker Environment**:
- `RPA_HOST_STRING`: `user@host`
- `RPA_HOST_PASSWORD`: `your_password`

## 3. Docker Run Command Example

```bash
docker run -d \
  --name m3-agent-v3.3 \
  -p 8888:8000 \
  -v /path/to/your/.ssh:/root/.ssh:ro \
  -e RPA_HOST_STRING="kori@192.168.9.125" \
  -e RPA_HOST_PASSWORD="your_password" \
  junpeng999/m3-agent-system:v3.3-arm64
```
