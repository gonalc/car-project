"""WebSocket server for Android app control"""
import asyncio
import websockets
import json
from motor_controller import MotorController

motor = None

async def handle_client(websocket, path):
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
```

## Advantages of Modular Approach

✅ **Reusability**: Use `MotorController` in keyboard, websocket, and REST servers
✅ **Testing**: Test motor logic independently
✅ **Maintainability**: Change pin configs in one place
✅ **Scalability**: Easy to add camera, sensors, autonomous mode
✅ **Multiple interfaces**: Run keyboard and websocket server simultaneously

## Disadvantages

❌ Slightly more complex to deploy (multiple files)
❌ Overkill for simple projects
❌ More imports to manage

## My Recommendation

**For right now**: Keep your single `car.py` file as-is. It's clean and works perfectly.

**When you add the Android app**: Refactor into the modular structure above. You'll want to reuse the motor control logic in both the keyboard script and websocket server.

**Future growth path**:
```
car.py (current)
    ↓
Split when adding Android app
    ↓
motor_controller.py + keyboard_control.py + websocket_server.py
    ↓
Add camera streaming
    ↓
Add camera_server.py
    ↓
Add autonomous mode
    ↓
Add sensors.py + autonomous.py
