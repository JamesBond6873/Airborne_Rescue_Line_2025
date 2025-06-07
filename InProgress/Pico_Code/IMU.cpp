#include "IMU.h"
#include <Wire.h>

// Constructor
IMU::IMU() {}

void IMU::begin(TwoWire &wire) {
    _wire = &wire;
    if (_imu.begin(*_wire, 1) != ICM_20948_Stat_Ok) {
        Serial.println("IMU initialization failed. Check connections.");
        while (1) { Serial.println("IMU initialization failed. Check connections."); }
    } else {
        Serial.println("IMU initialized successfully.");
    }
}

// Update 10DOF values
void IMU::update10DOF() {
    if (_imu.dataReady()) {
        _imu.getAGMT();
        // Accel
        _acc[0] = _imu.accX();
        _acc[1] = _imu.accY();
        _acc[2] = _imu.accZ();

        // Gyro
        _gyro[0] = _imu.gyrX();
        _gyro[1] = _imu.gyrY();
        _gyro[2] = _imu.gyrZ();

        // Mag
        _mag[0] = _imu.magX();
        _mag[1] = _imu.magY();
        _mag[2] = _imu.magZ();

        // Temp
        _temp = _imu.temp();

        // Fill _all
        for (int i = 0; i < 3; i++) {
            _all[i]     = _acc[i];
            _all[i+3]   = _gyro[i];
            _all[i+6]   = _mag[i];
        }
        _all[9] = _temp;
    }
    else {
        Serial.print("Data ready? ");
        Serial.println(_imu.dataReady());
    }
}

// Returning
float* IMU::getAccel() { 
  return _acc; 
}

float* IMU::getGyro()  {
  return _gyro;
}

float* IMU::getMag()   {
  return _mag;
}

float  IMU::getTemp()  {
  return _temp;
}

float* IMU::getAll()   {
  return _all;
}

String IMU::getAccelString() {
    return String(_acc[0], 3) + ", " + String(_acc[1], 3) + ", " + String(_acc[2], 3);
}

String IMU::getGyroString() {
    return String(_gyro[0], 3) + ", " + String(_gyro[1], 3) + ", " + String(_gyro[2], 3);
}

String IMU::getMagString() {
    return String(_mag[0], 3) + ", " + String(_mag[1], 3) + ", " + String(_mag[2], 3);
}

String IMU::getTempString() {
    return String(_temp, 3);
}

String IMU::getAllString() {
    String out = "";
    for (int i = 0; i < 9; i++) {
        out += String(_all[i], 3) + ", ";
    }
    out += String(_all[9], 3); // temp without trailing comma
    return out;
}

String IMU::getAllGraphString() {
    String output = "";

    // Use 2 decimal places and fixed spacing for easy parsing in Arduino Serial Plotter
    for (int i = 0; i < 9; i++) {
        output += String(_all[i], 2);
        output += ", ";
    }
    output += String(_all[9], 2);  // Temperature, no trailing comma

    return output;
}
