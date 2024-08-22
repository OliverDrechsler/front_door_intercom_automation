import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import yaml
import pyotp
from click.testing import CliRunner
from tools.totp_helper_cli import define_config_file, read_config, get_otp, verify_otp, cli

class TestTOTPHelperCLI(unittest.TestCase):

    @patch('os.path.isfile')
    def test_define_config_file(self, mock_isfile):
        # Simulate different scenarios for the config file location
        mock_isfile.side_effect = lambda path: path.endswith('config.yaml')
        self.assertEqual(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/tools/config.yaml", define_config_file())

        mock_isfile.side_effect = lambda path: path.endswith('config_template.yaml')
        self.assertEqual(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/tools/config_template.yaml", define_config_file())

        mock_isfile.side_effect = lambda path: False
        with self.assertRaises(NameError):
            define_config_file()

    @patch('builtins.open', new_callable=mock_open, read_data='otp:\n  password: secret\n  length: 6\n  interval: 30\n  hash_type: sha1')
    @patch('yaml.safe_load')
    def test_read_config(self, mock_yaml_load, mock_file):
        mock_yaml_load.return_value = {'otp': {'password': 'secret', 'length': 6, 'interval': 30, 'hash_type': 'sha1'}}
        config = read_config('dummy_path')
        mock_file.assert_called_with(file='dummy_path', mode='r')
        self.assertEqual(config['otp']['password'], 'secret')
        self.assertEqual(config['otp']['length'], 6)

    @patch('tools.totp_helper_cli.read_config')
    @patch('tools.totp_helper_cli.define_config_file')
    @patch('pyotp.TOTP.now')
    def test_get_otp(self, mock_otp_now, mock_define_config_file, mock_read_config):
        mock_define_config_file.return_value = 'dummy_path'
        mock_read_config.return_value = {'otp': {'password': 'secret', 'length': 6, 'interval': 30, 'hash_type': 'sha1'}}
        mock_otp_now.return_value = '123456'

        runner = CliRunner()
        result = runner.invoke(get_otp)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('123456', result.output)

    @patch('tools.totp_helper_cli.read_config')
    @patch('tools.totp_helper_cli.define_config_file')
    @patch('pyotp.TOTP.verify')
    def test_verify_otp(self, mock_otp_verify, mock_define_config_file, mock_read_config):
        mock_define_config_file.return_value = 'dummy_path'
        mock_read_config.return_value = {'otp': {'password': 'secret', 'length': 6, 'interval': 30, 'hash_type': 'sha1'}}
        mock_otp_verify.return_value = True

        runner = CliRunner()
        result = runner.invoke(verify_otp, ['123456'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('OTP is valid', result.output)

        mock_otp_verify.return_value = False
        result = runner.invoke(verify_otp, ['123456'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('OTP is invalid', result.output)

if __name__ == '__main__':
    unittest.main()
