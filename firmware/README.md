this folder contains firmware that to flash to the ESP32 S3, in order of development prototyping

1. stepper.py drives the stepper 90 degrees back and forth
2. push_button.py actively runs the motor and reverses it's direction upon button press
3. led.py flashes the LED between it's colors using PWM
4. state_machine.py combines these features to create the timer


state machine-
- LED color corresponds to state
- blue = idle (one button cycles through time select, the other starts)
- green = active (one button resets it, the other pauses)
- red = paused (one button resets it, the other resumes)

Each time has it's own position, as well as the reset position, which upon starting the stepper motor moves toward.
5 total positions- 15, 20, 25, 30, and the reset position.