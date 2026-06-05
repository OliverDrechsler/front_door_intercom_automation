import unittest
from unittest.mock import patch, mock_open
import yaml
from config.default_cam_enum import DefaultCam
from config.yaml_read_error import YamlReadError
from config.config_util import Configuration
import base64


class TestConfiguration(unittest.TestCase):

    @patch('config.config_util.Configuration._Configuration__get_bundle_base_path')
    @patch('config.config_util.Configuration._Configuration__get_base_path')
    @patch('config.config_util.Configuration._Configuration__read_config')
    @patch('config.config_util.Configuration._Configuration__define_config_file')
    @patch('telebot.TeleBot', autospec=True)
    def setUp(self, mock_telebot, mock_define_config_file, mock_read_config, mock_get_base_path,
              mock_get_bundle_base_path):
        self.mock_config = {
            'telegram': {
                'token': 'dummy_token',
                'chat_number': 12345,
                'allowed_user_ids': [67890]
            },
            'otp': {
                'password': 'dummy_password',
                'length': 6,
                'interval': 30,
                'hash_type': 'SHA1'
            },
            'GPIO': {
                'run_on_raspberry': True,
                'enable_door_bell_port': True,
                'enable_door_opener_port': True,
                'door_bell_port': 1,
                'door_bell_bounce_time': 5,
                'door_opener_port': 2,
                'testing_msg': True
            },
            'photo_general': {
                'image_path': '/path/to/image',
                'default_camera_type': 'blink',
                'enable_detect_daylight': True,
                'timezone': 'Europe/Berlin',
                'country': 'Germany',
                'city': 'Berlin',
                'lat': 1.1111111,
                'lon': 2.2222222,
                'brightness_enhancer': 3,
                'contrast_enhancer': 2
            },
            'blink': {
                'enabled': True,
                'username': 'dummy_user',
                'password': 'dummy_pass',
                'name': 'dummy_blink',
                'config_file': 'blink_config.yaml',
                'night_vision': True,
                'image_brightening': True
            },
            'picam': {
                'enabled': True,
                'url': 'http://picam.url',
                'image_width': 640,
                'image_hight': 480,
                'image_filename': 'picam_image.jpg',
                'exposure': 'auto',
                'rotation': 90,
                'iso': 100,
                'night_vision': True,
                'image_brightening': True
            },
            'web': {
                'enabled': True,
                'flask_web_host': '0.0.0.0',
                'flask_web_port': 5000,
                'flask_secret_key': 'dummy_secret',
                'browser_session_cookie_lifetime': 3600,
                'session_cookie_secure': False,
                'flask_users': [{'user1': 'id1'}, {'user2': 'id2'}]
            }
        }
        mock_get_base_path.return_value = '/dummy/base/path/'
        mock_get_bundle_base_path.return_value = '/dummy/bundle/path/'
        mock_define_config_file.return_value = '/dummy/base/path/config.yaml'
        mock_read_config.return_value = self.mock_config

        self.config = Configuration()

    def test_initialization(self):
        self.assertEqual(self.config.telegram_token, 'dummy_token')
        self.assertEqual(self.config.telegram_chat_nr, 12345)
        self.assertEqual(self.config.allowed_user_ids, [67890])
        self.assertEqual(self.config.otp_password, 'dummy_password')
        self.assertEqual(self.config.otp_length, 6)
        self.assertEqual(self.config.otp_interval, 30)
        self.assertEqual(self.config.hash_type, 'SHA1')
        self.assertEqual(self.config.run_on_raspberry, True)
        self.assertEqual(self.config.door_bell, 1)
        self.assertEqual(self.config.door_summer, 2)
        self.assertEqual(self.config.door_bell_enabled, True)
        self.assertEqual(self.config.door_bell_bounce_time, 5)
        self.assertEqual(self.config.door_summer_enabled, True)
        self.assertEqual(self.config.photo_image_path, '/path/to/image')
        self.assertEqual(DefaultCam.BLINK, self.config.default_camera_type)
        self.assertEqual(self.config.enable_detect_daylight, True)
        self.assertEqual(self.config.blink_enabled, True)
        self.assertEqual(self.config.blink_username, 'dummy_user')
        self.assertEqual(self.config.blink_password, 'dummy_pass')
        self.assertEqual(self.config.blink_name, 'dummy_blink')
        self.assertEqual(self.config.blink_config_file, '/dummy/base/path/blink_config.yaml')
        self.assertEqual(self.config.blink_night_vision, True)
        self.assertEqual(self.config.picam_enabled, True)
        self.assertEqual(self.config.picam_url, 'http://picam.url')
        self.assertEqual(self.config.picam_image_width, 640)
        self.assertEqual(self.config.picam_image_hight, 480)
        self.assertEqual(self.config.picam_image_filename, 'picam_image.jpg')
        self.assertEqual(self.config.picam_exposure, 'auto')
        self.assertEqual(self.config.picam_rotation, 90)
        self.assertEqual(self.config.picam_iso, 100)
        self.assertEqual(self.config.picam_night_vision, True)
        self.assertEqual(self.config.picam_image_brightening, True)
        self.assertEqual(self.config.flask_enabled, True)
        self.assertEqual(self.config.flask_web_host, '0.0.0.0')
        self.assertEqual(self.config.flask_web_port, 5000)
        self.assertEqual(self.config.flask_secret_key, 'dummy_secret')
        self.assertEqual(self.config.flask_browser_session_cookie_lifetime, 3600)
        self.assertFalse(self.config.flask_session_cookie_secure)
        self.assertEqual(self.config.web_user_dict, {'user1': 'id1', 'user2': 'id2'})

    @patch('os.getcwd', return_value='/launch/path')
    @patch('os.path.isfile', side_effect=lambda path: path == '/launch/path/config.yaml')
    def test_define_config_file_prefers_launch_dir(self, mock_isfile, mock_getcwd):
        config_file = self.config._Configuration__define_config_file()
        self.assertEqual(config_file, '/launch/path/config.yaml')

    @patch('os.getcwd', return_value='/launch/path')
    @patch('os.path.isfile', side_effect=lambda path: path == '/dummy/base/path/config.yaml')
    def test_define_config_file_uses_base_path_when_launch_config_missing(self, mock_isfile, mock_getcwd):
        config_file = self.config._Configuration__define_config_file()
        self.assertEqual(config_file, '/dummy/base/path/config.yaml')

    @patch('os.getcwd', return_value='/launch/path')
    @patch('os.path.isfile', return_value=False)
    @patch('os.path.exists', side_effect=lambda path: path == '/launch/path/config_template.yaml')
    def test_define_config_file_template_exists(self, mock_exists, mock_isfile, mock_getcwd):
        config_file = self.config._Configuration__define_config_file()
        self.assertEqual(config_file, '/launch/path/config_template.yaml')

    @patch('os.getcwd', return_value='/launch/path')
    @patch('os.path.isfile', return_value=False)
    @patch('os.path.exists', return_value=False)
    def test_define_config_file_not_exists(self, mock_exists, mock_isfile, mock_getcwd):
        with self.assertRaises(NameError):
            self.config._Configuration__define_config_file()

    def test_base32_encode_totp_password(self):
        encoded_password = self.config._Configuration__base32_encode_totp_password('new_password')
        self.assertEqual(encoded_password, base64.b32encode('NEW_PASSWORD'.encode('UTF-8')).decode('UTF-8'))

    @patch('builtins.open', new_callable=mock_open)
    def test_write_yaml_config(self, mock_file):
        self.config._Configuration__write_yaml_config('new_password')
        mock_file.assert_called_with('/dummy/base/path/config.yaml', 'w')
        self.assertEqual(self.config.config['otp']['password'], base64.b32encode('NEW_PASSWORD'.encode('UTF-8')).decode('UTF-8'))

    @patch('builtins.open', new_callable=mock_open)
    def test_write_yaml_config_uses_loaded_config_file(self, mock_file):
        self.config.config_file = '/dummy/base/path/custom.yaml'

        self.config._Configuration__write_yaml_config('new_password')

        mock_file.assert_called_with('/dummy/base/path/custom.yaml', 'w')

    def test_resolve_runtime_path_uses_config_dir_for_relative_files(self):
        self.config.config_dir = '/dummy/runtime'

        result = self.config._Configuration__resolve_runtime_path('blink_config.yaml')

        self.assertEqual(result, '/dummy/runtime/blink_config.yaml')

    def test_resolve_runtime_path_preserves_absolute_paths(self):
        result = self.config._Configuration__resolve_runtime_path('/absolute/blink_config.yaml')

        self.assertEqual(result, '/absolute/blink_config.yaml')

    def test_get_web_user_dict_empty(self):
        self.config.config["web"]["flask_users"] = []

        result = self.config._Configuration__get_web_user_dict()

        self.assertEqual(result, {})

    def test_get_web_user_dict_invalid_type(self):
        self.config.config["web"]["flask_users"] = "invalid"

        with self.assertRaises(YamlReadError):
            self.config._Configuration__get_web_user_dict()

    def test_get_web_user_dict_invalid_entry(self):
        self.config.config["web"]["flask_users"] = [{"user1": "id1"}, "invalid"]

        with self.assertRaises(YamlReadError):
            self.config._Configuration__get_web_user_dict()

    @patch('builtins.open', new_callable=mock_open, read_data='invalid: [yaml')
    @patch('yaml.load', side_effect=yaml.YAMLError('parse error'))
    def test_read_config_yaml_error(self, mock_yaml_load, mock_file):
        with self.assertRaises(YamlReadError):
            self.config._Configuration__read_config('/dummy/base/path/config.yaml')

    @patch('builtins.open', side_effect=PermissionError('denied'))
    def test_read_config_permission_error_is_not_masked(self, mock_file):
        with self.assertRaises(PermissionError):
            self.config._Configuration__read_config('/dummy/base/path/config.yaml')


if __name__ == '__main__':
    unittest.main()
