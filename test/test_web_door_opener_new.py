import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from config import config_util
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from bot import send_msg
from door import opener
import pyotp
# from web import web_door_opener
from web.web_door_opener import WebDoorOpener
import telebot


class TestWebDoorOpener(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock(spec=config_util.Configuration)
        self.config.web_user_dict = {"test_user": "test_password"}
        self.config.flask_secret_key = "test_secret"
        self.config.otp_password = "base32secret3232"
        self.config.otp_length = 6
        self.config.hash_type = "sha1"
        self.config.otp_interval = 30
        self.config.door_summer = "door_summer"
        self.config.run_on_raspberry = False
        self.config.telegram_chat_nr = "test_chat_nr"
        self.config.flask_web_port = 5000

        self.bot = MagicMock(spec=telebot.TeleBot)
        self.blink = MagicMock(spec=Blink)
        self.auth = MagicMock(spec=Auth)

        self.web_door_opener = WebDoorOpener(self.config, self.bot, self.blink, self.auth)
        self.app = self.web_door_opener.app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        self.web_door_opener.browsers = ["werkzeug"]

    def test_create_password_hash(self):
        password = "test_password"
        hashed_password = WebDoorOpener.create_password_hash(password)
        self.assertTrue(check_password_hash(hashed_password, password))

    def test_transform_values(self):
        transformed_users = self.web_door_opener.transform_values(WebDoorOpener.create_password_hash)
        for k, v in self.config.web_user_dict.items():
            self.assertTrue(check_password_hash(transformed_users[k], v))

    def test_verify_password_success(self):
        password_hash = WebDoorOpener.create_password_hash("test_password")
        self.web_door_opener.users = {"test_user": password_hash}
        self.assertEqual(self.web_door_opener.verify_password("test_user", "test_password"), "test_user")

    def test_verify_password_failure(self):
        self.web_door_opener.users = {"test_user": "wrong_password_hash"}
        self.assertIsNone(self.web_door_opener.verify_password("test_user", "test_password"))

    @patch('web_door_opener.request')
    def test_get_request_username_anonymous(self, mock_request):
        mock_request.authorization = None
        mock_request.headers.get.return_value = "some_user_agent"
        with self.app.test_request_context('/'):
            self.assertEqual(self.web_door_opener.get_request_username(), 'anonymous')

    @patch('web_door_opener.request')
    @patch('web_door_opener.session')
    def test_get_request_username_session(self, mock_session, mock_request):
        mock_request.headers.get.return_value = "chrome"
        mock_session.get.return_value = "test_user"
        with self.app.test_request_context('/'):
            self.assertEqual(self.web_door_opener.get_request_username(), 'test_user')

    @patch('web_door_opener.request')
    @patch('web_door_opener.session')
    def test_login_success(self, mock_session, mock_request):
        password_hash = WebDoorOpener.create_password_hash("test_password")
        self.web_door_opener.users = {"test_user": password_hash}
        mock_request.method = 'POST'
        mock_request.form = {'username': 'test_user', 'password': 'test_password'}
        with self.app.test_request_context('/login', method='POST'):
            response = self.web_door_opener.login()
            self.assertEqual(response.status_code, 302)
            self.assertTrue(mock_session.__setitem__.called)

    @patch('web_door_opener.request')
    def test_login_failure(self, mock_request):
        password_hash = WebDoorOpener.create_password_hash("test_password")
        self.web_door_opener.users = {"test_user": password_hash}
        mock_request.method = 'POST'
        mock_request.form = {'username': 'test_user', 'password': 'wrong_password'}
        with self.app.test_request_context('/login', method='POST'):
            response = self.web_door_opener.login()
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Invalid credentials, please try again.', response.data)

    @patch('web_door_opener.pyotp.TOTP.verify')
    @patch('web_door_opener.opener.open_door')
    @patch('web_door_opener.send_msg.telegram_send_message')
    @patch('web_door_opener.request')
    def test_open_success(self, mock_request, mock_send_msg, mock_open_door, mock_verify):
        mock_verify.return_value = True
        mock_request.get_json.return_value = {'totp': 'valid_totp'}
        mock_request.authorization = None
        mock_request.headers.get.return_value = "some_user_agent"
        with self.app.test_request_context('/open', method='POST'):
            response = self.web_door_opener.open()
            self.assertEqual(response.status_code, 201)
            mock_open_door.assert_called_once()
            mock_send_msg.assert_called_once()

    @patch('web_door_opener.pyotp.TOTP.verify')
    @patch('web_door_opener.send_msg.telegram_send_message')
    @patch('web_door_opener.request')
    def test_open_failure(self, mock_request, mock_send_msg, mock_verify):
        mock_verify.return_value = False
        mock_request.get_json.return_value = {'totp': 'invalid_totp'}
        mock_request.authorization = None
        mock_request.headers.get.return_value = "some_user_agent"
        with self.app.test_request_context('/open', method='POST'):
            response = self.web_door_opener.open()
            self.assertEqual(response.status_code, 400)
            mock_send_msg.assert_called_once()


if __name__ == '__main__':
    unittest.main()
