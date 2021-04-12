import unittest 
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from messaging.receive_msg import TelegramMessages
from messaging.send_msg import telegram_send_message
import json

class TelegramMessagesTestCase(unittest.TestCase):
    def setUp(self):
        with open('test/expected_conf.json') as json_file:
            self.CONFIG_DICT = json.load(json_file)

        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_received_msg = json.load(json_file)

        self.patcher_os_isfile = patch('common.config_util.os.path.isfile', 
            return_value = False)
        self.patcher_os_path = patch('common.config_util.os.path.exists',
            return_value = False)

        self.bot = MagicMock()
        self.blink = MagicMock()
        self.auth = MagicMock()
        
        self.patch_verify_totp_code = patch('messaging.otp.verify_totp_code', return_value=MagicMock())
        self.mock_verify_totp_code = self.patch_verify_totp_code.start()

        self.patch_choose_camera = patch('camera.cam_common.choose_camera', return_value=MagicMock())
        self.mock_choose_camera = self.patch_choose_camera.start()
        self.patch_send_msg = patch('messaging.send_msg.telegram_send_message', return_value=MagicMock())
        self.mock_send_msg = self.patch_send_msg.start()

        self.patch_blink2FA = patch('camera.blink_cam.add_2fa_blink_token', return_value=MagicMock())
        self.mock_blink2FA = self.patch_blink2FA.start()
        self.patch_blink_compare_config = patch('camera.blink_cam.blink_compare_config', return_value=MagicMock())
        self.mock_blink_compare_config = self.patch_blink_compare_config.start()

        self.mock_os_isfile = self.patcher_os_isfile.start()
        
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.log1:
            self.instance_TelegramMessages = TelegramMessages(self.bot, self.blink, self.auth)    

    def tearDown(self):
        self.patcher_os_isfile.stop()
        self.patch_verify_totp_code.stop()
        self.patch_send_msg.stop()
        self.patch_choose_camera.stop()
        self.patch_blink2FA.stop()
        self.patch_blink_compare_config.stop()

    def test_telegram_messages_config(self):    
        self.mock_os_isfile.assert_called()
        self.assertEqual (self.instance_TelegramMessages.bot,self.bot)
        self.assertEqual (self.instance_TelegramMessages.blink, self.blink)
        self.assertEqual (self.instance_TelegramMessages.auth, self.auth)
        self.assertEqual (self.instance_TelegramMessages.config, self.CONFIG_DICT)
        expected_log1 = ['DEBUG:fdia_telegram:reading config']
        self.assertEqual(self.log1.output, expected_log1)

    def test_receive_msg_text_allowed_user_and_group_unwanted_text(self):
        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_received_msg = json.load(json_file)
        expected_log2 = [
                'INFO:fdia_telegram:received a telegram message',
                'DEBUG:fdia_telegram:receiving a message text in chat id -4321',
                'INFO:fdia_telegram:received message = test4',
                'INFO:fdia_telegram:chat msg allowed: chat_group_id -4321 is in config',
                'INFO:fdia_telegram:chat msg allowed: user FirstName with from_id 123456789 is in config',
                'DEBUG:fdia_telegram:text not matched checking for totp code',
                'DEBUG:fdia_telegram:regex search string',
                'DEBUG:fdia_telegram:no code number detected'
            ]
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.log2:
            self.instance_TelegramMessages.handle_received_message(self.mocked_received_msg)
        self.assertEqual(self.log2.output, expected_log2)
        self.assertEqual(self.instance_TelegramMessages.content_type,"text")
        self.assertEqual(str(self.instance_TelegramMessages.chat_id), self.instance_TelegramMessages.telegram_chat_nr)
        self.assertIn(str(self.instance_TelegramMessages.from_id), self.instance_TelegramMessages.allowed_user_ids)
        self.mock_verify_totp_code.assert_not_called()

    def test_receive_msg_text_allowed_user_and_group_with_foto_text(self):
        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_received_msg = json.load(json_file)
        self.mocked_received_msg['text'] = "foto"
        expected_log3 = [
            'INFO:fdia_telegram:received a telegram message', 
            'DEBUG:fdia_telegram:receiving a message text in chat id -4321', 
            'INFO:fdia_telegram:received message = foto', 
            'INFO:fdia_telegram:chat msg allowed: chat_group_id -4321 is in config', 
            'INFO:fdia_telegram:chat msg allowed: user FirstName with from_id 123456789 is in config', 
            'DEBUG:fdia_telegram:text match foto found'
            ]
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.log3:
            self.instance_TelegramMessages.handle_received_message(self.mocked_received_msg)
        self.assertEqual(self.log3.output, expected_log3)
        self.assertEqual(self.instance_TelegramMessages.content_type,"text")
        self.assertEqual(str(self.instance_TelegramMessages.chat_id), self.instance_TelegramMessages.telegram_chat_nr)
        self.assertIn(str(self.instance_TelegramMessages.from_id), self.instance_TelegramMessages.allowed_user_ids)
        self.mock_send_msg.assert_called()
        self.mock_choose_camera.assert_called()

    def test_receive_msg_unallowed_user(self):
        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_received_msg = json.load(json_file)
        self.mocked_received_msg['from']['id'] = 2342356
        expected_log4 = [
            'INFO:fdia_telegram:received a telegram message', 
            'DEBUG:fdia_telegram:receiving a message text in chat id -4321', 
            'INFO:fdia_telegram:received message = test4', 
            'INFO:fdia_telegram:chat msg allowed: chat_group_id -4321 is in config', 
            'INFO:fdia_telegram:chat msg denied: from user FirstName with from_id 2342356 is NOT in config'
            ]
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.log4:
            self.instance_TelegramMessages.handle_received_message(self.mocked_received_msg)
        self.assertEqual(self.log4.output, expected_log4)
        self.assertNotIn(str(self.instance_TelegramMessages.from_id), self.instance_TelegramMessages.allowed_user_ids)

    def test_receive_msg_unallowed_group(self):
        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_received_msg = json.load(json_file)
        self.mocked_received_msg['chat']['id'] = 3566
        expected_log5 = [
            'INFO:fdia_telegram:received a telegram message', 
            'DEBUG:fdia_telegram:receiving a message text in chat id 3566', 
            'INFO:fdia_telegram:received message = test4', 
            'INFO:fdia_telegram:chat msg denied: chat_id 3566 is not in config'
            ]
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.log5:
            self.instance_TelegramMessages.handle_received_message(self.mocked_received_msg)
        self.assertEqual(self.log5.output, expected_log5)
        self.assertNotEqual(str(self.instance_TelegramMessages.chat_id), self.instance_TelegramMessages.telegram_chat_nr)

    def test_receive_msg_text_allowed_user_and_group_with_blink_2FA_code_text(self):
        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_received_msg = json.load(json_file)
        self.mocked_received_msg['text'] = "blink 356632"
        expected_log6 = [
            'INFO:fdia_telegram:received a telegram message', 
            f"DEBUG:fdia_telegram:receiving a message text in chat id {self.CONFIG_DICT['telegram']['chat_number']}", 
            'INFO:fdia_telegram:received message = blink 356632',
            f"INFO:fdia_telegram:chat msg allowed: chat_group_id {self.CONFIG_DICT['telegram']['chat_number']} is in config", 
            f"INFO:fdia_telegram:chat msg allowed: user FirstName with from_id {self.CONFIG_DICT['telegram']['allowed_user_ids'][0]} is in config", 
            'DEBUG:fdia_telegram:text match blink found', 
            'INFO:fdia_telegram:blink token received - will save config'
            ]
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.log6:
            self.instance_TelegramMessages.handle_received_message(self.mocked_received_msg)
        self.assertEqual(self.log6.output, expected_log6)
        self.assertEqual(str(self.instance_TelegramMessages.chat_id), self.instance_TelegramMessages.telegram_chat_nr)
        self.mock_blink2FA.assert_called()
        self.mock_blink_compare_config.assert_called()

    # def test_receive_msg_none_text_allowed_user_and_group(self):

    # def test_receive_msg_text_allowed_user_and_group_with_totp_code_text(self):
        
        
