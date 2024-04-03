import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

# Assuming the function daylight_detected and necessary imports are defined elsewhere

class TestDaylightDetection:
    @pytest.fixture
    def config_class_instance(self):
        class ConfigClass:
            pass
        return ConfigClass()

    def test_daylight_detected_true(self, config_class_instance, mocker):
        config_class_instance.enable_detect_daylight = True
        mocker.patch('datetime.datetime.now', return_value=datetime(2023, 6, 21, 12, 0, tzinfo=timezone.utc))
        assert daylight_detected(config_class_instance) == True

    def test_daylight_detected_false(self, config_class_instance, mocker):
        config_class_instance.enable_detect_daylight = True
        mocker.patch('datetime.datetime.now', return_value=datetime(2023, 12, 21, 12, 0, tzinfo=timezone.utc))
        assert daylight_detected(config_class_instance) == False

    def test_daylight_detected_disabled(self, config_class_instance):
        config_class_instance.enable_detect_daylight = False
        assert daylight_detected(config_class_instance) == False