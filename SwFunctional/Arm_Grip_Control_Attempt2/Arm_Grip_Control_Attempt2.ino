#include <Adafruit_PWMServoDriver.h>
#include "ArmGrip.h"

// Define channels for servos
const int leftHandServo = 0; // Channel 0 for the left hand servo
const int rightHandServo = 1; // Channel 1 for the right hand servo
const int leftArmServo = 2; // Channel 2 for the left arm servo
const int rightArmServo = 3; // Channel 3 for the right arm servo

// Create the PCA9685 object
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Create the ArmGrip object with specified channels for servos
ArmGrip Grip(pwm, rightHandServo, leftHandServo, rightArmServo, leftArmServo);

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  Grip.begin();
  Grip.openHand();
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');  // Read the input from the serial monitor
    input.trim();  // Remove any leading/trailing whitespace
    Serial.println(input);  // Echo the input back to the serial monitor

    if (input == "S0") { Grip.openHand(); }
    else if (input == "S1") { Grip.closeHand(); }
    else if (input == "S2") { Grip.moveAlive(); }
    else if (input == "S3") { Grip.moveDead(); }
    else if (input == "A0") { Grip.moveDown(); }
    else if (input == "A1") { Grip.moveUp(); }
    else if (input == "SA") { Grip.pickAlive(); }
    else if (input == "SD") { Grip.pickDead(); }

    else if (input.startsWith("S4,")) {
      // Parse the command for individual servo control
      int commaIndex1 = input.indexOf(',');
      int commaIndex2 = input.indexOf(',', commaIndex1 + 1);

      if (commaIndex1 != -1 && commaIndex2 != -1) {
        String servoIdStr = input.substring(commaIndex1 + 1, commaIndex2);
        String angleStr = input.substring(commaIndex2 + 1);

        int servoId = servoIdStr.toInt();
        int angle = angleStr.toInt();

        // Validate the servo angle
        if (angle >= 0 && angle <= 180) {
          Serial.print("Set servo ");
          Serial.print(servoId);
          Serial.print(" to ");
          Serial.print(angle);
          Serial.println(" degrees");
          Grip.customServoAngle(servoId, angle);
        } else {
          Serial.println("Invalid angle.");
        }
      } else {
        Serial.println("Invalid command format. Use S4,R,Angle");
      }
    }
  }
}
