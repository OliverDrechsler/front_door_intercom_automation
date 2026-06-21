# Fresh Raspberry Pi Installation with FDIA

This guide describes how to prepare a fresh Raspberry Pi OS installation and deploy FDIA on the device.

## Prepare the SD Card

1. Open Raspberry Pi Imager.
2. Select your Raspberry Pi model, choose `Raspberry Pi OS Lite (Debian Bookworm)`, and select the target SD card.
3. Continue to the advanced configuration screen.
4. Set the hostname.
5. Set the username and password.
6. Add your SSH public key under the SSH service settings.
7. Start the imaging process.

## First Boot and Network Setup

1. Insert the SD card into the Raspberry Pi and power it on.
2. Wait for the initial boot and automatic reboot to complete.
3. Log in to the system.
4. Switch to the root user:

```bash
sudo su
```

5. Inspect the current network configuration:

```bash
nmcli -p connection show
```

6. Configure a static IP address if required:

```bash
nmcli c mod "Wired connection 1" ipv4.addresses 10.0.0.220/24 ipv4.method manual
nmcli con mod "Wired connection 1" ipv4.gateway 10.0.0.1
nmcli con mod "Wired connection 1" ipv4.dns 10.0.0.1
```

7. If you want to use multiple DNS servers:

```bash
nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8,8.8.4.4"
```

8. If you want to assign multiple IP addresses:

```bash
nmcli c mod "Wired connection 1" ipv4.addresses "10.0.0.220/24,10.0.0.221/24,10.0.0.222/24" ipv4.method manual
```

9. Restart the connection to apply the changes:

```bash
nmcli c down "Wired connection 1"
nmcli c up "Wired connection 1"
```

10. Verify the final network configuration:

```bash
nmcli -p connection show "Wired connection 1"
```

## Install Base Software

Install the required base packages:

```bash
sudo apt install mc git screen curl python3-pip python3.11-venv direnv
```

If you are using a Raspberry Pi 1 with limited RAM, disable the RAM-based `/tmp` mount and reboot:

```bash
systemctl mask tmp.mount
reboot
```

## Additional Packages for Raspberry Pi 1 and Newer Python Versions

On Raspberry Pi 1 with Debian Trixie or newer, Pillow may need to be compiled locally for Python 3.13+.

Install the required build dependencies:

```bash
apt install -y \
  python3-dev python3-pip python3-setuptools python3-wheel \
  libjpeg-dev zlib1g-dev libtiff5-dev libfreetype6-dev \
  liblcms2-dev libwebp-dev libopenjp2-7-dev libjpeg62-turbo-dev \
  tk-dev tcl-dev
```

## Clone and Prepare the Project

1. Change to the installation directory:

```bash
cd /usr/local/bin
```

2. Clone the repository:

```bash
git clone https://github.com/OliverDrechsler/front_door_intercom_automation.git
cd front_door_intercom_automation
```

3. Create the virtual environment:

```bash
python3 -m venv .venv
chmod +x .venv/bin/activate
```

4. Activate the environment:

```bash
source .venv/bin/activate
```

## Optional direnv Setup

1. Add this line to `~/.bashrc`:

```bash
eval "$(direnv hook bash)"
```

2. Reload the shell:

```bash
source ~/.bashrc
```

3. Create `.envrc` in the project root:

```bash
export VIRTUAL_ENV=./.venv
layout python-venv $VIRTUAL_ENV
```

4. Allow the directory:

```bash
direnv allow
```

## Pillow Reinstall for Older ARM Systems

If you are using an older ARMv6 system and need to rebuild Pillow:

```bash
apt install -y \
  python3-dev python3-pip python3-setuptools python3-wheel \
  libjpeg-dev zlib1g-dev libtiff5-dev libfreetype6-dev \
  liblcms2-dev libwebp-dev libopenjp2-7-dev libjpeg62-turbo-dev \
  tk-dev tcl-dev

/usr/local/bin/front_door_intercom_automation/.venv/bin/pip3 install --no-cache-dir --force-reinstall Pillow
```

## Install Python Dependencies

```bash
.venv/bin/pip3 install -r requirements.txt
```

## Configure and Test FDIA

1. Create and edit `config.yaml`.
2. Run a test start:

```bash
.venv/bin/python3 -m fdia
```

## Configure the Systemd Service

Update `fdia.service` so that `ExecStart` points to the virtual environment Python interpreter and the correct project path:

```text
ExecStart=/usr/local/bin/front_door_intercom_automation/.venv/bin/python3 /usr/local/bin/front_door_intercom_automation/fdia.py
```

Install and enable the service:

```bash
cp fdia.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable fdia.service
systemctl start fdia
```

Check the logs:

```bash
journalctl -xu fdia -f
```

## direnv Error Fix

If `direnv allow` fails with an error such as:

```text
direnv: loading front_door_intercom_automation/.envrc
environment:747: layout_python-venv: command not found
direnv: export +VIRTUAL_ENV
```

create `~/.config/direnv/direnvrc` with the following content:

```bash
layout_python-venv() {
  local python=${1:-python3}
  [[ $# -gt 0 ]] && shift
  unset PYTHONHOME
  if [[ -n $VIRTUAL_ENV ]]; then
      VIRTUAL_ENV=$(realpath "${VIRTUAL_ENV}")
  else
      local python_version
      python_version=$("$python" -c "import platform; print(platform.python_version())")
      if [[ -z $python_version ]]; then
      log_error "Could not detect Python version"
      return 1
      fi
      VIRTUAL_ENV=$PWD/.direnv/python-venv-$python_version
  fi
  export VIRTUAL_ENV
  if [[ ! -d $VIRTUAL_ENV ]]; then
      log_status "no venv found; creating $VIRTUAL_ENV"
      "$python" -m venv "$VIRTUAL_ENV"
  fi
  PATH="${VIRTUAL_ENV}/bin:${PATH}"
  export PATH
}
```

Then run:

```bash
source ~/.bashrc
cd /usr/local/bin/front_door_intercom_automation
direnv allow
```
