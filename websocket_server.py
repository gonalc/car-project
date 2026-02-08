"""WebSocket server for Android app control"""
import asyncio
import logging
import websockets
import json
from motor_controller import MotorController
from config import JOYSTICK_DEAD_ZONE
from camera import capture_image
from stream import VideoStreamer

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

motor = None

async def handle_client(websocket):
    global motor
    log.info("Client connected: %s", websocket.remote_address)
    streamer = None

    try:
        async for message in websocket:
            log.info("Received: %s", message)
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                log.warning("Invalid JSON: %s", message)
                await websocket.send(json.dumps({'status': 'error', 'message': 'invalid JSON'}))
                continue

            command = data.get('command')
            if not command:
                log.warning("Missing 'command' key in message")
                await websocket.send(json.dumps({'status': 'error', 'message': 'missing command'}))
                continue

            if command == 'forward':
                motor.forward()
            elif command == 'backward':
                motor.backward()
            elif command == 'left':
                motor.left()
            elif command == 'right':
                motor.right()
            elif command == 'stop':
                motor.stop()
            elif command == 'speed':
                motor.set_speed(data.get('value', 75))
            elif command == 'joystick':
                x = max(-1.0, min(1.0, float(data.get('x', 0))))
                y = max(-1.0, min(1.0, float(data.get('y', 0))))

                if (x ** 2 + y ** 2) ** 0.5 < JOYSTICK_DEAD_ZONE:
                    x, y = 0.0, 0.0

                left = max(-1.0, min(1.0, y + x))
                right = max(-1.0, min(1.0, y - x))

                left_duty = left * motor.speed
                right_duty = right * motor.speed
                motor.drive(left_duty, right_duty)

                response = {
                    'status': 'ok',
                    'command': command,
                    'speed': motor.speed,
                    'left_motor': round(left_duty, 1),
                    'right_motor': round(right_duty, 1),
                }
                log.info("Response: %s", json.dumps(response))
                await websocket.send(json.dumps(response))
                continue
            elif command == 'capture':
                width = data.get('width', 640)
                height = data.get('height', 480)
                quality = data.get('quality', 80)

                result = capture_image(width=width, height=height, quality=quality)

                if result['success']:
                    response = {
                        'status': 'ok',
                        'command': 'capture',
                        'image': result['data'],
                        'width': result['width'],
                        'height': result['height'],
                    }
                else:
                    response = {
                        'status': 'error',
                        'command': 'capture',
                        'message': result['error'],
                    }

                log.info("Capture response: success=%s", result['success'])
                await websocket.send(json.dumps(response))
                continue
            elif command == 'stream':
                action = data.get('action', 'start')

                if action == 'start':
                    if streamer and streamer.running:
                        response = {
                            'status': 'error',
                            'command': 'stream',
                            'message': 'stream already running',
                        }
                    else:
                        width = data.get('width', 640)
                        height = data.get('height', 480)
                        framerate = data.get('framerate', 15)
                        quality = data.get('quality', 80)

                        streamer = VideoStreamer(
                            websocket,
                            width=width,
                            height=height,
                            framerate=framerate,
                            quality=quality
                        )
                        await streamer.start()
                        response = {
                            'status': 'ok',
                            'command': 'stream',
                            'action': 'start',
                            'width': width,
                            'height': height,
                            'framerate': framerate,
                        }

                elif action == 'stop':
                    if streamer:
                        await streamer.stop()
                        streamer = None
                    response = {
                        'status': 'ok',
                        'command': 'stream',
                        'action': 'stop',
                    }
                else:
                    response = {
                        'status': 'error',
                        'command': 'stream',
                        'message': f'unknown action: {action}',
                    }

                log.info("Stream response: %s", response)
                await websocket.send(json.dumps(response))
                continue
            else:
                log.warning("Unknown command: %s", command)
                await websocket.send(json.dumps({'status': 'error', 'message': f'unknown command: {command}'}))
                continue

            response = {
                'status': 'ok',
                'command': command,
                'speed': motor.speed,
            }
            log.info("Response: %s", json.dumps(response))
            await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed:
        log.info("Client disconnected: %s", websocket.remote_address)
    finally:
        if streamer:
            await streamer.stop()
        motor.stop()

async def main():
    global motor
    motor = MotorController()
    log.info("Running startup motor diagnostic...")
    motor.diagnose()
    log.info("Starting motor control server on port 8765...")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down...")
    finally:
        if motor:
            motor.cleanup()
