import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import threading
import queue
from config import config_util
from config.data_class import Message_Task
import telebot
from bot.send_msg import SendMessage

class TestSendMessage(unittest.TestCase):

    def setUp(self):
        self.shutdown_event = threading.Event()
        self.config = Mock(spec=config_util.Configuration)
        self.loop = Mock()
        self.message_task_queue = queue.Queue()
        self.config.bot = Mock(spec=telebot.TeleBot)
        self.send_message_instance = SendMessage(
            shutdown_event=self.shutdown_event,
            config=self.config,
            loop=self.loop,
            message_task_queue=self.message_task_queue
        )

    def test_initialization(self):
        self.assertEqual(self.send_message_instance.config, self.config)
        self.assertEqual(self.send_message_instance.loop, self.loop)
        self.assertEqual(self.send_message_instance.message_task_queue, self.message_task_queue)
        self.assertEqual(self.send_message_instance.bot, self.config.bot)
        self.assertEqual(self.send_message_instance.stop_polling, self.shutdown_event)

    @patch('logging.Logger.info')
    @patch('logging.Logger.debug')
    def test_start(self, mock_debug, mock_info):
        task = Message_Task(send=True, reply=False, photo=False, chat_id="123", data_text="Hello")
        self.message_task_queue.put(task)
        self.message_task_queue.put(None)  # Signal to stop the loop

        self.send_message_instance.send_message = Mock()

        self.send_message_instance.start()

        self.send_message_instance.send_message.assert_called_once_with(chat_id="123", text="Hello")
        mock_debug.assert_called()
        mock_info.assert_called()

    @patch('logging.Logger.info')
    def test_stop(self, mock_info):
        self.send_message_instance.stop()
        self.send_message_instance.bot.stop_polling.assert_called_once()
        self.send_message_instance.bot.remove_webhook.assert_called_once()
        mock_info.assert_called()

    @patch('logging.Logger.info')
    def test_send_message(self, mock_info):
        chat_id = "123"
        text = "Hello"
        self.send_message_instance.send_message(chat_id=chat_id, text=text)
        self.send_message_instance.bot.send_message.assert_called_once_with(chat_id=chat_id, text=text)
        mock_info.assert_called_with("send message : Hello")

    @patch('logging.Logger.info')
    def test_reply_message(self, mock_info):
        chat_id = "123"
        text = "Reply"
        message = Mock(spec=telebot.types.Message)
        self.send_message_instance.reply_message(chat_id=chat_id, text=text, message=message)
        self.send_message_instance.bot.reply_to.assert_called_once_with(message=message, text=text)
        mock_info.assert_called_with("reply message : Reply")

    @patch('logging.Logger.info')
    @patch('builtins.open', new_callable=mock_open)
    def test_send_photo(self, mock_open, mock_info):
        chat_id = "123"
        image_path = "path/to/photo.jpg"
        self.send_message_instance.send_photo(chat_id=chat_id, image_path=image_path)
        self.send_message_instance.bot.send_photo.assert_called_once_with(chat_id=chat_id, photo=open(image_path, 'rb'))
        mock_info.assert_called()
        call_args_list = mock_info.call_args_list
        contains_send_foto = any("send a foto" in str(call) for call in call_args_list)
        self.assertTrue(contains_send_foto, "Expected string 'send a foto' not found in logger calls")


if __name__ == '__main__':
    unittest.main()
