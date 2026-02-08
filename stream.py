"""WebSocket video streaming module using rpicam-vid"""
import asyncio
import base64
import json
import logging

log = logging.getLogger(__name__)

# Default stream settings
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FRAMERATE = 15
DEFAULT_QUALITY = 80


class VideoStreamer:
    """Manages video streaming to a WebSocket client"""

    def __init__(self, websocket, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                 framerate=DEFAULT_FRAMERATE, quality=DEFAULT_QUALITY):
        self.websocket = websocket
        self.width = width
        self.height = height
        self.framerate = framerate
        self.quality = quality
        self.process = None
        self.task = None
        self.running = False

    async def start(self):
        """Start streaming video frames to the WebSocket"""
        if self.running:
            log.warning("Stream already running")
            return False

        self.running = True
        self.task = asyncio.create_task(self._stream_loop())
        log.info("Video stream started: %dx%d@%dfps q%d",
                 self.width, self.height, self.framerate, self.quality)
        return True

    async def stop(self):
        """Stop the video stream"""
        if not self.running:
            return

        self.running = False

        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=2)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        log.info("Video stream stopped")

    async def _stream_loop(self):
        """Main streaming loop - captures frames and sends via WebSocket"""
        cmd = [
            'rpicam-vid',
            '-t', '0',
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(self.framerate),
            '--quality', str(self.quality),
            '--codec', 'mjpeg',
            '--nopreview',
            '-o', '-',
        ]

        log.debug("Starting camera: %s", ' '.join(cmd))

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            buffer = b''
            frame_count = 0

            while self.running:
                chunk = await self.process.stdout.read(4096)
                if not chunk:
                    break

                buffer += chunk

                # Extract complete JPEG frames (FFD8 = start, FFD9 = end)
                while True:
                    start = buffer.find(b'\xff\xd8')
                    end = buffer.find(b'\xff\xd9')

                    if start != -1 and end != -1 and end > start:
                        frame = buffer[start:end + 2]
                        buffer = buffer[end + 2:]

                        # Send frame as base64-encoded JSON message
                        frame_b64 = base64.b64encode(frame).decode('ascii')
                        message = {
                            'type': 'frame',
                            'data': frame_b64,
                            'frame': frame_count,
                        }

                        try:
                            await self.websocket.send(json.dumps(message))
                            frame_count += 1
                        except Exception as e:
                            log.error("Failed to send frame: %s", e)
                            self.running = False
                            break
                    else:
                        break

        except asyncio.CancelledError:
            log.debug("Stream loop cancelled")
        except Exception as e:
            log.error("Stream error: %s", e)
        finally:
            if self.process:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    self.process.kill()
                self.process = None
