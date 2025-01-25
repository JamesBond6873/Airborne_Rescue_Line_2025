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

int myServo::getAngle() const {
    return _angle;
}

int myServo::getChannel() const {
    return _channel;
}
