#ifndef MOTOR_H
#define MOTOR_H

#include <Arduino.h>
#include <Servo.h>

class Motor {
public:
    Motor(int pwmPin, int encPinA, int encPinB);
    void initialize();
    void controlMotor(int pulse);
    void updateSpeed();
    void setTargetRPM(float rpm);
    float getRPM();
    long getEncoderCount();

private:
    Servo _ESC;

    static const int MAX_MOTORS = 4;               // Maximum number of motor instances
    static Motor* motorInstances[MAX_MOTORS];      // Array to hold motor instances
    static int motorCount;                       // Counter for registered motors

    int _pwmPin;
    int encPinA;
    int encPinB;
    volatile long encoderCount;
    float currentRPM;
    float targetRPM;
    float Kp, Ki, Kd; // PID constants
    float integral, previousError;
    unsigned long lastUpdateTime;

    static void encoderInterruptHandler();         // Static interrupt handler
    void handleEncoderInterrupt();                 // Instance-specific interrupt handler
    void calculateRPM();
};

#endif
