#include "Arduino.h"
#include "ArmGrip.h"

ArmGrip::ArmGrip(int sdaPin, int sclPin, int rHandChannel, int lHandChannel) {
  // Initialize I2C with the specified pins
  Wire.setSDA(sdaPin);
  Wire.setSCL(sclPin);
  Wire.begin();

  // Initialize PCA9685
  Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
  pwm.begin();
  //pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates

  // define Servo Channels
  _rightHandChannel = rHandChannel;
  _leftHandChannel = lHandChannel;
}

void ArmGrip::defineHandPositions(int defPosRH, int defPosLH, int clPosRH, int clPosLH) {
  int _defaultPositionRightHand = defPosRH;
  int _defaultPositionLeftHand = defPosLH;
  int _closedPositionRightHand = clPosRH;
  int _closedPositionLeftHand = clPosLH;
}

void ArmGrip::setServoAngle(int servoChannel, int angle) {
  int pulseLen = map(angle, 0, 180, _SERVOMIN, _SERVOMAX);
  //pwm.setPWM(servoChannel, 0, pulseLen);
}

