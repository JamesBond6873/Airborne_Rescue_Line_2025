#ifndef ArmGrip_h
#define ArmGrip_h

#include "Arduino.h"
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

class ArmGrip {
  public:
    ArmGrip(int sdaPin, int sclPin, int rHandChannel, int lHandChannel);
    void defineHandPositions(int defPosRH, int defPosLH, int clPosRH, int clPosLH);
    void setServoAngle(int servoChannel, int angle);
    
  private:
  
    int _SERVOMIN = 150; // Minimum pulse length count (out of 4096)
    int _SERVOMAX = 600; // Maximum pulse length count (out of 4096)

    int _rightHandChannel;
    int _leftHandChannel;
    int _defaultPositionRightHand;
    int _defaultPositionLeftHand;
    int _closedPositionRightHand;
    int _closedPositionLeftHand;
};

#endif