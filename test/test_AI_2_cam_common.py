from unittest.mock import patch

class TestDaylightDetection:
    @pytest.fixture
    def config_class_instance(self):
        class ConfigClass:
            pass
        return ConfigClass()

    @patch('astral.sun.sun')
    def test_daylight_detected_true(self, mock_sun, config_class_instance, mocker):
        config_class_instance.enable_detect_daylight = True
        mock_sun.return_value = {'sunrise': datetime(2023, 6, 21, 6, 0, tzinfo=timezone.utc), 'sunset': datetime(2023, 6, 21, 18, 0, tzinfo=timezone.utc)}
        mocker.patch('datetime.datetime.now', return_value=datetime(2023, 6, 21, 12, 0, tzinfo=timezone.utc))
        assert daylight_detected(config_class_instance) == True

    @patch('astral.sun.sun')
    def test_daylight_detected_false(self, mock_sun, config_class_instance, mocker):
        config_class_instance.enable_detect_daylight = True
        mock_sun.return_value = {'sunrise': datetime(2023, 6, 21, 6, 0, tzinfo=timezone.utc), 'sunset': datetime(2023, 6, 21, 18, 0, tzinfo=timezone.utc)}
        mocker.patch('datetime.datetime.now', return_value=datetime(2023, 12, 21, 12, 0, tzinfo=timezone.utc))
        assert daylight_detected(config_class_instance) == False

    def test_daylight_detected_disabled(self, config_class_instance):
        config_class_instance.enable_detect_daylight = False
        assert daylight_detected(config_class_instance) == False