Arduino code:

Code Overview:
This Arduino code controls two motors: a stepper motor that moves the participant’s hand back and forth, and a servo motor that delivers two taps to the participant’s other hand—one with fixed intensity and another with a variable intensity. The motors operate based on commands received from a serial interface, which allows the experiment to be controlled remotely from a computer (usually through a Python script).

Summary:
Stepper Motor:

The stepper motor simulates the participant's finger hitting a wall by moving forward and backward by a specified distance (0.5 cm, 1.5 cm, or 3 cm) at either slow or fast speeds (1 cm/s or 2 cm/s).
Servo Motor:

The servo motor delivers two consecutive taps to the participant's second finger: one with a fixed intensity of 4, and the second with a variable intensity.
Serial Communication:

The Arduino listens for commands from the Python script over the serial port. The commands dictate the experimental condition (distance), and the intensities of the two taps (fixed and variable).
This setup forms the core of the experiment where the participant's response is collected after

Python code:

The Python script is designed to control an experiment involving a stepper motor and a servo motor through an Arduino. The experiment uses the QuestHandler algorithm to adaptively adjust the intensity of a second tap delivered by the servo motor. Participants respond to each trial by using a foot switch.  

Summary:
The script establishes a serial connection with an Arduino to control a stepper motor and a servo motor for an experiment involving two taps of varying intensity.
Pygame is used to capture participant responses
The QuestHandler algorithm dynamically adjusts the intensity of the second tap based on the participant's feedback
The experiment consists of 120 randomized trials, with varying distances, speeds, and tap intensities.

[![image](https://github.com/user-attachments/assets/90305b41-cd26-4fb1-acaf-7f9f7cc99faa)](https://www.youtube.com/watch?v=YJ5FuXm5OEo)



