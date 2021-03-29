import unittest 
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from door.bell import Door 


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


class DoorTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher_os_isfile = patch('common.config_util.os.path.isfile', 
                                    return_value = False)
        self.patcher_os_path = patch('common.config_util.os.path.exists',
                                    return_value = False)
        
        self.patch_time = patch('door.bell.time.sleep', return_value=MagicMock())
        self.mock_time = self.patch_time.start()

        self.bot = MagicMock()
        self.blink = MagicMock()
        self.auth = MagicMock()

        self.patch_button = patch('door.bell.Button', return_value=MagicMock())
        self.mock_button = self.patch_button.start()
        
        self.patch_send_msg = patch('door.bell.send_msg.telegram_send_message', return_value=MagicMock())
        self.mock_send_msg = self.patch_send_msg.start()
        
        self.patch_choose_camera = patch('door.bell.cam_common.choose_camera', return_value=MagicMock())
        self.mock_choose_camera = self.patch_choose_camera.start()
        
        self.mock_os_isfile = self.patcher_os_isfile.start()
        with self.assertLogs('door-bell', level='DEBUG') as self.dl_log:
            self.instance_door = Door(self.bot, self.blink, self.auth)



    def tearDown(self):
        # self.patcher_logger.stop()
        self.patcher_os_isfile.stop()


    def test_Door_config(self):
        

        # self.mock_logger.assert_called()
        self.mock_os_isfile.assert_called()
        self.assertEqual (self.instance_door.bot,self.bot)
        self.assertEqual (self.instance_door.blink, self.blink)
        self.assertEqual (self.instance_door.auth, self.auth)
        self.assertEqual (self.instance_door.config, CONFIG_DICT)
        expected_log = ['DEBUG:door-bell:reading config']
        self.assertEqual(self.dl_log.output, expected_log)


    def test_ring(self, test=True):
        
        log1 = [
            'INFO:door-bell:start monitoring door bell',
            'DEBUG:door-bell:RPI: start endless loop doorbell monitoring',
            'INFO:door-bell:Door bell ringing'
        ]
        with self.assertLogs('door-bell', level='DEBUG') as self.ring_log:
            self.instance_door.ring(test=True)
        self.assertEqual(self.ring_log.output, log1)
        self.mock_button.assert_called()
        self.mock_send_msg.assert_called()
        self.mock_choose_camera.assert_called()
        log2 = [
            'INFO:door-bell:start monitoring door bell',
            'DEBUG:door-bell:NOT on RPI: start empty endless loop',
        ]

        self.instance_door.run_on_raspberry = False
        with self.assertLogs('door-bell', level='DEBUG') as self.ring_log:
            self.instance_door.ring(test=True)
        self.assertEqual(self.ring_log.output, log2)


