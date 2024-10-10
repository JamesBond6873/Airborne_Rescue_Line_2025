#ifndef Motor_h
#define Motor_h

#include <Servo.h>

class Motor {
public:
    Motor(int pwmPin, int encoderPinA, int encoderPinB);
    void getReady();
    void controlMotor(int pulse);
    int getEncoderCount() const;

    static void encoderA_ISR();
    static void encoderB_ISR();

private:
    Servo _ESC;
    int _pwmPin;
    int _encoderPinA;
    int _encoderPinB;
    volatile int _encoderCount;
    int _lastEncoderStateA;
    int _lastEncoderStateB;

    static Motor* instances[4];  // Static array to hold motor instances
    static int instanceIndex;    // Index for tracking motors
};

#endif
