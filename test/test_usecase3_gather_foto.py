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

        with open('test/mocked_send_msg.json') as json_file:
            self.send_msg_return = json.load(json_file)

        with open('test/mocked_received_msg.json') as json_file:
            self.mocked_receive_msg = json.load(json_file)

        self.patcher_os_isfile = patch('common.config_util.os.path.isfile', 
            return_value = False)
        self.mock_os_isfile = self.patcher_os_isfile.start()

        self.bot = MagicMock() 
        self.bot.sendMessage.return_value = self.send_msg_return
        self.bot.sendPhoto.return_value = self.send_msg_return

        self.blink = MagicMock()
        self.blink.cameras.snap_picture.return_value = True

        self.blink.refresh.return_value = True
        self.blink.setup_post_verify = MagicMock()
        self.blink.save = MagicMock()

        self.auth = MagicMock()
        self.auth.login_attributes = True

        self.auth.send_auth_key = MagicMock()
        
        self.patch_open_file1 = patch('messaging.send_msg.open', return_value=MagicMock())
        self.mock_open_send_msg = self.patch_open_file1.start()
        self.patch_open_file2 = patch('camera.blink_cam.open', return_value=MagicMock())
        self.mock_open_blink_cam = self.patch_open_file2.start()
        self.patch_json_load = patch('camera.blink_cam.json', return_value=MagicMock())
        self.mock_json_load = self.patch_json_load.start()
        self.mock_json_load.load.return_value = True


    def tearDown(self):
        self.patcher_os_isfile.stop()
        self.patch_open_file1.stop()
        self.patch_open_file2.stop()
        self.patch_json_load.stop()
        
    def test_usecase3_gather_foto_from_front_door(self):    
        """UseCase 3 tests includes:

        receive telegram message,
        check if telegrom text message has foto request,
        send telegram message foto snapshot will be took,
        take a blink cam foto snapshot,
        send foto via telegram back.
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

        self.mocked_receive_msg['text'] = "foto"
        expected_method_log = [
            'INFO:fdia_telegram:received a telegram message', 
            f"DEBUG:fdia_telegram:receiving a message text in chat id {self.CONFIG_DICT['telegram']['chat_number']}", 
            'INFO:fdia_telegram:received message = foto', 
            f"INFO:fdia_telegram:chat msg allowed: chat_group_id {self.CONFIG_DICT['telegram']['chat_number']} is in config", 
            f"INFO:fdia_telegram:chat msg allowed: user FirstName with from_id {self.CONFIG_DICT['telegram']['allowed_user_ids'][0]} is in config", 
            'DEBUG:fdia_telegram:text match foto found', 
            'DEBUG:telegram thread:Foto request received', 
            'INFO:send_telegram_msg:send message : I will send a foto!', 
            'DEBUG:cam_common:choose camera', 
            'DEBUG:cam_common:blink cam choosen', 
            'INFO:cam_common:take a Blink Cam snapshot', 
            "INFO:blink_cam:i'll take a snapshot from cam Blink_Camera_name_here and store it here /tmp/foto.jpg", 
            'DEBUG:blink_cam:create a camera instance', 
            'DEBUG:blink_cam:take a snpshot', 
            'DEBUG:blink_cam:refresh blink server info', 
            'INFO:blink_cam:saving blink foto', 
            'DEBUG:blink_cam:load blink config file', 
            'DEBUG:blink_cam:saved blink config file == running config', 
            'INFO:send_telegram_msg:send a foto: success'
            ]
        with self.assertLogs(level='DEBUG') as self.method_log:
            self.instance_TelegramMessages.handle_received_message(self.mocked_receive_msg)
        self.assertEqual(self.method_log.output, expected_method_log)
        self.assertEqual(self.instance_TelegramMessages.content_type,"text")
        self.assertEqual(str(self.instance_TelegramMessages.chat_id), self.instance_TelegramMessages.telegram_chat_nr)
        self.assertIn(str(self.instance_TelegramMessages.from_id), self.instance_TelegramMessages.allowed_user_ids)        
        self.blink.cameras.__getitem__.assert_called_with('Blink_Camera_name_here')
        self.blink.cameras.__getitem__().snap_picture.assert_called()
        self.blink.refresh.assert_called()
        self.blink.cameras.__getitem__().image_to_file.assert_called_with('/tmp/foto.jpg')
        self.bot.sendPhoto.assert_called()
