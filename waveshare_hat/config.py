"""Pin, I2C, and channel configuration for the Waveshare Motor Driver HAT"""

# I2C
I2C_BUS = 1
PCA9685_ADDRESS = 0x40  # factory default

# PWM frequency — PCA9685 max is ~1526 Hz (25 MHz osc / (4096 * (prescale+1)), prescale min=3).
# This is a deliberate deviation from the old L298N config's 100 Hz — do not copy that value.
PWM_FREQUENCY = 1000  # Hz

# --- PCA9685 channel mapping (UNVERIFIED — see README "Troubleshooting") ---
# These values are a best-guess community pattern, NOT confirmed against Waveshare's own
# demo code (wiki example code / github.com/sbcshop/Motor-Driver-HAT PCA9685.py, Demo.py)
# or against real hardware. Verify empirically before trusting them — see README.
PWMA = 0  # Motor A speed (PWM)
AIN1 = 1  # Motor A direction pin 1
AIN2 = 2  # Motor A direction pin 2
PWMB = 5  # Motor B speed (PWM)
BIN1 = 3  # Motor B direction pin 1
BIN2 = 4  # Motor B direction pin 2

# --- Encoder GPIO pins (RESERVED — wired but NOT read by any code yet) ---
# Quadrature decoding/RPM is out of scope here; deferred to a future sensors.py.
ENCODER_A_C1 = 5
ENCODER_A_C2 = 6
ENCODER_B_C1 = 12
ENCODER_B_C2 = 16

# Settings
DEFAULT_SPEED = 80
JOYSTICK_DEAD_ZONE = 0.05
