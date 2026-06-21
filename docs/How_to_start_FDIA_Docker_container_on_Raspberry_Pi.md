# How to Start the FDIA Docker Container on Raspberry Pi

This document explains how to run FDIA in Docker on a Raspberry Pi, including the GPIO access required for bell detection and door opener control.

## Purpose

FDIA can access Raspberry Pi GPIO pins for:

- doorbell detection
- door opener relay control

Because Docker containers are isolated from the host system by default, GPIO access must be explicitly enabled when the container is started.

## Prerequisites

Required:

- Raspberry Pi
- Raspberry Pi OS or another Linux distribution running on the Pi
- Docker installed
- a valid `config.yaml`
- optional `blink_config.json` if Blink support is enabled

Check the Docker installation:

```bash
docker --version
```

## Important GPIO Requirement

The container must be given access to the Raspberry Pi GPIO device.

Preferred device mapping:

```bash
--device /dev/gpiomem:/dev/gpiomem
```

Optional fallback for older systems:

```bash
--device /dev/mem:/dev/mem
```

If neither device is provided, the container entrypoint stops with an error.

## Required Container Rights for GPIO Access

The container does not need full privileged mode.

Minimum requirements:

- device mapping for `/dev/gpiomem`
- a process user that can read and write the mapped device

Recommended setup:

- map `/dev/gpiomem`
- run the process as `root` inside the container

The current image runs as `root` by default, which is the simplest and most reliable option for `RPi.GPIO`.

Usually not required:

- `--privileged`
- `--cap-add SYS_RAWIO`
- `--cap-add ALL`
- host network mode only for GPIO access

Legacy fallback only if needed:

- `--device /dev/mem:/dev/mem`

If you intentionally run the container as a non-root user, that user must be able to access the GPIO device group from the host.

Check the device owner and group on the Raspberry Pi host:

```bash
ls -l /dev/gpiomem
stat -c '%g' /dev/gpiomem
```

Example for a non-root container:

```bash
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --user 1000:1000 \
  --group-add "$(stat -c '%g' /dev/gpiomem)" \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -e TZ=Europe/Berlin \
  ghcr.io/oliverdrechsler/front_door_intercom_automation:latest
```

If you do not need a non-root container, use the default root user.

## Prepare Configuration Files

Create your configuration before starting the container:

```bash
cp config_template.yaml config.yaml
```

Then update `config.yaml` with your real settings.

If Blink support is enabled, also provide `blink_config.json`.

## Build the Container Locally

From the project root:

```bash
docker build -t fdia:local .
```

## Start the Container from a Local Image

Example:

```bash
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -v "$(pwd)/blink_config.json:/app/blink_config.json:rw" \
  -e TZ=Europe/Berlin \
  fdia:local
```

## Start the Container from GHCR

If the image is published by GitHub Actions, you can pull and run it from GitHub Container Registry.

Example:

```bash
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -v "$(pwd)/blink_config.json:/app/blink_config.json:rw" \
  -e TZ=Europe/Berlin \
  ghcr.io/oliverdrechsler/front_door_intercom_automation:latest
```

If you do not use Blink, remove the `blink_config.json` volume mapping.

## Recommended Volume Mappings

Typical mappings:

- `config.yaml` to `/app/config.yaml`
- `blink_config.json` to `/app/blink_config.json`

Example without Blink:

```bash
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -e TZ=Europe/Berlin \
  ghcr.io/oliverdrechsler/front_door_intercom_automation:latest
```

## Optional Fallback with `/dev/mem`

Some older environments may still require `/dev/mem`.

Example:

```bash
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --device /dev/gpiomem:/dev/gpiomem \
  --device /dev/mem:/dev/mem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -e TZ=Europe/Berlin \
  ghcr.io/oliverdrechsler/front_door_intercom_automation:latest
```

## Host Permission Notes

The host system must allow GPIO access.

Useful checks on the Raspberry Pi host:

```bash
ls -l /dev/gpiomem
getent group gpio
groups
```

If needed, add your host user to the `gpio` group:

```bash
sudo usermod -aG gpio "$USER"
```

Then log out and log in again so the group change takes effect.
