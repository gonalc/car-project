"""Core motor control functionality"""
import RPi.GPIO as GPIO
from config import *

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
    
    def forward(self):
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)
    
    def backward(self):
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)
    
    def left(self):
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)
    
    def right(self):
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        self.pwm_a.ChangeDutyCycle(self.speed)
        self.pwm_b.ChangeDutyCycle(self.speed)
    
    def stop(self):
        self.pwm_a.ChangeDutyCycle(0)
        self.pwm_b.ChangeDutyCycle(0)
        GPIO.output([IN1, IN2, IN3, IN4], GPIO.LOW)
    
    def set_speed(self, speed):
        self.speed = max(0, min(100, speed))
    
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
        self.stop()
        GPIO.cleanup()
