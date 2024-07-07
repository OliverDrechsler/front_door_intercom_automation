import unittest
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from door.bell import DoorBell
import json


class DoorTestCase(unittest.TestCase):
    def setUp(self):
        with open("test/expected_conf.json") as json_file:
            self.CONFIG_DICT = json.load(json_file)

        self.patcher_os_isfile = patch(
            "common.config_util.os.path.isfile", return_value=False
        )
        self.patcher_os_path = patch(
            "common.config_util.os.path.exists", return_value=False
        )

        self.patch_time = patch("door.bell.time.sleep", return_value=MagicMock())
        self.mock_time = self.patch_time.start()

        self.bot = MagicMock()
        self.blink = MagicMock()
        self.auth = MagicMock()

        self.patch_button = patch("door.bell.Button", return_value=MagicMock())
        self.mock_button = self.patch_button.start()

        self.patch_send_msg = patch(
            "door.bell.send_msg.telegram_send_message", return_value=MagicMock()
        )
        self.mock_send_msg = self.patch_send_msg.start()

        self.patch_choose_camera = patch(
            "door.bell.cam_common.choose_camera", return_value=MagicMock()
        )
        self.mock_choose_camera = self.patch_choose_camera.start()

        self.mock_os_isfile = self.patcher_os_isfile.start()
        with self.assertLogs("door-bell", level="DEBUG") as self.dl_log:
            self.instance_door = DoorBell(self.bot, self.blink, self.auth)

    def tearDown(self):
        # self.patcher_logger.stop()
        self.patcher_os_isfile.stop()
        self.patch_time.stop()
        self.patch_button.stop()
        self.patch_send_msg.stop()
        self.patch_choose_camera.stop()

    def test_edge_case_ring_not_running_on_RPi_eq_test_mode(self, test=True):

        self.mock_os_isfile.assert_called()
        self.assertEqual(self.instance_door.bot, self.bot)
        self.assertEqual(self.instance_door.blink, self.blink)
        self.assertEqual(self.instance_door.auth, self.auth)
        self.assertEqual(self.instance_door.config, self.CONFIG_DICT)
        expected_log = ["DEBUG:door-bell:reading config"]
        self.assertEqual(self.dl_log.output, expected_log)

        log1 = [
            "INFO:door-bell:start monitoring door bell",
            "DEBUG:door-bell:NOT on RPI: start empty endless loop",
        ]
        self.instance_door.run_on_raspberry = False
        with self.assertLogs("door-bell", level="DEBUG") as self.ring_log:
            self.instance_door.ring(test=True)
        self.assertEqual(self.ring_log.output, log1)
