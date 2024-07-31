import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from config import config_util
from config.config_util import Configuration
from config.yaml_read_error import YamlReadError
from base64 import b64encode
from web.web_door_opener import WebDoorOpener
import threading
import asyncio
import queue
import random

class WebDoorOpenerTestCase(unittest.TestCase):

    # @classmethod
    def setUp(self):
        # Mock configuration
        self.mock_config = MagicMock(spec=config_util.Configuration)
        self.mock_config.flask_secret_key = 'test_secret_key'
        self.mock_config.web_user_dict = {'testuser': 'testpassword'}
        self.mock_config.otp_password = 'base32secret3232'
        self.mock_config.otp_length = 6
        self.mock_config.hash_type = 'sha1'
        self.mock_config.otp_interval = 30
        self.mock_config.flask_web_port = 0
        self.mock_config.flask_web_host = '127.0.0.1'
        self.mock_config.telegram_chat_nr = 123456789
        self.mock_config.flask_browser_session_cookie_lifetime = 1

        # Mock event and queues
        self.mock_shutdown_event = threading.Event()
        self.mock_message_task_queue = queue.Queue()
        self.mock_camera_task_queue_async = asyncio.Queue()
        self.mock_door_open_task_queue = queue.Queue()

        # Create WebDoorOpener instance
        self.web_door_opener = WebDoorOpener(
            shutdown_event=self.mock_shutdown_event,
            config=self.mock_config,
            loop=asyncio.get_event_loop(),
            message_task_queue=self.mock_message_task_queue,
            camera_task_queue_async=self.mock_camera_task_queue_async,
            door_open_task_queue=self.mock_door_open_task_queue
        )
        self.client = self.web_door_opener.app.test_client()
        self.web_door_opener.app.config['TESTING'] = True
        self.web_door_opener.browsers = ["werkzeug"]

    # @classmethod
    # def tearDown(self):
    #     # self.web_door_opener.app.app_context().pop()
    #     pass

    def test_transform_values(self):
        with self.web_door_opener.app.app_context():
            result = self.web_door_opener.transform_values(self.web_door_opener.create_password_hash)
            self.assertIn('testuser', result)
            self.assertTrue(check_password_hash(result['testuser'], 'testpassword'))

    def test_verify_password(self):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        with self.web_door_opener.app.app_context():
            self.assertIsNotNone(self.web_door_opener.verify_password('testuser', 'testpassword'))
            self.assertIsNone(self.web_door_opener.verify_password('testuser', 'wrongpassword'))

    def test_login_get(self):
        with self.web_door_opener.app.app_context():
            response = self.client.get('/login')
            self.assertEqual(200, response.status_code)
            self.assertIn(b'Login', response.data)

    def test_login_post_success(self):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        with self.web_door_opener.app.app_context():
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            self.assertEqual(response.status_code, 302)  # Redirects to index

    def test_login_post_failure(self):
        with self.web_door_opener.app.app_context():
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Invalid credentials, please try again.', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success_with_web_session(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = ["werkzeug"]
        with self.client:
            login_response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            # Extract cookies from the login response
            cookies = login_response.headers.getlist('Set-Cookie')
            self.client.set_cookie(cookies[0])
            self.assertEqual(login_response.status_code, 302)  # Redirects to index
            response = self.client.post('/open', json={'totp': '123456'})
            self.assertEqual(201, response.status_code)
            self.assertIn(b'TOTP is valid! Opening!', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = ["api_call"]
        auth_header = {
            'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
        }
        with self.web_door_opener.app.app_context():
            response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})
            self.assertEqual(201, response.status_code)
            self.assertIn(b'TOTP is valid! Opening!', response.data)

    @patch('pyotp.TOTP.verify', return_value=False)
    def test_open_failure(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = ["api_call"]
        auth_header = {
            'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
        }
        with self.web_door_opener.app.app_context():
            response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})
            self.assertEqual(response.status_code, 400)
            self.assertIn(b'Invalid TOTP. Retry again -> will notify owner.', response.data)


if __name__ == '__main__':
    unittest.main()






