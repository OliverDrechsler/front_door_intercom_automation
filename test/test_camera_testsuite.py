import asyncio
import os

import pytest
import requests
import queue
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from zoneinfo import ZoneInfo

from camera.camera import Camera
from config import Camera_Task
from config.config_util import Configuration


class AsyncCameraTestSuite(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.config = Configuration()
        self.config.timezone = 'Europe/Berlin'
        self.config.lat = 52.5200
        self.config.lon = 13.4050
        self.config.blink_enabled = True
        self.config.picam_url = MagicMock()
        self.config.blink_config_file = MagicMock()
        self.config.photo_image_path = MagicMock()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.camera_task_queue_async = AsyncMock(asyncio.Queue)
        self.message_task_queue = queue.Queue()

        self.camera = Camera(self.config, self.loop, self.camera_task_queue_async, self.message_task_queue)

        self.mock_logger_info = MagicMock()
        self.mock_logger_debug = MagicMock()
        self.mock_logger_error = MagicMock()
        self.camera.logger.info = self.mock_logger_info
        self.camera.logger.debug = self.mock_logger_debug
        self.camera.logger.error = self.mock_logger_error

    async def test_blink_foto_helper_success(self):
        self.camera.blink_enabled = True
        with patch.object(self.camera, 'blink_snapshot', new_callable=AsyncMock) as mock_snapshot:
            mock_snapshot.return_value = True
            task = Camera_Task(photo=True, chat_id=123)

            result = await self.camera._blink_foto_helper(task)

            assert result == True
            mock_snapshot.assert_called_once()
            self.assertFalse(self.message_task_queue.empty())
            self.mock_logger_debug.assert_any_call("_blink_foto_helper - blink enabled")
            self.mock_logger_debug.assert_any_call("blink snapshot success")

    async def test_blink_foto_helper_false_result(self):
        self.camera.blink_enabled = True
        with patch.object(self.camera, 'blink_snapshot', new_callable=AsyncMock) as mock_snapshot:
            mock_snapshot.return_value = False
            task = Camera_Task(photo=True, chat_id=1234)

            result = await self.camera._blink_foto_helper(task)

            assert result == False
            mock_snapshot.assert_called_once()
            self.assertFalse(self.message_task_queue.empty())
            self.mock_logger_debug.assert_any_call("_blink_foto_helper - blink enabled")
            self.mock_logger_error.assert_any_call("blink snapshot error detected")

    async def test_blink_foto_helper_disabled(self):
        self.config.blink_enabled = False
        task = Camera_Task(photo=True, chat_id=1234)
        result = await self.camera._blink_foto_helper(task)

        assert result == False
        self.mock_logger_debug.assert_not_called()
        self.mock_logger_info.assert_any_call("_blink_foto_helper - blink disabled")

    async def test_check_picam_result(self):
        task = Camera_Task(photo=True, chat_id=1)
        result = await self.camera._check_picam_result(task, True)
        self.mock_logger_debug.assert_any_call("picam _check_picam_result")
        self.assertTrue(result)

    async def test_check_picam_result_false_blink_disabled(self):
        task = Camera_Task(photo=True, chat_id=2)
        self.config.blink_enabled = False
        result = await self.camera._check_picam_result(task, False)
        self.mock_logger_debug.assert_any_call("picam _check_picam_result")
        self.mock_logger_debug.assert_any_call("_check_picam_result FALSE")
        self.mock_logger_error.assert_any_call("_check_picam_result - blink not enabled for second try")
        self.assertFalse(result)

    async def test_check_picam_result_false_blink_enabled(self):
        self.config.blink_enabled = True
        task = Camera_Task(photo=True, chat_id=3)
        with patch.object(self.camera, '_blink_foto_helper', new_callable=AsyncMock) as mock_snapshot:
            mock_snapshot.return_value = True
            result = await self.camera._check_picam_result(task, False)
        mock_snapshot.assert_called_once()
        self.mock_logger_debug.assert_any_call("picam _check_picam_result")
        self.mock_logger_debug.assert_any_call("_check_picam_result FALSE")
        self.mock_logger_error.assert_any_call("_check_picam_result - second try now with blink")
        self.assertTrue(result)

    async def test_check_blink_result(self):
        task = Camera_Task(photo=True, chat_id=4)
        self.config.picam_enabled = True
        result = await self.camera._check_blink_result(task, True)
        self.mock_logger_debug.assert_any_call("blink _check_blink_result")
        self.assertTrue(result)

    async def test_check_blink_result_false_disabled_picam(self):
        task = Camera_Task(photo=True, chat_id=5)
        self.config.picam_enabled = False
        result = await self.camera._check_blink_result(task, False)
        self.mock_logger_debug.assert_any_call("blink _check_blink_result")
        self.mock_logger_debug.assert_any_call("blink _check_blink_result FALSE")
        self.mock_logger_error.assert_any_call("_check_blink_result - picam not enabled for second try")
        self.assertFalse(result)

    async def test_check_blink_result_false_picam_enabled(self):
        self.config.picam_enabled = True
        task = Camera_Task(photo=True, chat_id=6)
        with patch.object(self.camera, '_picam_foto_helper', new_callable=AsyncMock) as mock_snapshot:
            mock_snapshot.return_value = True
            result = await self.camera._check_blink_result(task, False)
        mock_snapshot.assert_called_once()
        self.mock_logger_debug.assert_any_call("blink _check_blink_result")
        self.mock_logger_debug.assert_any_call("blink _check_blink_result FALSE")
        self.mock_logger_error.assert_any_call("_check_blink_result - second try now with picam")
        self.assertTrue(result)

    async def test_put_msg_queue_photo_reply(self):
        task = Camera_Task(reply=True, chat_id=7, message="test")
        self.camera.put_msg_queue_photo(task)
        self.assertEqual(self.message_task_queue.qsize(), 1)
        message_task = self.message_task_queue.get()
        print(message_task.filename)
        self.assertEqual(message_task.filename, self.config.photo_image_path)
        self.assertEqual("test", message_task.message)

    async def test_put_msg_queue_photo_not_reply(self):
        task = Camera_Task(chat_id=9)
        self.camera.put_msg_queue_photo(task)
        self.assertEqual(self.message_task_queue.qsize(), 1)
        message_task = self.message_task_queue.get()
        print(message_task.filename)
        self.assertEqual(message_task.filename, self.config.photo_image_path)
        self.assertIsNone(message_task.message)

    async def test_put_msg_queue_error_reply(self):
        task = Camera_Task(reply=True, chat_id=9, message="test_error")

        self.camera.put_msg_queue_error(task, "data_error")

        self.assertEqual(self.message_task_queue.qsize(), 1)
        message_task = self.message_task_queue.get()
        print(message_task.filename)
        self.assertEqual("test_error", message_task.message)
        self.assertEqual("data_error", message_task.data_text)

    async def test_put_msg_queue_error_not_reply(self):
        task = Camera_Task(chat_id=10)

        self.camera.put_msg_queue_error(task, "data_error")

        self.assertEqual(self.message_task_queue.qsize(), 1)
        message_task = self.message_task_queue.get()
        print(message_task.filename)
        self.assertIsNone(message_task.message)
        self.assertEqual("data_error", message_task.data_text)

    def test_daylight_detected_with_coordinates(self):
        with patch('camera.camera.sun', new_callable=MagicMock) as mock_sun:
            with patch('camera.camera.datetime', new_callable=MagicMock) as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 6, 21, 12, 0, 0, tzinfo=ZoneInfo('Europe/Berlin'))
                mock_sun.return_value = {'sunrise': datetime(2023, 6, 21, 4, 0, 0, tzinfo=ZoneInfo('Europe/Berlin')),
                                         'sunset': datetime(2023, 6, 21, 22, 0, 0, tzinfo=ZoneInfo('Europe/Berlin'))}
                self.assertTrue(self.camera.detect_daylight())
                self.mock_logger_debug.assert_any_call("using coordinates for daylight detection")
                self.mock_logger_info.assert_any_call(msg="Is daylight detected: True")

    def test_night_detected_with_coordinates(self):
        with patch('camera.camera.sun', new_callable=MagicMock) as mock_sun:
            with patch('camera.camera.datetime', new_callable=MagicMock) as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 6, 21, 2, 0, 0, tzinfo=ZoneInfo('Europe/Berlin'))
                mock_sun.return_value = {'sunrise': datetime(2023, 6, 21, 4, 0, 0, tzinfo=ZoneInfo('Europe/Berlin')),
                                         'sunset': datetime(2023, 6, 21, 22, 0, 0, tzinfo=ZoneInfo('Europe/Berlin'))}
                self.assertFalse(self.camera.detect_daylight())
                self.mock_logger_debug.assert_any_call("using coordinates for daylight detection")
                self.mock_logger_info.assert_any_call(msg="Is daylight detected: False")

    def test_night_detected_with_location(self):
        self.config.lat = None
        self.config.lon = None
        self.config.country = "Berlin"
        with patch('camera.camera.sun', new_callable=MagicMock) as mock_sun:
            with patch('camera.camera.datetime', new_callable=MagicMock) as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 6, 21, 2, 0, 0, tzinfo=ZoneInfo('Europe/Berlin'))
                mock_sun.return_value = {'sunrise': datetime(2023, 6, 21, 4, 0, 0, tzinfo=ZoneInfo('Europe/Berlin')),
                                         'sunset': datetime(2023, 6, 21, 22, 0, 0, tzinfo=ZoneInfo('Europe/Berlin'))}
                self.assertFalse(self.camera.detect_daylight())
                self.mock_logger_info.assert_any_call(msg="Is daylight detected: False")
                self.mock_logger_debug.assert_any_call("using country - city for daylight detection")

    def test_invalid_location_data(self):
        with patch('camera.camera.sun', new_callable=MagicMock) as mock_sun:
            with patch('camera.camera.datetime', new_callable=MagicMock) as mock_datetime:
                mock_datetime.now.side_effect = ValueError("Invalid Location data")
                self.assertTrue(self.camera.detect_daylight())

    def test_invalid_location_data(self):
        self.config.lat = None
        self.config.lon = None
        self.config.country = None
        self.assertTrue(self.camera.detect_daylight())
        self.mock_logger_error.assert_any_call("Invalid Location data: No valid country data provided")

    def test_exception_handling(self):
        with patch('camera.camera.sun', new_callable=MagicMock) as mock_sun:
            with patch('camera.camera.datetime', new_callable=MagicMock) as mock_datetime:
                mock_datetime.now.side_effect = Exception("Error in daylight calculation")
                self.assertTrue(self.camera.detect_daylight())

    @patch('camera.camera.os.makedirs')
    @patch('camera.camera.os.path.exists', return_value=True)
    @patch('camera.camera.os.remove')
    @patch('camera.camera.Blink', autospec=True)
    @patch('camera.camera.aiohttp.ClientSession', autospec=True)
    async def test_blink_snapshot(self, mock_client_session, mock_blink, mock_remove, mock_exists, mock_makedirs):
        # Mock the Blink instance and its methods
        mock_blink_instance = mock_blink.return_value
        mock_blink_instance.refresh = AsyncMock()
        mock_blink_instance.cameras = {self.config.blink_name: MagicMock()}
        mock_camera_instance = mock_blink_instance.cameras[self.config.blink_name]
        mock_camera_instance.snap_picture = AsyncMock()
        mock_camera_instance.image_to_file = AsyncMock()
        self.camera.detect_daylight = MagicMock(return_value=True)
        self.config.blink_image_brightning = True
        self.camera.adjust_image = MagicMock(return_value=True)

        # Mock the ClientSession instance
        mock_client_session_instance = mock_client_session.return_value
        self.camera.session = mock_client_session_instance
        self.camera.blink = mock_blink_instance

        # Call the method under test
        result = await self.camera.blink_snapshot()

        # Assertions
        self.assertTrue(result)
        mock_blink_instance.refresh.assert_called_with(force=True)
        mock_camera_instance.snap_picture.assert_called_once()
        mock_camera_instance.image_to_file.assert_called_once_with(self.config.photo_image_path)
        mock_exists.assert_called_once_with(self.config.photo_image_path)
        mock_makedirs.assert_not_called()
        mock_remove.assert_called_once_with(self.config.photo_image_path)
        print("")
        print("logs")
        print(self.mock_logger_info.call_args_list)
        print(self.mock_logger_debug.call_args_list)
        self.mock_logger_info.assert_any_call(
            msg="i'll take a snapshot from blink cam {0} and store it here {1}".format(self.config.blink_name,
                                                                                       self.config.photo_image_path))
        self.mock_logger_info.assert_any_call('saving blink foto')
        self.mock_logger_debug.assert_any_call('create a camera instance')
        self.mock_logger_debug.assert_any_call('refresh blink server info')
        self.mock_logger_debug.assert_any_call('a file already exists and will be deleted before hand')

    @patch('camera.camera.Blink', autospec=True)
    async def test_blink_snapshot_with_refresh_exception_(self, mock_blink):
        mock_blink_instance = mock_blink.return_value
        mock_blink_instance.refresh = AsyncMock(side_effect=Exception("Refresh failed"))
        self.camera.blink = mock_blink_instance

        result = await self.camera.blink_snapshot()

        self.assertFalse(result)
        mock_blink_instance.refresh.assert_called_with(force=True)
        self.mock_logger_error.assert_any_call("Error: Refresh failed")

    @patch('camera.camera.Blink', autospec=True)
    @patch('camera.camera.aiohttp.ClientSession', autospec=True)
    async def test_blink_snapshot_with_snap_picture_exception(self, mock_client_session, mock_blink):
        mock_blink_instance = mock_blink.return_value
        mock_blink_instance.refresh = AsyncMock()
        mock_blink_instance.cameras = {self.config.blink_name: MagicMock()}
        mock_camera_instance = mock_blink_instance.cameras[self.config.blink_name]
        mock_camera_instance.snap_picture = AsyncMock(side_effect=Exception("Custom exception"))
        mock_client_session_instance = mock_client_session.return_value
        self.camera.session = mock_client_session_instance
        self.camera.blink = mock_blink_instance

        result = await self.camera.blink_snapshot()

        self.assertFalse(result)
        mock_blink_instance.refresh.assert_called_with(force=True)
        mock_camera_instance.snap_picture.assert_called_once()
        self.mock_logger_error.assert_any_call("Error: Custom exception")

    @patch('camera.camera.os.makedirs')
    @patch('camera.camera.os.path.exists', return_value=False)
    @patch('camera.camera.os.remove')
    @patch('camera.camera.Blink', autospec=True)
    @patch('camera.camera.aiohttp.ClientSession', autospec=True)
    async def test_blink_snapshot_with_image_to_file_exception(self, mock_client_session, mock_blink, mock_remove,
                                                               mock_exists, mock_makedirs):
        mock_blink_instance = mock_blink.return_value
        mock_blink_instance.refresh = AsyncMock()
        mock_blink_instance.cameras = {self.config.blink_name: MagicMock()}
        mock_camera_instance = mock_blink_instance.cameras[self.config.blink_name]
        mock_camera_instance.snap_picture = AsyncMock()
        mock_camera_instance.image_to_file = AsyncMock(side_effect=Exception("Custom exception image to file"))
        mock_client_session_instance = mock_client_session.return_value
        self.camera.session = mock_client_session_instance
        self.camera.blink = mock_blink_instance

        result = await self.camera.blink_snapshot()

        self.assertFalse(result)
        mock_blink_instance.refresh.assert_called_with(force=True)
        mock_camera_instance.snap_picture.assert_called_once()
        self.mock_logger_error.assert_any_call("Error: Custom exception image to file")
        mock_camera_instance.image_to_file.assert_called_once_with(self.config.photo_image_path)
        mock_exists.assert_called_once_with(self.config.photo_image_path)
        mock_remove.assert_not_called()
        mock_makedirs.assert_called_once_with(os.path.dirname(self.config.photo_image_path), exist_ok=True)

    @patch('camera.camera.aiohttp.ClientSession', autospec=True)
    @patch('camera.camera.os.path.exists', return_value=True)
    @patch('camera.camera.json_load', new_callable=AsyncMock)
    @patch('camera.camera.Auth')
    async def test_read_blink_config_file_exists(self, mock_auth, mock_json_load, mock_path_exists,
                                                 mock_client_session):
        mock_json_load.return_value = {"username": "test_user", "password": "test_password"}
        mock_auth_instance = mock_auth.return_value
        mock_client_session_instance = mock_client_session.return_value
        self.camera.session = mock_client_session_instance
        self.camera.blink = MagicMock()  # Set the blink attribute

        await self.camera.read_blink_config()

        mock_path_exists.assert_called_once_with(self.config.blink_config_file)
        mock_json_load.assert_called_once_with(self.config.blink_config_file)
        mock_auth.assert_called_once_with(mock_json_load.return_value, no_prompt=True, session=self.camera.session)
        self.assertEqual(self.camera.blink.auth, mock_auth_instance)
        self.camera.logger.info.assert_called_with("blink aut with file done")

    @patch('camera.camera.aiohttp.ClientSession', autospec=True)
    @patch('camera.camera.os.path.exists', return_value=False)
    @patch('camera.camera.Auth')
    async def test_read_blink_config_file_not_exists(self, mock_auth, mock_path_exists, mock_client_session):
        mock_auth_instance = mock_auth.return_value
        mock_client_session_instance = mock_client_session.return_value
        self.camera.session = mock_client_session_instance
        self.camera.blink = MagicMock()  # Set the blink attribute

        await self.camera.read_blink_config()

        mock_path_exists.assert_called_once_with(self.config.blink_config_file)
        mock_auth.assert_called_once_with(
            {"username": self.config.blink_username, "password": self.config.blink_password},
            no_prompt=True,
            session=self.camera.session
        )
        self.assertEqual(self.camera.blink.auth, mock_auth_instance)
        self.camera.logger.info.assert_called_with("no blink_config.json found - 2FA authentication token required")

    @patch('camera.camera.Blink', autospec=True)
    async def test_save_blink_config(self, mock_blink):
        mock_blink_instance = mock_blink.return_value
        self.camera.blink = mock_blink_instance

        result = await self.camera.save_blink_config()

        mock_blink_instance.save.assert_called_once_with(self.config.blink_config_file)
        self.camera.logger.info.assert_called_with("saving blink authenticated session infos into config file")
        self.assertTrue(result)

    @patch('camera.camera.Auth.send_auth_key', new_callable=AsyncMock)
    @patch('camera.camera.Blink.setup_post_verify', new_callable=AsyncMock)
    async def test_add_2fa_blink_token(self, mock_setup_post_verify, mock_send_auth_key):
        task = Camera_Task(blink_mfa="123456")
        self.camera.blink = MagicMock()  # Set the blink attribute
        self.camera.blink.auth = MagicMock()  # Set the auth attribute
        self.camera.blink.auth.send_auth_key = mock_send_auth_key  # Mock the send_auth_key method
        self.camera.blink.setup_post_verify = mock_setup_post_verify  # Mock the setup_post_verify method

        result = await self.camera.add_2fa_blink_token(task)

        mock_send_auth_key.assert_called_once_with(self.camera.blink, "123456")
        mock_setup_post_verify.assert_called_once()
        self.camera.logger.debug.assert_any_call("add a 2FA token for authentication")
        self.camera.logger.debug.assert_any_call("verify 2FA token")
        self.camera.logger.info.assert_called_with("added 2FA token 123456")
        self.assertTrue(result)

    @patch('camera.camera.requests')
    def test_picam_request_take_foto(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        result = self.camera.picam_request_take_foto()

        self.mock_logger_info.assert_called_with(msg="take a PiCam snapshot")
        self.assertTrue(result)

    @patch('camera.camera.requests')
    def test_picam_request_take_foto_exception(self, mock_requests):
        mock_response = mock_requests.post.return_value
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError

        result = self.camera.picam_request_take_foto()

        self.assertFalse(result)
        self.mock_logger_info.assert_called_with(msg="take a PiCam snapshot")
        self.mock_logger_error.assert_called_with("Exception: ")

    @patch('camera.camera.requests')
    @patch('camera.camera.os.path.exists', return_value=True)
    @patch('camera.camera.os.remove')
    def test_picam_request_download_foto(self, mock_remove, mock_exists, mock_requests):
        self.camera.config.picam_url = "http://example.com"
        self.camera.config.picam_image_filename = "foto.jpg"
        self.camera.config.photo_image_path = "/tmp/photo.jpg"
        self.camera.detect_daylight = MagicMock(return_value=True)
        self.config.picam_image_brightning = True
        self.camera.adjust_image = MagicMock(return_value=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        mock_requests.get.return_value = mock_response

        mock_file = unittest.mock.mock_open()
        with patch('builtins.open', mock_file):
            result = self.camera.picam_request_download_foto()

        mock_requests.get.assert_called_once_with(
            url="http://example.com?filename=foto.jpg"
        )
        mock_file.assert_any_call("/tmp/photo.jpg", 'wb')
        mock_file().write.assert_called_once_with(mock_response.content)
        self.assertTrue(result)
        self.mock_logger_info.assert_any_call(msg='downloading PiCam foto')
        self.mock_logger_debug.assert_any_call(msg='downloading foto ended with status 200')
        self.mock_logger_debug.assert_any_call(msg='end downloading foto')

    @patch('camera.camera.requests')
    @patch('camera.camera.os.path.exists', return_value=True)
    @patch('camera.camera.os.remove')
    def test_picam_request_download_foto_with_request_exception(self, mock_remove, mock_exists, mock_requests):
        self.camera.config.picam_url = "http://example.com"
        self.camera.config.picam_image_filename = "foto.jpg"
        self.camera.config.photo_image_path = "/tmp/photo.jpg"
        self.camera.detect_daylight = MagicMock(return_value=True)
        mock_requests.get.reset_mock()
        mock_requests.get.side_effect = requests.exceptions.RequestException

        mock_file = unittest.mock.mock_open()
        with patch('builtins.open', mock_file):
            result = self.camera.picam_request_download_foto()

        mock_requests.get.assert_called_once_with(
            url="http://example.com?filename=foto.jpg"
        )
        self.assertFalse(result)
        mock_file.assert_any_call("/tmp/photo.jpg", 'wb')
        self.mock_logger_info.assert_any_call(msg='downloading PiCam foto')
        self.mock_logger_error.assert_any_call('Error: ')
        self.mock_logger_error.assert_any_call('Error args: ()')

    @patch('camera.camera.os.path.exists', return_value=True)
    @patch('camera.camera.Image.open')
    @patch('camera.camera.ImageEnhance.Contrast')
    @patch('camera.camera.ImageEnhance.Brightness')
    def test_adjust_image(self, mock_brightness, mock_enhancer, mock_open, mock_exists):
        self.config.photo_image_path = "test_image.jpg"
        self.config.image_brightness = 3
        self.config.image_contrast = 2

        mock_image = MagicMock()
        mock_open.return_value = mock_image
        mock_enhancer.return_value = MagicMock()
        mock_brightness.return_value = mock_enhancer

        result = self.camera.adjust_image()

        mock_exists.assert_called_once_with(self.config.photo_image_path)
        mock_open.assert_called_once_with(self.config.photo_image_path)
        mock_brightness.assert_called_once_with(mock_image)
        mock_enhancer.enhance.assert_called_once_with(self.config.image_brightness)
        self.assertTrue(result)

    @patch('camera.camera.os.path.exists', return_value=False)
    def test_adjust_image_file_not_exists(self, mock_exists):
        self.config.photo_image_path = "test_image.jpg"  # Stellen Sie sicher, dass der Pfad gesetzt ist
        result = self.camera.adjust_image()
        mock_exists.assert_called_once_with(self.config.photo_image_path)
        self.assertFalse(result)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(AsyncCameraTestSuite)
    unittest.TextTestRunner().run(suite)
