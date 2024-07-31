import unittest
from unittest.mock import patch, mock_open, MagicMock
import yaml
from config.default_cam_enum import DefaultCam
from config.yaml_read_error import YamlReadError
from config.config_util import Configuration
import base64

import time


class TestConfiguration(unittest.TestCase):

    @patch('config.config_util.Configuration.get_base_path')
    @patch('config.config_util.Configuration.read_config')
    @patch('config.config_util.Configuration.define_config_file')
    @patch('telebot.TeleBot', autospec=True)
    def setUp(self, mock_telebot, mock_define_config_file, mock_read_config, mock_get_base_path):
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
                'door_bell_port': 1,
                'door_opener_port': 2,
                'testing_msg': True
            },
            'photo_general': {
                'image_path': '/path/to/image',
                'default_camera_type': 'blink',
                'enable_detect_daylight': True
            },
            'blink': {
                'enabled': True,
                'username': 'dummy_user',
                'password': 'dummy_pass',
                'name': 'dummy_blink',
                'config_file': 'blink_config.yaml',
                'night_vision': True
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
                'night_vision': True
            },
            'web': {
                'flask_web_host': '0.0.0.0',
                'flask_web_port': 5000,
                'flask_secret_key': 'dummy_secret',
                'browser_session_cookie_lifetime': 3600,
                'flask_users': [{'user1': 'id1'}, {'user2': 'id2'}]
            }
        }
        mock_get_base_path.return_value = '/dummy/base/path/'
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
        self.assertEqual(self.config.flask_web_port, 5000)
        self.assertEqual(self.config.flask_secret_key, 'dummy_secret')
        self.assertEqual(self.config.flask_browser_session_cookie_lifetime, 3600)
        self.assertEqual(self.config.web_user_dict, {'user1': 'id1', 'user2': 'id2'})

    @patch('os.path.isfile', return_value=True)
    def test_define_config_file_exists(self, mock_isfile):
        config_file = self.config.define_config_file()
        self.assertEqual(config_file, '/dummy/base/path/config.yaml')

    @patch('os.path.isfile', return_value=False)
    @patch('os.path.exists', return_value=True)
    def test_define_config_file_template_exists(self, mock_exists, mock_isfile):
        config_file = self.config.define_config_file()
        self.assertEqual(config_file, '/dummy/base/path/config_template.yaml')

    @patch('os.path.isfile', return_value=False)
    @patch('os.path.exists', return_value=False)
    def test_define_config_file_not_exists(self, mock_exists, mock_isfile):
        with self.assertRaises(NameError):
            self.config.define_config_file()

    def test_base32_encode_totp_password(self):
        encoded_password = self.config.base32_encode_totp_password('new_password')
        self.assertEqual(encoded_password, base64.b32encode('NEW_PASSWORD'.encode('UTF-8')).decode('UTF-8'))

    @patch('builtins.open', new_callable=mock_open)
    def test_write_yaml_config(self, mock_file):
        self.config.write_yaml_config('new_password')
        mock_file.assert_called_with('/dummy/base/path/config.yaml', 'w')
        self.assertEqual(self.config.config['otp']['password'], base64.b32encode('NEW_PASSWORD'.encode('UTF-8')).decode('UTF-8'))


if __name__ == '__main__':
    unittest.main()
