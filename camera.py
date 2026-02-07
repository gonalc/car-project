"""Camera module for Raspberry Pi Camera Module 2"""
import subprocess
import base64
import tempfile
import os
import logging

log = logging.getLogger(__name__)

# Default capture settings
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_QUALITY = 80


def capture_image(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, quality=DEFAULT_QUALITY):
    """
    Capture a single image using rpicam-still.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        quality: JPEG quality (0-100)

    Returns:
        dict with 'success' bool and either 'data' (base64 image) or 'error' message
    """
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            'rpicam-still',
            '-o', tmp_path,
            '--width', str(width),
            '--height', str(height),
            '--quality', str(quality),
            '--nopreview',
            '--timeout', '1000',  # 1 second timeout for camera to initialize
        ]

        log.info("Capturing image: %s", ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            log.error("rpicam-still failed: %s", result.stderr)
            return {'success': False, 'error': result.stderr or 'capture failed'}

        with open(tmp_path, 'rb') as f:
            image_data = f.read()

        encoded = base64.b64encode(image_data).decode('utf-8')
        log.info("Image captured: %d bytes, base64 length: %d", len(image_data), len(encoded))

        return {
            'success': True,
            'data': encoded,
            'width': width,
            'height': height,
        }

    except subprocess.TimeoutExpired:
        log.error("Camera capture timed out")
        return {'success': False, 'error': 'capture timed out'}
    except FileNotFoundError:
        log.error("rpicam-still not found")
        return {'success': False, 'error': 'rpicam-still not found'}
    except Exception as e:
        log.error("Capture error: %s", e)
        return {'success': False, 'error': str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
