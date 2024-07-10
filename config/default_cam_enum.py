from enum import Enum
class DefaultCam(str, Enum):
    """A custom enumeration that is YAML-safe."""
    PICAM = "PICAM"
    BLINK = "BLINK"