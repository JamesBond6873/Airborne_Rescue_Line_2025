#include "Motor.h"

// Static array to hold pointers to motor instances for interrupt handling
Motor* Motor::motorInstances[Motor::MAX_MOTORS] = {nullptr};
int Motor::motorCount = 0;

Motor::Motor(int pwmPin, int encPinA, int encPinB)
    : _pwmPin(pwmPin), encPinA(encPinA), encPinB(encPinB), encoderCount(0),
      currentRPM(0), targetRPM(0), Kp(0.2), Ki(0.01), Kd(0.1),
      integral(0), previousError(0), lastUpdateTime(0) {
    if (motorCount < MAX_MOTORS) {
        motorInstances[motorCount++] = this; // Register this instance
    }
}

void Motor::initialize() {
    _ESC.attach(_pwmPin);

    pinMode(encPinA, INPUT);
    pinMode(encPinB, INPUT);

    // Attach the static interrupt handler, passing in the encoder pin as a parameter
    attachInterrupt(digitalPinToInterrupt(encPinA), Motor::encoderInterruptHandler, RISING);

    // Initial motor calibration to neutral position using analogWrite
    controlMotor(2000);
    delay(50);
    controlMotor(1500);
    delay(50);
    controlMotor(1520);
}

void Motor::controlMotor(int pulse) {
    if (pulse >= 1000 && pulse <= 2000) {
        //_ESC.writeMicroseconds(pulse);
    } else {
        Serial.println("Invalid pulse value");
    }
}

// Static interrupt handler function
void Motor::encoderInterruptHandler() {
    // Loop through motor instances to find which motor's encoder was triggered
    for (int i = 0; i < motorCount; ++i) {
        if (motorInstances[i] != nullptr) {
            motorInstances[i]->handleEncoderInterrupt(); // Call the instance-specific handler
        }
    }
}

void Motor::handleEncoderInterrupt() {
    encoderCount++;
}

void Motor::calculateRPM() {
    unsigned long currentTime = millis();
    unsigned long elapsedTime = currentTime - lastUpdateTime;
    int COUNTS_PER_REVOLUTION = 11;
    if (elapsedTime > 0) {
        currentRPM = (encoderCount / (float)elapsedTime) * 60000 / COUNTS_PER_REVOLUTION;
        encoderCount = 0; // Reset the count after RPM calculation
        lastUpdateTime = currentTime;
    }
}

void Motor::updateSpeed() {
    calculateRPM();

    float error = targetRPM - currentRPM;
    integral += error * (millis() - lastUpdateTime);
    float derivative = (error - previousError) / (millis() - lastUpdateTime);
    float output = Kp * error + Ki * integral + Kd * derivative;

    output = constrain(output, 1500, 2000); // Ensure PWM value is within range
    Serial.print("Output: ");
    Serial.println(output);
    //analogWrite(pwmPin, output);

    controlMotor(output);

    previousError = error;
}

long Motor::getEncoderCount() {
    return encoderCount;
}

float Motor::getRPM() {
    return currentRPM;
}

void Motor::setTargetRPM(float rpm) {
    targetRPM = rpm;
}
