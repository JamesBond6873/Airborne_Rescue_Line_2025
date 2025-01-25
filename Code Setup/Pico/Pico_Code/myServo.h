#ifndef Servo_h
#define Servo_h

#include <Adafruit_PWMServoDriver.h>

class myServo {
public:
    myServo(int channel, Adafruit_PWMServoDriver& pwmDriver, bool camera, bool ballStorage);
    void setAngle(int angle);
    void setDefault(int defaultValue);
    void moveDefault();
    void lineFollowing();
    void EvacuationZone();
    void close();
    void dropAlive();
    void dropDead();
    int getAngle() const;
    int getChannel() const;

private:
    int _channel;
    int _angle;
    int _defaultAngle;
    bool _camera;
    bool _ballStorage;
    Adafruit_PWMServoDriver& _pwm;
    const int SERVOMIN = 150;
    const int SERVOMAX = 600;
};

#endif
