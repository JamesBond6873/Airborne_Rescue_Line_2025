#include "Servo.h"

Servo::Servo(int channel, Adafruit_PWMServoDriver& pwmDriver)
    : _channel(channel), _pwm(pwmDriver), _angle(0), _defaultAngle(0) {}

void Servo::setAngle(int angle) {
    _angle = angle;
    int pulseLen = map(angle, 0, 180, SERVOMIN, SERVOMAX);
    _pwm.setPWM(_channel, 0, pulseLen);
}

void Servo::setDefault(int defaultValue) {
    _defaultAngle = defaultValue;
}

void Servo::moveDefault() {
    setAngle(_defaultAngle);
}

int Servo::getAngle() const {
    return _angle;
}

int Servo::getChannel() const {
    return _channel;
}
