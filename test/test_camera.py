import unittest
from unittest.mock import patch, MagicMock, AsyncMock, call
from camera.camera import Camera
from config.config_util import Configuration, DefaultCam
from config.data_class import Camera_Task, Message_Task
import asyncio
import queue
import logging

class TestCamera(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()
        self.loop = asyncio.new_event_loop()
        self.camera_task_queue_async = AsyncMock(asyncio.Queue)
        self.message_task_queue = MagicMock(queue.Queue)
        self.camera = Camera(self.config, self.loop, self.camera_task_queue_async, self.message_task_queue)

    @patch('camera.aiohttp.ClientSession')
    @patch('camera.Blink')
    async def test_start(self, mock_blink, mock_client_session):
        mock_blink_instance = mock_blink.return_value
        mock_client_session_instance = mock_client_session.return_value

        self.config.blink_enabled = True
        self.camera_task_queue_async.get = AsyncMock(return_value=None)

        await self.camera.start()

        self.camera.logger.debug.assert_called_with(msg="thread camera start")
        mock_client_session.assert_called_once()
        mock_blink_instance.start.assert_called_once()
        self.assertFalse(self.camera.running)
        mock_client_session_instance.close.assert_called_once()

    @patch('camera.Blink')
    @patch('camera.ClientSession')
    async def test_read_blink_config(self, mock_blink, mock_client_session):
        mock_blink_instance = mock_blink.return_value

        with patch('os.path.exists', return_value=True):
            with patch('camera.json_load', new_callable=AsyncMock):
                await self.camera._read_blink_config()
                self.camera.logger.info.assert_called_with("blink aut with file done")
                self.assertTrue(mock_blink_instance.auth.no_prompt)

    @patch('camera.Blink')
    @patch('camera.ClientSession')
    async def test_save_blink_config(self, mock_blink, mock_client_session):
        mock_blink_instance = mock_blink.return_value

        result = await self.camera._save_blink_config()
        self.camera.logger.info.assert_called_with("saving blink authenticated session infos into config file")
        self.assertTrue(result)

    @patch('camera.Blink')
    @patch('camera.ClientSession')
    async def test_blink_snapshot(self, mock_blink, mock_client_session):
        mock_blink_instance = mock_blink.return_value
        mock_camera = MagicMock()
        mock_blink_instance.cameras.__getitem__.return_value = mock_camera

        result = await self.camera._blink_snapshot()
        self.camera.logger.info.assert_called_with(
            msg="i'll take a snapshot from blink cam {0} and store it here {1}".format(
                self.config.blink_name, self.config.photo_image_path))
        self.assertTrue(result)
        mock_camera.snap_picture.assert_called_once()
        mock_camera.image_to_file.assert_called_once_with(self.config.photo_image_path)

    @patch('camera.camera.requests')
    def test_picam_request_take_foto(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        mock_logger_info = MagicMock()
        self.camera.logger.info = mock_logger_info

        result = self.camera._picam_request_take_foto()
        mock_logger_info.assert_called_with(msg="take a PiCam snapshot")
        self.assertTrue(result)


    @patch('camera.camera.requests')
    def test_picam_request_download_foto(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        mock_logger_info = MagicMock()
        self.camera.logger.info = mock_logger_info

        with patch('builtins.open', unittest.mock.mock_open()):
            result = self.camera._picam_request_download_foto()
            mock_logger_info.assert_called_with(msg="downloading PiCam foto")
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
