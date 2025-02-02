import asyncio
import pytest
from unittest.mock import MagicMock, patch
from config.data_class import Camera_Task, Message_Task
from config.config_util import Configuration
from camera.camera import Camera


@pytest.fixture
def camera_setup():
    """Fixture für die Kamera-Setup-Konfiguration"""
    config = Configuration()
    config.picam_enabled = True
    loop = asyncio.new_event_loop()  # Geändert von get_event_loop() zu new_event_loop()
    asyncio.set_event_loop(loop)     # Setze den neuen Loop als aktuellen Loop
    camera_queue = asyncio.Queue()
    message_queue = MagicMock()
    camera = Camera(config, loop, camera_queue, message_queue)
    
    yield camera, camera_queue, message_queue
    
    # Cleanup
    loop.close()


@pytest.mark.asyncio
async def test_start_picam_photo_success(camera_setup):
    # Setup
    camera, camera_queue, message_queue = camera_setup  # Entfernt await
    
    # Mock die Hilfsmethoden
    camera.picam_request_take_foto = MagicMock(return_value=True)
    camera.picam_request_download_foto = MagicMock(return_value=True)
    
    # Mock die Session für die start-Methode
    camera.session = MagicMock()
    camera.session.close = MagicMock()
    
    # Erstelle Test-Task
    test_task = Camera_Task(picam_photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)  # Stoppsignal
    
    # Ausführen der start-Methode
    await camera.start()
    
    # Überprüfungen
    camera.picam_request_take_foto.assert_called_once()
    camera.picam_request_download_foto.assert_called_once()
    
    # Überprüfe Message Queue
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.photo is True
    assert call_args.chat_id == 123456


@pytest.mark.asyncio
async def test_start_picam_photo_take_foto_failure(camera_setup):
    # Setup
    camera, camera_queue, message_queue = camera_setup  # Entfernt await
    
    # Mock die Hilfsmethoden
    camera.picam_request_take_foto = MagicMock(return_value=False)
    camera.picam_request_download_foto = MagicMock(return_value=True)
    
    # Mock die Session für die start-Methode
    camera.session = MagicMock()
    camera.session.close = MagicMock()
    
    # Erstelle Test-Task
    test_task = Camera_Task(picam_photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)  # Stoppsignal
    
    # Ausführen der start-Methode
    await camera.start()
    
    # Überprüfungen
    camera.picam_request_take_foto.assert_called_once()
    camera.picam_request_download_foto.assert_not_called()
    
    # Überprüfe Message Queue für Fehlermeldung
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.send is True
    assert "error" in call_args.data_text.lower()


@pytest.mark.asyncio
async def test_start_picam_photo_download_failure(camera_setup):
    # Setup
    camera, camera_queue, message_queue = camera_setup  # Entfernt await
    
    # Mock die Hilfsmethoden
    camera.picam_request_take_foto = MagicMock(return_value=True)
    camera.picam_request_download_foto = MagicMock(return_value=False)
    
    # Mock die Session für die start-Methode
    camera.session = MagicMock()
    camera.session.close = MagicMock()
    
    # Erstelle Test-Task
    test_task = Camera_Task(picam_photo=True, chat_id=123456)
    await camera_queue.put(test_task)
    await camera_queue.put(None)  # Stoppsignal
    
    # Ausführen der start-Methode
    await camera.start()
    
    # Überprüfungen
    camera.picam_request_take_foto.assert_called_once()
    camera.picam_request_download_foto.assert_called_once()
    
    # Überprüfe Message Queue für Fehlermeldung
    message_queue.put.assert_called_once()
    call_args = message_queue.put.call_args[0][0]
    assert isinstance(call_args, Message_Task)
    assert call_args.send is True
    assert "error" in call_args.data_text.lower()