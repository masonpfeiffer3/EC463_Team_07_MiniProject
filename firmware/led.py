"""
RGB LED test for XIAO ESP32-S3 running MicroPython.
Pulses Red -> Blue -> Green (fade up, fade down) at ~1s per cycle,
confirmed common-cathode wiring (common leg -> GND).

Pinout:
    GPIO7 -> 220ohm resistor -> Red leg
    GPIO8 -> 220ohm resistor -> Blue leg
    GPIO9 -> 220ohm resistor -> Green leg
    Common leg -> GND
"""

from machine import Pin, PWM
import utime

PULSE_PERIOD_MS = 1000  # one full fade-up + fade-down cycle
FADE_STEPS = 50
CYCLES_PER_COLOR = 2

red = PWM(Pin(7), freq=1000, duty_u16=0)
blue = PWM(Pin(8), freq=1000, duty_u16=0)
green = PWM(Pin(9), freq=1000, duty_u16=0)

leds = (
    ("Red", red),
    ("Blue", blue),
    ("Green", green),
)


def all_off():
    for _, led in leds:
        led.duty_u16(0)


def pulse(led, cycles=CYCLES_PER_COLOR):
    """Fade the given PWM LED up to full brightness and back down, `cycles` times."""
    step_delay_ms = (PULSE_PERIOD_MS // 2) // FADE_STEPS
    for _ in range(cycles):
        for i in range(FADE_STEPS + 1):
            led.duty_u16(int(65535 * i / FADE_STEPS))
            utime.sleep_ms(step_delay_ms)
        for i in range(FADE_STEPS, -1, -1):
            led.duty_u16(int(65535 * i / FADE_STEPS))
            utime.sleep_ms(step_delay_ms)


if __name__ == "__main__":
    all_off()

    while True:
        for name, led in leds:
            print(name)
            pulse(led)
