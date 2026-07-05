"""Low-level I2C driver for the PCA9685 PWM controller"""
import logging
import time

from smbus2 import SMBus

log = logging.getLogger(__name__)

# Registers
MODE1 = 0x00
MODE2 = 0x01
PRESCALE = 0xFE
LED0_ON_L = 0x06  # channel n's 4 registers start at LED0_ON_L + 4*n

# MODE1 bits
SLEEP = 0x10
AI = 0x20
RESTART = 0x80

# ON/OFF full-on / full-off bit (bit 4 of the *_H byte, NXP datasheet section 7.3.3)
FULL_BIT = 0x10

OSCILLATOR_HZ = 25_000_000


class PCA9685:
    def __init__(self, bus=None, address=None):
        from config import I2C_BUS, PCA9685_ADDRESS, PWM_FREQUENCY

        self.address = address if address is not None else PCA9685_ADDRESS
        self.bus = SMBus(bus if bus is not None else I2C_BUS)
        self.reset()
        self.set_pwm_freq(PWM_FREQUENCY)
        log.info("PCA9685 initialized at address 0x%02X", self.address)

    def reset(self):
        self.bus.write_byte_data(self.address, MODE1, 0x00)
        time.sleep(0.005)

    def set_pwm_freq(self, freq_hz):
        prescale = round(OSCILLATOR_HZ / (4096 * freq_hz)) - 1
        old_mode = self.bus.read_byte_data(self.address, MODE1)
        sleep_mode = (old_mode & 0x7F) | SLEEP
        self.bus.write_byte_data(self.address, MODE1, sleep_mode)
        self.bus.write_byte_data(self.address, PRESCALE, prescale)
        self.bus.write_byte_data(self.address, MODE1, old_mode)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, MODE1, old_mode | RESTART | AI)
        log.info("PWM frequency set: %d Hz (prescale=%d)", freq_hz, prescale)

    def set_pwm(self, channel, on, off):
        base = LED0_ON_L + 4 * channel
        self.bus.write_i2c_block_data(self.address, base, [
            on & 0xFF, (on >> 8) & 0xFF,
            off & 0xFF, (off >> 8) & 0xFF,
        ])

    def set_full_on(self, channel):
        base = LED0_ON_L + 4 * channel
        self.bus.write_i2c_block_data(self.address, base, [0, FULL_BIT, 0, 0])

    def set_full_off(self, channel):
        base = LED0_ON_L + 4 * channel
        self.bus.write_i2c_block_data(self.address, base, [0, 0, 0, FULL_BIT])

    def set_digital(self, channel, level):
        if level:
            self.set_full_on(channel)
        else:
            self.set_full_off(channel)

    def set_duty_cycle(self, channel, percent):
        percent = max(0, min(100, percent))
        if percent == 0:
            self.set_full_off(channel)
        elif percent == 100:
            self.set_full_on(channel)
        else:
            self.set_pwm(channel, 0, int(4095 * percent / 100))

    def close(self):
        self.bus.close()
