#include "ToF.h"

#define TCAADDR 0x70  // Default I2C address for TCA9548A

// Static function to select a channel on the multiplexer
void tcaSelect(uint8_t channel, TwoWire* wire) {
  wire->beginTransmission(TCAADDR);
  wire->write(1 << channel);
  wire->endTransmission();
  delay(5);  // Allow signal to settle
}

// Constructor
ToF::ToF(int backRightChan, int frontRightChan, int frontCenterChan, int frontLeftChan, int backLeftChan) {
  _channels[0] = backRightChan;
  _channels[1] = frontRightChan;
  _channels[2] = frontCenterChan;
  _channels[3] = frontLeftChan;
  _channels[4] = backLeftChan;
}

// Initialization
void ToF::begin(TwoWire &wire) {
  _wire = &wire;

  for (int i = 0; i < 5; i++) {
    tcaSelect(_channels[i], _wire);
    VL53L0X sensor;
    sensor.setBus(_wire);

    if (!sensor.init()) {
      Serial.print("Failed to init ToF sensor on channel ");
      Serial.println(_channels[i]);
    } else {
      sensor.setTimeout(500);
      sensor.setMeasurementTimingBudget(20000);  // Fast mode
      sensor.startContinuous();
      Serial.print("ToF sensor on channel ");
      Serial.print(_channels[i]);
      Serial.println(" started.");
    }
  }
}

// Update distances from all sensors
void ToF::updateToF5() {
  for (int i = 0; i < 5; i++) {
    tcaSelect(_channels[i], _wire);

    VL53L0X sensor;
    sensor.setBus(_wire);
    uint16_t dist = sensor.readRangeContinuousMillimeters();

    if (sensor.timeoutOccurred()) {
      _distances[i] = -1;  // Error case
    } else {
      _distances[i] = dist;
    }
  }
}

// Getters for float
float ToF::getBackRight()    { updateToF5(); return _distances[0]; }
float ToF::getFrontRight()   { updateToF5(); return _distances[1]; }
float ToF::getFrontCenter()  { updateToF5(); return _distances[2]; }
float ToF::getFrontLeft()    { updateToF5(); return _distances[3]; }
float ToF::getBackLeft()     { updateToF5(); return _distances[4]; }
float* ToF::getAll()         { updateToF5(); return _distances; }

// Getters for string
String ToF::getBackRightString()   { updateToF5(); return String(_distances[0]); }
String ToF::getFrontRightString()  { updateToF5(); return String(_distances[1]); }
String ToF::getFrontCenterString() { updateToF5(); return String(_distances[2]); }
String ToF::getFrontLeftString()   { updateToF5(); return String(_distances[3]); }
String ToF::getBackLeftString()    { updateToF5(); return String(_distances[4]); }

String ToF::getAllString() {
  updateToF5();
  return String(_distances[0]) + ", " + 
         String(_distances[1]) + ", " + 
         String(_distances[2]) + ", " + 
         String(_distances[3]) + ", " + 
         String(_distances[4]);
}
