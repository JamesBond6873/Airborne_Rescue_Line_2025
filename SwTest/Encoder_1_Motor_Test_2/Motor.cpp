#include "Motor.h"

// Static pointer array for mapping interrupts to motor instances
Motor* Motor::instances[4] = {nullptr, nullptr, nullptr, nullptr};
int Motor::instanceIndex = 0;

// Constructor
Motor::Motor(int pwmPin, int encoderPinA, int encoderPinB) {
    _pwmPin = pwmPin;
    _encoderPinA = encoderPinA;
    _encoderPinB = encoderPinB;
    _encoderCount = 0;

    _lastEncoderStateA = 0;
    _lastEncoderStateB = 0;

    // Store this instance in the instances array
    instances[instanceIndex++] = this;
}

void Motor::getReady() {
    // Attach Motor Pin
    _ESC.attach(_pwmPin);

    // Setup Input mode for Encoder
    pinMode(_encoderPinA, INPUT);
    pinMode(_encoderPinB, INPUT);

    // Attach interrupts to encoder pins
    attachInterrupt(digitalPinToInterrupt(_encoderPinA), Motor::encoderA_ISR, CHANGE);
    attachInterrupt(digitalPinToInterrupt(_encoderPinB), Motor::encoderB_ISR, CHANGE);

    // Arm Motor
    controlMotor(2000); // Start with max pulse for ESC
    delay(50);
    controlMotor(1500); // Bring to neutral position
    delay(50);
    controlMotor(1520); // Stop motor
}

void Motor::controlMotor(int pulse) {
    if (pulse >= 1000 && pulse <= 2000) {
        _ESC.writeMicroseconds(pulse);  // Control ESC with pulse width
    } else {
        Serial.println("Invalid pulse value");
    }
}

// Static ISR for encoder A
void Motor::encoderA_ISR() {
    for (int i = 0; i < instanceIndex; i++) {
        if (digitalRead(instances[i]->_encoderPinA) == digitalRead(instances[i]->_encoderPinB)) {
            instances[i]->_encoderCount++;  // Moving forward
        } else {
            instances[i]->_encoderCount--;  // Moving backward
        }
    }
}

// Static ISR for encoder B
void Motor::encoderB_ISR() {
    for (int i = 0; i < instanceIndex; i++) {
        if (digitalRead(instances[i]->_encoderPinA) == digitalRead(instances[i]->_encoderPinB)) {
            instances[i]->_encoderCount++;  // Moving forward
        } else {
            instances[i]->_encoderCount--;  // Moving backward
        }
    }
}

int Motor::getEncoderCount() const {
    return _encoderCount;
}

/*
int Motor::encoderStateA() {
    return digitalRead(_encoderPinA);
}

int Motor::encoderStateB() {
    return digitalRead(_encoderPinB);
}

int Motor::getEncoderCount() const {
    return _encoderCount;
}
*/