#ifndef IMU_h
#define IMU_h

#include "ICM_20948.h"
#include <Wire.h>

class IMU {
public:
    IMU();

    void begin(TwoWire &wire);   // Call in setup()
    void update10DOF();          // Fetch new sensor values

    String getAccelString();    // x, y, z
    String getGyroString();     // x, y, z
    String getMagString();      // x, y, z
    String getTempString();     // temp
    String getAllString();      // accx, accy, accz, gyrox, gyroy, gyroz, magx, magy, magz, temp
    String getAllGraphString(); // Ready for arduino ide graph

    float* getAccel();          // Returns pointer to [x, y, z]
    float* getGyro();           // Returns pointer to [x, y, z]
    float* getMag();            // Returns pointer to [x, y, z]
    float  getTemp();           
    float* getAll();            // Returns pointer to [Ax, Ay, Az, Gx, Gy, Gz, Mx, My, Mz, T]

private:
    TwoWire* _wire;
    ICM_20948_I2C _imu;

    float _acc[3];
    float _gyro[3];
    float _mag[3];
    float _temp;
    float _all[10]; // Optional: pre-filled array for getAll()
};

#endif