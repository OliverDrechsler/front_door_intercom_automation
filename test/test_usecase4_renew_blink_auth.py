import unittest
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from messaging.receive_msg import TelegramMessages
from messaging.send_msg import telegram_send_message
import json


class TelegramMessagesTestCase(unittest.TestCase):
    def setUp(self):
        with open("test/expected_conf.json") as json_file:
            self.CONFIG_DICT = json.load(json_file)

        with open("test/mocked_send_msg.json") as json_file:
            self.send_msg_return = json.load(json_file)

        with open("test/mocked_received_msg.json") as json_file:
            self.mocked_receive_msg = json.load(json_file)

        self.patcher_os_isfile = patch(
            "common.config_util.os.path.isfile", return_value=False
        )
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
        self.auth.login_attributes = False
        self.auth.send_auth_key = MagicMock()

        self.patch_open_file1 = patch(
            "messaging.send_msg.open", return_value=MagicMock()
        )
        self.mock_open_send_msg = self.patch_open_file1.start()
        self.patch_open_file2 = patch("camera.blink_cam.open", return_value=MagicMock())
        self.mock_open_blink_cam = self.patch_open_file2.start()
        self.patch_json_load = patch("camera.blink_cam.json", return_value=MagicMock())
        self.mock_json_load = self.patch_json_load.start()
        self.mock_json_load.load.return_value = True

    def tearDown(self):
        self.patcher_os_isfile.stop()
        self.patch_open_file1.stop()
        self.patch_open_file2.stop()
        self.patch_json_load.stop()

    def test_usecase3_gather_foto_from_front_door(self):
        """UseCase 4 tests includes:

        receive telegram message,
        check if telegram text message has blink token,
        add / update blink token to blink_config file,
        send telegram message about blink config update.
        """

        # prepare telegram config class
        with self.assertLogs("fdia_telegram", level="DEBUG") as self.instance_log:
            self.instance_TelegramMessages = TelegramMessages(
                self.bot, self.blink, self.auth
            )
        self.mock_os_isfile.assert_called()
        self.assertEqual(self.instance_TelegramMessages.bot, self.bot)
        self.assertEqual(self.instance_TelegramMessages.blink, self.blink)
        self.assertEqual(self.instance_TelegramMessages.auth, self.auth)
        self.assertEqual(self.instance_TelegramMessages.config, self.CONFIG_DICT)
        expected_instance_log = ["DEBUG:fdia_telegram:reading config"]
        self.assertEqual(self.instance_log.output, expected_instance_log)

        self.mocked_receive_msg["text"] = "blink 123456"
        expected_method_log = [
            "INFO:fdia_telegram:received a telegram message",
            f"DEBUG:fdia_telegram:receiving a message text in chat id {self.CONFIG_DICT['telegram']['chat_number']}",
            "INFO:fdia_telegram:received message = blink 123456",
            f"INFO:fdia_telegram:chat msg allowed: chat_group_id {self.CONFIG_DICT['telegram']['chat_number']} is in config",
            f"INFO:fdia_telegram:chat msg allowed: user FirstName with from_id {self.CONFIG_DICT['telegram']['allowed_user_ids'][0]} is in config",
            "DEBUG:fdia_telegram:search_key: blink in message: blink 123456",
            "DEBUG:fdia_telegram:text match blink found",
            "INFO:fdia_telegram:blink token received - will save config",
            "INFO:send_telegram_msg:send message : Blink token received 123456",
            "DEBUG:blink_cam:add a 2FA token for authentication",
            "DEBUG:blink_cam:verify 2FA token",
            "INFO:blink_cam:added 2FA token 123456",
            "DEBUG:blink_cam:load blink config file",
            "DEBUG:blink_cam:saved blink config file differs from running config",
            "DEBUG:blink_cam:blink config object = False",
            "DEBUG:blink_cam:blink config file   = True",
            "INFO:blink_cam:will update blink config file",
            "INFO:blink_cam:saving blink authenticated session infos into config file",
        ]

        with self.assertLogs(level="DEBUG") as self.method_log:
            self.instance_TelegramMessages.handle_received_message(
                self.mocked_receive_msg
            )
        self.assertEqual(self.method_log.output, expected_method_log)
        self.assertEqual(self.instance_TelegramMessages.content_type, "text")
        self.assertEqual(
            str(self.instance_TelegramMessages.chat_id),
            self.instance_TelegramMessages.telegram_chat_nr,
        )
        self.assertIn(
            str(self.instance_TelegramMessages.from_id),
            self.instance_TelegramMessages.allowed_user_ids,
        )
        self.blink.setup_post_verify.assert_called()
        self.blink.save.assert_called()
        self.auth.send_auth_key.assert_called()
        # print(self.method_log.output)
        # print(" ")
        # print(self.blink.call_args_list)
        # print(self.blink.method_calls)
        # print(self.blink.mock_calls)
