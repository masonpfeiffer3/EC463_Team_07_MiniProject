# 07-Miniproject
[Demo Link](https://drive.google.com/file/d/174wR8b0HiahtT9Z3u5mZbhheMCSKgrk_/view?usp=sharing)

[Project Board Link (responsibilities listed here)](https://app.notion.com/p/Mini-Project-Board-3da2b21b7a02809690e9f732688cc1ad?source=copy_link)

## Product Photo

<p align="center">
  <img src="photos/product.png" width="60%" />
</p>

## How to Use

The device has two buttons (A and B) and one RGB status LED. On power-up the pointer is assumed to be parked at the home/reset position (0°).

1. **Idle / Time Select** — LED glows steady green.
   - Press **Button A** to cycle through the four presets (15, 20, 25, 30 min). Each press drives the stepper motor to move the pointer to that preset's angle.
   - Press **Button B** to start the countdown for the currently selected preset.
2. **Count Down** — LED flashes green.
   - The pointer sweeps continuously from the preset angle back toward the home position over the course of the countdown, arriving back at 0° exactly at timeout.
   - Press **Button A** to reset immediately (pointer returns home, state returns to idle).
   - Press **Button B** to pause.
3. **Pause** — LED flashes red/green.
   - Press **Button A** to reset (pointer returns home).
   - Press **Button B** to resume the countdown from where it left off.

### Building blocks demonstrated

- **GPIO** — both buttons are read as debounced digital inputs, and the microcontroller's output pins drive the L293D motor driver's control lines; GPIO is the foundation every other subsystem (motor, LED, buttons) is built on.
- **PWM** — the RGB LED's steady/flashing states are produced by driving each color's GPIO pin with a PWM duty cycle that ramps up and down (`PulsingRGB` in `firmware/angle_config.py`, prototyped in `firmware/led.py`).
- **Motor control** — a 28BYJ-48 stepper motor, wave-driven through an L293D H-bridge (`Stepper28BYJ48` in `firmware/angle_config.py`), moves the clock-hand pointer to precise preset angles and sweeps it proportionally during the countdown.
- **Low-power operation** — the stepper's coils are de-energized (`release()`) as soon as a move completes, so the motor only draws current (and generates heat) while actively stepping rather than continuously holding torque at a fixed position.

## Repository Structure

```
.
├── firmware/                # Micro source code
├── Hardware/
│   ├── Electrical/          # Schematics, wiring diagrams, and component docs
│   └── Mechanical/          # Enclosure CAD/STL files and drawings
├── photos/                  # All project images (schematics, CAD drawings, product photos, etc.)
└── README.md
```

## Flow Chart & Electrical Schematic

<p align="center">
  <img src="photos/flow_chart.jpg" height="300" />
  <img src="photos/SchematicWiring.png" height="300" />
</p>

## Approach & Progress

After setting up the team repo with a branch protection ruleset for `main`, development started on the breadboard circuitry needed to interface with the embedded hardware alongside the software prototype.

This was built up one step at a time:

1. Verified the ESP32-S3 could be flashed via Thonny MicroPython with a simple blink test on the onboard LED.
2. Wired the necessary GPIO pins to the motor controller, including grounding, supplying voltage, and tying the enable pins high, then connected the motor to the controller.
3. Tested with a simple script that spun the motor 90° back and forth based on its gear ratio.
4. Attached the push buttons to additional I/O and continuously ran the motor until a button press was detected (with software debouncing) — one button reverses direction, the other pauses/resumes motion.
5. Connected 3 GPIO pins to each RGB LED anode prong (through resistors) and grounded the cathode, then drove PWM signals to the GPIO pins to experiment with flashing frequencies.
6. Implemented the finite state machine for operation — the core of the project. With all other embedded components functioning, wiring up the clock-specific use case was trivial beyond the state machine itself.

The software/embedded prototype now exists, and the rest of the team can carry it forward to the final version.

### Design Intentionality and Tradeoffs

| State | LED | Button A | Button B |
|---|---|---|---|
| Idle / Time Select | Blue | Time select | Start |
| Count Down | Green | Reset | Pause |
| Pause | Red | Reset | Resume |

In the idle state, the pointer indicates the selected time in 360°/5 = 72° increments (requiring a clock face labeled at each position). Upon start, the pointer moves from the selected time position to the reset position. There are 5 total positions — 4 time options plus the reset position.

There are multiple ways to lay out these positions, and the tradeoff considered here is that total movement isn't proportional to the selected time (15 min is 72° from reset, 20 min is 144°, etc.), but functionally the user can still gauge the proportion of time that has passed since the timer started.

<p align="center">
  <img src="photos/design_concept.png" width="70%" />
</p>

**Update:** the final version changed this so the countdown is proportional. Even though only 15/20/25/30 are selectable times, the dial reserves the space for 5 and 10 minutes between each selection and the reset (0) position — so the pointer's distance from reset always reflects how much time is actually left, regardless of which time was selected.

## Team

| Role | Named Members |
|------|---------|
| Mechanical Housing | Lana Kader, Niyati Patel, Arham Mufti |
| Electrical Wiring | Lana Kader, Mason Pfeiffer, Ethan Manfredi |
| uController Firmware | Darwin Quizhpi, Phillip Omohundro, Mason Pfeiffer, Ethan Manfredi |

[Project Board Link (responsibilities listed here)](https://app.notion.com/p/Mini-Project-Board-3da2b21b7a02809690e9f732688cc1ad?source=copy_link)
