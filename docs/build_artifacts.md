# Building Binary Artifacts and Docker Images

This guide describes how to build the supported binary targets and the Docker image defined by the project `Dockerfile`. The commands follow `.github/workflows/ci.yml`.

## Binary Build Prerequisites

- Check out the repository and run commands from its root directory.
- Install Python 3.14, `pip`, and the build tools for the target platform.
- Linux ARMv7 builds require an ARMv7 system or an ARMv7 environment running with QEMU.
- PyInstaller should build binaries on the target operating system. Build Windows on Windows, macOS on macOS, and Linux on Linux. Use a runner with the target architecture for ARM64 and Intel macOS builds.

Install the dependencies and PyInstaller on each target system:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

CI uses Python 3.14. On Windows, use `py -3.14` instead of `python` if required by your installation.

## Windows x64

Run the following in PowerShell from the repository root:

```powershell
py -3.14 -m pip install --upgrade pip
py -3.14 -m pip install -r requirements.txt
py -3.14 -m pip install pyinstaller
py -3.14 -m PyInstaller --clean --noconfirm --onefile `
  --collect-data certifi `
  --add-data "web/templates;web/templates" `
  --add-data "web/static;web/static" `
  --add-data "config_template.yaml;." `
  --name fdia fdia.py
```

Output: `dist/fdia.exe`.

## Linux x86_64

Run on a Linux x86_64 system:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --clean --noconfirm --onefile \
  --collect-data certifi \
  --add-data "web/templates:web/templates" \
  --add-data "web/static:web/static" \
  --add-data "config_template.yaml:." \
  --name fdia fdia.py
```

Output: `dist/fdia`.

## Linux ARM 32-bit (ARMv7)

The CI build uses `uraimo/run-on-arch-action@v3` with Ubuntu 22.04 and `arch: armv7`. Run the following inside that ARMv7 environment:

```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv build-essential libjpeg-dev zlib1g-dev
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller
pyinstaller --clean --noconfirm --onefile \
  --collect-data certifi \
  --add-data "web/templates:web/templates" \
  --add-data "web/static:web/static" \
  --add-data "config_template.yaml:." \
  --name fdia fdia.py
```

Output: `dist/fdia`. The build must run inside an ARMv7 environment; a regular x86_64 build does not produce an ARMv7 binary.

## Linux ARM64

On a Linux ARM64 system, such as the CI runner `ubuntu-24.04-arm`, run the same commands as for Linux x86_64. The native ARM64 binary is created at `dist/fdia`.

## macOS

Build on a macOS runner with the desired architecture. CI uses `macos-15-intel` for Intel and `macos-14` for Apple Silicon. The commands are the same as the Linux build, using `:` as the `--add-data` separator:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --clean --noconfirm --onefile \
  --collect-data certifi \
  --add-data "web/templates:web/templates" \
  --add-data "web/static:web/static" \
  --add-data "config_template.yaml:." \
  --name fdia fdia.py
```

Output: `dist/fdia`. The binary has no file extension; its architecture matches the macOS runner.

## Build a Docker Image from the Dockerfile

Install and start Docker. From the repository root, build an image for the local Docker builder's default platform:

```bash
docker build --file Dockerfile --tag fdia:local .
```

For Raspberry Pi deployment, additional GPIO options are required. See [Running the Docker container on Raspberry Pi](How_to_start_FDIA_Docker_container_on_Raspberry_Pi.md).

To build a multi-platform OCI image archive for Linux AMD64, ARM64, and ARMv7 without publishing it to a registry, use Docker Buildx:

```bash
docker buildx create --name fdia-builder --use
docker buildx build \
  --file Dockerfile \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag fdia:latest \
  --output type=oci,dest=fdia-multiarch.tar .
```

This creates `fdia-multiarch.tar` in the current directory. The image is not uploaded to GHCR or any other registry.
