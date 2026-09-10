from __future__ import annotations

import base64
import json
import logging
import os
import sys
from collections import ChainMap
from typing import Any

import telebot
import yaml

from config.default_cam_enum import DefaultCam
from config.yaml_read_error import YamlReadError

logger = logging.getLogger("config")


class Configuration:
    """Reads gerneral yaml Config file into class."""

    def __init__(self) -> None:
        """Initial class definition.

        Read from config.yaml file it configuration into class attribute
        config dict and from there into multiple attributes.
        :return: Nothing adds class instance attribues
        :rtype: None
        """
        self.logger = logging.getLogger("config")
        self.base_path = self.__get_base_path()
        self.bundle_base_path = self.__get_bundle_base_path()
        self.config_file = self.__define_config_file()
        self.config_dir = os.path.dirname(self.config_file)
        self.config = self.__read_config(self.config_file)

        self.bot: telebot.TeleBot = None

        self.admin_users: list[str] = self.config.get("general", {}).get("admin_users", [])
        self.telegram_token: str = self.config["telegram"]["token"]
        self.telegram_chat_nr = self.config["telegram"]["chat_number"]
        self.allowed_user_ids = self.__get_allowed_user_dict()
        self.user_state_file: str = self.__resolve_runtime_path(
            self.config.get("general", {}).get("user_state_file", "user_state.json")
        )

        self.otp_password: str = self.config["otp"]["password"]
        self.otp_length: int = self.config["otp"]["length"]
        self.otp_interval: int = self.config["otp"]["interval"]
        self.hash_type: str = self.config["otp"]["hash_type"]

        self.run_on_raspberry: bool = self.config["GPIO"]["run_on_raspberry"]
        self.door_bell: int = self.config["GPIO"]["door_bell_port"]
        self.door_bell_enabled: bool = self.config["GPIO"]["enable_door_bell_port"]
        self.door_bell_bounce_time: int = self.config["GPIO"]["door_bell_bounce_time"]
        self.door_summer: int = self.config["GPIO"]["door_opener_port"]
        self.door_summer_enabled: bool = self.config["GPIO"]["enable_door_opener_port"]
        self.testing_bell_msg: bool = self.config["GPIO"]["testing_msg"]

        self.photo_image_path: str = self.config["photo_general"]["image_path"]
        self.default_camera_type = DefaultCam(self.config["photo_general"]["default_camera_type"].upper())
        self.enable_detect_daylight: bool = self.config["photo_general"]["enable_detect_daylight"]
        self.timezone: str = self.config["photo_general"]["timezone"]  # Timezone name for daylight detection
        self.country: str = self.config["photo_general"]["country"]  # Country name for timezone and daylight detection
        self.city: str = self.config["photo_general"].get("city", None)  # City name for timezone and daylight detection
        self.lat: float = self.config["photo_general"].get("lat", None)  # optional value see config_template.yaml for more information
        self.lon: float = self.config["photo_general"].get("lon", None)  # optional value see config_template.yaml for more information
        self.image_brightness: float = self.config["photo_general"].get("brightness_enhancer", None)  # optional value see config_template.yaml for more information
        self.image_contrast: float = self.config["photo_general"].get("contrast_enhancer", None)  # optional value see config_template.yaml for more information

        self.blink_enabled: bool = self.config["blink"]["enabled"]
        self.blink_username: str = self.config["blink"]["username"]
        self.blink_password: str = self.config["blink"]["password"]
        self.blink_name: str = self.config["blink"]["name"]
        self.blink_config_file: str = self.__resolve_runtime_path(self.config["blink"]["config_file"])
        self.blink_night_vision: bool = self.config["blink"]["night_vision"]
        self.blink_image_brightening: bool = self.config["blink"].get("image_brightening", False) # optional value see config_template.yaml for more information

        self.picam_enabled: bool = self.config["picam"]["enabled"]
        self.picam_url: str = self.config["picam"]["url"]
        self.picam_image_width: int = self.config["picam"]["image_width"]
        self.picam_image_hight: int = self.config["picam"]["image_hight"]
        self.picam_image_filename: str = self.config["picam"]["image_filename"]
        self.picam_exposure: str = self.config["picam"]["exposure"]
        self.picam_rotation: int = self.config["picam"]["rotation"]
        self.picam_iso: int = self.config["picam"]["iso"]
        self.picam_night_vision: bool = self.config["picam"]["night_vision"]
        self.picam_image_brightening: bool = self.config["picam"].get("image_brightening", False)  # optional value see config_template.yaml for more information

        self.web_user_dict: dict[str, str] = self.__get_web_user_dict()
        self.flask_enabled: bool = self.config["web"]["enabled"]
        self.flask_web_host: str = self.config["web"]["flask_web_host"]
        self.flask_web_port: int = self.config["web"]["flask_web_port"]
        self.flask_secret_key: str = self.config["web"]["flask_secret_key"]
        self.flask_browser_session_cookie_lifetime: int = self.config["web"]["browser_session_cookie_lifetime"]
        self.flask_session_cookie_secure: bool = self.config["web"].get("session_cookie_secure", False)
        self.flask_trusted_reverse_proxies: list[str] = self.config["web"].get("trusted_reverse_proxies", [])

    def __get_allowed_user_dict(self) -> dict[str, str]:
        """Get configured telegram users as username to user-id mapping."""
        allowed_user_ids = self.config["telegram"].get("allowed_user_ids", {})
        if not isinstance(allowed_user_ids, dict):
            raise YamlReadError("telegram.allowed_user_ids must be a dictionary of username to user id")
        return {str(username): str(user_id) for username, user_id in allowed_user_ids.items()}

    def get_telegram_user_state(self) -> dict[str, list[str]]:
        """
        Load enabled/disabled telegram users from the runtime json file.
        Missing files are initialized with all configured users enabled.
        """
        if not os.path.exists(self.user_state_file):
            return self.__initialize_user_state()["telegram"]
        return self.__get_user_state_for_domain(
            domain="telegram",
            allowed_users=list(self.allowed_user_ids.keys()),
            admin_users=self.__get_domain_admin_users(self.allowed_user_ids),
        )

    def write_telegram_user_state(self, state: dict[str, list[str]]) -> None:
        """Persist enabled/disabled telegram users into the runtime json file."""
        self.__write_user_state_for_domain(
            domain="telegram",
            state=state,
            allowed_users=list(self.allowed_user_ids.keys()),
            admin_users=self.__get_domain_admin_users(self.allowed_user_ids),
        )

    def get_web_user_state(self) -> dict[str, list[str]]:
        """Load enabled/disabled web users from the runtime json file."""
        if not os.path.exists(self.user_state_file):
            return self.__initialize_user_state()["web"]
        return self.__get_user_state_for_domain(
            domain="web",
            allowed_users=list(self.web_user_dict.keys()),
            admin_users=self.__get_domain_admin_users(self.web_user_dict),
        )

    def write_web_user_state(self, state: dict[str, list[str]]) -> None:
        """Persist enabled/disabled web users into the runtime json file."""
        self.__write_user_state_for_domain(
            domain="web",
            state=state,
            allowed_users=list(self.web_user_dict.keys()),
            admin_users=self.__get_domain_admin_users(self.web_user_dict),
        )

    def __initialize_user_state(self) -> dict[str, dict[str, list[str]]]:
        """Create and normalize the shared state for all configured user domains."""
        raw_state = self.__read_user_state_raw()
        state = {
            "telegram": self.__normalize_domain_user_state(
            state=raw_state.get("telegram", {}),
            allowed_users=list(self.allowed_user_ids.keys()),
            admin_users=self.__get_domain_admin_users(self.allowed_user_ids),
            ),
            "web": self.__normalize_domain_user_state(
            state=raw_state.get("web", {}),
            allowed_users=list(self.web_user_dict.keys()),
            admin_users=self.__get_domain_admin_users(self.web_user_dict),
            ),
        }
        self.__write_user_state_raw(state)
        return state

    def __get_domain_admin_users(self, users: dict[str, Any]) -> list[str]:
        """Return configured admin names using the domain's canonical casing."""
        users_by_casefold = {str(username).casefold(): str(username) for username in users}
        return [
            users_by_casefold[admin_user.casefold()]
            for admin_user in map(str, self.admin_users)
            if admin_user.casefold() in users_by_casefold
        ]

    def __normalize_domain_user_state(
        self,
        state: dict[str, Any],
        allowed_users: list[str],
        admin_users: list[str],
    ) -> dict[str, list[str]]:
        """Normalize enabled/disabled user state for one domain."""
        allowed_lookup = {str(username).casefold(): str(username) for username in allowed_users}

        enabled_input = state.get("enabled", []) if isinstance(state, dict) else []
        disabled_input = state.get("disabled", []) if isinstance(state, dict) else []
        if not isinstance(enabled_input, list):
            enabled_input = []
        if not isinstance(disabled_input, list):
            disabled_input = []

        enabled: list[str] = []
        for username in enabled_input:
            username_key = allowed_lookup.get(str(username).casefold())
            if username_key and username_key not in enabled:
                enabled.append(username_key)

        disabled: list[str] = []
        for username in disabled_input:
            username_key = allowed_lookup.get(str(username).casefold())
            if username_key and username_key not in disabled:
                disabled.append(username_key)

        enabled = [username for username in enabled if username not in disabled]

        if not enabled and not disabled and allowed_users:
            enabled = list(allowed_users)

        for admin_user in admin_users:
            if admin_user in allowed_users and admin_user not in enabled:
                enabled.append(admin_user)
            disabled = [user for user in disabled if user != admin_user]

        return {"enabled": enabled, "disabled": disabled}

    def __read_user_state_raw(self) -> dict[str, Any]:
        """Read the shared user state JSON document."""
        if not os.path.exists(self.user_state_file):
            return {}

        with open(self.user_state_file, "r", encoding="utf-8") as json_file:
            raw_state = json.load(json_file)

        if not isinstance(raw_state, dict):
            return {}

        # Accept the original single-domain document if it is already at the
        # configured shared state-file location.
        if "telegram" not in raw_state and "web" not in raw_state and (
            "enabled" in raw_state or "disabled" in raw_state
        ):
            return {"telegram": raw_state}

        return raw_state

    def __write_user_state_raw(self, raw_state: dict[str, Any]) -> None:
        """Write full raw user state document."""
        with open(self.user_state_file, "w", encoding="utf-8") as json_file:
            json.dump(raw_state, json_file, indent=4)

    def __get_user_state_for_domain(self, domain: str, allowed_users: list[str], admin_users: list[str]) -> dict[str, list[str]]:
        """Get normalized state for one domain and persist normalization if required."""
        raw_state = self.__read_user_state_raw()
        domain_state = raw_state.get(domain, {}) if isinstance(raw_state, dict) else {}
        normalized_state = self.__normalize_domain_user_state(
            state=domain_state if isinstance(domain_state, dict) else {},
            allowed_users=allowed_users,
            admin_users=admin_users,
        )

        if not isinstance(raw_state, dict):
            raw_state = {}
        if raw_state.get(domain) != normalized_state:
            raw_state[domain] = normalized_state
            self.__write_user_state_raw(raw_state)

        return normalized_state

    def __write_user_state_for_domain(
        self,
        domain: str,
        state: dict[str, list[str]],
        allowed_users: list[str],
        admin_users: list[str],
    ) -> None:
        """Normalize and persist one domain state while preserving other domains."""
        raw_state = self.__read_user_state_raw()
        if not isinstance(raw_state, dict):
            raw_state = {}

        raw_state[domain] = self.__normalize_domain_user_state(
            state=state,
            allowed_users=allowed_users,
            admin_users=admin_users,
        )
        self.__write_user_state_raw(raw_state)

    def get_camera_config_state(self) -> dict[str, Any]:
        """Return current camera-related runtime configuration."""
        return {
            "photo_general": {
                "default_camera_type": self.default_camera_type.value.lower(),
                "enable_detect_daylight": self.enable_detect_daylight,
            },
            "blink": {
                "enabled": self.blink_enabled,
                "night_vision": self.blink_night_vision,
                "image_brightening": self.blink_image_brightening,
            },
            "picam": {
                "enabled": self.picam_enabled,
                "night_vision": self.picam_night_vision,
                "image_brightening": self.picam_image_brightening,
            },
        }

    def switch_default_camera_type(self) -> str:
        """Toggle default camera type between blink and picam and persist the config."""
        new_camera_type = "picam" if self.default_camera_type == DefaultCam.BLINK else "blink"
        return self.set_default_camera_type(new_camera_type)

    def set_default_camera_type(self, camera_type: str) -> str:
        """Set photo_general.default_camera_type to blink or picam and persist the config."""
        normalized_camera_type = str(camera_type).strip().lower()
        if normalized_camera_type not in ("blink", "picam"):
            raise ValueError("default_camera_type must be blink or picam")

        self.config["photo_general"]["default_camera_type"] = normalized_camera_type
        self.default_camera_type = DefaultCam(normalized_camera_type.upper())
        self.__write_full_yaml_config()
        return normalized_camera_type

    def set_camera_bool_option(self, section: str, option: str, value: bool) -> bool:
        """Set a camera-related bool option and persist the config."""
        allowed_options: dict[str, dict[str, str]] = {
            "photo_general": {"enable_detect_daylight": "enable_detect_daylight"},
            "blink": {
                "enabled": "blink_enabled",
                "night_vision": "blink_night_vision",
                "image_brightening": "blink_image_brightening",
            },
            "picam": {
                "enabled": "picam_enabled",
                "night_vision": "picam_night_vision",
                "image_brightening": "picam_image_brightening",
            },
        }
        section_key = str(section).strip().lower()
        option_key = str(option).strip().lower()
        section_mapping = allowed_options.get(section_key)
        if section_mapping is None or option_key not in section_mapping:
            raise ValueError(f"unsupported camera option: {section}.{option}")

        bool_value = bool(value)
        self.config[section_key][option_key] = bool_value
        setattr(self, section_mapping[option_key], bool_value)
        self.__write_full_yaml_config()
        return bool_value

    def __get_web_user_dict(self) -> dict:
        """Get user dict from list of yaml telegram.list

        :return: dict of user key and values of telegram id
        :rtype: dict
        """
        flask_users = self.config["web"].get("flask_users", [])
        if not isinstance(flask_users, list):
            raise YamlReadError("web.flask_users must be a list of dictionaries")
        if not flask_users:
            return {}
        if not all(isinstance(entry, dict) for entry in flask_users):
            raise YamlReadError("web.flask_users must contain only dictionaries")
        return dict(ChainMap(*flask_users))

    def __get_base_path(self) -> str:
        """
        Get the runtime base path.

        For PyInstaller binaries this is the directory of the executable.
        For source execution this is the project root.
        """
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable)) + "/"
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"

    def __get_bundle_base_path(self) -> str:
        """
        Get the path containing bundled application resources.

        In a PyInstaller onefile build this points to the temporary extraction
        directory. In source execution it equals the project root.
        """
        if getattr(sys, "frozen", False):
            return getattr(sys, "_MEIPASS", self.base_path) + "/"
        return self.base_path

    def __read_config(self, config_file: str) -> dict[str, Any]:
        """
        Reads config.yaml file into variables.

        :params config_file: the config file to be read
        :type config_file: string
        :return: Noting - adds class attribute self.config dictionary
          from config yaml file
        :rtype: None
        """
        self.logger.debug("reading config {0} file info dict".format(config_file))
        try:
            with open(file=config_file, mode="r") as file:
                return yaml.load(file, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            self.logger.error("Could not find %s", self.config_file)
            raise FileNotFoundError("Could not find config file")
        except yaml.YAMLError as err:
            self.logger.error("a YAML error is occured during parsing file %s ", self.config_file)
            raise YamlReadError("a YAML error is occured during parsing file") from err

    def __define_config_file(self) -> str:
        """
        Checks and defines Config yaml file path.

        :return: adds a new class path attribute for the config file.
        :rtype: None
        """
        self.logger.debug("checking if config.yaml file exists")
        config_candidates: list[str] = []
        launch_dir = os.getcwd() + "/"

        for candidate in (
            launch_dir + "config.yaml",
            self.base_path + "config.yaml",
            self.bundle_base_path + "config.yaml",
        ):
            if candidate not in config_candidates:
                config_candidates.append(candidate)

        for candidate in config_candidates:
            if os.path.isfile(candidate):
                self.logger.info("Using config file: %s", candidate)
                return candidate

        self.logger.info("No config.yaml file detected. Using" + " temeplate one.")
        template_candidates: list[str] = []
        for candidate in (
            launch_dir + "config_template.yaml",
            self.base_path + "config_template.yaml",
            self.bundle_base_path + "config_template.yaml",
        ):
            if candidate not in template_candidates:
                template_candidates.append(candidate)

        for candidate in template_candidates:
            if os.path.exists(candidate):
                self.logger.info("Using template config file: %s", candidate)
                return candidate

        if not os.path.exists(self.base_path + "config_template.yaml"):
            raise (NameError("No config file found!"))
        return self.base_path + "config_template.yaml"

    def __resolve_runtime_path(self, path: str) -> str:
        """
        Resolve relative runtime files against the active config directory.
        """
        if os.path.isabs(path):
            return path
        return os.path.join(self.config_dir, path)

    def __base32_encode_totp_password(self, new_password):
        """
        Encodes a new provided password into BASE32 string

        :param new_password: new provided TOTP ASCII password
        :type new_password: string
        """
        return (base64.b32encode(new_password.upper().encode("UTF-8"))).decode("UTF-8")

    def __write_yaml_config(self, new_password):
        """Writes or updates the config.yaml file with the new provided TOTP password

        :param new_password: new provided TOTP ASCII password
        :type new_password: string
        """
        target_config_file = self.config_file
        if target_config_file.endswith("config_template.yaml"):
            target_config_file = os.path.join(self.base_path, "config.yaml")
        self.config["otp"]["password"] = self.__base32_encode_totp_password(new_password)
        self.__write_full_yaml_config(target_config_file=target_config_file)

    def __write_full_yaml_config(self, target_config_file: str | None = None) -> None:
        """Persist the complete in-memory yaml configuration to disk."""
        target_file = target_config_file or self.config_file
        if target_file.endswith("config_template.yaml"):
            target_file = os.path.join(self.base_path, "config.yaml")

        with open(target_file, "w") as yaml_file:
            yaml.dump(self.config, yaml_file, default_flow_style=False, sort_keys=False)
