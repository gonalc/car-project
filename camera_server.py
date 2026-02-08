"""MJPEG HTTP streaming server for Raspberry Pi Camera Module 2"""
import subprocess
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import signal
import sys

# Track active camera processes for cleanup
active_processes = set()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Stream settings
STREAM_WIDTH = 640
STREAM_HEIGHT = 480
STREAM_FRAMERATE = 15
STREAM_PORT = 8080


class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves MJPEG stream"""

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = f'''<!DOCTYPE html>
<html>
<head><title>Pi Camera Stream</title></head>
<body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;">
    <img src="/stream" style="max-width:100%;max-height:100%;">
</body>
</html>'''
            self.wfile.write(html.encode())

        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()

            cmd = [
                'rpicam-vid',
                '-t', '0',
                '--width', str(STREAM_WIDTH),
                '--height', str(STREAM_HEIGHT),
                '--framerate', str(STREAM_FRAMERATE),
                '--codec', 'mjpeg',
                '--nopreview',
                '-o', '-',
            ]

            log.info("Starting camera: %s", ' '.join(cmd))
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_processes.add(process)

            try:
                buffer = b''
                while True:
                    chunk = process.stdout.read(4096)
                    if not chunk:
                        break

                    buffer += chunk

                    # Find JPEG boundaries (FFD8 = start, FFD9 = end)
                    while True:
                        start = buffer.find(b'\xff\xd8')
                        end = buffer.find(b'\xff\xd9')

                        if start != -1 and end != -1 and end > start:
                            # Extract complete JPEG frame
                            frame = buffer[start:end + 2]
                            buffer = buffer[end + 2:]

                            # Send as multipart chunk
                            self.wfile.write(b'--frame\r\n')
                            self.wfile.write(b'Content-Type: image/jpeg\r\n')
                            self.wfile.write(f'Content-Length: {len(frame)}\r\n'.encode())
                            self.wfile.write(b'\r\n')
                            self.wfile.write(frame)
                            self.wfile.write(b'\r\n')
                        else:
                            break

            except (BrokenPipeError, ConnectionResetError):
                log.info("Client disconnected")
            finally:
                process.terminate()
                process.wait()
                active_processes.discard(process)
                log.info("Camera stopped")

        else:
            self.send_error(404)

    def log_message(self, format, *args):
        log.debug("%s - %s", self.address_string(), format % args)


def run_server():
    server = HTTPServer(('0.0.0.0', STREAM_PORT), MJPEGHandler)
    log.info("MJPEG stream available at http://0.0.0.0:%d/stream", STREAM_PORT)
    log.info("Web viewer at http://0.0.0.0:%d/", STREAM_PORT)

    def shutdown(sig, frame):
        log.info("Shutting down...")
        # Kill any active camera processes
        for proc in list(active_processes):
            proc.terminate()
        # Shutdown server in a thread to avoid deadlock
        Thread(target=server.shutdown).start()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        server.serve_forever()
    finally:
        log.info("Server stopped")
        sys.exit(0)


if __name__ == "__main__":
    run_server()
