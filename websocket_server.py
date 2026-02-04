"""WebSocket server for Android app control"""
import asyncio
import logging
import websockets
import json
from motor_controller import MotorController
from config import JOYSTICK_DEAD_ZONE

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

                left = y + x
                right = y - x
                max_val = max(abs(left), abs(right), 1.0)
                left /= max_val
                right /= max_val

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
