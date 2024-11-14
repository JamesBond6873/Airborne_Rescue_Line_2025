#include <Servo.h>
#include "myServo.h"
#include "Motor.h"
#include <Adafruit_PWMServoDriver.h>
#include "ArmGrip.h"

// -------------- Motor Vars --------------

const int enc1A = 2;
const int enc1B = 3;
const int enc2A = 14;
const int enc2B = 15;
const int enc3A = 8;
const int enc3B = 9;
const int enc4A = 20;
const int enc4B = 21;

Motor motors[4] = {
    Motor(19, enc1A, enc1B),
    Motor(16, enc2A, enc2B),
    Motor(18, enc3A, enc3B),
    Motor(17, enc4A, enc4B)
};

int value;
int values[4] = {1520,1520,1520,1520};
unsigned long t0;  // control sampling rate (period ini)
unsigned long t1;  // control sampling rate (period end)
long timeInterval = 10;  // 10ms per loop = 100Hz


// -------------- Arm Vars --------------

const int leftHandServo = 0; // Channel 0 for the left hand servo
const int rightHandServo = 1; // Channel 1 for the right hand servo
const int leftArmServo = 2; // Channel 2 for the left arm servo
const int rightArmServo = 3; // Channel 3 for the right arm servo

// Create the PCA9685 object
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Create the ArmGrip object with specified channels for servos
ArmGrip Grip(pwm, rightHandServo, leftHandServo, rightArmServo, leftArmServo);


// -------------- Setup --------------

void setup() {
  // put your setup code here, to run once:
  for (int i = 0; i < 4; i++) {
    motors[i].getReady();
  }

  pinMode(LED_BUILTIN, OUTPUT);

  Grip.begin();
  Grip.openHand();

  Serial.begin(115200);

  t0 = millis();
}

void loop() {
  t1 = t0 + timeInterval;

  updateValuesFromSerial();

  Serial.print("Motors Values: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(values[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();

  for (int i = 0; i < 4; i++) {
    motors[i].controlMotor(values[i]);
  }

  while (millis() <= t1) {
    delay(1);
  }


  t0 = t1;
}


// Function to read serial input and update the list
void updateValuesFromSerial() {
  String input = readSerial();

  if (input.startsWith("M(") && input.endsWith(")")) {
    input = input.substring(2, input.length() - 1);

    int commaIndex = input.indexOf(',');
    if (commaIndex != -1) {

      // Get values a and b from the string
      int a = input.substring(0, commaIndex).toInt();
      int b = input.substring(commaIndex + 1).toInt();

      // Update the list with [a, a, b, b]
      values[0] = a;
      values[1] = a;
      values[2] = b;
      values[3] = b;
    } 
  }

  // -------------- Arm Commands -------------- 

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


String readSerial() {
  int c;
  String str = "";

  if (Serial.available() <= 0) {
    return str;
  }

  while (1) {
    c = Serial.read();
    if (c == 0 || c == 0x0A || c == 0x0D) break;
    str = str + String(char(c));
    if (Serial.available() <= 0) {
      delay(1);
      if (Serial.available() <= 0) break;
    }
  }

  return str;
}