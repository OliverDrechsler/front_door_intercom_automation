import unittest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash, check_password_hash
from base64 import b64encode
from web.web_door_opener import WebDoorOpener
import threading
import asyncio
import queue
import json

class WebDoorOpenerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Mock configuration
        cls.mock_config = MagicMock()
        cls.mock_config.flask_secret_key = 'test_secret_key'
        cls.mock_config.web_user_dict = {'testuser': 'testpassword'}
        cls.mock_config.otp_password = 'base32secret3232'
        cls.mock_config.otp_length = 6
        cls.mock_config.hash_type = 'sha1'
        cls.mock_config.otp_interval = 30
        cls.mock_config.flask_web_port = 0
        cls.mock_config.flask_web_host = '127.0.0.1'
        cls.mock_config.telegram_chat_nr = 123456789
        cls.mock_config.flask_browser_session_cookie_lifetime = 1

        # Mock event and queues - don't use asyncio.Queue in sync context
        cls.mock_shutdown_event = threading.Event()
        cls.mock_message_task_queue = queue.Queue()
        cls.mock_camera_task_queue_async = MagicMock()  # Mock async queue instead of real asyncio.Queue
        cls.mock_door_open_task_queue = queue.Queue()

        # Create a new event loop for each test
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

        # Create WebDoorOpener instance outside test cases
        cls.web_door_opener = WebDoorOpener(
            shutdown_event=cls.mock_shutdown_event,
            config=cls.mock_config,
            loop=cls.loop,
            message_task_queue=cls.mock_message_task_queue,
            camera_task_queue_async=cls.mock_camera_task_queue_async,
            door_open_task_queue=cls.mock_door_open_task_queue
        )

        # Test client for sending HTTP requests in tests
        cls.client = cls.web_door_opener.app.test_client()

        # Ensure the app is in testing mode
        cls.web_door_opener.app.config['TESTING'] = True
        cls.web_door_opener.browsers = ["werkzeug"]

    def setUp(self):
        # Clear session data for each test
        # Create a fresh test client for each test to isolate sessions
        self.client = self.web_door_opener.app.test_client()

    def test_transform_values(self):
        result = self.web_door_opener.transform_values(self.web_door_opener.create_password_hash)
        self.assertIn('testuser', result)
        self.assertTrue(check_password_hash(result['testuser'], 'testpassword'))

    def test_verify_password(self):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.assertTrue(self.web_door_opener.verify_password('testuser', 'testpassword'))
        self.assertFalse(self.web_door_opener.verify_password('testuser', 'wrongpassword'))

    def test_login_get(self):
        self.web_door_opener.browsers = ["werkzeug"]
        response = self.client.get('/login')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Login', response.data)

    def test_login_post_success(self):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        response = self.client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(302, response.status_code)  # Redirects to index

    def test_login_post_failure(self):
        response = self.client.post('/login', data={'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials, please try again.', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success_with_web_session(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = ["werkzeug"]
        
        # Mock the async queue put method to return a coroutine
        async def async_put(item):
            pass
        self.web_door_opener.camera_task_queue_async.put = MagicMock(side_effect=lambda item: async_put(item))
        
        login_response = self.client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
        response = self.client.post('/open', json={'totp': '123456'})
        self.assertEqual(201, response.status_code)
        self.assertIn(b'TOTP is valid! Opening!', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success_with_basic_auth(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = ["api_call"]
        
        # Mock the async queue put method to return a coroutine
        async def async_put(item):
            pass
        self.web_door_opener.camera_task_queue_async.put = MagicMock(side_effect=lambda item: async_put(item))
        
        auth_header = {
            'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
        }
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
        response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})
        self.assertEqual(400, response.status_code)
        self.assertIn(b'Invalid TOTP. Retry again -> will notify owner.', response.data)

    def test_handle_not_found(self):
        self.web_door_opener.browsers = ["werkzeug"]
        response = self.client.get('/nonexistent_endpoint')
        self.assertEqual(302, response.status_code)
        self.assertIn(b'Redirecting', response.data)
        # self.assertEqual(404, response.status_code)
        # self.assertIn(b'NotFound', response.data)

    def test_handle_unauthorized_without_session(self):
        self.web_door_opener.browsers = ["safari", "firefox", "mozilla", "chrome", "edge"]
        response = self.client.get('/open')
        self.assertEqual(401, response.status_code)
        self.assertIn(b'Unauthorized', response.data)

    def test_handle_unauthorized_with_invalid_credentials(self):
        self.web_door_opener.browsers = ["safari", "firefox", "mozilla", "chrome", "edge"]
        response = self.client.post('/open', headers={
            'Authorization': 'Basic ' + b64encode(b'invaliduser:invalidpassword').decode('utf-8')
        })
        self.assertEqual(401, response.status_code)
        self.assertIn(b'Unauthorized', response.data)

    @classmethod
    def tearDownClass(cls):
        # Stop and close the event loop
        try:
            # Cancel all remaining tasks
            pending = asyncio.all_tasks(cls.loop)
            for task in pending:
                task.cancel()
            # Run the loop one more time to process cancellations
            cls.loop.run_until_complete(asyncio.sleep(0))
            cls.loop.stop()
            cls.loop.close()
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main()
