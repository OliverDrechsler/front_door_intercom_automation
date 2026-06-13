import unittest
from unittest.mock import patch, MagicMock
from base64 import b64encode
from web.web_door_opener import WebDoorOpener
import threading
import asyncio
import queue

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
        cls.mock_config.flask_session_cookie_secure = False
        cls.mock_config.flask_trusted_reverse_proxies = ['127.0.0.1']

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

    def _get_csrf_token(self):
        self.client.get('/login')
        with self.client.session_transaction() as session:
            return session['csrf_token']

    def test_verify_password(self):
        self.web_door_opener.users = {'testuser': 'testpassword'}
        self.assertTrue(self.web_door_opener.verify_password('testuser', 'testpassword'))
        self.assertFalse(self.web_door_opener.verify_password('testuser', 'wrongpassword'))

    def test_login_get(self):
        self.web_door_opener.browsers = ["werkzeug"]
        response = self.client.get('/login')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Login', response.data)

    def test_login_post_success(self):
        self.web_door_opener.users = {'testuser': 'testpassword'}
        csrf_token = self._get_csrf_token()
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'csrf_token': csrf_token,
        })
        self.assertEqual(302, response.status_code)  # Redirects to index

    def test_login_post_failure(self):
        csrf_token = self._get_csrf_token()
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
            'csrf_token': csrf_token,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials, please try again.', response.data)

    def test_login_post_missing_csrf_fails(self):
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword',
        })
        self.assertEqual(400, response.status_code)
        self.assertIn(b'Invalid credentials, please try again.', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success_with_web_session(self, mock_verify):
        self.web_door_opener.users = {'testuser': 'testpassword'}
        self.web_door_opener.browsers = ["werkzeug"]
        
        # Mock the async queue put method to return a coroutine
        async def async_put(item):
            pass
        self.web_door_opener.camera_task_queue_async.put = MagicMock(side_effect=lambda item: async_put(item))

        csrf_token = self._get_csrf_token()
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'csrf_token': csrf_token,
        })
        with self.client.session_transaction() as session:
            open_csrf_token = session['csrf_token']

        response = self.client.post('/open', json={'totp': '123456'}, headers={
            'X-CSRF-Token': open_csrf_token,
        })
        self.assertEqual(201, response.status_code)
        self.assertIn(b'TOTP is valid! Opening!', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success_with_basic_auth(self, mock_verify):
        self.web_door_opener.users = {'testuser': 'testpassword'}
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

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_with_basic_auth_verifies_password_once_per_request(self, mock_verify):
        self.web_door_opener.users = {'testuser': 'hashed-password'}

        async def async_put(item):
            pass

        self.web_door_opener.camera_task_queue_async.put = MagicMock(side_effect=lambda item: async_put(item))

        auth_header = {
            'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
        }

        with patch.object(self.web_door_opener, 'verify_password', return_value='testuser') as mock_verify_password:
            response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})

        self.assertEqual(201, response.status_code)
        self.assertEqual(1, mock_verify_password.call_count)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_with_web_session_missing_csrf_fails(self, mock_verify):
        self.web_door_opener.users = {'testuser': 'testpassword'}

        csrf_token = self._get_csrf_token()
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'csrf_token': csrf_token,
        })
        response = self.client.post('/open', json={'totp': '123456'})
        self.assertEqual(400, response.status_code)
        self.assertIn(b'CSRF validation failed.', response.data)

    @patch('pyotp.TOTP.verify', return_value=False)
    def test_open_failure(self, mock_verify):
        self.web_door_opener.users = {'testuser': 'testpassword'}
        self.web_door_opener.browsers = ["api_call"]
        auth_header = {
            'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
        }
        response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})
        self.assertEqual(400, response.status_code)
        self.assertIn(b'Invalid TOTP. Retry again -> will notify owner.', response.data)

    def test_open_rejects_invalid_json(self):
        self.web_door_opener.users = {'testuser': 'testpassword'}
        auth_header = {
            'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
        }
        response = self.client.post('/open', headers=auth_header, data='not-json', content_type='application/json')
        self.assertEqual(400, response.status_code)
        self.assertIn(b'Request body must be valid JSON.', response.data)

    def test_handle_not_found(self):
        self.web_door_opener.users = {'testuser': 'testpassword'}
        csrf_token = self._get_csrf_token()
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'csrf_token': csrf_token,
        })
        response = self.client.get('/nonexistent_endpoint')
        self.assertEqual(404, response.status_code)
        self.assertIn(b'NotFound', response.data)

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

    def test_login_response_contains_security_headers(self):
        response = self.client.get('/login')
        self.assertEqual('nosniff', response.headers['X-Content-Type-Options'])
        self.assertEqual('DENY', response.headers['X-Frame-Options'])
        self.assertEqual('strict-origin-when-cross-origin', response.headers['Referrer-Policy'])
        self.assertEqual('no-store', response.headers['Cache-Control'])
        self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])

    def test_login_uses_configured_non_secure_session_cookie_for_http(self):
        response = self.client.get('/login')
        self.assertIn('HttpOnly', response.headers['Set-Cookie'])
        self.assertNotIn('Secure', response.headers['Set-Cookie'])

    def test_log_request_info_redacts_form_secrets(self):
        with self.web_door_opener.app.test_request_context(
            '/login',
            method='POST',
            data={
                'username': 'testuser',
                'password': 'testpassword',
                'csrf_token': 'csrf-secret',
            },
        ):
            sanitized = self.web_door_opener._WebDoorOpener__get_sanitized_request_data()

        self.assertEqual(
            sanitized,
            b'username=testuser&password=%2A%2A%2A&csrf_token=%2A%2A%2A',
        )

    def test_get_request_remote_ip_uses_trusted_forwarded_for(self):
        with self.web_door_opener.app.test_request_context(
            '/',
            headers={'X-Forwarded-For': '203.0.113.10, 127.0.0.1'},
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        ):
            remote_ip = self.web_door_opener._WebDoorOpener__get_request_remote_ip()
        self.assertEqual('203.0.113.10', remote_ip)

    def test_get_request_remote_ip_ignores_untrusted_forwarded_for(self):
        with self.web_door_opener.app.test_request_context(
            '/',
            headers={'X-Forwarded-For': '203.0.113.10'},
            environ_base={'REMOTE_ADDR': '10.0.0.55'},
        ):
            remote_ip = self.web_door_opener._WebDoorOpener__get_request_remote_ip()
        self.assertEqual('10.0.0.55', remote_ip)

    def test_handle_exception_hides_internal_error_details(self):
        with self.web_door_opener.app.test_request_context('/'):
            response, status_code = self.web_door_opener.handle_exception(RuntimeError('secret stack detail'))
        self.assertEqual(500, status_code)
        self.assertIn(b'An internal server error occurred.', response.data)
        self.assertNotIn(b'secret stack detail', response.data)

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
