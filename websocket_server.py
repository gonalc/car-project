"""WebSocket server for Android app control"""
import asyncio
import websockets
import json
from motor_controller import MotorController

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
