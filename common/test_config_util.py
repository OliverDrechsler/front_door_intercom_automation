import unittest 
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from common.config_util import Configuration, YamlReadError

CONFIG_DICT = {
            'telegram': {
                'token': 'telegram_bot_token_code_here',
                'chat_number': '-GroupChatNumber', 
                'allowed_user_ids': ['123456789', '987654321']
                }, 
            'otp': {
                'password': 'Base32CodePasswordHere', 
                'length': 6, 
                'interval': 30, 
                'hash_type': 'hashlib.sha1'
                }, 
            'GPIO': {
                'door_bell_port': 1, 
                'door_opener_port': 2
                }, 
            'blink': {
                'username': 'blink_account_email_address_here', 
                'password': 'blink_account_password_here', 
                'name': 'Blink_Camera_name_here', 
                'config_file': 'blink_config.json'
                }, 
            'picam': {
                'url': 'http://IP:8000/foto/', 
                'image_width': 640, 
                'image_hight': 480, 
                'image_filename': 'foto.jpg', 
                'exposure': 'auto', 
                'rotation': 0, 
                'iso': 0
                }, 
            'common': {
                'image_path': '/tmp/foto.jpg', 
                'camera_type': 'blink', 
                'run_on_raspberry': True
                }
            }


class FDIaTestCase(unittest.TestCase):

    def setUp(self):
        self.patcher_os_isfile = patch('common.config_util.os.path.isfile', 
                                    return_value = False)
        self.patcher_os_path = patch('common.config_util.os.path.exists',
                                    return_value = False)

        self.mock_os_isfile = self.patcher_os_isfile.start()
        # self.patcher_logger = patch('logging.getLogger', 
        #                         autospec=True)
        # self.mock_logger = self.patcher_logger.start()
        with self.assertLogs('config', level='DEBUG') as self.dl_log:
            self.instance_configuration = Configuration()
        
    def tearDown(self):
        # self.patcher_logger.stop()
        self.patcher_os_isfile.stop()

    def test_Configuration(self):
        # self.mock_logger.assert_called()
        self.mock_os_isfile.assert_called()
        self.assertEqual (self.instance_configuration.telegram_token,"telegram_bot_token_code_here")
        self.assertEqual (self.instance_configuration.telegram_chat_nr, "-GroupChatNumber")
        self.assertEqual (self.instance_configuration.allowed_user_ids, ['123456789', '987654321'])
        self.assertEqual (self.instance_configuration.otp_password, 'Base32CodePasswordHere')
        self.assertEqual (self.instance_configuration.otp_length, 6)
        self.assertEqual (self.instance_configuration.otp_interval, 30)
        self.assertEqual (self.instance_configuration.hash_type, "hashlib.sha1")
        self.assertEqual (self.instance_configuration.door_bell, 1)
        self.assertEqual (self.instance_configuration.door_summer, 2)
        self.assertEqual (self.instance_configuration.blink_username, 'blink_account_email_address_here')
        self.assertEqual (self.instance_configuration.blink_password, 'blink_account_password_here')
        self.assertEqual (self.instance_configuration.blink_name, 'Blink_Camera_name_here')
        self.assertEqual (self.instance_configuration.blink_config_file, self.instance_configuration.base_path + "blink_config.json")
        self.assertEqual (self.instance_configuration.common_image_path, "/tmp/foto.jpg")
        self.assertEqual (self.instance_configuration.common_camera_type, 'blink')
        self.assertEqual (self.instance_configuration.picam_url, 'http://IP:8000/foto/')
        self.assertEqual (self.instance_configuration.picam_image_width, 640)
        self.assertEqual (self.instance_configuration.picam_image_hight, 480)
        self.assertEqual (self.instance_configuration.picam_image_filename, "foto.jpg")
        self.assertEqual (self.instance_configuration.picam_exposure, 'auto')
        self.assertEqual (self.instance_configuration.picam_rotation, 0)
        self.assertEqual (self.instance_configuration.picam_iso, 0)
        self.assertEqual (self.instance_configuration.run_on_raspberry, True)
        self.assertEqual (self.instance_configuration.config, CONFIG_DICT)
        expected_log = [
            'DEBUG:config:checking if config.yaml file exists', 
            'INFO:config:No config.yaml file detected. Using temeplate one.', 
            'DEBUG:config:reading config {} file info dict'.format(self.instance_configuration.base_path + 'config_template.yaml')
        ]
        self.assertEqual(self.dl_log.output, expected_log)

    def test_define_config_file_with_exception(self):
        self.patcher_os_path.start()
        self.assertEqual(self.instance_configuration.config_file, self.instance_configuration.base_path + 'config_template.yaml')
        with self.assertRaises(NameError):
            self.instance_configuration.define_config_file()
        # with pytest.raises(NameError) as excinfo:
        #     self.instance_configuration.define_config_file()
        # excinfo.match("No config file found!")
        self.patcher_os_path.stop()

    def test_read_config_file_exception(self):
        with patch ("builtins.open") as patched_open:
            with pytest.raises(FileNotFoundError) as excinfo:
                patched_open.side_effect = FileNotFoundError()
                self.instance_configuration.read_config(self.instance_configuration.config_file)
            excinfo.match("Could not find config file")

            with pytest.raises(YamlReadError) as excinfo:
                patched_open.side_effect = YamlReadError()
                self.instance_configuration.read_config(self.instance_configuration.config_file)
            excinfo.match("a YAML error is occured during parsing file")

    def test_Configuration_with_original_config_yaml(self):
        self.patcher_os_isfile.stop()
        self.instance_configuration.config_file = self.instance_configuration.define_config_file()
        self.assertEqual(self.instance_configuration.config_file, self.instance_configuration.base_path + 'config.yaml')
        self.patcher_os_isfile.start()

