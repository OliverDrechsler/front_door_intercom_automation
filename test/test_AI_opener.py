import pytest
from unittest.mock import patch, MagicMock

# Assuming the open_door function is defined in a module named door_opener
from door_opener import open_door

class TestOpenDoor:
    @patch("door_opener.GPIO")
    @patch("door_opener.logger")
    def test_open_door_on_raspberry(self, mock_logger, mock_gpio):
        assert open_door(17, True) == True
        mock_logger.info.assert_called_with("opening the door")
        mock_gpio.setmode.assert_called_with(mock_gpio.BCM)
        mock_gpio.setup.assert_called_with(17, mock_gpio.OUT)
        mock_gpio.output.assert_called_with(17, mock_gpio.HIGH)

    @patch("door_opener.GPIO")
    @patch("door_opener.logger")
    def test_open_door_not_on_raspberry(self, mock_logger, mock_gpio):
        assert open_door(17, False) == False
        mock_logger.info.assert_called_with("not running on raspberry pi - will not open the door")
        mock_gpio.setmode.assert_not_called()

    @patch("door_opener.GPIO")
    @patch("door_opener.logger")
    def test_open_door_invalid_gpio_port(self, mock_logger, mock_gpio):
        mock_gpio.setup.side_effect = ValueError("Invalid GPIO port")
        with pytest.raises(ValueError):
            open_door(-1, True)
        mock_logger.info.assert_called_with("opening the door")