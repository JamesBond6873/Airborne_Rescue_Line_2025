#include "Motor.h"

Motor* Motor::instances[4];  // Array to hold motor instances
int Motor::instanceIndex = 0;

// Constructor
Motor::Motor(int pwmPin, int encoderPinA, int encoderPinB) {
    _pwmPin = pwmPin;
    _encoderPinA = encoderPinA;
    _encoderPinB = encoderPinB;
    _encoderCount = 0;
    _lastSpeedCalc = 0;
    _currentRPM = 0;
    _lastUpdate = 0;

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
    controlMotor(2000);  // Max pulse for ESC
    delay(50);
    controlMotor(1500);  // Neutral position
    delay(50);
    controlMotor(1520);  // Stop motor
}

void Motor::controlMotor(int pulse) {
    if (pulse >= 1000 && pulse <= 2000) {
        _ESC.writeMicroseconds(pulse);  // Control ESC with pulse width
    } else {
        Serial.println("Invalid pulse value");
    }
}

float Motor::getRPS() {
    unsigned long currentTime = millis();
    float timeElapsed;  // Declare the missing timeElapsed variable

    if (currentTime - _lastSpeedCalc >= speedSampleInterval) {
        timeElapsed = (currentTime - _lastUpdate) / 1000.0;  // Convert ms to seconds

        if (timeElapsed > 0) {
            _currentRPM = (_encoderCount / float(pulsesPerRevolution)) / timeElapsed;
        } else {
            _currentRPM = 0;  // Avoid inf or invalid values
        }

        _lastSpeedCalc = currentTime;  // Update the last speed calculation time
        _encoderCount = 0;             // Reset encoder count for next interval
    }

    return _currentRPM;  // Return stored value from last valid calculation
}

float Motor::getRPM() {
    return getRPS() * 60;  // Convert RPS to RPM
}

// Encoder Interrupt Service Routines (ISR)
void Motor::encoderA_ISR() {
    for (int i = 0; i < instanceIndex; i++) {
        if (digitalRead(instances[i]->_encoderPinA) == digitalRead(instances[i]->_encoderPinB)) {
            instances[i]->_encoderCount++;  // Moving forward
        } else {
            instances[i]->_encoderCount--;  // Moving backward
        }
    }
}

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
