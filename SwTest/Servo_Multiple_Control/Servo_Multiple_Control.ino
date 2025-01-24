#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Create the PCA9685 object
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Define servo positions
#define SERVOMIN  150 // Minimum pulse length count (out of 4096)
#define SERVOMAX  600 // Maximum pulse length count (out of 4096)

// Define channels for servos
const int leftHandServo = 0; // Channel 0 for the left hand servo
const int rightHandServo = 1; // Channel 1 for the right hand servo
const int leftArmServo = 2; // Channel 2 for the left arm servo
const int rightArmServo = 3; // Channel 3 for the right arm servo


// Servo positions
int defPosRH = 180; // Default (Open) position for right servo
int defPosLH = 8;  // Default (Open) position for left servo
int PosRH = defPosRH; // Current Pos right servo
int PosLH = defPosLH; // Current Pos left servo
int clPosRH = 130;   // Close position for right servo
int clPosLH = 50;   // Close position for left servo

void setup() {
  Serial.begin(9600);
  //Wire.setSDA(2); // Set SDA to GPIO 16
  //Wire.setSCL(3); // Set SCL to GPIO 17
  Wire.begin();    // Initialize I2C with the specified pins on GPIO 4 and 5
  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates

  // Initialize servos to default positions to avoid shaking
  setServoAngle(rightHandServo, defPosRH);
  setServoAngle(leftHandServo, defPosLH);
  setServoAngle(rightArmServo, 0);
  setServoAngle(leftArmServo, 180);

  Serial.println("Enter the command (S0, S1, or S3,R,Angle) to move the servo:");
}

void setServoAngle(int servoNum, int angle) {
  int pulseLen = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  pwm.setPWM(servoNum, 0, pulseLen);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');  // Read the input from the serial monitor
    input.trim();  // Remove any leading/trailing whitespace
    Serial.println(input);  // Echo the input back to the serial monitor

    // Check if the entered command is valid
    if (input == "S0") {
      Serial.println("Open Hand");
      setServoAngle(rightHandServo, defPosRH);
      setServoAngle(leftHandServo, defPosLH);
      PosRH = defPosRH;
      PosLH = defPosLH;
    } 
    else if (input == "S1") {
      Serial.println("Close Hand");
      setServoAngle(rightHandServo, clPosRH);
      setServoAngle(leftHandServo, clPosLH);
      PosRH = clPosRH;
      PosLH = clPosLH;
    } 
    else if (input == "S2") {
      Serial.println("Right Side");
      setServoAngle(rightHandServo, 170);
      setServoAngle(leftHandServo, 85);
      PosRH = defPosRH;
      PosLH = 80;
    }
    else if (input == "S3") {
      Serial.println("Left Side");
      setServoAngle(rightHandServo, 87);
      setServoAngle(leftHandServo, 8);
    }
    else if (input.startsWith("S4,")) {
      // Parse the command for individual servo control
      int commaIndex1 = input.indexOf(',');
      int commaIndex2 = input.indexOf(',', commaIndex1 + 1);

      if (commaIndex1 != -1 && commaIndex2 != -1) {
        String servoIdStr = input.substring(commaIndex1 + 1, commaIndex2);
        String angleStr = input.substring(commaIndex2 + 1);

        int servoId = servoIdStr.toInt();
        int angle = angleStr.toInt();

        // Validate the servo ID and angle
        if (angle >= 0 && angle <= 180) {
          Serial.print("Set servo ");
          Serial.print(servoId);
          Serial.print(" to ");
          Serial.print(angle);
          Serial.println(" degrees");
          setServoAngle(servoId, angle);
        } else {
          Serial.println("Invalid angle.");
        }
      } else {
        Serial.println("Invalid command format. Use S3,R,Angle");
      }
    }
    else if (input == "A0") {
      setServoAngle(rightArmServo, 0);
      setServoAngle(leftArmServo, 180);
    }
    else if (input == "A1") {
      setServoAngle(rightArmServo, 180);
      setServoAngle(leftArmServo, 0);
    }
    else {
      Serial.println("Not a command. Input S0, S1, or S3,R,Angle!");
    }
  }
}
