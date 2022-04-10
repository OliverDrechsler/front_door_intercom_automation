import unittest
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from camera.picam import request_take_foto, request_download_foto
from common.config_util import Configuration, YamlReadError
import json


class DoorTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher_os_isfile = patch(
            "common.config_util.os.path.isfile", return_value=False
        )
        self.mock_os_isfile = self.patcher_os_isfile.start()

        self.patch_requests_post = patch(
            "camera.picam.requests.post", return_value=MagicMock()
        )
        self.mock_requests_post = self.patch_requests_post.start()
        self.mock_requests_post.return_value.status_code = 200
        self.mock_requests_post.return_value.json.return_value = {
            "status": "new foto created",
            "foto resolution": "640x480",
            "foto rotation": 0,
            "exposure mode": "auto",
            "iso": 0,
            "filename": "foto.jpg",
        }
        self.patch_requests_get = patch(
            "camera.picam.requests.get", return_value=MagicMock()
        )
        self.mock_requests_get = self.patch_requests_get.start()
        self.mock_requests_get.return_value.status_code = 200

        self.patch_open_file = patch("camera.picam.open", return_value=MagicMock())
        self.mock_open_file = self.patch_open_file.start()

    def tearDown(self):
        self.patcher_os_isfile.stop()
        self.patch_requests_post.stop()
        self.patch_requests_get.stop()
        self.patch_open_file.stop()

    def test_request_take_foto(self):
        """Tests function to take a PiCam API foto."""
        self.instance_configuration = Configuration()

        expected_log = [
            "INFO:PiCam:take a PiCam snapshot",
            f"DEBUG:PiCam:post url={self.instance_configuration.picam_url}",
            "DEBUG:PiCam:{'rotation': 0, 'width': 640, 'filename': 'foto.jpg', 'hight': 480, 'exposure': 'auto', 'iso': 0}",
            "DEBUG:PiCam:{'content-type': 'application/json'}",
            "DEBUG:PiCam:make a snapshot ended with http status 200",
        ]
        with self.assertLogs(level="DEBUG") as self.log1:
            self.take_foto = request_take_foto(
                self.instance_configuration.picam_url,
                self.instance_configuration.picam_image_width,
                self.instance_configuration.picam_image_hight,
                self.instance_configuration.picam_image_filename,
                self.instance_configuration.picam_exposure,
                self.instance_configuration.picam_rotation,
                self.instance_configuration.picam_iso,
            )
        self.assertEqual(self.log1.output, expected_log)
        # expected return status code
        self.assertEqual(self.take_foto, 200)
        self.assertNotEqual(self.take_foto, 400)
        self.assertNotEqual(self.take_foto, 500)

    def test_request_download_foto(self):
        """Tests the request get download foto.jpg file"""
        self.instance_configuration = Configuration()

        expected_download_log = [
            "INFO:PiCam:downloading PiCam foto",
            "DEBUG:PiCam:downloading foto ended with status 200",
            "DEBUG:PiCam:end downloading foto",
        ]
        with self.assertLogs(level="DEBUG") as self.log2:
            self.download_foto1 = request_download_foto(
                self.instance_configuration.picam_url,
                self.instance_configuration.picam_image_filename,
                self.instance_configuration.common_image_path,
            )
        self.assertEqual(self.log2.output, expected_download_log)
        # expected return status code
        self.assertEqual(self.download_foto1, 200)
        self.assertNotEqual(self.download_foto1, 400)
        self.assertNotEqual(self.download_foto1, 500)

        with patch("camera.picam.os.path.exists", return_value=True) as mock_file_exist:
            with patch("camera.picam.os.remove", return_value=True) as mock_file_remove:
                self.download_foto2 = request_download_foto(
                    self.instance_configuration.picam_url,
                    self.instance_configuration.picam_image_filename,
                    self.instance_configuration.common_image_path,
                )
        self.assertEqual(self.download_foto1, 200)
        mock_file_exist.assert_called_with("/tmp/foto.jpg")
        mock_file_remove.assert_called_with("/tmp/foto.jpg")
