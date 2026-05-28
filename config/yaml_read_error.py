class YamlReadError(Exception):
    """Exception raised for config yaml file read error.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="A YAML config file readerror is occured during parsing file"):
        super().__init__(message)
