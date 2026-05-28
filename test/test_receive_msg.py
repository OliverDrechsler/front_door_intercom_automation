import unittest
from concurrent.futures import Future
from unittest.mock import MagicMock, Mock, patch, AsyncMock
import asyncio
import threading
import queue
import telebot
from config import config_util
from config.data_class import Camera_Task, Open_Door_Task
from bot.receive_msg import ReceivingMessage


class TestReceivingMessage(unittest.TestCase):

    def setUp(self):
        self.shutdown_event = threading.Event()
        self.config = Mock(spec=config_util.Configuration)
        self.loop = asyncio.new_event_loop()
        self.camera_task_queue_async = AsyncMock(asyncio.Queue)
        self.door_open_task_queue = queue.Queue()
        self.bot = MagicMock(spec=telebot.TeleBot)
        self.bot.message_handler.side_effect = lambda *args, **kwargs: (lambda func: func)

        self.config.bot = self.bot
        self.config.telegram_chat_nr = 123456
        self.config.allowed_user_ids = [111, 222]
        self.config.otp_password = "base32secret3232"
        self.config.otp_length = 6
        self.config.hash_type = 'sha1'
        self.config.otp_interval = 30

        self.receiving_message = ReceivingMessage(
            self.shutdown_event,
            self.config,
            self.loop,
            self.camera_task_queue_async,
            self.door_open_task_queue
        )

    @staticmethod
    def _mock_run_coroutine_threadsafe(coroutine, loop):
        coroutine.close()
        future = Future()
        future.set_result(None)
        return future

    def test_start_bot_polling(self):
        self.receiving_message.bot.infinity_polling = MagicMock()
        self.receiving_message.start()
        self.receiving_message.bot.infinity_polling.assert_called_once()

    def test_stop_bot_polling(self):
        self.receiving_message.bot.stop_polling = MagicMock()
        self.receiving_message.bot.remove_webhook = MagicMock()
        self.receiving_message.stop()
        self.receiving_message.bot.stop_polling.assert_called_once()
        self.receiving_message.bot.remove_webhook.assert_called_once()

    @patch('telebot.types.Message')
    def test_receive_any_msg_text(self, MockMessage):
        mock_message = MockMessage()
        mock_message.chat.id = "123456"
        mock_message.from_user.id = "111"
        mock_message.text = "123456"

        self.receiving_message._ReceivingMessage__get_allowed = MagicMock(return_value=True)
        self.receiving_message._ReceivingMessage__validate_msg_text_has_code = MagicMock(return_value=True)

        self.receiving_message.receive_any_msg_text(mock_message)
        self.receiving_message._ReceivingMessage__validate_msg_text_has_code.assert_called_once_with(message=mock_message)

    @patch('telebot.types.Message')
    def test_take_foto(self, MockMessage):
        mock_message = MockMessage()
        mock_message.chat.id = "123456"
        mock_message.from_user.id = "111"

        self.receiving_message._ReceivingMessage__get_allowed = MagicMock(return_value=True)

        with patch('bot.receive_msg.asyncio.run_coroutine_threadsafe',
                   side_effect=self._mock_run_coroutine_threadsafe):
            self.receiving_message.take_foto(mock_message)

        self.camera_task_queue_async.put.assert_called_once()

    @patch('telebot.types.Message')
    def test_take_picam_foto(self, MockMessage):
        mock_message = MockMessage()
        mock_message.chat.id = "123456"
        mock_message.from_user.id = "111"

        self.receiving_message._ReceivingMessage__get_allowed = MagicMock(return_value=True)

        with patch('bot.receive_msg.asyncio.run_coroutine_threadsafe',
                   side_effect=self._mock_run_coroutine_threadsafe):
            self.receiving_message.take_picam_foto(mock_message)

        self.camera_task_queue_async.put.assert_called_once()

    @patch('telebot.types.Message')
    def test_take_blink_foto(self, MockMessage):
        mock_message = MockMessage()
        mock_message.chat.id = "123456"
        mock_message.from_user.id = "111"

        self.receiving_message._ReceivingMessage__get_allowed = MagicMock(return_value=True)

        with patch('bot.receive_msg.asyncio.run_coroutine_threadsafe',
                   side_effect=self._mock_run_coroutine_threadsafe):
            self.receiving_message.take_blink_foto(mock_message)

        self.camera_task_queue_async.put.assert_called_once()

    @patch('telebot.types.Message')
    def test_register_bink_authentication(self, MockMessage):
        mock_message = MockMessage()
        mock_message.chat.id = "123456"
        mock_message.from_user.id = "111"

        self.receiving_message._ReceivingMessage__get_allowed = MagicMock(return_value=True)
        self.receiving_message._ReceivingMessage__rcv_blink_auth = MagicMock()

        self.receiving_message.register_bink_authentication(mock_message)
        self.receiving_message._ReceivingMessage__rcv_blink_auth.assert_called_once_with(mock_message)

    @patch('telebot.types.Message')
    def test_rcv_blink_auth_invalid_token(self, MockMessage):
        mock_message = MockMessage()
        mock_message.text = "/blink_auth abc123"

        self.receiving_message._ReceivingMessage__rcv_blink_auth(mock_message)

        self.bot.reply_to.assert_called_once_with(message=mock_message, text="no blink token detected")

    @patch('telebot.types.Message')
    def test_get_allowed(self, MockMessage):
        mock_message = MockMessage()
        mock_message.chat.id = "123456"
        self.receiving_message._ReceivingMessage__get_allowed_user = MagicMock(return_value=True)

        result = self.receiving_message._ReceivingMessage__get_allowed(mock_message)
        self.assertTrue(result)

    @patch('telebot.types.Message')
    def test_get_allowed_user(self, MockMessage):
        mock_message = MockMessage()
        mock_message.from_user.id = "111"

        result = self.receiving_message._ReceivingMessage__get_allowed_user(mock_message)
        self.assertTrue(result)

    def test_schedule_camera_task_logs_scheduling_failure(self):
        with patch('bot.receive_msg.asyncio.run_coroutine_threadsafe',
                   side_effect=RuntimeError("loop closed")), \
                patch.object(self.receiving_message.logger, 'error') as mock_error:
            self.receiving_message._ReceivingMessage__schedule_camera_task(
                Camera_Task(chat_id="123456", reply=True, photo=True)
            )

        mock_error.assert_called_once()

    def test_validate_msg_text_has_code(self):
        mock_message = MagicMock()
        mock_message.text = "123456"

        self.receiving_message._ReceivingMessage__verify_otp_code_in_msg = MagicMock(return_value=True)

        result = self.receiving_message._ReceivingMessage__validate_msg_text_has_code(mock_message)
        self.assertTrue(result)

    @patch('telebot.types.Message')
    @patch('pyotp.TOTP.verify')
    def test_verify_otp_code_in_msg(self, MockVerify, MockMessage):
        mock_message = MockMessage()
        mock_message.text = "123456"

        MockVerify.return_value = True

        result = self.receiving_message._ReceivingMessage__verify_otp_code_in_msg(mock_message)
        self.assertTrue(result)
        self.assertFalse(self.door_open_task_queue.empty())
        task = self.door_open_task_queue.get()
        self.assertEqual(task.open, True)
        self.assertEqual(task.reply, True)
        self.assertEqual(task.chat_id, 123456)
        self.assertEqual(task.message, mock_message)


if __name__ == '__main__':
    unittest.main()
