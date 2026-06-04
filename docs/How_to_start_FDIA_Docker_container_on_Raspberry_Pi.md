# How to start FDIA Docker container on Raspberry Pi

This document explains how to run the FDIA Docker container on a Raspberry Pi with GPIO access.

- [How to start FDIA Docker container on Raspberry Pi](#how-to-start-fdia-docker-container-on-raspberry-pi)
  - [Purpose](#purpose)
  - [Prerequisites](#prerequisites)
  - [Important GPIO requirement](#important-gpio-requirement)
  - [Required container rights for GPIO access](#required-container-rights-for-gpio-access)
  - [Prepare configuration files](#prepare-configuration-files)
  - [Build the container locally](#build-the-container-locally)
  - [Start the container from a local image](#start-the-container-from-a-local-image)
  - [Start the container from GHCR](#start-the-container-from-ghcr)
  - [Recommended volume mappings](#recommended-volume-mappings)
  - [Optional fallback with /dev/mem](#optional-fallback-with-devmem)
  - [Host permission notes](#host-permission-notes)
  - [Container behavior](#container-behavior)
  - [Logs](#logs)
  - [Update the container](#update-the-container)
  - [Troubleshooting](#troubleshooting)
  - [Recommendation](#recommendation)

## Purpose

The FDIA application can access Raspberry Pi GPIO pins for:
- door bell detection
- door opener relay control

Because Docker containers are isolated from the host system by default, GPIO access must be explicitly enabled when the container is started.

## Prerequisites

Required:
- Raspberry Pi
- Raspberry Pi OS or another Linux distribution running on the Pi
- Docker installed
- a valid `config.yaml`
- optional `blink_config.json` if Blink camera support is used

Check Docker:

```bash
docker --version
```

## Important GPIO requirement

The container needs access to the Raspberry Pi GPIO device.

Preferred device mapping:

```bash
--device /dev/gpiomem:/dev/gpiomem
```

Optional fallback for older systems:

```bash
--device /dev/mem:/dev/mem
```

If these devices are not provided, the container entrypoint stops with an error message.

## Required container rights for GPIO access

For this project, the container does not need full privileged mode.

Minimum required rights:
- device mapping for `/dev/gpiomem`
- a container user that can read and write that device

Recommended setup:
- run the container with `--device /dev/gpiomem:/dev/gpiomem`
- run the process as `root` inside the container

The current image starts as `root` by default. That is the simplest and most robust option for `RPi.GPIO`.

Not required in the normal case:
- `--privileged`
- `--cap-add SYS_RAWIO`
- `--cap-add ALL`
- host network mode only because of GPIO

Optional only for special legacy setups:
- `--device /dev/mem:/dev/mem`

If you intentionally run the container as a non-root user, that user must have access to the same numeric group as the mapped GPIO device on the host.

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

If you do not have a specific reason to run as non-root, use the default root user.

## Prepare configuration files

Create your configuration before starting the container:

```bash
cp config_template.yaml config.yaml
```

Then edit `config.yaml` with your real settings.

If Blink is used, also provide your `blink_config.json`.

## Build the container locally

From the project root:

```bash
docker build -t fdia:local .
```

## Start the container from a local image

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

## Start the container from GHCR

If the image was published by GitHub Actions, use the package from GHCR.

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

## Recommended volume mappings

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

## Optional fallback with /dev/mem

Some environments may still require `/dev/mem`.

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

## Host permission notes

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

Then log out and log in again.

Important distinction:
- the host user needs permission to talk to Docker
- the container process needs permission for `/dev/gpiomem`

With the default image, the container runs as `root`, so the main required runtime right is the `--device` mapping.

## Container behavior

The container starts `python fdia.py`.

Before the application starts, the entrypoint checks whether GPIO device access is available.

Default behavior:
- GPIO access is required
- startup fails if no GPIO device is available

Optional override:

```bash
-e FDIA_REQUIRE_GPIO=0
```

This is only useful for testing without real GPIO hardware.

## Logs

Show logs:

```bash
docker logs -f fdia
```

Stop container:

```bash
docker stop fdia
```

Remove container:

```bash
docker rm -f fdia
```

## Update the container

For a locally built image:

```bash
docker build -t fdia:local .
docker rm -f fdia
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -e TZ=Europe/Berlin \
  fdia:local
```

For an image from GHCR:

```bash
docker pull ghcr.io/oliverdrechsler/front_door_intercom_automation:latest
docker rm -f fdia
docker run -d \
  --name fdia \
  --restart unless-stopped \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -e TZ=Europe/Berlin \
  ghcr.io/oliverdrechsler/front_door_intercom_automation:latest
```

## Troubleshooting

### Error: GPIO device access is not available

Cause:
- `--device /dev/gpiomem:/dev/gpiomem` was not passed

Fix:
- start the container again with the GPIO device mapping

### Error: GPIO device exists but is not readable and writable inside the container

Cause:
- the container was started as a non-root user without the matching GPIO group

Fix:
- run the container with the default root user
- or add the host GPIO group with `--group-add "$(stat -c '%g' /dev/gpiomem)"`

### Container starts but door opener or bell detection does not work

Possible causes:
- wrong GPIO pin numbers in `config.yaml`
- hardware wiring issue
- host permissions are missing
- application is configured with `run_on_raspberry: false`

### Blink config file not found

Cause:
- `blink_config.json` is not mounted into `/app`

Fix:
- add the volume mapping or disable Blink usage in the config

## Recommendation

For productive Raspberry Pi usage:
- use `--restart unless-stopped`
- mount `config.yaml` from the host
- pass `/dev/gpiomem`
- keep the default container user `root` unless you have a specific hardening requirement
- only add `/dev/mem` if your setup actually needs it
- do not use `--privileged` unless you have a separate reason unrelated to FDIA GPIO access
