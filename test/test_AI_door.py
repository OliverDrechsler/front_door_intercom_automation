import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Assuming the Door class and other necessary imports are defined elsewhere
from your_module import Door, telegram_send_message, choose_camera

class TestDoor:
    @patch('your_module.Button')
    @patch('your_module.telegram_send_message')
    @patch('your_module.choose_camera')
    def test_door_ring(self, mock_choose_camera, mock_telegram_send_message, mock_button):
        bot = MagicMock()
        blink_instance = MagicMock()
        blink_auth_instance = MagicMock()
        door = Door(bot, blink_instance, blink_auth_instance)
        mock_button.return_value.is_pressed = True
        with patch('your_module.time.sleep', side_effect=InterruptedError):
            with pytest.raises(InterruptedError):
                door.ring(test=True)
        mock_telegram_send_message.assert_called_once()
        mock_choose_camera.assert_called_once()

    @patch('your_module.Button')
    @patch('your_module.telegram_send_message')
    @patch('your_module.choose_camera')
    def test_door_ring_no_press(self, mock_choose_camera, mock_telegram_send_message, mock_button):
        bot = MagicMock()
        blink_instance = MagicMock()
        blink_auth_instance = MagicMock()
        door = Door(bot, blink_instance, blink_auth_instance)
        mock_button.return_value.is_pressed = False
        with patch('your_module.time.sleep', side_effect=InterruptedError):
            with pytest.raises(InterruptedError):
                door.ring(test=True)
        mock_telegram_send_message.assert_not_called()
        mock_choose_camera.assert_not_called()

    @patch('your_module.Button')
    @patch('your_module.telegram_send_message')
    @patch('your_module.choose_camera')
    def test_door_ring_multiple_presses(self, mock_choose_camera, mock_telegram_send_message, mock_button):
        bot = MagicMock()
        blink_instance = MagicMock()
        blink_auth_instance = MagicMock()
        door = Door(bot, blink_instance, blink_auth_instance)
        mock_button.return_value.is_pressed = True
        with patch('your_module.time.sleep', side_effect=[None, None, InterruptedError]):
            with pytest.raises(InterruptedError):
                door.ring(test=True)
        assert mock_telegram_send_message.call_count == 2
        assert mock_choose_camera.call_count == 2