#include "ArmGrip.h"

// Corrected constructor definition
ArmGrip::ArmGrip(Adafruit_PWMServoDriver& pwmDriver, int ServoChannelRH, int ServoChannelLH, int ServoChannelRA, int ServoChannelLA)
  : pwm(pwmDriver), _RightHandServo(ServoChannelRH, pwmDriver, false, false), _LeftHandServo(ServoChannelLH, pwmDriver, false, false), _RightArmServo(ServoChannelRA, pwmDriver, false, false), _LeftArmServo(ServoChannelLA, pwmDriver, false, false) {}

void ArmGrip::begin() {
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(60);
  _RightHandServo.setDefault(_defPosRH);
  _LeftHandServo.setDefault(_defPosLH);
}

void ArmGrip::info(int detail) {
  if (detail == 1) {
    // Right Hand
    Serial.print("Right Hand Servo - Channel: ");
    Serial.print(_RightHandServo.getChannel());
    Serial.print("\t Angle: ");
    Serial.print(_RightHandServo.getAngle());
    Serial.print("\t Move: ");
    Serial.println(_movRH);

    // Left Hand
    Serial.print("Left Hand Servo - Channel: ");
    Serial.print(_LeftHandServo.getChannel());
    Serial.print("\t Angle: ");
    Serial.print(_LeftHandServo.getAngle());
    Serial.print("\t Move: ");
    Serial.println(_movLH);
  }
  else if (detail == 2) {
    // Right Arm
    Serial.print("Right Arm Servo - Channel: ");
    Serial.print(_RightArmServo.getChannel());
    Serial.print("\t Angle: ");
    Serial.println(_RightArmServo.getAngle());
    
    // Left Arm
    Serial.print("Left Arm Servo - Channel: ");
    Serial.print(_LeftArmServo.getChannel());
    Serial.print("\t Angle: ");
    Serial.println(_LeftArmServo.getAngle());
  }
}

void ArmGrip::customServoAngle(int servoChannel, int angle) {
  if (servoChannel == _RightHandServo.getChannel()) {_RightHandServo.setAngle(angle);}
  else if (servoChannel == _LeftHandServo.getChannel()) {_LeftHandServo.setAngle(angle);}
  else if (servoChannel == _RightArmServo.getChannel()) {_RightArmServo.setAngle(angle);}
  else if (servoChannel == _LeftArmServo.getChannel()) {_LeftArmServo.setAngle(angle);}
  else {Serial.println("Wrong Servo Channel!");}
}

void ArmGrip::slowMove(int targetRH, int targetLH) {
  // Get Initial Angle and Max Moving Servo
  _initRH = _RightHandServo.getAngle();
  _initLH = _LeftHandServo.getAngle();

  _movRH = targetRH - _initRH;
  _movLH = targetLH - _initLH;
  info(1);

  _maxMov = max(abs(_movRH), abs(_movLH));

  // Move servos slowly
  for (int i = 0; i <= _maxMov; i++) {
    _RightHandServo.setAngle(_initRH + (_movRH * i) / _maxMov);
    _LeftHandServo.setAngle(_initLH + (_movLH * i) / _maxMov);
    delay(5);
  }  
}

void ArmGrip::openHand() {
  Serial.println("------Open Hand------");

  // Move slowly
  slowMove(_defPosRH, _defPosLH);

  // Make Sure you get There
  _RightHandServo.setAngle(_defPosRH);
  _LeftHandServo.setAngle(_defPosLH);

}

void ArmGrip::closeHand() {
  Serial.println("------Close Hand------");
  
  // Move slowly
  slowMove(_clPosRH, _clPosLH);

  // Make Sure you get There
  _RightHandServo.setAngle(_clPosRH);
  _LeftHandServo.setAngle(_clPosLH);
}

void ArmGrip::moveAlive() {
  Serial.println("------Move Alive------");
  
  // Move slowly
  slowMove(_alivePosRH, _alivePosLH);
  
  // Make Sure you get There
  _RightHandServo.setAngle(_alivePosRH);
  _LeftHandServo.setAngle(_alivePosLH);
}

void ArmGrip::moveDead() {
  Serial.println("------Move Dead------");
  
  // Move slowly
  slowMove(_deadPosRH, _deadPosLH);

  // Make Sure you get There
  _RightHandServo.setAngle(_deadPosRH);
  _LeftHandServo.setAngle(_deadPosLH);
}

void ArmGrip::moveDown() {
  Serial.println("------Move Down------");
  
  info(2);

  // Move Slowly
  for (int i = 0; i <= _defPosLA; i++) {
    _RightArmServo.setAngle(180 - i);
    _LeftArmServo.setAngle(i);
    delay(5);
  }

  // Make Sure you get There
  _RightArmServo.setAngle(_defPosRA);
  _LeftArmServo.setAngle(_defPosLA);
}

void ArmGrip::moveUp() {
  Serial.println("------Move Up------");

  info(2);

  // Move Slowly
  for (int i = 0; i <= _upPosRA; i++) {
    _RightArmServo.setAngle(i);
    _LeftArmServo.setAngle(180 - i);
    delay(5);
  }

  // Make Sure you get There
  _RightArmServo.setAngle(_upPosRA);
  _LeftArmServo.setAngle(_upPosLA);
}

void ArmGrip::pickAlive() {
  Serial.println("");
  Serial.println("Picking Up Alive Victim \t");

  // Pick Ball in the Middle
  closeHand();
  delay(200);

  // Take Ball to the dead Side
  moveAlive();
  delay(500);

  // Go Up to the Drop Zone
  moveUp();
  delay(1000);

  // Release the Ball
  openHand();
}

void ArmGrip::pickDead() {
  Serial.println("");
  Serial.println("Picking Up Dead Victim \t");

  // Pick Ball in the Middle
  closeHand();
  delay(200);

  // Take Ball to the dead Side
  moveDead();
  delay(500);

  // Go Up to the Drop Zone
  moveUp();
  delay(1000);

  // Release the Ball
  openHand();
}

void ArmGrip::defaultPosition() {
  //Empty - Place holder
  //Pass
}
