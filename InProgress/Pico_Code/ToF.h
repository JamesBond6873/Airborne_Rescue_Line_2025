#ifndef TOF_h
#define TOF_h

#include <Wire.h>
#include <VL53L0X.h>

class ToF {
public:
  ToF(int backRightChan, int frontRightChan, int frontCenterChan, int frontLeftChan, int backLeftChan);

  void begin(TwoWire &wire);       // Initialize sensors (through mux)
  void updateToF5();                   // Update all distance values

  float getBackRight();
  float getFrontRight();
  float getFrontCenter();
  float getFrontLeft();
  float getBackLeft();
  float* getAll();  // Returns pointer to _distances[5]

  String getBackRightString();     
  String getFrontRightString();
  String getFrontCenterString();
  String getFrontLeftString();
  String getBackLeftString();
  String getAllString();     // "123.4,120.1,110.0,119.2,125.6"

private:
  TwoWire* _wire;
  int _channels[5];          // [BR, FR, FC, FL, BL]
  float _distances[5];       // Raw distance values in mm or cm

};

#endif
