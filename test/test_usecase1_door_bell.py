import unittest
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from door.bell import Door
import json
import datetime


class DoorTestCase(unittest.TestCase):
    def setUp(self):
        """Prepare TestSuite UseCase 1 tests"""
        with open("test/expected_conf.json") as json_file:
            self.CONFIG_DICT = json.load(json_file)

        with open("test/mocked_send_msg.json") as json_file:
            self.send_msg_return = json.load(json_file)

        self.patcher_os_isfile = patch(
            "common.config_util.os.path.isfile", return_value=False
        )
        self.mock_os_isfile = self.patcher_os_isfile.start()

        self.patch_time = patch("door.bell.time.sleep", return_value=MagicMock())
        self.mock_time = self.patch_time.start()

        self.now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        self.bot = MagicMock()
        self.bot.sendMessage.return_value = self.send_msg_return
        self.bot.sendPhoto.return_value = self.send_msg_return

        self.blink = MagicMock()
        self.blink.cameras.snap_picture.return_value = True
        self.auth = MagicMock()
        self.auth.login_attributes = True

        self.patch_open_file1 = patch(
            "messaging.send_msg.open", return_value=MagicMock()
        )
        self.mock_open_send_msg = self.patch_open_file1.start()
        self.patch_open_file2 = patch("camera.blink_cam.open", return_value=MagicMock())
        self.mock_open_blink_cam = self.patch_open_file2.start()
        self.patch_json_load = patch("camera.blink_cam.json", return_value=MagicMock())
        self.mock_json_load = self.patch_json_load.start()
        self.mock_json_load.load.return_value = True

        self.patch_button = patch("door.bell.Button", return_value=MagicMock())
        self.mock_button = self.patch_button.start()

    def tearDown(self):
        """Cleanup TestSuite"""
        self.patcher_os_isfile.stop()
        self.patch_time.stop()
        self.patch_button.stop()
        self.patch_open_file1.stop()
        self.patch_open_file2.stop()
        self.patch_json_load.stop()

    def test_usecase1_door_bell_ring(self, test=True):
        """UseCase 1 tests includes:

        Simulate door bell ring,
        send telegram message,
        take a blink cam foto snapshot,
        send foto via telegram.
        """

        with self.assertLogs("door-bell", level="DEBUG") as self.dl_log:
            self.instance_door = Door(self.bot, self.blink, self.auth)
        instance_door_log = ["DEBUG:door-bell:reading config"]
        self.assertEqual(self.dl_log.output, instance_door_log)
        self.mock_os_isfile.assert_called()
        self.assertEqual(self.instance_door.bot, self.bot)
        self.assertEqual(self.instance_door.blink, self.blink)
        self.assertEqual(self.instance_door.auth, self.auth)
        self.assertEqual(self.instance_door.config, self.CONFIG_DICT)

        expected_ring_log = [
            "INFO:door-bell:start monitoring door bell",
            "DEBUG:door-bell:RPI: start endless loop doorbell monitoring",
            "INFO:door-bell:Door bell ringing",
            f"INFO:send_telegram_msg:send message : Ding Dong! {self.now}",
            "DEBUG:cam_common:choose camera",
            "DEBUG:cam_common:blink cam choosen",
            "INFO:cam_common:take a Blink Cam snapshot",
            "INFO:blink_cam:i'll take a snapshot from cam Blink_Camera_name_here and store it here /tmp/foto.jpg",
            "DEBUG:blink_cam:create a camera instance",
            "DEBUG:blink_cam:take a snpshot",
            "DEBUG:blink_cam:refresh blink server info",
            "INFO:blink_cam:saving blink foto",
            "DEBUG:blink_cam:load blink config file",
            "DEBUG:blink_cam:saved blink config file == running config",
            "INFO:send_telegram_msg:send a foto: success",
        ]
        with self.assertLogs(level="DEBUG") as self.ring_log:
            self.instance_door.ring(test=True)
        self.mock_button.assert_called()
        self.bot.sendMessage.assert_called_with("-4321", f"Ding Dong! {self.now}")
        self.blink.cameras.__getitem__.assert_called_with("Blink_Camera_name_here")
        self.blink.cameras.__getitem__().snap_picture.assert_called()
        self.blink.refresh.assert_called()
        self.blink.cameras.__getitem__().image_to_file.assert_called_with(
            "/tmp/foto.jpg"
        )
        self.bot.sendPhoto.assert_called()
        self.assertEqual(self.ring_log.output, expected_ring_log)
