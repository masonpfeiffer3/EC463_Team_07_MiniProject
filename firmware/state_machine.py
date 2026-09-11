"""
Meeting timer state machine for XIAO ESP32-S3 (MicroPython).

States:
    IDLE    -- selecting a preset, hand parked at the preset's position, LED blue
    RUNNING -- counting down, hand sweeping from the preset position back to
               home (0 deg), LED green
    PAUSED  -- countdown frozen in place, LED red

Stepper positions, 5 total, 72 degrees apart (360 / 5):
    0 deg   -- home / reset position
    72 deg  -- 15 min preset
    144 deg -- 20 min preset
    216 deg -- 25 min preset
    288 deg -- 30 min preset
While RUNNING, the hand sweeps continuously from its preset angle down to
0 deg over the preset's duration, arriving at 0 deg exactly at timeout --
timeout and reset land on the same physical position by design.

Buttons (see firmware/README for pin table):
    GPIO5 (Button 1) -- IDLE: cycle preset selection | RUNNING/PAUSED: reset to home
    GPIO6 (Button 2) -- IDLE: start countdown        | RUNNING/PAUSED: pause/resume

LED (common-cathode RGB, GPIO7=Red, GPIO8=Blue, GPIO9=Green), pulsing ~1s period:
    IDLE = blue, RUNNING = green, PAUSED = red

Known simplifications:
    - No homing sensor: the hand is assumed to be physically parked at the
      home/reset position when the board powers on.
    - Moving to a new preset (idle select) or resetting are done as a single
      blocking move -- buttons aren't polled mid-move for those two actions.
"""

from machine import Pin, PWM
import utime

# ---- Stepper ----------------------------------------------------------

class Stepper28BYJ48:
    # Wave drive sequence: one coil high at a time. 1-3-2-4 order (not 1-2-3-4)
    # avoids jitter-in-place on this specific 28BYJ-48 unit.
    _SEQUENCE = (
        (1, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 0, 0, 1),
    )
    STEPS_PER_REV = 2048

    def __init__(self, pins=(1, 2, 3, 4), step_delay_ms=3):
        self._coils = [Pin(p, Pin.OUT) for p in pins]
        self.step_delay_ms = step_delay_ms
        self._index = 0
        self.angle = 0.0  # assumed home at power-on, see module docstring
        self._write((0, 0, 0, 0))

    def _write(self, state):
        for coil, value in zip(self._coils, state):
            coil.value(value)

    def step(self, direction):
        """Advance one step. direction: +1 = forward, -1 = reverse."""
        self._index = (self._index + direction) % len(self._SEQUENCE)
        self._write(self._SEQUENCE[self._index])
        self.angle = (self.angle + direction * 360.0 / self.STEPS_PER_REV) % 360.0
        utime.sleep_ms(self.step_delay_ms)

    def release(self):
        self._write((0, 0, 0, 0))

    def move_to(self, target_deg):
        """Blocking move to an absolute angle via the shortest direction."""
        diff = (target_deg - self.angle + 540) % 360 - 180
        steps = round(diff * self.STEPS_PER_REV / 360.0)
        direction = 1 if steps >= 0 else -1
        for _ in range(abs(steps)):
            self.step(direction)
        self.angle = target_deg % 360.0  # snap, avoids rounding drift
        self.release()


# ---- Button ------------------------------------------------------------

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


# ---- LED -----------------------------------------------------------------

PULSE_PERIOD_MS = 1000


class PulsingRGB:
    """Non-blocking breathing pulse on one of three PWM channels at a time."""

    def __init__(self, red_pin, blue_pin, green_pin):
        self._channels = {
            "red": PWM(Pin(red_pin), freq=1000, duty_u16=0),
            "blue": PWM(Pin(blue_pin), freq=1000, duty_u16=0),
            "green": PWM(Pin(green_pin), freq=1000, duty_u16=0),
        }
        self._active = None

    def set_color(self, color):
        if color != self._active:
            for name, pwm in self._channels.items():
                pwm.duty_u16(0)
            self._active = color

    def update(self, now_ms):
        """Call every loop iteration to advance the pulse."""
        if self._active is None:
            return
        half = PULSE_PERIOD_MS // 2
        phase = now_ms % PULSE_PERIOD_MS
        level = phase / half if phase < half else (PULSE_PERIOD_MS - phase) / half
        self._channels[self._active].duty_u16(int(65535 * level))


# ---- State machine ---------------------------------------------------

IDLE, RUNNING, PAUSED = "IDLE", "RUNNING", "PAUSED"

# TESTING ONLY: durations are in seconds here (15/20/25/30s) instead of
# minutes so bring-up doesn't require waiting through a real countdown.
# Revert to minutes (and restore the *60*1000 conversion below) before demo.
PRESET_SECONDS = {1: 15, 2: 20, 3: 25, 4: 30}

if __name__ == "__main__":
    motor = Stepper28BYJ48(pins=(1, 2, 3, 4), step_delay_ms=3)
    button_select_reset = DebouncedButton(5)
    button_start_pause = DebouncedButton(6)
    led = PulsingRGB(red_pin=7, blue_pin=8, green_pin=9)

    state = IDLE
    preset_index = 0  # 0 = none selected / home, 1-4 = preset slot
    steps_remaining = 0
    step_interval_ms = 0.0
    active_elapsed_ms = 0.0

    led.set_color("blue")
    print("Idle. Button1 (GPIO5) selects a preset / resets, Button2 (GPIO6) starts/pauses/resumes.")

    last_loop_ms = utime.ticks_ms()

    while True:
        now = utime.ticks_ms()
        dt = utime.ticks_diff(now, last_loop_ms)
        last_loop_ms = now

        if state == IDLE:
            if button_select_reset.pressed():
                preset_index = (preset_index % 4) + 1
                motor.move_to(preset_index * 72)
                print("Selected preset:", PRESET_SECONDS[preset_index], "s (testing units)")

            elif button_start_pause.pressed():
                if preset_index != 0:
                    seconds = PRESET_SECONDS[preset_index]
                    steps_remaining = round(preset_index * 72 * Stepper28BYJ48.STEPS_PER_REV / 360.0)
                    step_interval_ms = (seconds * 1000) / steps_remaining
                    active_elapsed_ms = 0.0
                    state = RUNNING
                    led.set_color("green")
                    print("Started:", seconds, "s countdown")
                else:
                    print("No preset selected -- press Button1 first")

        elif state == RUNNING:
            if button_select_reset.pressed():
                motor.move_to(0)
                state = IDLE
                preset_index = 0
                steps_remaining = 0
                active_elapsed_ms = 0.0
                led.set_color("blue")
                print("Reset")

            elif button_start_pause.pressed():
                state = PAUSED
                led.set_color("red")
                print("Paused")

            else:
                active_elapsed_ms += dt
                while steps_remaining > 0 and active_elapsed_ms >= step_interval_ms:
                    motor.step(-1)
                    steps_remaining -= 1
                    active_elapsed_ms -= step_interval_ms

                if steps_remaining == 0:
                    state = IDLE
                    preset_index = 0
                    active_elapsed_ms = 0.0
                    led.set_color("blue")
                    print("Timer complete")

        elif state == PAUSED:
            if button_select_reset.pressed():
                motor.move_to(0)
                state = IDLE
                preset_index = 0
                steps_remaining = 0
                active_elapsed_ms = 0.0
                led.set_color("blue")
                print("Reset")

            elif button_start_pause.pressed():
                state = RUNNING
                led.set_color("green")
                print("Resumed")

        led.update(now)
        utime.sleep_ms(5)
