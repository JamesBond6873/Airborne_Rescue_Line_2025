#ifndef Motor_h
#define Motor_h

#include <Servo.h>

class Motor {
public:
    Motor(int pwmPin, int encoderPinA, int encoderPinB);
    void getReady();
    void setSpeed(int Speed);
    void updateCounter();
    void controlMotor(int pulse);
    int encoderStateA();
    int encoderStateB();
    int getEncoderPinA() const;
    int getEncoderPinB() const;
    int getEncoderCount() const;

private:
    Servo _ESC;
    int _Speed;
    int _currentSpeed;
    int _pwmPin;
    int _encoderPinA;
    int _encoderPinB;
    int _lastEncoderStateA;
    int _lastEncoderStateB;
    int _encoderCount;
};

#endif