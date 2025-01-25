#ifndef ArmGrip_h
#define ArmGrip_h

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "myServo.h"

class ArmGrip {
public:
  ArmGrip(Adafruit_PWMServoDriver& pwmDriver, int ServoChannelRH, int ServoChannelLH, int ServoChannelRA, int ServoChannelLA);
  void begin();
  void info(int detail);
  void customServoAngle(int servoChannel, int angle);
  void slowMove(int targetRH, int targetLH);
  void openHand();
  void closeHand();
  void moveAlive();
  void moveDead();
  void moveDown();
  void moveUp();
  void pickAlive();
  void pickDead();
  void defaultPosition();

private:
  Adafruit_PWMServoDriver& pwm;

  myServo _RightHandServo;
  myServo _LeftHandServo;
  myServo _RightArmServo;
  myServo _LeftArmServo;

  // Hand Vars
  int _defPosRH = 180;
  int _defPosLH = 8;
  int _PosRH = _defPosRH;
  int _PosLH = _defPosLH;
  int _clPosRH = 130;
  int _clPosLH = 50;
  int _alivePosRH = 170;
  int _alivePosLH = 85;
  int _deadPosRH = 87;
  int _deadPosLH = 8;

  // Arm Vars
  int _defPosRA = 5;
  int _defPosLA = 175;
  int _upPosRA = 180;
  int _upPosLA = 0;

  // Efficiency Vars
  int _movRH;
  int _movLH;
  int _maxMov;
  int _initRH;
  int _initLH;
};

#endif
