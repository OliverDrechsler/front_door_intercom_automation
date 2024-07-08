from enum import Enum
class DefaultCam(str, Enum):
    """A custom enumeration that is YAML-safe."""
    PICAM = "picam"
    BLINK = "BLINK"