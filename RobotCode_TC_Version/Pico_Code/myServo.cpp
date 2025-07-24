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
    setAngle(_camLineFollowingAng);
    delay(500);
  }
  else { Serial.println("Error 404 - Not Camera Servo"); }
}

/*void myServo::freeServo() {
  _pwm.setPWM(_channel, 0, 4096);
}*/

void myServo::freeServo() {
  _pwm.setPWM(_channel, 0, 0); // Always low
}

void myServo::EvacuationZone() {
  if (_camera == true) {
    setAngle(_camEvacuationAng);
    delay(500);
  }
  else { Serial.println("Error 404 - Not Camera Servo"); }
}

void myServo::close() {
  if (_ballStorage == true) {
    setAngle(_ballStorageCloseAng);
  }
  else { Serial.println("Error 404 - Not Ball Storage Servo"); }
}

void myServo::dropAlive() {
  if (_ballStorage == true) {
    setAngle(_ballStorageAliveAng);
  }
  else { Serial.println("Error 404 - Not Ball Storage Servo"); }
}

void myServo::dropDead() {
  if (_ballStorage == true) {
    setAngle(_ballStorageDeadAng);
  }
  else { Serial.println("Error 404 - Not Ball Storage Servo"); }
}

int myServo::getAngle() const {
    return _angle;
}

int myServo::getChannel() const {
    return _channel;
}
