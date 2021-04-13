import unittest 
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from messaging.receive_msg import TelegramMessages
from messaging.send_msg import telegram_send_message
from messaging.otp import generate_totp_code
import json

class TelegramMessagesTestCase(unittest.TestCase):
    def setUp(self):
        with open('test/expected_conf.json') as json_file:
            self.CONFIG_DICT = json.load(json_file)

        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_receive_msg_totp_code = json.load(json_file)

        self.patcher_os_isfile = patch('common.config_util.os.path.isfile', 
            return_value = False)
        self.mock_os_isfile = self.patcher_os_isfile.start()

        self.bot = MagicMock()
        self.blink = MagicMock()
        self.auth = MagicMock()
        
    def tearDown(self):
        self.patcher_os_isfile.stop()
        # self.patch_verify_totp_code.stop()
        
    def test_usecase2_open_door_after_received_correct_totp_code(self):    
        """UseCase 2 tests includes:

        receive telegram message,
        check if telegrom text message matches totp code,
        response telegram message that door will be opened
        call RPI GPIO to open door.
        """

        # prepare telegram config class
        with self.assertLogs('fdia_telegram', level='DEBUG') as self.instance_log:
            self.instance_TelegramMessages = TelegramMessages(self.bot, self.blink, self.auth)    
        self.mock_os_isfile.assert_called()
        self.assertEqual (self.instance_TelegramMessages.bot,self.bot)
        self.assertEqual (self.instance_TelegramMessages.blink, self.blink)
        self.assertEqual (self.instance_TelegramMessages.auth, self.auth)
        self.assertEqual (self.instance_TelegramMessages.config, self.CONFIG_DICT)
        expected_instance_log = ['DEBUG:fdia_telegram:reading config']
        self.assertEqual(self.instance_log.output, expected_instance_log)
        # generate new totp code
        new_totp = generate_totp_code(self.instance_TelegramMessages.otp_password,
                            self.instance_TelegramMessages.otp_length, 
                            self.instance_TelegramMessages.otp_interval, 
                            self.instance_TelegramMessages.hash_type)
        # set code not to run on RPi
        self.instance_TelegramMessages.run_on_raspberry = False
        # set new totp code to be received
        self.mocked_receive_msg_totp_code['text'] = new_totp
        # define expected log output
        expected_method_log = [
            'INFO:fdia_telegram:received a telegram message', 
            f"DEBUG:fdia_telegram:receiving a message text in chat id {self.CONFIG_DICT['telegram']['chat_number']}", 
            f"INFO:fdia_telegram:received message = {new_totp}", 
            f"INFO:fdia_telegram:chat msg allowed: chat_group_id {self.CONFIG_DICT['telegram']['chat_number']} is in config", 
            f"INFO:fdia_telegram:chat msg allowed: user FirstName with from_id {self.CONFIG_DICT['telegram']['allowed_user_ids'][0]} is in config", 
            'DEBUG:fdia_telegram:text not matched checking for totp code', 
            'DEBUG:fdia_telegram:regex search string', 
            'DEBUG:TOTP:verify totp with library passlib', 
            f"INFO:fdia_telegram:{new_totp} TOTP code correct", 
            'INFO:send_telegram_msg:send message : Code accepted.',
            'INFO:door-opener:not running on raspberry pi - will not open the door', 
            'INFO:fdia_telegram:Door opened for 5 Sec.'
            ]
        # run code test
        with self.assertLogs(level='DEBUG') as self.method_log:
            self.instance_TelegramMessages.handle_received_message(self.mocked_receive_msg_totp_code)
        # check expected results
        self.assertEqual(self.method_log.output, expected_method_log)
        self.assertEqual(self.instance_TelegramMessages.content_type,"text")
        self.assertEqual(str(self.instance_TelegramMessages.chat_id), self.instance_TelegramMessages.telegram_chat_nr)
        self.assertIn(str(self.instance_TelegramMessages.from_id), self.instance_TelegramMessages.allowed_user_ids)        
        # print(self.method_log.output)
        # print(" ")
        # print(self.blink.call_args_list)
        # print(self.blink.method_calls)
        # print(self.blink.mock_calls)
