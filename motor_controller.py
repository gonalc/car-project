"""Core motor control functionality"""
import logging
import time
import RPi.GPIO as GPIO
from config import *

log = logging.getLogger(__name__)

class MotorController:
    def __init__(self):
        self.speed = DEFAULT_SPEED
        self.pwm_a = None
        self.pwm_b = None
        self.setup()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)

        self.pwm_a = GPIO.PWM(ENA, PWM_FREQUENCY)
        self.pwm_b = GPIO.PWM(ENB, PWM_FREQUENCY)
        self.pwm_a.start(0)
        self.pwm_b.start(0)
        log.info("GPIO setup complete — pins: ENA=%d IN1=%d IN2=%d ENB=%d IN3=%d IN4=%d",
                 ENA, IN1, IN2, ENB, IN3, IN4)
        log.info("PWM frequency: %d Hz, default speed: %d%%", PWM_FREQUENCY, DEFAULT_SPEED)

    def diagnose(self, pulse_duration=0.3):
        """Pulse each motor individually so the user can verify connections.

        Returns a dict with pin readback results. If a motor doesn't spin
        during its pulse, the wiring or driver board is likely the problem.
        """
        log.info("=== Motor Diagnostic Start ===")
        results = {}

        # --- Motor A ---
        log.info("Testing Motor A (ENA=%d, IN1=%d, IN2=%d) — should spin forward briefly", ENA, IN1, IN2)
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(60)
        time.sleep(pulse_duration)
        a_in1 = GPIO.input(IN1)
        a_in2 = GPIO.input(IN2)
        self.pwm_a.ChangeDutyCycle(0)
        GPIO.output(IN1, GPIO.LOW)
        results['motor_a'] = {'IN1': a_in1, 'IN2': a_in2, 'expected': 'IN1=1 IN2=0'}
        log.info("  Motor A readback: IN1=%d IN2=%d (expected 1/0)", a_in1, a_in2)
        if a_in1 != 1 or a_in2 != 0:
            log.warning("  Motor A pin readback unexpected — check wiring")

        time.sleep(0.2)

        # --- Motor B ---
        log.info("Testing Motor B (ENB=%d, IN3=%d, IN4=%d) — should spin forward briefly", ENB, IN3, IN4)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwm_b.ChangeDutyCycle(60)
        time.sleep(pulse_duration)
        b_in3 = GPIO.input(IN3)
        b_in4 = GPIO.input(IN4)
        self.pwm_b.ChangeDutyCycle(0)
        GPIO.output(IN3, GPIO.LOW)
        results['motor_b'] = {'IN3': b_in3, 'IN4': b_in4, 'expected': 'IN3=1 IN4=0'}
        log.info("  Motor B readback: IN3=%d IN4=%d (expected 1/0)", b_in3, b_in4)
        if b_in3 != 1 or b_in4 != 0:
            log.warning("  Motor B pin readback unexpected — check wiring")

        ok = (a_in1 == 1 and a_in2 == 0 and b_in3 == 1 and b_in4 == 0)
        if ok:
            log.info("=== Diagnostic PASSED — both motors pulsed, pins read back correctly ===")
        else:
            log.warning("=== Diagnostic FAILED — review warnings above ===")

        results['ok'] = ok
        return results
    
    def forward(self):
        log.debug("forward — speed=%d%%", self.speed)
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)

    def backward(self):
        log.debug("backward — speed=%d%%", self.speed)
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)

    def left(self):
        log.debug("left — speed=%d%%", self.speed)
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)

    def right(self):
        log.debug("right — speed=%d%%", self.speed)
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)

    def stop(self):
        log.debug("stop")
        self.pwm_a.ChangeDutyCycle(0)
        self.pwm_b.ChangeDutyCycle(0)
        GPIO.output([IN1, IN2, IN3, IN4], GPIO.LOW)
    
    def set_speed(self, speed):
        self.speed = max(0, min(100, speed))
        log.debug("set_speed — %d%%", self.speed)
    
    def increase_speed(self, increment=10):
        self.speed = min(100, self.speed + increment)
        return self.speed
    
    def decrease_speed(self, decrement=10):
        self.speed = max(0, self.speed - decrement)
        return self.speed
    
    def drive(self, left_speed, right_speed):
        """Drive motors with independent speed and direction.

        Args:
            left_speed: -100 to 100 (negative = backward)
            right_speed: -100 to 100 (negative = backward)
        """
        log.debug("drive — left=%.1f right=%.1f", left_speed, right_speed)
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))

        if left_speed >= 0:
            GPIO.output(IN1, GPIO.HIGH)
            GPIO.output(IN2, GPIO.LOW)
        else:
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.HIGH)

        if right_speed >= 0:
            GPIO.output(IN3, GPIO.HIGH)
            GPIO.output(IN4, GPIO.LOW)
        else:
            GPIO.output(IN3, GPIO.LOW)
            GPIO.output(IN4, GPIO.HIGH)

        self.pwm_a.ChangeDutyCycle(abs(left_speed))
        self.pwm_b.ChangeDutyCycle(abs(right_speed))

    def cleanup(self):
        log.info("Cleaning up GPIO")
        self.stop()
        GPIO.cleanup()
