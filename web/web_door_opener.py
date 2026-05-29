import asyncio
import hmac
import ipaddress
import logging
import os
import queue
import secrets
import threading
from functools import wraps
from datetime import datetime, timezone, timedelta

import pyotp
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session, g
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import make_server

from config import config_util
from config.data_class import Message_Task, Camera_Task, Open_Door_Task

logger: logging.Logger = logging.getLogger(name="web_door_opener")


class WebDoorOpener:

    @staticmethod
    def custom_auth_required(f):
        """
            A decorator for custom authentication required function.
        """

        @wraps(f)
        def decorator(self, *args, **kwargs):
            """
            Allows either session-based authentication for the browser UI or
            HTTP basic authentication for API clients without relying on the
            user agent.
            """
            auth_user = self.__authenticate_request()
            if auth_user is None:
                if request.endpoint == "index":
                    return redirect(url_for('login'))
                return self.__handle_401_unauthenticated()

            g.auth_user = auth_user
            return f(self, *args, **kwargs)
        return decorator

    @staticmethod
    def create_password_hash(input):
        """
        Generates a password hash using the `generate_password_hash` function.

        Parameters:
            input (str): The password to be hashed.

        Returns:
            str: The hashed password.
        """
        return generate_password_hash(input)

    def transform_values(self, func):
        """
        Transforms the values of the `web_user_dict` dictionary in the `config` object
        using the provided `func` function.

        Args:
            func (function): The function to apply to each value in the dictionary.

        Returns:
            dict: A new dictionary with the transformed values.
        """
        return {k: func(v) for k, v in self.config.web_user_dict.items()}

    def __init__(self, shutdown_event: threading.Event, config: config_util.Configuration, loop,
                 message_task_queue: queue.Queue, camera_task_queue_async: asyncio.Queue,
                 door_open_task_queue: queue.Queue) -> None:
        """
        Initializes the WebApp with the provided parameters.

        Args:
            shutdown_event (threading.Event): The event to signal shutdown.
            config (config_util.Configuration): The configuration object.
            loop: The loop object.
            message_task_queue (queue.Queue): The queue for message tasks.
            camera_task_queue_async (asyncio.Queue): The queue for camera tasks.
            door_open_task_queue (queue.Queue): The queue for door open tasks.

        Returns:
            None
        """
        self.logger: logging.Logger = logging.getLogger(name="WebApp")
        self.shutdown_event: threading.Event = shutdown_event
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue: queue.Queue = message_task_queue
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async
        self.door_open_task_queue: queue.Queue = door_open_task_queue
        self.blink_json_data: dict[any, any] = {}


        self.app = Flask(__name__)
        self.app.secret_key = self.config.flask_secret_key
        self.server = None
        self.app.permanent_session_lifetime = timedelta(days=self.config.flask_browser_session_cookie_lifetime)
        self.app.config.update(
            PERMANENT_SESSION_LIFETIME=timedelta(days=self.config.flask_browser_session_cookie_lifetime),
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE="Strict",
            SESSION_COOKIE_SECURE=True,
        )

        self.app.before_request(self.log_request_info)
        self.app.after_request(self.log_response_info)

        self.str_log_level = logging.getLevelName(logger.getEffectiveLevel())
        self.log_level = logger.getEffectiveLevel()

        self.users = self.transform_values(self.create_password_hash)
        self.__setup_logging()
        self.__setup_routes()
        self.__setup_error_handlers()

    def run(self):
        """
        Runs the server in debug mode if the log level is set to "DEBUG", otherwise runs the server in non-debug mode.

        This function checks the value of `self.str_log_level` and sets `self.app.debug` accordingly. If the log level is "DEBUG",
        the server is started in debug mode by setting `self.app.debug` to `True`. Otherwise, the server is started in
        non-debug mode by setting `self.app.debug` to `False`.

        Parameters:
            None

        Returns:
            None
        """
        self.logger.info("Start web server")
        if self.server is None:
            self.server = make_server(
                self.config.flask_web_host,
                self.config.flask_web_port,
                self.app,
            )
        if (self.str_log_level == "DEBUG"):
            self.app.debug = True
            self.server.serve_forever()
        else:
            self.app.debug = False
            self.server.serve_forever()

    def shutdown(self):
        """
        A description of the entire function, its parameters, and its return types.
        """
        self.logger.info("Shutting down web server")
        if self.server is not None:
            self.server.shutdown()
        self.logger.info("Shutting down web server - done!")

    def __setup_logging(self):
        """
        Set up the logging configuration for the application.

        This function configures the logging level of the application logger based on the value of `self.log_level`.

        Parameters:
            None

        Returns:
            None
        """
        self.app.logger.setLevel(self.log_level)

    def verify_password(self, username, password):
        """
        Verify the provided username and password for authentication.

        Parameters:
            username (str): The username to be verified.
            password (str): The password corresponding to the username.

        Returns:
            str or None: The authenticated username if successful, None otherwise.
        """
        if username in self.users and check_password_hash(self.users.get(username), password):
            self.app.logger.debug("Authentication: Success: User %s authenticated", username)
            return username
        self.app.logger.info("Authentication: Failed: User: %s - user or password wrong", username)
        self.app.logger.debug("Authentication: Failed: User %s used password %s", username, password)
        return None

    def __get_authenticated_session_user(self) -> str | None:
        """
        Returns the session user when the browser UI is authenticated.
        """
        return session.get('username')

    def __get_authenticated_basic_user(self) -> str | None:
        """
        Returns the authenticated basic auth user if valid credentials were provided.
        """
        auth = request.authorization
        if not auth:
            return None
        return self.verify_password(auth.username, auth.password)

    def __authenticate_request(self) -> str | None:
        """
        Authenticates the current request either via HTTP basic auth or via the
        existing browser session.
        """
        basic_user = self.__get_authenticated_basic_user()
        if basic_user is not None:
            return basic_user
        return self.__get_authenticated_session_user()

    @staticmethod
    def __get_or_create_csrf_token() -> str:
        """
        Stores and returns a session-bound CSRF token for browser requests.
        """
        token = session.get("csrf_token")
        if token is None:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return token

    def __is_session_authenticated(self) -> bool:
        """
        Returns True when the request is authenticated by the browser session
        and not by HTTP basic auth.
        """
        return self.__get_authenticated_basic_user() is None and self.__get_authenticated_session_user() is not None

    def __validate_csrf(self) -> bool:
        """
        Validates the CSRF token for unsafe session-authenticated requests.
        """
        expected_token = session.get("csrf_token")
        if not expected_token:
            return False

        provided_token = request.headers.get("X-CSRF-Token")
        if provided_token is None:
            if request.is_json:
                payload = request.get_json(silent=True) or {}
                provided_token = payload.get("csrf_token")
            else:
                provided_token = request.form.get("csrf_token")

        return isinstance(provided_token, str) and hmac.compare_digest(provided_token, expected_token)

    def __get_request_username(self) -> str:
        """
        Returns the authenticated user name for logging purposes.

        Returns:
            str: The username obtained from auth context or 'anonymous' if not found.
        """
        auth_user = getattr(g, "auth_user", None)
        if auth_user is not None:
            return auth_user

        authenticated_user = self.__authenticate_request()
        if authenticated_user is not None:
            g.auth_user = authenticated_user
            return authenticated_user

        return 'anonymous'

    def __get_request_remote_ip(self) -> str:
        """
        Get the remote IP address of the request.
        Only trusts X-Forwarded-For when the direct peer is a configured
        reverse proxy.
        :return: String containing the remote IP address
        """
        remote_addr = request.remote_addr or "unknown"
        trusted_proxies = set(self.config.flask_trusted_reverse_proxies)
        if remote_addr not in trusted_proxies:
            return remote_addr

        forwarded_for = request.headers.get('X-Forwarded-For')
        if not forwarded_for:
            return remote_addr

        client_ip = forwarded_for.split(",")[0].strip()
        try:
            return str(ipaddress.ip_address(client_ip))
        except ValueError:
            self.app.logger.warning("Ignoring invalid X-Forwarded-For value: %s", forwarded_for)
            return remote_addr

    def log_request_info(self):
        """
        Logs information about the incoming HTTP request.

        This function checks if the request is made from a browser session. If it is, and the user is 'anonymous' and the endpoint is not 'login', 'favicon', or 'static', it redirects to the 'login' endpoint. If the user is 'anonymous' and there is no browser session, it handles the 401 Unauthenticated error.

        After that, it logs the user, method, path, and request headers to the logger. It also logs the request data.

        Parameters:
            self (WebDoorOpener): The instance of the WebDoorOpener class.

        Returns:
            None: If the request is redirected or if the user is 'anonymous' and there is no browser session.
            redirect: If the user is 'anonymous' and the endpoint is not 'login', 'favicon', or 'static'.
            handle_401_unauthenticated: If the user is 'anonymous' and there is no browser session.
        """
        g.csp_nonce = secrets.token_urlsafe(16)
        user = self.__get_request_username()
        self.app.logger.info('Request from: %s User: %s, Method: %s, Path: %s', self.__get_request_remote_ip(), user, request.method, request.path)
        self.app.logger.debug("")
        self.app.logger.debug("======== HTTP Request: ==========")
        self.app.logger.debug("")
        self.app.logger.info('User: %s, Method: %s, Path: %s', user, request.method, request.path)
        self.app.logger.debug('Request Headers: %s', request.headers)
        self.app.logger.debug('Request Data: %s', request.get_data())
        self.app.logger.debug("======== HTTP Request END ==========")

        if request.endpoint == 'login':
            self.__get_or_create_csrf_token()

        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and self.__is_session_authenticated():
            if not self.__validate_csrf():
                return self.__handle_bad_request(message="CSRF validation failed.")

        if request.endpoint in ['favicon', 'static']:
            return None

        if user == 'anonymous':
            if request.endpoint == 'login':
                return None
            if request.endpoint == 'index':
                return redirect(url_for('login'))
            return self.__handle_401_unauthenticated()

    def log_response_info(self, response):
        """
        Logs the response information including user, method, path, status, headers, and response data.
        """
        user = self.__get_request_username()

        self.app.logger.debug("")
        self.app.logger.debug("======== HTTP Response: ==========")
        self.app.logger.debug("")
        self.app.logger.info('User: %s, Method: %s, Path: %s, Status: %s', user, request.method, request.path,
                             response.status)
        self.app.logger.debug('Response Headers: %s', response.headers)

        if (request.endpoint not in ['favicon', 'static']):
            self.app.logger.debug('Response Data: %s', response.get_data(as_text=True))
        self.app.logger.debug("======== HTTP Response END ==========")

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{g.csp_nonce}'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "manifest-src 'self'"
        )

        return response

    def login(self) -> str:
        """
        Login method for interactive browser sessions
        :return: html login page as string
        :rtype: str
        """
        if request.method == 'POST':
            if not self.__validate_csrf():
                return render_template("login_invalid.html", csrf_token=self.__get_or_create_csrf_token()), 400

            username = request.form['username']
            password = request.form['password']
            if username in self.users and check_password_hash(self.users.get(username), password):
                session.clear()
                session.permanent = True
                session['username'] = username
                session['csrf_token'] = secrets.token_urlsafe(32)
                return redirect(url_for('index'))
            else:
                return render_template("login_invalid.html", csrf_token=self.__get_or_create_csrf_token())

        return render_template("login.html", csrf_token=self.__get_or_create_csrf_token())

    def favicon(self):
        """
        A function to serve the favicon file by sending it from the static directory.
        """
        return send_from_directory(os.path.join(self.app.root_path, 'static'), 'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')

    @custom_auth_required
    def index(self) -> str:
        """
        A function that returns the homepage HTML content as a string after ensuring custom authentication.
        """
        return render_template("homepage.html", csrf_token=self.__get_or_create_csrf_token(), csp_nonce=g.csp_nonce)

    @custom_auth_required
    def open(self):
        """
        A function to open the door when a valid TOTP code is provided.

        This function is decorated with `@custom_auth_required`, which ensures that the user is authenticated before accessing this endpoint.

        Parameters:
            None

        Returns:
            - If the provided TOTP code is valid, the function sends a message to open the door and takes a photo, and returns a success response with status code 201 and a message "TOTP is valid! Opening!".
            - If the provided TOTP code is invalid, the function sends a message indicating the invalid TOTP code and returns a bad request response with a message "Invalid TOTP. Retry again -> will notify owner.".
        """
        auth_user = self.__get_request_username()
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return self.__handle_bad_request(message="Request body must be valid JSON.")
        web_input_totp = data.get('totp')
        totp_config = pyotp.TOTP(s=self.config.otp_password, digits=self.config.otp_length,
                                 digest=self.config.hash_type, interval=self.config.otp_interval)
        if totp_config.verify(web_input_totp):
            self.app.logger.info('User %s send TOTP %s is valid -> will open', auth_user, web_input_totp)
            self.door_open_task_queue.put(Open_Door_Task(open=True, chat_id=self.config.telegram_chat_nr))
            self.message_task_queue.put(Message_Task(send=True, chat_id=self.config.telegram_chat_nr,
                                                     data_text=f"{auth_user} request open door"))
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(
                self.camera_task_queue_async.put(Camera_Task(photo=True, chat_id=self.config.telegram_chat_nr)),
                self.loop)
            return self.__handle_success_response(status_text="success", status=201, message="TOTP is valid! Opening!")
        else:
            self.app.logger.warning('User %s send invalid TOTP %s', auth_user, web_input_totp)
            self.message_task_queue.put(Message_Task(send=True, chat_id=self.config.telegram_chat_nr,
                                                     data_text=f"{auth_user} request TOTP code is invalid!"))
            return self.__handle_bad_request(message="Invalid TOTP. Retry again -> will notify owner.")

    def handle_exception(self, e):
        """
        Default error exception handler for any error response.
        Results in http status code 500 - internal server error
        :param e: Error
        :return: http json response
        :rtype: json
        """
        self.app.logger.error('Error: %s', str(e), exc_info=True)
        if isinstance(e, HTTPException):
            return jsonify(self.__error_response_json(status=e.code, error=e.name, message=e.description)), e.code
        return jsonify(self.__error_response_json(
            status=500,
            error="Internal Server Error",
            message="An internal server error occurred."
        )), 500

    def handle_not_found(self, error):
        """
        A method to handle the not found error response.
        :param error: Error object describing the not found error
        :return: JSON response with status 404 and error details
        :rtype: json
        """
        self.app.logger.error('Error: %s', str(error), exc_info=True)
        return jsonify(self.__error_response_json(status=404, error="NotFound", message=error.description)), 404

    def __handle_401_unauthenticated(self):
        """
        Generates a JSON response for a 401 Unauthorized error.

        This function sets the status code of the response to 401, sets the 'WWW-Authenticate' header to 'Basic realm="Main"',
        and sets the 'Location' header to the URL of the login page.

        Returns:
            The JSON response with the error details.

        """
        status = 401
        resp = jsonify(self.__error_response_json(status=status, error="Unauthorized",
            message="Access Diened for resource! Authenticate first or send basic Authroization header."))
        resp.status_code = status
        resp.headers['WWW-Authenticate'] = 'Basic realm="Main"'
        resp.headers['Location'] = request.host_url + 'login'
        return resp

    def __handle_bad_request(self, message: str):
        """
        A method to handle a bad request error response.

        :param message: A string message describing the bad request error.
        :return: JSON response with status 400, error details, and the status code 400.
        :rtype: json
        """
        return jsonify(self.__error_response_json(status=400, error="Bad Request", message=message)), 400

    def __error_response_json(self, status, error, message) -> dict:
        """
        Returns a standard error response json
        :param status: Http Status code
        :param error: Error Code text
        :param message: Error message
        :return: dictonary
        :rtype: dict
        """
        return {'timestamp': datetime.now(tz=timezone.utc), 'status': status, 'error': error, 'message': message}

    def __handle_success_response(self, status_text, status, message):
        """
        Handles to create a success json http response
        :param status_text: Http status code text
        :param status: http status code integer
        :param message: a response message or dict
        :return: json
        """
        return jsonify({'timestamp': datetime.now(tz=timezone.utc), 'status': status, 'statusText': status_text,
            'message': message}), status

    def __setup_routes(self):
        """
        Setup routes for various URLs in the web application.
        """
        self.app.add_url_rule('/favicon.ico', 'favicon', self.favicon)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/open', 'open', self.open, methods=['POST'])

    def __setup_error_handlers(self):
        """
        Setup error handlers for the Flask application.

        Registers error handlers for the `Exception` and `NotFound` exceptions.
        The `handle_exception` method is called when an `Exception` occurs,
        and the `handle_not_found` method is called when a `NotFound` exception occurs.

        This method does not take any parameters.

        This method does not return anything.
        """
        self.app.register_error_handler(Exception, self.handle_exception)
        self.app.register_error_handler(NotFound, self.handle_not_found)
