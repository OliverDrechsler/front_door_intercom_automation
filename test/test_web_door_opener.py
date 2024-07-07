import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from config import config_util
from base64 import b64encode
from web.web_door_opener import WebDoorOpener

class WebDoorOpenerTestCase(unittest.TestCase):

    def setUp(self):
        # Mock configuration
        self.mock_config = MagicMock(spec=config_util.Configuration)
        self.mock_config.flask_secret_key = 'test_secret_key'
        self.mock_config.web_user_dict = {'testuser': 'testpassword'}
        self.mock_config.otp_password = 'base32secret3232'
        self.mock_config.otp_length = 6
        self.mock_config.hash_type = 'sha1'
        self.mock_config.otp_interval = 30
        self.mock_config.flask_web_port = 5002

        # Mock Blink and Auth instances
        self.mock_blink = MagicMock()
        self.mock_auth = MagicMock()

        # Create WebDoorOpener instance
        self.web_door_opener = WebDoorOpener(
            config=self.mock_config,
            blink_instance=self.mock_blink,
            blink_auth_instance=self.mock_auth
        )
        self.client = self.web_door_opener.app.test_client()
        self.web_door_opener.app.config['TESTING'] = True
        self.web_door_opener.browsers = ["werkzeug"]

    def tearDown(self):
        pass


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
            print(response.status_code)
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
            print("Response data:", response.data)
            print("Response status code:", response.status_code)
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
        with self.web_door_opener.app.app_context():
            with self.client:
                login_response = self.client.post('/login', data={
                    'username': 'testuser',
                    'password': 'testpassword'
                })
                # Extract cookies from the login response
                cookies = login_response.headers.getlist('Set-Cookie')
                session_cookie = ""
                for cookie in cookies:
                    # self.client.set_cookie(cookie.split(';')[0].split('=')[0],
                    #                        cookie.split(';')[0].split('=')[1])
                    session_cookie = cookie.split(';')[0]
                self.assertEqual(login_response.status_code, 302)  # Redirects to index
                # auth_header = {
                #     'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
                # }
                # response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})
                response = self.client.post('/open', cookie=session_cookie, json={'totp': '123456'})
                self.assertEqual(200, response.status_code)
                self.assertIn(b'TOTP is valid! Opening!', response.data)

    @patch('pyotp.TOTP.verify', return_value=True)
    def test_open_success(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = [ "api_call"]
        with self.web_door_opener.app.app_context():
            auth_header = {
                'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
            }
            response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})
            self.assertEqual(200, response.status_code)
            self.assertIn(b'TOTP is valid! Opening!', response.data)


    @patch('pyotp.TOTP.verify', return_value=False)
    def test_open_failure(self, mock_verify):
        hashed_password = generate_password_hash('testpassword')
        self.web_door_opener.users = {'testuser': hashed_password}
        self.web_door_opener.browsers = [ "api_call"]
        with self.web_door_opener.app.app_context():
            auth_header = {
                'Authorization': 'Basic ' + b64encode(b'testuser:testpassword').decode('utf-8')
            }
            response = self.client.post('/open', headers=auth_header, json={'totp': '123456'})

            self.assertEqual(response.status_code, 400)
            self.assertIn(b'Invalid TOTP. Retry again', response.data)

if __name__ == '__main__':
    unittest.main()
