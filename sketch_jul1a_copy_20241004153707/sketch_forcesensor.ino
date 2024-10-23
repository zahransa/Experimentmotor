#include <Servo.h>
#include <TMC2208Stepper.h>
#include <TMC2208Stepper_REGDEFS.h>

// Pin Definitions
#define EN_PIN 6   // Enable pin for the stepper driver
#define STEP_PIN 7 // Step pin for the stepper driver
#define DIR_PIN 8  // Direction pin for the stepper driver
#define sensorPinA A6 // Force sensor pin A
#define sensorPinB A7 // Force sensor pin B

Servo servo;        // Create a servo object
int neutralPos = 30; // Neutral position for the servo
float iterationStep = 0.00247551686615886833514689880305; // cm per step

void setup() {
  // Initialize the stepper motor control pins
  pinMode(EN_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  // Set initial states
  digitalWrite(EN_PIN, LOW); // Activate stepper driver (LOW active)
  digitalWrite(STEP_PIN, LOW);
  digitalWrite(DIR_PIN, LOW); // Default direction

  // Initialize servo motor on pin 2
  servo.attach(2);
  servo.write(neutralPos); // Set servo to neutral position

  // Initialize serial communication
  Serial.begin(57600);
  Serial.println("Arduino is ready");
}

// Function to move the stepper motor for a specified number of steps at a given speed
void moveStepper(int steps, int direction, float speed) {
  digitalWrite(DIR_PIN, direction); // Set the direction
  digitalWrite(EN_PIN, LOW);        // Activate the stepper driver

  // Calculate delay based on the speed
  float timePerStep = iterationStep / speed;   // Time for one step in seconds
  int delayTime = timePerStep * 1000000;       // Convert to microseconds

  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(delayTime); // Use calculated delay based on speed
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(delayTime); // Adjust delay based on speed
  }
  digitalWrite(EN_PIN, HIGH); // Deactivate the stepper driver when done
}

// Function to control the intensity of the tap (servo motor)
void moveServo(int intensity) {
  int angle = neutralPos + (intensity * 10);  // Scale intensity to angle
  Serial.print("Moving servo to angle: ");
  Serial.println(angle);
  servo.write(angle);  // Set the servo position based on intensity
  delay(200);          // Hold the position for a brief moment
  servo.write(neutralPos);  // Return to the neutral position (simulate the tap)
}

// Function to read the force sensor difference
int readForceSensor() {
  int sensorValueA = analogRead(sensorPinA);  // Read value from sensor pin A
  int sensorValueB = analogRead(sensorPinB);  // Read value from sensor pin B
  int sensorDifference = abs(sensorValueA - sensorValueB); // Calculate absolute difference
  Serial.print("Force sensor difference: ");
  Serial.println(sensorDifference);  // Print the sensor difference
  return sensorDifference;
}

void loop() {
  // Read and print force sensor data continuously
  int forceValue = readForceSensor();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace or newline characters

    // Command format: "MOVE <distance> <speed>"
    if (command.startsWith("MOVE_BACK")) {
      int stepsToPerform = 3 / iterationStep;  // Move 3 cm back
      float speed = 1.0;  // Always slow for condition 8
      Serial.println("Moving stepper back 3 cm at slow speed.");
      moveStepper(stepsToPerform, LOW, speed);
    } 
    else if (command.startsWith("MOVE_FORWARD")) {
      int stepsToPerform = 3 / iterationStep;  // Move back to the wall
      float speed = 1.0;  // Speed for returning to the wall
      Serial.println("Returning to the wall.");
      moveStepper(stepsToPerform, HIGH, speed);
    }
    // Command format: "0<condition><fixed_intensity><variable_intensity>"
    else if (command.startsWith("0")) {
      int condition = command.substring(1, 2).toInt();
      int fixed_intensity = command.substring(2, 3).toInt();
      int variable_intensity = command.substring(3, 4).toInt();

      if (condition == 8) {
        // Move back 3 cm, apply taps, and wait for space bar press
        int stepsToPerform = 3 / iterationStep;
        float speedForDrive = 1.0; // Slow speed
        moveStepper(stepsToPerform, LOW, speedForDrive);
        
        // Apply the first tap (fixed intensity)
        moveServo(fixed_intensity);
        delay(1000);  // 1 second delay between taps

        // Apply the second tap (variable intensity)
        moveServo(variable_intensity);

        // Wait for the "continue" signal from Python
        Serial.println("Waiting for foot press...");
        while (true) {
          if (Serial.available() > 0) {
            String nextCommand = Serial.readStringUntil('\n');
            nextCommand.trim();
            if (nextCommand == "continue") {
              // Speed for returning to the wall is always fast for condition 8
              moveStepper(stepsToPerform, HIGH, 2.0);  // Move forward to the wall at fast speed
              Serial.println("Returning to the wall.");
              break;
            }
          }
        }
      } else {
        // Conditions 1 to 6: Move stepper and apply two taps
        int stepsToPerform = 0;
        float speedFor1stDrive = 0.5;  // Default slow speed
        float speedFor2ndDrive = 1.0;  // Speed for returning (fast or slow depending on the condition)

        if (condition == 1) {  // 0.5 cm, slow speed
          stepsToPerform = 0.5 / iterationStep;
          speedFor1stDrive = 1.0;
          speedFor2ndDrive = 1.0;  // Return at same speed
        } else if (condition == 2) {  // 0.5 cm, fast speed
          stepsToPerform = 0.5 / iterationStep;
          speedFor1stDrive = 2.0;
          speedFor2ndDrive = 2.0;  // Return at same speed
        } else if (condition == 3) {  // 1.5 cm, slow speed
          stepsToPerform = 1.5 / iterationStep;
          speedFor1stDrive = 1.0;
          speedFor2ndDrive = 1.0;  // Return at same speed
        } else if (condition == 4) {  // 1.5 cm, fast speed
          stepsToPerform = 1.5 / iterationStep;
          speedFor1stDrive = 2.0;
          speedFor2ndDrive = 2.0;  // Return at same speed
        } else if (condition == 5) {  // 3 cm, slow speed
          stepsToPerform = 3 / iterationStep;
          speedFor1stDrive = 1.0;
          speedFor2ndDrive = 1.0;  // Return at same speed
        } else if (condition == 6) {  // 3 cm, fast speed
          stepsToPerform = 3 / iterationStep;
          speedFor1stDrive = 2.0;
          speedFor2ndDrive = 2.0;  // Return at same speed
        }

        // Move stepper forward with speedFor1stDrive
        moveStepper(stepsToPerform, LOW, speedFor1stDrive);

        delay(1000);

        // Move stepper back to original position with speedFor2ndDrive
        moveStepper(stepsToPerform, HIGH, speedFor2ndDrive);

        // Perform two taps
        moveServo(fixed_intensity);
        delay(1000);
        moveServo(variable_intensity);
      }
    }
  }
}
