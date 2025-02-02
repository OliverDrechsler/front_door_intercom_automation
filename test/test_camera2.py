import pytest
import asyncio
import queue
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from config.config_util import Configuration, DefaultCam
from config.data_class import Camera_Task, Message_Task
from camera.camera import Camera

@pytest.fixture
def config():
    config = Mock(spec=Configuration)
    config.blink_enabled = True
    config.picam_enabled = True
    config.enable_detect_daylight = False
    config.default_camera_type = DefaultCam.BLINK
    config.photo_image_path = "/tmp/test.jpg"
    config.blink_name = "test_camera"
    config.timezone = "Europe/Berlin"
    config.location = "Berlin"
    return config


@pytest.fixture
def camera(config):
    loop = asyncio.get_event_loop()
    camera_queue = asyncio.Queue()
    message_queue = queue.Queue()
    return Camera(config, loop, camera_queue, message_queue)


@pytest.mark.asyncio
async def test_blink_foto_helper_success(camera):
    task = Camera_Task(photo=True, chat_id=123)
    
    with patch.object(camera, 'blink_snapshot', new_callable=AsyncMock) as mock_snapshot:
        mock_snapshot.return_value = True
        
        result = await camera._blink_foto_helper(task)
        
        assert result == True
        mock_snapshot.assert_called_once()
        assert not camera.message_task_queue.empty()


@pytest.mark.asyncio
async def test_blink_foto_helper_failure(camera):
    task = Camera_Task(photo=True, chat_id=123)
    
    with patch.object(camera, 'blink_snapshot', new_callable=AsyncMock) as mock_snapshot:
        mock_snapshot.return_value = False
        
        result = await camera._blink_foto_helper(task)
        
        assert result == False
        mock_snapshot.assert_called_once()
        assert not camera.message_task_queue.empty()


@pytest.mark.asyncio
async def test_picam_foto_helper_success(camera):
    task = Camera_Task(photo=True, chat_id=123)
    
    with patch.object(camera, 'picam_request_take_foto') as mock_take_foto:
        with patch.object(camera, 'picam_request_download_foto') as mock_download_foto:
            mock_take_foto.return_value = True
            mock_download_foto.return_value = True
            
            result = await camera._picam_foto_helper(task)
            
            assert result == True
            mock_take_foto.assert_called_once()
            mock_download_foto.assert_called_once()
            assert not camera.message_task_queue.empty()


def test_detect_daylight(camera):
    with patch('camera.camera.sun') as mock_sun:
        # Simuliere Tageslicht
        current_time = datetime.now(tz=ZoneInfo(camera.config.timezone))  # Konvertiere String zu ZoneInfo
        mock_sun.return_value = {
            'sunrise': current_time.replace(hour=6),
            'sunset': current_time.replace(hour=20)
        }
        
        result = camera.detect_daylight()
        assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_choose_cam_default_blink(camera):
    task = Camera_Task(photo=True, chat_id=123)
    camera.config.enable_detect_daylight = False
    camera.config.default_camera_type = DefaultCam.BLINK
    
    with patch.object(camera, '_blink_foto_helper', new_callable=AsyncMock) as mock_blink:
        mock_blink.return_value = True
        
        await camera.choose_cam(task)
        
        mock_blink.assert_called_once_with(task)


@pytest.mark.asyncio
async def test_choose_cam_default_picam(camera):
    task = Camera_Task(photo=True, chat_id=123)
    camera.config.enable_detect_daylight = False
    camera.config.default_camera_type = DefaultCam.PICAM
    
    with patch.object(camera, '_picam_foto_helper', new_callable=AsyncMock) as mock_picam:
        mock_picam.return_value = True
        
        await camera.choose_cam(task)
        
        mock_picam.assert_called_once_with(task)


def test_put_msg_queue_photo(camera):
    task = Camera_Task(photo=True, chat_id=123, reply=True, message="test")
    camera.put_msg_queue_photo(task)
    
    msg = camera.message_task_queue.get_nowait()
    assert isinstance(msg, Message_Task)
    assert msg.photo == True
    assert msg.chat_id == 123


def test_put_msg_queue_error(camera):
    task = Camera_Task(photo=True, chat_id=123, reply=True, message="test")
    error_message = "Test error"
    camera.put_msg_queue_error(task, error_message)
    
    msg = camera.message_task_queue.get_nowait()
    assert isinstance(msg, Message_Task)
    assert msg.reply == True
    assert msg.data_text == error_message
    assert msg.chat_id == 123