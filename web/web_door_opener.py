import logging
import os
from datetime import datetime, timezone, timedelta

import pyotp
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, \
    url_for, session
from flask_httpauth import HTTPBasicAuth
from werkzeug.exceptions import NotFound
from werkzeug.security import generate_password_hash, check_password_hash

from config import config_util
from door import opener
from config.data_class import Message_Task, Camera_Task, Open_Door_Task
import asyncio
import queue

logger: logging.Logger = logging.getLogger(name="web_door_opener")
app = Flask(__name__)
auth = HTTPBasicAuth()


class WebDoorOpener:

    @staticmethod
    def custom_auth_required(f):
        def decorator(self, *args, **kwargs):
            user_agent = request.headers.get('User-Agent')
            if any(browser in user_agent.lower() for browser in self.browsers):
                if 'username' not in session:
                    return redirect(url_for('login'))
            else:
                auth = request.authorization
                if not auth or not self.verify_password(auth.username, auth.password):
                    return self.handle_401_unauthenticated()
            return f(self, *args, **kwargs)

        decorator.__name__ = f.__name__
        return decorator

    @staticmethod
    def create_password_hash(input):
        """
        Generates a scrypt password hash with werkzeug.security

        :param input: given password
        :type x: str
        :return: scrypt hashed password
        :rtype: str
        """
        return generate_password_hash(input)

    def __init__(self,
                 config: config_util.Configuration,
                 loop,
                 message_task_queue: queue.Queue,
                 camera_task_queue_async: asyncio.Queue,
                 door_open_task_queue: queue.Queue
                 ) -> None:
        self.loop = loop
        self.message_task_queue: queue.Queue = message_task_queue
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async
        self.door_open_task_queue: queue.Queue = door_open_task_queue
        self.blink_json_data: dict[any, any] = {}
        self.config: config_util.Configuration = config
        self.app = app
        self.app.permanent_session_lifetime = timedelta(days=self.config.flask_browser_session_cookie_lifetime)
        self.auth = auth
        self.browsers = ["safari", "firefox", "mozilla", "chrome", "edge"]
        self.str_log_level = logging.getLevelName(logger.getEffectiveLevel())
        self.log_level = logger.getEffectiveLevel()
        self.app.secret_key = self.config.flask_secret_key
        self.users = self.transform_values(self.create_password_hash)
        self.setup_logging()
        self.setup_routes()
        self.setup_error_handlers()

    def transform_values(self, func):
        """
        Transforms all values of a dict with the given fuction.

        :param d: Dictionary, that will be transformed
        :param func: Funktion, that will be applied on the value
        :return: new dictonary with transformed values
        """
        return {k: func(v) for k, v in self.config.web_user_dict.items()}

    def setup_logging(self):
        self.app.logger.setLevel(self.log_level)

    def verify_password(self, username, password):
        if username in self.users and check_password_hash(self.users.get(username), password):
            self.app.logger.debug("Authentication: Success: User %s authenticated", username)
            return username
        self.app.logger.info("Authentication: Failed: User: %s - user or password wrong", username)
        self.app.logger.debug("Authentication: Failed: User %s used password %s", username, password)
        return None

    def get_brwoser_session(self) -> bool:
        """
        Get http request user agent header to identify if it's interactive user seseeion.
        :return: Boolean
        :rtype: bool
        """
        user_agent = request.headers.get('User-Agent')
        if any(browser in user_agent.lower() for browser in self.browsers):
            return True
        return False

    def get_request_username(self) -> str:
        """
        Get http request username.
        Either it's a http basic auth from request or if browser session exists it get extracted from browser
        session login username. If none could be extraced it assumes to be anonymous and returns it.
        :return: userme
        :rtype: str
        """
        if self.get_brwoser_session():
            return session.get('username', 'anonymous')
        else:
            req_auth = request.authorization
            try:
                return req_auth.username
            except AttributeError:
                return 'anonymous'

    def log_request_info(self):
        """
        Logs incoming http request
        :return: none
        """
        browser_session = self.get_brwoser_session()
        user = self.get_request_username()
        if browser_session:
            if (user == 'anonymous' and request.endpoint not in ['login', 'favicon', 'static']):
                return redirect(url_for('login'))
        else:
            if (user == 'anonymous'):
                return self.handle_401_unauthenticated()

        self.app.logger.debug("")
        self.app.logger.debug("======== HTTP Request: ==========")
        self.app.logger.debug("")
        self.app.logger.info('User: %s, Method: %s, Path: %s', user, request.method, request.path)
        self.app.logger.debug('Request Headers: %s', request.headers)
        self.app.logger.debug('Request Data: %s', request.get_data())
        self.app.logger.debug("======== HTTP Request END ==========")

    def log_response_info(self, response):
        """
        Logs outgoing http response
        :return: none
        """
        user = self.get_request_username()

        self.app.logger.debug("")
        self.app.logger.debug("======== HTTP Response: ==========")
        self.app.logger.debug("")
        self.app.logger.info('User: %s, Method: %s, Path: %s, Status: %s',
                             user, request.method, request.path, response.status)
        self.app.logger.debug('Response Headers: %s', response.headers)

        if (request.endpoint not in ['favicon', 'static']):
            self.app.logger.debug('Response Data: %s', response.get_data(as_text=True))
        self.app.logger.debug("======== HTTP Response END ==========")

        return response

    def login(self) -> str:
        """
        Login method for interactive browser seesions
        :return: html login page as string
        :rtype: str
        """
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username in self.users and check_password_hash(self.users.get(username), password):
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template("login_invalid.html")

        return render_template("login.html")

    def favicon(self):
        """
        Get favicon for browser - bookmarks
        :return:
        """
        return send_from_directory(os.path.join(self.app.root_path, 'static'), 'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')

    @custom_auth_required
    def index(self) -> str:
        """
        Get / default page
        :return: homepage
        :rtype: str
        """
        return render_template("homepage.html")

    @custom_auth_required
    def open(self):
        """
        Get's timebased onetime password to open door.

        :return: Http json response
        :rtype: json
        """
        auth_user = self.get_request_username()
        # auth_user = self.auth.current_user()
        data = request.get_json()
        web_input_totp = data.get('totp')
        totp_config = pyotp.TOTP(s=self.config.otp_password,
                                 digits=self.config.otp_length,
                                 digest=self.config.hash_type,
                                 interval=self.config.otp_interval)
        if totp_config.verify(web_input_totp):
            self.app.logger.info('User %s send TOTP %s is valid -> will open', auth_user, web_input_totp)
            self.door_open_task_queue.put(Open_Door_Task(open=True, chat_id=self.config.telegram_chat_nr))
            self.message_task_queue.put(Message_Task(send=True,
                                                     chat_id=self.config.telegram_chat_nr,
                                                     data_text=f"User {auth_user} web request TOTP code {web_input_totp} " +
                                           f"accepted - opening door"
                                                     ))
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(
                    photo=True,
                    chat_id=self.config.telegram_chat_nr
                )
            ),
                self.loop)
            return self.handle_success_response(status_text="success",
                                                status=201,
                                                message="TOTP is valid! Opening!")
        else:
            self.app.logger.warning('User %s send invalid TOTP %s', auth_user, web_input_totp)
            self.message_task_queue.put(Message_Task(send=True,
                                                  chat_id=self.config.telegram_chat_nr,
                                                  data_text=f"User {auth_user} web request TOTP code " +
                                                  f"{web_input_totp} invalid!"
                                                  ))
            return self.handle_bad_request(message="Invalid TOTP. Retry again -> will notify owner.")

    def handle_exception(self, e):
        """
        Default error exception handler for any error response.
        Results in http status code 500 - internal server error
        :param e: Error
        :return: http json response
        :rtype: json
        """
        self.app.logger.error('Error: %s', str(e), exc_info=True)
        return jsonify(self.error_response_json(
            status=500,
            error="Internal Server Error",
            message=str(e)
        )), 500

    def handle_not_found(self, error):
        """
        Handles not found http 404 response.
        :param error: The error
        :return: http json response
        :rtype: json
        """
        self.app.logger.error('Error: %s', str(error), exc_info=True)
        return jsonify(self.error_response_json(
            status=404,
            error="NotFound",
            message=error.description
        )), 404

    def handle_401_unauthenticated(self):
        """
        Hadles unauthenticated http 401 response
        :return: http json response
        :rtype: json
        """
        status = 401
        resp = jsonify(self.error_response_json(
            status=status,
            error="Unauthorized",
            message="Access Diened for resource! Authenticate first or send basic Authroization header."))
        resp.status_code = status
        resp.headers['WWW-Authenticate'] = 'Basic realm="Main"'
        resp.headers['Location'] = request.host_url + 'login'
        return resp

    def handle_bad_request(self, message: str):
        """
        Handles Http 400 bad request responses
        :param message: str
        :return: json
        """
        return jsonify(self.error_response_json(
            status=400,
            error="Bad Request",
            message=message
        )), 400

    def error_response_json(self, status, error, message) -> dict:
        """
        Returns a standard error response json
        :param status: Http Status code
        :param error: Error Code text
        :param message: Error message
        :return: dictonary
        :rtype: dict
        """
        return {
            'timestamp': datetime.now(tz=timezone.utc),
            'status': status,
            'error': error,
            'message': message
        }

    def handle_success_response(self, status_text, status, message):
        """
        Handles to create a success json http response
        :param status_text: Http status code text
        :param status: http status code integer
        :param message: a response message or dict
        :return: json
        """
        return jsonify(
            {
                'timestamp': datetime.now(tz=timezone.utc),
                'status': status,
                'statusText': status_text,
                'message': message
            }
        ), status

    def setup_routes(self):
        """
        Setup flask
        - logging
        - app routes
        - authentication
        :return: none
        """
        self.app.before_request(self.log_request_info)
        self.app.after_request(self.log_response_info)
        self.auth.verify_password(self.verify_password)
        self.app.add_url_rule('/favicon.ico', 'favicon', self.favicon)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/open', 'open', self.open, methods=['POST'])

    def setup_error_handlers(self):
        """
        Setup flask error handler http resonses
        :return: none
        """
        self.app.register_error_handler(Exception, self.handle_exception)
        self.app.register_error_handler(NotFound, self.handle_not_found)

    def run(self):
        """
        start method of flask
        :return: none
        """
        if (self.str_log_level == "DEBUG"):
            self.app.run(debug=True, port=self.config.flask_web_port, use_reloader=False)
        else:
            self.app.run(debug=False, port=self.config.flask_web_port, use_reloader=False)

# def run_web_app():
#     app = WebDoorOpener()
#     app.run()
#
# if __name__ == '__main__':
#     thread = threading.Thread(target=run_web_app)
#     thread.start()
#     thread.join()  # Ensure the main thread waits for the Flask thread to finish
