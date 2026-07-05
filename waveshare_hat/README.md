# Waveshare Motor Driver HAT profile

This folder is an **alternate hardware profile** for this robot car project — it is not a
replacement for the root-level code. Use this folder if your robot is built with a
**Waveshare Motor Driver HAT**. If you're using a plain L298N-style driver wired directly to
GPIO pins, use the files at the repo root instead.

## Why this is a separate folder

The root-level code drives motors by toggling raw GPIO pins directly (`RPi.GPIO`), because it
was written for an L298N-style board. This HAT is different hardware: it has an onboard
**PCA9685** chip (16-channel I2C PWM controller, factory address `0x40`) that in turn drives an
onboard **TB6612FNG** dual H-bridge. The Pi talks to the PCA9685 over **I2C** — it never touches
the H-bridge's control pins directly. The HAT plugs straight onto the Pi's 40-pin header (it's a
stacking board), so there's no loose wiring between the Pi and the HAT for I2C or motor control
itself.

`RPi.GPIO` is **not** used for motor control in this profile.

## Wiring

### Battery
Connect your 4×AA battery pack (6V) to the HAT:
- Battery **+** → HAT `VIN` screw terminal
- Battery **−** → HAT `GND` screw terminal

### Motors
Each GA12-N20 motor has 6 wires: 2 for driving the motor, 4 for its built-in encoder.

| Motor pin | What it is | Connects to |
|---|---|---|
| `M1` | Motor power | HAT `MA1` (Motor A) or `MB1` (Motor B) |
| `M2` | Motor power | HAT `MA2` (Motor A) or `MB2` (Motor B) |

If a motor spins the wrong direction once everything is running, **swap its `M1`/`M2` leads at
the screw terminal** — don't try to fix it in software.

### Encoders (wired now, not used by software yet)

The encoder wires are **not read by any code in this folder** — quadrature decoding and RPM
calculation are planned for a future `sensors.py`. Wire them now so they're ready later:

| Wire | Motor A → Pi | Motor B → Pi | Notes |
|---|---|---|---|
| `VCC` | 3.3V pin | 3.3V pin | Use **3.3V, not 5V** — keeps the encoder's C1/C2 output signals at a safe level for the Pi's GPIO inputs |
| `GND` | any Pi GND pin | any Pi GND pin | |
| `C1` (encoder phase A) | GPIO5 | GPIO12 | |
| `C2` (encoder phase B) | GPIO6 | GPIO16 | |

These pins are reserved as constants in `config.py` (`ENCODER_A_C1`, `ENCODER_A_C2`,
`ENCODER_B_C1`, `ENCODER_B_C2`) but nothing reads them yet.

### The HAT itself
Plug the HAT directly onto the Raspberry Pi's 40-pin GPIO header. That's it — I2C and power are
carried automatically through the header, no jumper wires needed for the HAT-to-Pi connection.

## Dependencies

```bash
pip install smbus2 websockets
```

`RPi.GPIO` is not required by anything in this folder.

## Enable I2C on the Pi

```bash
sudo raspi-config
```
Interface Options → I2C → Enable, then reboot.

## Before running anything: confirm the HAT is detected

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

You should see `40` appear in the grid, e.g.:

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
...
```

If you don't see `40`, don't bother running the Python scripts yet — see Troubleshooting below.

## Running

```bash
cd waveshare_hat
python3 keyboard_control.py
```

or

```bash
cd waveshare_hat
python3 websocket_server.py
```

The WebSocket server listens on port `8765`, same as the root profile, and supports the same
commands (`forward`, `backward`, `left`, `right`, `stop`, `speed`, `joystick`, `capture`). It
reuses the root project's `camera.py` for image capture. **Don't run this server and the
root-level `websocket_server.py` on the same Pi at the same time** — they're alternate profiles
for physically different robots, not meant to run side by side.

## Troubleshooting

**No green "power on" LED to check, unlike the old L298N board** — this HAT's real
power-and-communication indicator is `i2cdetect` showing `40`. Don't judge whether the board is
working by any onboard LED; use the I2C scan.

**`i2cdetect -y 1` shows nothing at `40`:**
- Confirm I2C is enabled in `raspi-config` and you rebooted after enabling it.
- Confirm the HAT is fully and evenly seated on the 40-pin header.
- Confirm the battery pack is connected to `VIN`/`GND` (the HAT's logic side is powered from the
  Pi's header regardless, but double-check this wiring anyway).

**`i2cdetect` shows `40`, but the motors don't move at all:**
- Check the battery pack wiring at `VIN`/`GND` and that it has charge.
- Check that both motor leads are firmly seated in the `MA1`/`MA2` or `MB1`/`MB2` screw
  terminals.

**Running `diagnose()` spins the wrong motor, or neither motor spins:**
This points at the PCA9685 channel mapping in `config.py` (`PWMA`, `AIN1`, `AIN2`, `PWMB`,
`BIN1`, `BIN2`). Those constants are a **best-guess placeholder, not confirmed** against
Waveshare's own example code or this specific board. To fix it:
1. Download Waveshare's official demo code from the product wiki's example-code section (or
   check `github.com/sbcshop/Motor-Driver-HAT`, a mirror of the same board's code) and copy the
   real channel numbers from their `PCA9685.py`/`Demo.py` into `config.py`.
2. Or verify empirically: use `pca9685.py` directly to drive one channel at a time (e.g.
   `PCA9685().set_duty_cycle(0, 40)`) and note which motor, if any, responds, then update the
   constants in `config.py` to match.

**A motor spins the wrong direction:** swap its two leads at the `MA1`/`MA2` or `MB1`/`MB2`
screw terminal. Don't change the code for this.

## Status of encoder support

Encoder wiring is documented and its GPIO pins are reserved in `config.py`, but no code in this
folder reads them yet. Quadrature decoding and speed/position feedback are planned for a future
`sensors.py`.
