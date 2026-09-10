The firmware file stepper.py contains a test for the micro controller that is intended to turn the stepper motor 90º in one direction and then 90º back to its original position. This test allows us to ensure that our wiring is correct and that we engage the correct motor pins to allow us to move the motor.

At the top of the file is the pinout that specifies which GPIO port is connected to which pin and which wire each of those pins is connected to. We then define the steps per revolution which is needed to specify how much each step rotates the rod. 

Finally, we execute the rotation, turning 90º in the positive direction before pausing and turning back
