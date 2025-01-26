#include "myServo.h"

myServo::myServo(int channel, Adafruit_PWMServoDriver& pwmDriver, bool camera, bool ballStorage)
    : _channel(channel), _pwm(pwmDriver), _angle(0), _defaultAngle(0), _camera(camera), _ballStorage(ballStorage) {}

void myServo::setAngle(int angle) {
    _angle = angle;
    int pulseLen = map(angle, 0, 180, SERVOMIN, SERVOMAX);
    _pwm.setPWM(_channel, 0, pulseLen);
}

void myServo::setDefault(int defaultValue) {
    _defaultAngle = defaultValue;
}

void myServo::moveDefault() {
    setAngle(_defaultAngle);
}

void myServo::lineFollowing() {
  if (_camera == true) {
    //Empty
    //Place Holder
  }
}

void myServo::EvacuationZone() {
  if (_camera == true) {
    //Empty
    //Place Holder
  }
}

void myServo::close() {
  if (_ballStorage == true) {
    //Empty
    //Place Holder
  }
}

void myServo::dropAlive() {
  if (_ballStorage == true) {
    //Empty
    //Place Holder
  }
}

void myServo::dropDead() {
  if (_ballStorage == true) {
    //Empty
    //Place Holder
  }
}

int myServo::getAngle() const {
    return _angle;
}

int myServo::getChannel() const {
    return _channel;
}
