import unittest
from unittest.mock import patch, MagicMock, PropertyMock, AsyncMock
import asyncio
import threading
import queue
from door.bell import DoorBell
from config import config_util
from config.data_class import Message_Task, Camera_Task


class TestDoorBell(unittest.TestCase):

    @patch('door.bell.detect_rpi.detect_rpi', return_value=True)
    @patch('door.bell.Button')
    def test_ring_on_rpi(self, mock_button, mock_detect_rpi):
        shutdown_event = threading.Event()
        config = MagicMock(spec=config_util.Configuration)
        config.run_on_raspberry = True
        config.telegram_chat_nr = "test_chat_id"
        config.door_bell_pin = 17
        loop = asyncio.new_event_loop()
        message_task_queue = queue.Queue()
        camera_task_queue_async = asyncio.Queue()

        door_bell = DoorBell(shutdown_event, config, loop, message_task_queue, camera_task_queue_async)

        mock_button_instance = mock_button.return_value
        type(mock_button_instance).is_pressed = PropertyMock(side_effect=[True, False])

        with patch('door.bell.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-07-12_12:00:00"
            with patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine_threadsafe:
                with patch.object(camera_task_queue_async, 'put', new_callable=AsyncMock) as mock_put:
                    with patch('time.sleep', side_effect=lambda x: shutdown_event.set()):
                        door_bell.ring(test=True)

        self.assertEqual(message_task_queue.qsize(), 1)
        self.assertEqual(mock_put.call_count, 1)
        message_task = message_task_queue.get()
        camera_task = mock_put.call_args[0][0]
        self.assertIsInstance(message_task, Message_Task)
        self.assertIsInstance(camera_task, Camera_Task)
        self.assertTrue(message_task.send)
        self.assertTrue(camera_task.photo)
        self.assertEqual(message_task.chat_id, "test_chat_id")
        self.assertIn("Ding Dong! 2024-07-12_12:00:00", message_task.data_text)

    @patch('door.bell.detect_rpi.detect_rpi', return_value=False)
    def test_ring_not_on_rpi(self, mock_detect_rpi):
        shutdown_event = threading.Event()
        config = MagicMock(spec=config_util.Configuration)
        config.run_on_raspberry = False
        config.testing_bell_msg = True
        config.telegram_chat_nr = "test_chat_id"
        config.door_bell_pin = 17
        loop = asyncio.new_event_loop()
        message_task_queue = queue.Queue()
        camera_task_queue_async = asyncio.Queue()

        door_bell = DoorBell(shutdown_event, config, loop, message_task_queue, camera_task_queue_async)

        with patch('door.bell.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-07-12_12:00:00"
            with patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine_threadsafe:
                with patch.object(camera_task_queue_async, 'put', new_callable=AsyncMock) as mock_put:
                    with patch('time.sleep', side_effect=lambda x: shutdown_event.set()):
                        door_bell.ring(test=True)

        self.assertEqual(message_task_queue.qsize(), 1)
        self.assertEqual(mock_put.call_count, 1)
        message_task = message_task_queue.get()
        camera_task = mock_put.call_args[0][0]
        self.assertIsInstance(message_task, Message_Task)
        self.assertIsInstance(camera_task, Camera_Task)
        self.assertTrue(message_task.send)
        self.assertTrue(camera_task.photo)
        self.assertEqual(message_task.chat_id, "test_chat_id")
        self.assertIn("Ding Dong! 2024-07-12_12:00:00", message_task.data_text)


if __name__ == '__main__':
    unittest.main()
