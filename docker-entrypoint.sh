#!/bin/sh
set -eu

if [ "${FDIA_REQUIRE_GPIO:-1}" = "1" ]; then
    GPIO_DEVICE=""

    if [ -e /dev/gpiomem ]; then
        GPIO_DEVICE="/dev/gpiomem"
    elif [ -e /dev/mem ]; then
        GPIO_DEVICE="/dev/mem"
    fi

    if [ -z "${GPIO_DEVICE}" ]; then
        echo "GPIO device access is not available." >&2
        echo "Start the container on Raspberry Pi with at least:" >&2
        echo "  --device /dev/gpiomem:/dev/gpiomem" >&2
        echo "Optional fallback for older setups:" >&2
        echo "  --device /dev/mem:/dev/mem" >&2
        exit 1
    fi

    if [ ! -r "${GPIO_DEVICE}" ] || [ ! -w "${GPIO_DEVICE}" ]; then
        echo "GPIO device exists but is not readable and writable inside the container: ${GPIO_DEVICE}" >&2
        echo "Required:" >&2
        echo "  - run the container as root" >&2
        echo "    or" >&2
        echo "  - run with a matching gpio group inside the container" >&2
        echo "Recommended start option:" >&2
        echo "  --device /dev/gpiomem:/dev/gpiomem" >&2
        echo "If you use a non-root container user, also add the host gpio group GID via --group-add." >&2
        exit 1
    fi
fi

exec "$@"
