import unittest
from unittest.mock import patch, MagicMock, Mock
import threading
import queue
import time

# Import the DoorOpener class and related classes from opener.py
# Assume they are available in the current context as opener.DoorOpener, etc.
from door.opener import DoorOpener
import door.opener
from config import config_util
from config.data_class import Open_Door_Task, Message_Task
from door import detect_rpi

class TestDoorOpener(unittest.TestCase):

    def setUp(self):
        # Mock the sys.modules for RPi and RPi.GPIO
        self.gpio_patcher = patch.dict('sys.modules', {
            'RPi': MagicMock(),
            'RPi.GPIO': MagicMock()
        })
        self.mock_gpio = self.gpio_patcher.start()


        self.mock_gpio = self.gpio_patcher.start()
        self.addCleanup(self.gpio_patcher.stop)

        # Ensure the GPIO mock is available in the door.bell module
        door.opener.GPIO = self.mock_gpio['RPi.GPIO']
        self.GPIO = self.mock_gpio['RPi.GPIO']

        # Mock the detect_rpi function
        self.detect_rpi_patcher = patch('door.detect_rpi.detect_rpi', return_value=True)
        self.mock_detect_rpi = self.detect_rpi_patcher.start()

        # Setup mock config
        self.mock_config = Mock(spec=config_util.Configuration)
        self.mock_config.telegram_chat_nr = 12345
        self.mock_config.door_summer = 18
        self.mock_config.run_on_raspberry = True

        # Create the queues
        self.message_task_queue = queue.Queue()
        self.door_open_task_queue = queue.Queue()

        # Shutdown event
        self.shutdown_event = threading.Event()

        # Create the DoorOpener instance
        self.door_opener = DoorOpener(
            shutdown_event=self.shutdown_event,
            config=self.mock_config,
            loop=None,
            message_task_queue=self.message_task_queue,
            door_open_task_queue=self.door_open_task_queue
        )

    def tearDown(self):
        self.gpio_patcher.stop()
        self.detect_rpi_patcher.stop()

    def test_open_door_successful(self):
        # Test the open_door method when running on a Raspberry Pi
        result = self.door_opener.open_door()
        self.assertTrue(result)
        self.GPIO.setmode.assert_called_once_with(self.GPIO.BCM)
        self.GPIO.setup.assert_called_once_with(self.mock_config.door_summer, self.GPIO.OUT)
        self.GPIO.output.assert_any_call(self.mock_config.door_summer, self.GPIO.HIGH)
        self.GPIO.output.assert_any_call(self.mock_config.door_summer, self.GPIO.LOW)

    def test_open_door_not_on_rpi(self):
        # Test the open_door method when not running on a Raspberry Pi
        self.mock_detect_rpi.return_value = False
        result = self.door_opener.open_door()
        self.assertFalse(result)
        self.GPIO.setmode.assert_not_called()

    def test_start_process_open_door_task(self):
        # Add a task to the queue
        task = Open_Door_Task(open=True, reply=True, message="Hello", chat_id=67890)
        self.door_open_task_queue.put(task)

        # Run the start method in a separate thread
        def run_start():
            self.door_opener.start()

        start_thread = threading.Thread(target=run_start)
        start_thread.start()

        # Allow some time for the thread to process
        time.sleep(0.2)

        # Signal shutdown and join thread
        self.shutdown_event.set()
        start_thread.join()

        # Check the message task queue for expected message
        result_task = self.message_task_queue.get_nowait()
        self.assertEqual(result_task.reply, True)
        self.assertEqual(result_task.chat_id, task.chat_id)
        self.assertEqual(result_task.message, task.message)
        self.assertEqual(result_task.data_text, "Door opened!")

    def test_start_process_open_door_task_no_reply(self):
        # Add a task to the queue without a reply
        task = Open_Door_Task(open=True, reply=False, message=None, chat_id=67890)
        self.door_open_task_queue.put(task)

        # Run the start method in a separate thread
        def run_start():
            self.door_opener.start()

        start_thread = threading.Thread(target=run_start)
        start_thread.start()

        # Allow some time for the thread to process
        time.sleep(0.2)

        # Signal shutdown and join thread
        self.shutdown_event.set()
        start_thread.join()

        # Check the message task queue for expected message
        result_task = self.message_task_queue.get_nowait()
        self.assertEqual(result_task.send, True)
        self.assertEqual(result_task.chat_id, self.mock_config.telegram_chat_nr)
        self.assertEqual(result_task.data_text, "Door opened!")

if __name__ == '__main__':
    unittest.main()
