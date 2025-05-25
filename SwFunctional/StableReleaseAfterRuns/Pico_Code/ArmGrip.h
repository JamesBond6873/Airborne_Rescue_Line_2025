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
  void slowMoveHand(int targetRH, int targetLH);
  void slowMoveArm(int targetRA, int targetLA);
  void openHand();
  void closeHand();
  void moveAlive();
  void moveDead();
  void moveDown();
  void moveUp();
  void pickAlive();
  void pickDead();
  void defaultPosition();
  void freeAllServos();
  void freeXServo(int servoChannel);

private:
  Adafruit_PWMServoDriver& pwm;

  myServo _RightHandServo;
  myServo _LeftHandServo;
  myServo _RightArmServo;
  myServo _LeftArmServo;

  // Hand Vars
  int _defPosRH = 170;
  int _defPosLH = 10;
  //int _PosRH = _defPosRH;
  //int _PosLH = _defPosLH;
  int _clPosRH = 125;
  int _clPosLH = 55;
  int _alivePosRH = 170;
  int _alivePosLH = 95;
  int _deadPosRH = 85;
  int _deadPosLH = 10;

  // Arm Vars
  int _defPosRA = 5;
  int _defPosLA = 180;
  int _upPosRA = 180;
  int _upPosLA = 0;

  // Efficiency Vars
  int _movRH;
  int _movLH;
  int _movRA;
  int _movLA;
  int _maxMov;
  int _initRH;
  int _initLH;
  int _initRA;
  int _initLA;
};

#endif
