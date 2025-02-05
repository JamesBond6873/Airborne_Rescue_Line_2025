#include "Motor.h"
#include <Arduino.h>

Motor* Motor::instances[4] = {nullptr, nullptr, nullptr, nullptr};
int Motor::instanceIndex = 0;

// Constructor
Motor::Motor(int pwmPin, int encoderPinA, int encoderPinB) 
  : _pwmPin(pwmPin), _encoderPinA(encoderPinA), _encoderPinB(encoderPinB), _encoderCount(0), _lastUpdate(0) {
    instances[instanceIndex++] = this;
}

void Motor::getReady() {
    _ESC.attach(_pwmPin);

    //pinMode(_encoderPinA, INPUT);
    //pinMode(_encoderPinB, INPUT);

    //attachInterrupt(digitalPinToInterrupt(_encoderPinA), []() { Motor::instances[0]->encoderISR(); }, CHANGE);

    controlMotor(2000);
    delay(50);
    controlMotor(1500);
    delay(50);
    controlMotor(1520); 
}

void Motor::controlMotor(int pulse) {
    if (pulse >= 1000 && pulse <= 2000) {
        _ESC.writeMicroseconds(pulse);
    } else {
        Serial.println("Invalid pulse value");
    }
}

void Motor::encoderISR() {
    int stateA = digitalRead(_encoderPinA);
    int stateB = digitalRead(_encoderPinB);

    if (stateA == stateB) {
        _encoderCount++;
    } else {
        _encoderCount--;
    }

    // Calculate speed (based on time intervals)
    unsigned long currentTime = millis();
    if (_lastUpdate > 0) {
        _timeElapsed = (currentTime - _lastUpdate) / 1000.0;  // Convert ms to seconds
    }
    _lastUpdate = currentTime;
}

int Motor::getEncoderCount() const {
    return _encoderCount;
}

float Motor::getRPS() {
    // Return revolutions per second
    return (_encoderCount / float(pulsesPerRevolution)) / _timeElapsed;
}

float Motor::getRPM() {
    // Return revolutions per minute
    return getRPS() * 60;
}
