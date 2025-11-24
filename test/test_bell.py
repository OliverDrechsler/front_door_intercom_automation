import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import threading
import queue
import time
from door.bell import DoorBell
from config import config_util
from config.data_class import Message_Task, Camera_Task

# Import door.bell at the module level
import door.bell


class TestDoorBell(unittest.TestCase):

    def setUp(self):
        # Patch RPi.GPIO module at the system level
        self.gpio_patcher = patch.dict('sys.modules', {
            'RPi': MagicMock(),
            'RPi.GPIO': MagicMock()
        })
        self.mock_gpio = self.gpio_patcher.start()
        self.addCleanup(self.gpio_patcher.stop)

        # Ensure the GPIO mock is available in the door.bell module
        door.bell.GPIO = self.mock_gpio['RPi.GPIO']
        self.GPIO = self.mock_gpio['RPi.GPIO']

    @patch('door.bell.detect_rpi.detect_rpi', return_value=True)
    def test_ring_on_rpi(self, mock_detect_rpi):
        # Setup GPIO mocks
        self.GPIO.LOW = 0
        self.GPIO.HIGH = 1
        self.GPIO.BCM = 'BCM'
        self.GPIO.PUD_UP = 'PUD_UP'

        # Simulate button press (LOW) and release (HIGH)
        self.GPIO.input = MagicMock(side_effect=[self.GPIO.LOW, self.GPIO.HIGH])

        shutdown_event = threading.Event()
        config = MagicMock(spec=config_util.Configuration)
        config.run_on_raspberry = True
        config.telegram_chat_nr = "test_chat_id"
        config.door_bell = 17  # pin number
        loop = asyncio.new_event_loop()
        message_task_queue = queue.Queue()
        camera_task_queue_async = asyncio.Queue()

        door_bell = DoorBell(shutdown_event, config, loop, message_task_queue, camera_task_queue_async)

        with patch('door.bell.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-07-12_12:00:00"
            with patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine_threadsafe:
                async def async_put_side_effect(item):
                    pass
                with patch.object(camera_task_queue_async, 'put', new_callable=AsyncMock, side_effect=async_put_side_effect) as mock_put:
                    def stop_loop_after_first_press(*args, **kwargs):
                        # Set shutdown_event to stop the loop after first press
                        shutdown_event.set()
                        return original_sleep(0.01)

                    original_sleep = time.sleep
                    with patch('time.sleep', side_effect=stop_loop_after_first_press):
                        door_bell.ring(test=True)
                    # Cleanup any pending coroutines
                    try:
                        for task in asyncio.all_tasks(loop):
                            task.cancel()
                        loop.run_until_complete(asyncio.sleep(0))
                    except RuntimeError:
                        pass
        
        # Cleanup loop after test
        loop.close()

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

        # Ensure GPIO setup and cleanup are called
        self.GPIO.setmode.assert_called_once_with(self.GPIO.BCM)
        self.GPIO.setup.assert_called_once_with(17, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.cleanup.assert_called_once()

    @patch('door.bell.detect_rpi.detect_rpi', return_value=False)
    def test_ring_not_on_rpi(self, mock_detect_rpi):
        shutdown_event = threading.Event()
        config = MagicMock(spec=config_util.Configuration)
        config.run_on_raspberry = False
        config.testing_bell_msg = True
        config.telegram_chat_nr = "test_chat_id"
        config.door_bell = 17  # pin number
        loop = asyncio.new_event_loop()
        message_task_queue = queue.Queue()
        camera_task_queue_async = asyncio.Queue()

        door_bell = DoorBell(shutdown_event, config, loop, message_task_queue, camera_task_queue_async)

        with patch('door.bell.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-07-12_12:00:00"
            with patch('asyncio.run_coroutine_threadsafe') as mock_run_coroutine_threadsafe:
                async def async_put_side_effect(item):
                    pass
                with patch.object(camera_task_queue_async, 'put', new_callable=AsyncMock, side_effect=async_put_side_effect) as mock_put:
                    def stop_after_one_ring(*args, **kwargs):
                        # Trigger shutdown_event after one loop to stop execution
                        shutdown_event.set()
                        return original_sleep(0.01)

                    original_sleep = time.sleep
                    with patch('time.sleep', side_effect=stop_after_one_ring):
                        door_bell.ring(test=True)
                    # Cleanup any pending coroutines
                    try:
                        for task in asyncio.all_tasks(loop):
                            task.cancel()
                        loop.run_until_complete(asyncio.sleep(0))
                    except RuntimeError:
                        pass
        
        # Cleanup loop after test
        loop.close()

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
