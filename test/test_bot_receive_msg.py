import unittest
from unittest.mock import MagicMock, patch
from telebot.types import Message
from bot import receive_msg


class TestReceivingMessage(unittest.TestCase):

    @patch('bot.receive_msg.threading.Thread')
    def test_success_receive_user_mails_allowed_user_and_group(self, mock_thread):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="/username")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "/username"
        
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        receiving_message.get_allowed = MagicMock(return_value=True)
        receiving_message.receive_user_mails(message)
        
        mock_thread.assert_called_once()
        bot.reply_to.assert_called_with(message, "username - I'll start fetching new mails")

    @patch('bot.receive_msg.threading.Thread')
    def test_success_receive_user_mails_not_allowed_user_and_group(self, mock_thread):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="/username")
        message.chat = MagicMock()
        message.chat.id = "54321"
        message.from_user = MagicMock()
        message.from_user.id = "09876"
        message.text = "/username"
        
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        receiving_message.get_allowed = MagicMock(return_value=False)
        receiving_message.receive_user_mails(message)
        
        mock_thread.assert_not_called()
        bot.reply_to.assert_not_called()


    @patch('bot.receive_msg.threading.Thread')
    def test_failed_receive_msg_not_user_command(self, mock_thread):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="/unknownUser")
        message.chat = MagicMock()
        message.chat.id = "54321"
        message.from_user = MagicMock()
        message.from_user.id = "09876"
        message.text = "/unknownUser"
        
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        receiving_message.get_allowed = MagicMock(return_value=False)
        receiving_message.receive_user_mails(message)
        
        mock_thread.assert_not_called()
        bot.reply_to.assert_not_called()

    def test_failed_receive_user_mails_none_message(self):
        bot = MagicMock()
        config = MagicMock()
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        with self.assertRaises(AttributeError):
            receiving_message.receive_user_mails(None)

    @patch('bot.receive_msg.threading.Thread')
    def test_success_receive_msg_mail_request(self, mock_thread):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        config.user_dict = {"username": ["67890"]}
        config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="mail")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        receiving_message.get_allowed = MagicMock(return_value=True)
        receiving_message.receive_mail_for_requested_user(message)
        
        mock_thread.assert_called_once()
        bot.reply_to.assert_called_with(message, " - I'll start fetching new mails for username")


    @patch('bot.receive_msg.threading.Thread')
    def test_failed_receive_msg_unknown_request(self, mock_thread):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        config.user_dict = {"username": ["67890"]}
        config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="any text")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        receiving_message.get_allowed = MagicMock(return_value=False)
        receiving_message.receive_user_mails(message)
        
        mock_thread.assert_not_called()
        bot.reply_to.assert_not_called()

    def test_sucess_get_allowed_with_allowed_user_in_correct_chat(allowed_user_config):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        config.user_dict = {"username": ["67890"]}
        config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="any text")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        assert receiving_message.get_allowed(message=message) == True


    def test_failed_get_allowed_with_allowed_user_in_correct_chat(allowed_user_config):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["0911"]
        config.user_dict = {"username": ["0911"]}
        config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="any text")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        assert receiving_message.get_allowed(message=message) == False

    def test_failed_get_allowed_in_wrong_chat(allowed_user_config):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        # config.list_id = ["0911"]
        # config.user_dict = {"username": ["0911"]}
        # config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=9911,
            content_type="text",
            options={},
            json_string="any text")
        message.chat = MagicMock()
        message.chat.id = "9911"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        assert receiving_message.get_allowed(message=message) == False

    def test_failed_get_allowed_user_in_correct_chat(allowed_user_config):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["0911"]
        config.user_dict = {"username": ["0911"]}
        config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="any text")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        assert receiving_message.get_allowed_user(message=message) == False
    
    def test_success_get_allowed_user_in_correct_chat(allowed_user_config):
        bot = MagicMock()
        config = MagicMock()
        config.telegram_chat_nr = "12345"
        config.list_id = ["67890"]
        config.user_dict = {"username": ["67890"]}
        config.list_user = ["aUser"]
        message = Message(
            message_id=1,
            from_user="username",
            date=None,
            chat=12345,
            content_type="text",
            options={},
            json_string="any text")
        message.chat = MagicMock()
        message.chat.id = "12345"
        message.from_user = MagicMock()
        message.from_user.id = "67890"
        message.text = "mail"
        receiving_message = receive_msg.ReceivingMessage(bot, config)
        assert receiving_message.get_allowed_user(message=message) == True

if __name__ == '__main__':
    unittest.main()