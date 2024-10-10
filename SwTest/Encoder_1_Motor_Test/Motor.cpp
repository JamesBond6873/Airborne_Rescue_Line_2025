#include "Motor.h"

Motor::Motor(int pwmPin, int encoderPinA, int encoderPinB) {
    _pwmPin = pwmPin;
    _encoderPinA = encoderPinA;
    _encoderPinB = encoderPinB;
}

void Motor::getReady() {
    // Atach Motor Pin
    _ESC.attach(_pwmPin);

    // Setup Input mode for Encoder
    pinMode(_encoderPinA, INPUT);
    pinMode(_encoderPinB, INPUT);

    // Arm Motor
    controlMotor(2000);
    delay(50);
    controlMotor(1500);
    delay(50);

    // Leave it Stopped
    controlMotor(1520);
}


void Motor::setSpeed(int Speed) {
    _Speed = Speed;
}

void Motor::updateCounter() {
    if (encoderStateA() == 1 && _lastEncoderStateA != 1) {
        _encoderCount ++;
        _lastEncoderStateA = 1;
    }
    if (encoderStateA() == 0 && _lastEncoderStateA != 0) {
        _lastEncoderStateA = 0;
    }
}
// Main file

void Motor::controlMotor(int pulse) {
    if (pulse >= 1000 && pulse <= 2000) {
        _ESC.writeMicroseconds(pulse);  // Control ESC2 globally
    } else {
        Serial.println("Invalid pulse value");
    }
}

int Motor::encoderStateA() {
    return digitalRead(_encoderPinA);
}

int Motor::encoderStateB() {
    return digitalRead(_encoderPinB);
}

int Motor::getEncoderPinA() const {
    return _encoderPinA;
}

int Motor::getEncoderPinB() const {
    return _encoderPinB;
}

int Motor::getEncoderCount() const {
    return _encoderCount;
}