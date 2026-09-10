"""
28BYJ-48 stepper motor driver (wave drive: one coil energized at a time)
via L293D H-bridge, for XIAO ESP32-S3 running MicroPython.

Pinout (see hardware/electrical docs):
    GPIO1 -> L293D Pin 2  (1A) -> L293D Pin 3  (1Y) -> Motor Orange (Coil 1)
    GPIO2 -> L293D Pin 7  (2A) -> L293D Pin 6  (2Y) -> Motor Pink   (Coil 2)
    GPIO3 -> L293D Pin 10 (3A) -> L293D Pin 11 (3Y) -> Motor Yellow (Coil 3)
    GPIO4 -> L293D Pin 15 (4A) -> L293D Pin 14 (4Y) -> Motor Blue   (Coil 4)
"""

from machine import Pin
import utime


class Stepper28BYJ48:
    # Wave drive sequence: one coil high at a time. Reversing this list reverses direction.
    # NOTE: order is 1-3-2-4, not 1-2-3-4 -- the 28BYJ-48's coil pairs aren't wired
    # in physical winding order by wire label, so straight sequential activation
    # causes jitter-in-place instead of rotation. Adjust here if direction/behavior
    # still looks wrong for your specific unit.
    _SEQUENCE = (
        (1, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 0, 0, 1),
    )

    # 28BYJ-48 has a ~64:1 gearbox; wave drive takes 2048 steps per output-shaft revolution.
    STEPS_PER_REV = 2048

    def __init__(self, pins=(1, 2, 3, 4), step_delay_ms=3):
        self._coils = [Pin(p, Pin.OUT) for p in pins]
        self.step_delay_ms = step_delay_ms
        self._index = 0
        self._deenergize()

    def _write(self, state):
        for coil, value in zip(self._coils, state):
            coil.value(value)

    def _deenergize(self):
        self._write((0, 0, 0, 0))

    def step(self, steps, release=True):
        """Move `steps` steps. Positive = forward, negative = reverse."""
        direction = 1 if steps >= 0 else -1
        for _ in range(abs(steps)):
            self._index = (self._index + direction) % len(self._SEQUENCE)
            self._write(self._SEQUENCE[self._index])
            utime.sleep_ms(self.step_delay_ms)
        if release:
            self._deenergize()

    def rotate(self, degrees, release=True):
        """Move by an angle in degrees. Positive = forward, negative = reverse."""
        steps = round(self.STEPS_PER_REV * degrees / 360)
        self.step(steps, release=release)

    def release(self):
        """De-energize all coils (cuts current draw / heat while idle)."""
        self._deenergize()


if __name__ == "__main__":
    motor = Stepper28BYJ48(pins=(1, 2, 3, 4), step_delay_ms=3)

    print("Rotating forward 90 degrees...")
    motor.rotate(90)
    utime.sleep(1)

    print("Rotating back 90 degrees...")
    motor.rotate(-90)

    print("Done.")
