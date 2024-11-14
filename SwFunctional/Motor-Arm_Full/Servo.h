#ifndef Servo_h
#define Servo_h

#include <Adafruit_PWMServoDriver.h>

class Servo {
public:
    Servo(int channel, Adafruit_PWMServoDriver& pwmDriver);
    void setAngle(int angle);
    void setDefault(int defaultValue);
    void moveDefault();
    int getAngle() const;
    int getChannel() const;

private:
    int _channel;
    int _angle;
    int _defaultAngle;
    Adafruit_PWMServoDriver& _pwm;
    const int SERVOMIN = 150;
    const int SERVOMAX = 600;
};

#endif
