# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi robot car controller. Python project that drives a two-motor car via GPIO pins using an L298N motor driver (or similar H-bridge). Runs exclusively on Raspberry Pi hardware due to RPi.GPIO dependency.

## Running

Both entry points must be run on the Raspberry Pi with `RPi.GPIO` and `websockets` installed:

```bash
# Terminal-based keyboard control (arrow keys / WASD)
python keyboard_control.py

# WebSocket server for remote control (listens on 0.0.0.0:8765)
python websocket_server.py
```

There is no build step, no test suite, no linter configuration, and no `requirements.txt`. Dependencies are `RPi.GPIO` and `websockets`.

## Architecture

```
Control Layer          →   Core Layer   →   Hardware
─────────────────────────────────────────────────────
keyboard_control.py         │                 │
websocket_server.py    → MotorController  → RPi.GPIO
                            │                 │
                        config.py         GPIO pins
```

- **`config.py`** — GPIO pin assignments (BCM numbering) and defaults (speed 80%, PWM 100Hz). Motor A: ENA=27, IN1=23, IN2=24. Motor B: ENB=16, IN3=26, IN4=6.
- **`motor_controller.py`** — `MotorController` class. Wraps all GPIO setup, PWM, movement commands (forward/backward/left/right/stop), and speed control (0–100%). All control interfaces should use this class.
- **`keyboard_control.py`** — Reads raw terminal input for arrow keys and WASD. Standalone entry point.
- **`websocket_server.py`** — Async WebSocket server (port 8765). Accepts JSON commands (`{"command": "forward"}`, etc.) and replies with `{"status": "ok", "command": "...", "speed": N}`. Designed for an Android app client.

## Key Conventions

- GPIO uses BCM pin numbering (`GPIO.setmode(GPIO.BCM)`).
- Turning is differential: left/right spin motors in opposite directions (tank-style steering).
- All entry points call `motor.cleanup()` on exit to release GPIO resources. New entry points must do the same.
- The WebSocket server uses a module-level global `motor` instance shared across client connections.

## Planned Extensions

Camera streaming module (`camera_server.py`), sensor integration (`sensors.py`), and autonomous driving mode (`autonomous.py`).
