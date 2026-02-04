"""Keyboard control interface"""
import logging
import sys
import tty
import termios
import time
from motor_controller import MotorController

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == '\x1b':
            key += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

def main():
    motor = MotorController()
    log.info("Running startup motor diagnostic...")
    motor.diagnose()

    print("\n=== Robot Motor Control ===")
    print("Arrow Keys: ↑←↓→ to move")
    print("WASD: Alternative controls")
    print("+/-: Increase/decrease speed")
    print("Space: Stop")
    print("Q: Quit")
    print("===========================\n")
    
    try:
        while True:
            key = get_key()
            
            # Arrow keys
            if key == '\x1b[A':
                motor.forward()
                print("↑ Forward")
            elif key == '\x1b[B':
                motor.backward()
                print("↓ Backward")
            elif key == '\x1b[D':
                motor.left()
                print("← Left")
            elif key == '\x1b[C':
                motor.right()
                print("→ Right")
            
            # WASD
            elif key.lower() == 'w':
                motor.forward()
                print("↑ Forward")
            elif key.lower() == 's':
                motor.backward()
                print("↓ Backward")
            elif key.lower() == 'a':
                motor.left()
                print("← Left")
            elif key.lower() == 'd':
                motor.right()
                print("→ Right")
            
            # Speed control
            elif key in ('+', '='):
                speed = motor.increase_speed()
                print(f"Speed: {speed}%")
            elif key in ('-', '_'):
                speed = motor.decrease_speed()
                print(f"Speed: {speed}%")
            
            # Stop and quit
            elif key == ' ':
                motor.stop()
                print("⏹ Stop")
            elif key.lower() == 'q':
                print("\nExiting...")
                break
            
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        motor.cleanup()
        print("Cleanup complete. Goodbye!")

if __name__ == "__main__":
    main()
