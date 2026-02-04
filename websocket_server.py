"""WebSocket server for Android app control"""
import asyncio
import websockets
import json
from motor_controller import MotorController
from config import JOYSTICK_DEAD_ZONE

motor = None

async def handle_client(websocket):
    global motor
    print(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            data = json.loads(message)
            command = data.get('command')

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

                await websocket.send(json.dumps({
                    'status': 'ok',
                    'command': command,
                    'speed': motor.speed,
                    'left_motor': round(left_duty, 1),
                    'right_motor': round(right_duty, 1)
                }))
                continue

            await websocket.send(json.dumps({
                'status': 'ok',
                'command': command,
                'speed': motor.speed
            }))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        motor.stop()

async def main():
    global motor
    motor = MotorController()

    print("Starting motor control server on port 8765...")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if motor:
            motor.cleanup()
