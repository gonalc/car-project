"""Core motor control functionality for the Waveshare Motor Driver HAT (PCA9685 + TB6612FNG)"""
import logging
import time

from config import *
from pca9685 import PCA9685

log = logging.getLogger(__name__)


class MotorController:
    def __init__(self):
        self.speed = DEFAULT_SPEED
        self.pca = None
        self.setup()

    def setup(self):
        self.pca = PCA9685()
        for channel in (AIN1, AIN2, BIN1, BIN2):
            self.pca.set_digital(channel, False)
        self.pca.set_duty_cycle(PWMA, 0)
        self.pca.set_duty_cycle(PWMB, 0)
        log.info(
            "PCA9685 setup complete — Motor A: PWMA=%d AIN1=%d AIN2=%d, "
            "Motor B: PWMB=%d BIN1=%d BIN2=%d",
            PWMA, AIN1, AIN2, PWMB, BIN1, BIN2,
        )
        log.info("PWM frequency: %d Hz, default speed: %d%%", PWM_FREQUENCY, DEFAULT_SPEED)
        log.warning(
            "Channel mapping above is UNVERIFIED against real hardware — "
            "see README 'Troubleshooting' if the wrong motor (or no motor) responds"
        )

    def _drive_channels(self, in1_ch, in2_ch, pwm_ch, duty, forward=True):
        if forward:
            self.pca.set_digital(in1_ch, True)
            self.pca.set_digital(in2_ch, False)
        else:
            self.pca.set_digital(in1_ch, False)
            self.pca.set_digital(in2_ch, True)
        self.pca.set_duty_cycle(pwm_ch, abs(duty))

    def diagnose(self, pulse_duration=1.0, duty_cycle=35):
        """Pulse each motor briefly so the human can visually confirm it spins.

        Unlike the GPIO-based driver, the PCA9685 drives the TB6612FNG's control
        pins directly on the HAT — there is no wire back to the Pi to read, so
        no electrical pass/fail readback is possible here. This only reports
        that a pulse was sent; the human must watch and confirm.
        """
        log.info("=== Motor Diagnostic Start ===")
        log.info("No electrical readback is possible with this HAT — watch the motors and confirm visually.")
        results = {}

        log.info("Testing Motor A (PWMA=%d, AIN1=%d, AIN2=%d) — should spin forward briefly", PWMA, AIN1, AIN2)
        self._drive_channels(AIN1, AIN2, PWMA, duty_cycle, forward=True)
        time.sleep(pulse_duration)
        self.pca.set_duty_cycle(PWMA, 0)
        self.pca.set_digital(AIN1, False)
        results['motor_a'] = 'pulsed — confirm visually'

        time.sleep(0.2)

        log.info("Testing Motor B (PWMB=%d, BIN1=%d, BIN2=%d) — should spin forward briefly", PWMB, BIN1, BIN2)
        self._drive_channels(BIN1, BIN2, PWMB, duty_cycle, forward=True)
        time.sleep(pulse_duration)
        self.pca.set_duty_cycle(PWMB, 0)
        self.pca.set_digital(BIN1, False)
        results['motor_b'] = 'pulsed — confirm visually'

        results['note'] = 'no electrical readback available'
        log.info("=== Diagnostic complete — if a motor didn't spin (or the wrong one did), "
                  "see README 'Troubleshooting' about the unverified channel mapping ===")
        return results

    def forward(self):
        log.debug("forward — speed=%d%%", self.speed)
        self._drive_channels(AIN1, AIN2, PWMA, self.speed, forward=True)
        self._drive_channels(BIN1, BIN2, PWMB, self.speed, forward=True)

    def backward(self):
        log.debug("backward — speed=%d%%", self.speed)
        self._drive_channels(AIN1, AIN2, PWMA, self.speed, forward=False)
        self._drive_channels(BIN1, BIN2, PWMB, self.speed, forward=False)

    def left(self):
        log.debug("left — speed=%d%%", self.speed)
        self._drive_channels(AIN1, AIN2, PWMA, self.speed, forward=False)
        self._drive_channels(BIN1, BIN2, PWMB, self.speed, forward=True)

    def right(self):
        log.debug("right — speed=%d%%", self.speed)
        self._drive_channels(AIN1, AIN2, PWMA, self.speed, forward=True)
        self._drive_channels(BIN1, BIN2, PWMB, self.speed, forward=False)

    def stop(self):
        log.debug("stop")
        self.pca.set_duty_cycle(PWMA, 0)
        self.pca.set_duty_cycle(PWMB, 0)
        for channel in (AIN1, AIN2, BIN1, BIN2):
            self.pca.set_digital(channel, False)

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
            left_speed: -100 to 100 (negative = backward) — Motor A
            right_speed: -100 to 100 (negative = backward) — Motor B
        """
        log.debug("drive — left=%.1f right=%.1f", left_speed, right_speed)
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))

        self._drive_channels(AIN1, AIN2, PWMA, left_speed, forward=left_speed >= 0)
        self._drive_channels(BIN1, BIN2, PWMB, right_speed, forward=right_speed >= 0)

    def cleanup(self):
        log.info("Cleaning up PCA9685")
        self.stop()
        self.pca.close()
