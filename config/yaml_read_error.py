class YamlReadError(Exception):
    """Exception raised for config yaml file read error.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="A YAML config file readerror" + " is occured during parsing file"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"
