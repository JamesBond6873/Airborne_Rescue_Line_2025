#ifndef Motor_h
#define Motor_h

#include <Servo.h>

class Motor {
public:
    Motor(int pwmPin, int encoderPinA, int encoderPinB);
    void getReady();
    void controlMotor(int pulse);
    int getEncoderCount() const;
    float getRPS();   // Revolutions per second
    float getRPM();   // Revolutions per minute

    static void encoderA_ISR();
    static void encoderB_ISR();

private:
    Servo _ESC;
    int _pwmPin;
    int _encoderPinA;
    int _encoderPinB;
    volatile int _encoderCount;
    
    unsigned long _lastSpeedCalc;  // Last time speed was calculated
    unsigned long _lastUpdate;     // Last update for speed calculation
    float _currentRPM;
    const unsigned long speedSampleInterval = 100;  // Time interval (ms) for calculating speed
    const int pulsesPerRevolution = 20;  // Number of pulses per motor revolution

    static Motor* instances[4];  // Static array to hold motor instances
    static int instanceIndex;    // Index for tracking motors
};

#endif
