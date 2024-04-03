import pytest
import os
from unittest.mock import patch, mock_open
from configuration import Configuration, YamlReadError

class TestConfiguration:
    @patch("builtins.open", new_callable=mock_open, read_data="telegram: {token: '12345'}")
    @patch("os.path.isfile", return_value=True)
    def test_read_config(self, mock_isfile, mock_file):
        config = Configuration()
        assert config.telegram_token == '12345', "The Configuration class should correctly parse the configuration file"

    @patch("os.path.isfile", return_value=False)
    def test_no_config_file(self, mock_isfile):
        with pytest.raises(FileNotFoundError):
            Configuration()

    def test_base32_encode_totp_password(self):
        config = Configuration()
        encoded_password = config.base32_encode_totp_password("password")
        assert encoded_password == "KBQWY3DPO5XXE3DE", "The Configuration class should correctly encode a new password into BASE32 string"