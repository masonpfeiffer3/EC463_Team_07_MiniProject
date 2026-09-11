"""
Continuous stepper drive with button-controlled direction toggle and
button-controlled start/stop, for XIAO ESP32-S3 running MicroPython.

Pinout:
    GPIO1 -> L293D Pin 2  (1A) -> L293D Pin 3  (1Y) -> Motor Orange (Coil 1)
    GPIO2 -> L293D Pin 7  (2A) -> L293D Pin 6  (2Y) -> Motor Pink   (Coil 2)
    GPIO3 -> L293D Pin 10 (3A) -> L293D Pin 11 (3Y) -> Motor Yellow (Coil 3)
    GPIO4 -> L293D Pin 15 (4A) -> L293D Pin 14 (4Y) -> Motor Blue   (Coil 4)
    GPIO5 -> Button 1 (start/stop), other leg -> GND (uses internal pull-up, active low)
    GPIO6 -> Button 2 (direction), other leg -> GND (uses internal pull-up, active low)
"""

from machine import Pin
import utime


class Stepper28BYJ48:
    # Wave drive sequence: one coil high at a time. Reversing this list reverses direction.
    # NOTE: order is 1-3-2-4, not 1-2-3-4 -- the 28BYJ-48's coil pairs aren't wired
    # in physical winding order by wire label, so straight sequential activation
    # causes jitter-in-place instead of rotation.
    _SEQUENCE = (
        (1, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 0, 0, 1),
    )

    def __init__(self, pins=(1, 2, 3, 4), step_delay_ms=3):
        self._coils = [Pin(p, Pin.OUT) for p in pins]
        self.step_delay_ms = step_delay_ms
        self._index = 0
        self._write((0, 0, 0, 0))

    def _write(self, state):
        for coil, value in zip(self._coils, state):
            coil.value(value)

    def step(self, direction):
        """Advance one step. direction: +1 = forward, -1 = reverse."""
        self._index = (self._index + direction) % len(self._SEQUENCE)
        self._write(self._SEQUENCE[self._index])
        utime.sleep_ms(self.step_delay_ms)

    def release(self):
        """De-energize all coils (cuts current draw / heat while stopped)."""
        self._write((0, 0, 0, 0))


class DebouncedButton:
    """Time-based hysteresis debounce for a single active-low GPIO button."""

    def __init__(self, pin_num, debounce_ms=30):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._debounce_ms = debounce_ms
        self._raw = self._pin.value()
        self._stable = self._raw
        self._last_change_ms = utime.ticks_ms()

    def pressed(self):
        """Returns True once per press (stable release -> pressed transition)."""
        raw = self._pin.value()
        now = utime.ticks_ms()

        if raw != self._raw:
            self._raw = raw
            self._last_change_ms = now

        edge = False
        if utime.ticks_diff(now, self._last_change_ms) >= self._debounce_ms and self._raw != self._stable:
            self._stable = self._raw
            edge = self._stable == 0  # 0 = pressed (active low)

        return edge


if __name__ == "__main__":
    motor = Stepper28BYJ48(pins=(1, 2, 3, 4), step_delay_ms=3)
    button_run = DebouncedButton(5)
    button_dir = DebouncedButton(6)
    direction = 1
    running = True

    print("Running. Button 1 (GPIO5) = start/stop, Button 2 (GPIO6) = reverse direction.")

    while True:
        if button_run.pressed():
            running = not running
            print("Started" if running else "Stopped")
            if not running:
                motor.release()

        if button_dir.pressed():
            direction *= -1
            print("Direction reversed:", "forward" if direction == 1 else "reverse")

        if running:
            motor.step(direction)
        else:
            utime.sleep_ms(10)
