# Raspberry Pi Robot Car

A Python-controlled two-motor robot car powered by a Raspberry Pi and an L298N H-bridge motor driver. Drive it from the terminal with arrow keys, or remotely over WebSocket from an Android app or any WebSocket client.

```
  ┌─────────────────────────────────┐
  │        Raspberry Pi             │
  │                                 │
  │  keyboard_control.py ──┐       │
  │                         ├─→ MotorController ──→ L298N ──→ Motors
  │  websocket_server.py ──┘       │
  │         ▲                       │
  └─────────┼───────────────────────┘
            │
     Android App / WebSocket Client
```

## Hardware Setup

### Components

- Raspberry Pi (any model with GPIO)
- L298N dual H-bridge motor driver
- 2 DC motors
- External power supply for motors (e.g., battery pack)

### Wiring (BCM Pin Numbering)

| Function     | GPIO Pin | L298N Pin | Description            |
|-------------|----------|-----------|------------------------|
| Motor A PWM | 27       | ENA       | Left motor speed       |
| Motor A Dir | 23       | IN1       | Left motor direction   |
| Motor A Dir | 24       | IN2       | Left motor direction   |
| Motor B PWM | 16       | ENB       | Right motor speed      |
| Motor B Dir | 26       | IN3       | Right motor direction  |
| Motor B Dir | 6        | IN4       | Right motor direction  |

```
Raspberry Pi              L298N
─────────────           ─────────
GPIO 27 ───────────────→ ENA
GPIO 23 ───────────────→ IN1        ┌─── Motor A (Left)
GPIO 24 ───────────────→ IN2   ─────┘
GPIO 16 ───────────────→ ENB
GPIO 26 ───────────────→ IN3        ┌─── Motor B (Right)
GPIO 6  ───────────────→ IN4   ─────┘
GND     ───────────────→ GND
```

Pin assignments can be changed in `config.py`.

## Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd car_project

# Install dependencies
pip install RPi.GPIO websockets
```

> **Note:** `RPi.GPIO` only works on Raspberry Pi hardware. This project cannot run on other machines.

## Usage

### Keyboard Control

Drive the car directly from a terminal on the Pi:

```bash
python keyboard_control.py
```

| Key              | Action       |
|-----------------|--------------|
| `W` / `Arrow Up`    | Forward  |
| `S` / `Arrow Down`  | Backward |
| `A` / `Arrow Left`  | Turn left  |
| `D` / `Arrow Right` | Turn right |
| `Space`            | Stop       |
| `+` / `=`           | Speed up (+10%)  |
| `-` / `_`           | Speed down (-10%) |
| `Q`                | Quit       |

### WebSocket Server (Remote Control)

Start the server to accept remote connections:

```bash
python websocket_server.py
```

The server listens on `0.0.0.0:8765` and accepts JSON commands.

#### Commands

**Movement:**

```json
{"command": "forward"}
{"command": "backward"}
{"command": "left"}
{"command": "right"}
{"command": "stop"}
```

**Speed:**

```json
{"command": "speed", "value": 75}
```

`value` is 0-100, representing PWM duty cycle percentage.

**Joystick (analog control):**

```json
{"command": "joystick", "x": 0.5, "y": 1.0}
```

- `x`: horizontal axis, -1.0 (left) to 1.0 (right)
- `y`: vertical axis, -1.0 (backward) to 1.0 (forward)
- A dead zone of 0.05 magnitude filters out stick drift

The joystick input is converted to differential motor speeds using tank-drive math:

```
left_motor  = y + x
right_motor = y - x
```

Values are normalized to prevent over-saturation, then scaled by the current speed setting.

#### Response Format

All commands return:

```json
{"status": "ok", "command": "forward", "speed": 80}
```

Joystick commands include motor values:

```json
{"status": "ok", "command": "joystick", "speed": 80, "left_motor": 0.75, "right_motor": 0.50}
```

#### Quick Test

```bash
# From another terminal or machine on the same network
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://<pi-ip>:8765') as ws:
        await ws.send(json.dumps({'command': 'forward'}))
        print(await ws.recv())
        await ws.send(json.dumps({'command': 'stop'}))
        print(await ws.recv())
asyncio.run(test())
"
```

## How It Works

### Steering

The car uses **tank-style differential steering** -- there is no steering axle. Turning is achieved by spinning the motors in opposite directions:

| Movement | Left Motor | Right Motor |
|----------|-----------|-------------|
| Forward  | Forward   | Forward     |
| Backward | Backward  | Backward    |
| Left     | Backward  | Forward     |
| Right    | Forward   | Backward    |

### Speed Control

Motor speed is controlled via PWM (Pulse Width Modulation) on the enable pins. The duty cycle (0-100%) determines how much power reaches the motors. Default speed is **80%**, adjustable in increments of 10%.

### Architecture

```
config.py                Pin assignments and defaults
    │
    ▼
motor_controller.py      MotorController class (GPIO + PWM)
    ▲            ▲
    │            │
keyboard_control.py    websocket_server.py
(terminal input)       (network input, port 8765)
```

All motor interaction goes through the `MotorController` class, which handles GPIO setup, PWM initialization, movement commands, and cleanup. Both control interfaces are thin layers that translate user input into `MotorController` method calls.

## Project Structure

```
car_project/
├── config.py              # GPIO pins, speed defaults, PWM frequency
├── motor_controller.py    # MotorController class
├── keyboard_control.py    # Terminal-based driving (arrow keys / WASD)
├── websocket_server.py    # WebSocket server for remote control
└── utils.py               # Utilities (reserved for future use)
```

## Configuration

All hardware and tuning constants live in `config.py`:

```python
# Motor A (Left)
ENA = 27    # PWM pin
IN1 = 23    # Direction pin 1
IN2 = 24    # Direction pin 2

# Motor B (Right)
ENB = 16    # PWM pin
IN3 = 26    # Direction pin 1
IN4 = 6     # Direction pin 2

DEFAULT_SPEED = 80         # 80% duty cycle
PWM_FREQUENCY = 100        # 100 Hz
JOYSTICK_DEAD_ZONE = 0.05  # Analog stick drift threshold
```

## Planned Features

- **Camera streaming** -- Live video feed from a Pi camera module
- **Sensor integration** -- Ultrasonic distance sensors for obstacle detection
- **Autonomous mode** -- Self-driving using sensor data
