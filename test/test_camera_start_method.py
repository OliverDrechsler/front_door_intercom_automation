import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from config.data_class import Camera_Task, Message_Task
from config.config_util import Configuration
from camera.camera import Camera


@pytest.fixture
def camera_setup():
    # Setup
    config = Configuration()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    camera_queue = asyncio.Queue()
    message_queue = MagicMock()

    with patch('camera.camera.Blink') as mock_blink, \
         patch('camera.camera.Auth') as mock_auth, \
         patch('camera.camera.json_load') as mock_json_load, \
         patch('camera.camera.aiohttp.ClientSession') as mock_session:

        mock_blink_instance = AsyncMock()
        mock_blink_instance.start = AsyncMock()
        mock_blink.return_value = mock_blink_instance

        camera = Camera(config, loop, camera_queue, message_queue)

        mock_session_instance = AsyncMock()
        mock_session_instance.close = AsyncMock()
        mock_session.return_value = mock_session_instance
        camera.session = mock_session_instance

        async def mock_read_config():
            camera.blink.auth = AsyncMock()
            return

        camera.read_blink_config = mock_read_config
        
        yield camera, camera_queue, message_queue

    # Teardown
    loop.close()


@pytest.mark.asyncio
async def test_start_picam_photo(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.picam_enabled = True
    camera.picam_request_take_foto = MagicMock(return_value=True)
    camera.picam_request_download_foto = MagicMock(return_value=True)
    test_task = Camera_Task(picam_photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)  # Stoppsignal
    
    await camera.start()
    
    camera.picam_request_take_foto.assert_called_once()
    camera.picam_request_download_foto.assert_called_once()
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.photo is True
    assert call_args.chat_id == 123456


@pytest.mark.asyncio
async def test_start_choose_cam(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.picam_enabled = True
    camera.choose_cam = MagicMock(return_value=True)
    test_task = Camera_Task(photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)

    await camera.start()

    camera.choose_cam.assert_called_once()


@pytest.mark.asyncio
async def test_start_blink_photo(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.blink_enabled = True
    camera._blink_foto_helper = MagicMock(return_value=True)
    test_task = Camera_Task(blink_photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)

    await camera.start()

    camera._blink_foto_helper.assert_called_once()


@pytest.mark.asyncio
async def test_start_blink_mfa_success(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.blink_enabled = True
    camera.add_2fa_blink_token = AsyncMock(return_value=True)
    camera.save_blink_config = AsyncMock(return_value=True)
    mock_logger_info = MagicMock()
    mock_logger_debug = MagicMock()
    mock_logger_error = MagicMock()
    camera.logger.info = mock_logger_info
    camera.logger.debug = mock_logger_debug
    camera.logger.error = mock_logger_error
    test_task = Camera_Task(blink_mfa=True, chat_id=12345678)
    await camera_queue.put(test_task)
    await camera_queue.put(None)

    await camera.start()

    camera.add_2fa_blink_token.assert_called_once()
    camera.save_blink_config.assert_called_once()
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.reply is True
    assert call_args.chat_id == 12345678
    assert call_args.data_text == 'blink MFA added'
    mock_logger_info.assert_any_call("asyncthread received task: Camera_Task(chat_id=12345678, message=None, reply=False, photo=False, blink_photo=False, picam_photo=False, blink_mfa=True)")
    mock_logger_info.assert_any_call("processing task.blink_mfa: True")
    mock_logger_debug.assert_any_call("start blink session")
    mock_logger_debug.assert_any_call("add session to blink")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")
    mock_logger_debug.assert_any_call("Async Processing Camera_Task with data: Camera_Task(chat_id=12345678, message=None, reply=False, photo=False, blink_photo=False, picam_photo=False, blink_mfa=True)")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")


@pytest.mark.asyncio
async def test_start_blink_mfa_saved_failed(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.blink_enabled = True
    camera.add_2fa_blink_token = AsyncMock(return_value=True)
    camera.save_blink_config = AsyncMock(return_value=False)
    mock_logger_info = MagicMock()
    mock_logger_debug = MagicMock()
    mock_logger_error = MagicMock()
    camera.logger.info = mock_logger_info
    camera.logger.debug = mock_logger_debug
    camera.logger.error = mock_logger_error
    test_task = Camera_Task(blink_mfa=True, chat_id=12345678)
    await camera_queue.put(test_task)
    await camera_queue.put(None)

    await camera.start()

    camera.add_2fa_blink_token.assert_called_once()
    camera.save_blink_config.assert_called_once()
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.reply is True
    assert call_args.chat_id == 12345678
    assert call_args.data_text == 'an error occured during blink MFA processing'
    mock_logger_info.assert_any_call(
        "asyncthread received task: Camera_Task(chat_id=12345678, message=None, reply=False, photo=False, blink_photo=False, picam_photo=False, blink_mfa=True)")
    mock_logger_info.assert_any_call("processing task.blink_mfa: True")
    mock_logger_debug.assert_any_call("start blink session")
    mock_logger_debug.assert_any_call("add session to blink")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")
    mock_logger_debug.assert_any_call(
        "Async Processing Camera_Task with data: Camera_Task(chat_id=12345678, message=None, reply=False, photo=False, blink_photo=False, picam_photo=False, blink_mfa=True)")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")


@pytest.mark.asyncio
async def test_start_blink_mfa_add_2fa_blink_token_failed(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.blink_enabled = True
    camera.add_2fa_blink_token = AsyncMock(return_value=False)
    mock_logger_info = MagicMock()
    mock_logger_debug = MagicMock()
    mock_logger_error = MagicMock()
    camera.logger.info = mock_logger_info
    camera.logger.debug = mock_logger_debug
    camera.logger.error = mock_logger_error
    test_task = Camera_Task(blink_mfa=True, chat_id=12345678)
    await camera_queue.put(test_task)
    await camera_queue.put(None)

    await camera.start()

    camera.add_2fa_blink_token.assert_called_once()
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.reply is True
    assert call_args.chat_id == 12345678
    assert call_args.data_text == 'an error occured during blink MFA processing'
    mock_logger_info.assert_any_call(
        "asyncthread received task: Camera_Task(chat_id=12345678, message=None, reply=False, photo=False, blink_photo=False, picam_photo=False, blink_mfa=True)")
    mock_logger_info.assert_any_call("processing task.blink_mfa: True")
    mock_logger_debug.assert_any_call("start blink session")
    mock_logger_debug.assert_any_call("add session to blink")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")
    mock_logger_debug.assert_any_call(
        "Async Processing Camera_Task with data: Camera_Task(chat_id=12345678, message=None, reply=False, photo=False, blink_photo=False, picam_photo=False, blink_mfa=True)")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")

@pytest.mark.asyncio
async def test_start_blink_mfa_add_2fa_blink_token_failed(camera_setup):
    camera, camera_queue, message_queue = camera_setup
    camera.config.picam_enabled = True
    camera._picam_foto_helper = AsyncMock(side_effect=Exception('picam_request_take_foto'))
    test_task = Camera_Task(picam_photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)
    mock_logger_info = MagicMock()
    mock_logger_debug = MagicMock()
    mock_logger_error = MagicMock()
    camera.logger.info = mock_logger_info
    camera.logger.debug = mock_logger_debug
    camera.logger.error = mock_logger_error
    test_task = Camera_Task(blink_mfa=True, chat_id=12345678)
    await camera_queue.put(test_task)
    await camera_queue.put(None)

    await camera.start()

    camera._picam_foto_helper.assert_called_once()
    mock_logger_info.assert_any_call(
        "asyncthread received task: Camera_Task(chat_id=123456, message=None, reply=False, photo=False, blink_photo=False, picam_photo=True, blink_mfa=False)")
    mock_logger_info.assert_any_call("processing task.picam_photo: True")
    mock_logger_info.assert_any_call("no task")
    mock_logger_debug.assert_any_call("start blink session")
    mock_logger_debug.assert_any_call("add session to blink")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")
    mock_logger_debug.assert_any_call(
        "Async Processing Camera_Task with data: Camera_Task(chat_id=123456, message=None, reply=False, photo=False, blink_photo=False, picam_photo=True, blink_mfa=False)")
    mock_logger_debug.assert_any_call("camera_task_queue_async get task")
    mock_logger_error.assert_any_call("Error: picam_request_take_foto")