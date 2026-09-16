![Flow Chart](../photos/flow_chart.jpg)

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

stepper.py-
The firmware file stepper.py contains a test for the micro controller that is intended to turn the stepper motor 90º in one direction and then 90º back to its original position. This test allows us to ensure that our wiring is correct and that we engage the correct motor pins to allow us to move the motor.

At the top of the file is the pinout that specifies which GPIO port is connected to which pin and which wire each of those pins is connected to. We then define the steps per revolution which is needed to specify how much each step rotates the rod.

Finally, we execute the rotation, turning 90º in the positive direction before pausing and turning back
