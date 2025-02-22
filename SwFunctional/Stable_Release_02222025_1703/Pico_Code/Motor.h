#ifndef Motor_h
#define Motor_h

#include <Servo.h>
#include <Arduino.h>

class Motor {
public:
    Motor(int pwmPin, int encoderPinA, int encoderPinB);
    void getReady();
    void controlMotor(int pulse);
    int getEncoderCount() const;

    void encoderISR();  // Non-static, handles interrupts for this motor
    float getRPS();     // Return revolutions per second
    float getRPM();     // Return revolutions per minute

private:
    Servo _ESC;
    int _pwmPin;
    int _encoderPinA;
    int _encoderPinB;
    volatile int _encoderCount;
    unsigned long _lastUpdate;  // Track the last time the encoder was updated
    float _timeElapsed;         // Time between encoder changes
    bool _motorReady = false;

    static const int pulsesPerRevolution = 360;  // Change this according to your encoder
    static Motor* instances[4];  // Optional for global ISR management
    static int instanceIndex;
};

#endif
