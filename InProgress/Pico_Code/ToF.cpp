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

void ToF::begin(TwoWire &wire) {
  _wire = &wire;

  for (int i = 0; i < 5; i++) {
    tcaSelect(_channels[i], _wire);

    _sensors[i].setBus(_wire);
    if (!_sensors[i].init()) {
      Serial.print("Failed to init ToF sensor on channel ");
      Serial.println(_channels[i]);
    } else {
      _sensors[i].setTimeout(5);
      _sensors[i].setMeasurementTimingBudget(20000); // Minimum is 20000...
      _sensors[i].startContinuous();
      Serial.print("ToF sensor on channel ");
      Serial.print(_channels[i]);
      Serial.println(" started.");
    }
  }
}


void ToF::updateToF5() {
  for (int i = 0; i < 5; i++) {
    tcaSelect(_channels[i], _wire);  // switch to the correct channel

    uint16_t dist = _sensors[i].readRangeContinuousMillimeters();
    if (_sensors[i].timeoutOccurred()) {
      _distances[i] = -1;
    } else {
      _distances[i] = dist;
    }
  }
}

void ToF::updateSingleToF(int idx) {
    if (idx < 0 || idx >= 5) return;

    tcaSelect(_channels[idx], _wire);

    uint16_t dist = _sensors[idx].readRangeContinuousMillimeters();
    if (_sensors[idx].timeoutOccurred()) {
        _distances[idx] = -1;
    } else {
        _distances[idx] = dist;
    }
}

// Getters for float
float ToF::getBackRight()    { return _distances[0]; }
float ToF::getFrontRight()   { return _distances[1]; }
float ToF::getFrontCenter()  { return _distances[2]; }
float ToF::getFrontLeft()    { return _distances[3]; }
float ToF::getBackLeft()     { return _distances[4]; }
float* ToF::getAll()         { return _distances; }

// Getters for string
String ToF::getBackRightString()   { return String(_distances[0]); }
String ToF::getFrontRightString()  { return String(_distances[1]); }
String ToF::getFrontCenterString() { return String(_distances[2]); }
String ToF::getFrontLeftString()   { return String(_distances[3]); }
String ToF::getBackLeftString()    { return String(_distances[4]); }

String ToF::getAllString() {
  return String(_distances[0]) + ", " + 
         String(_distances[1]) + ", " + 
         String(_distances[2]) + ", " + 
         String(_distances[3]) + ", " + 
         String(_distances[4]);
}
