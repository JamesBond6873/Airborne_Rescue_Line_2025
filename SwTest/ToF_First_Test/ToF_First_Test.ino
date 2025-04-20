#include <Wire.h>
#include <Adafruit_VL53L0X.h>

#define TCAADDR 0x70  // Default I2C address for TCA9548A

Adafruit_VL53L0X sensor;

// Function to select a channel on the TCA9548A
void tcaSelect(uint8_t channel) {
  if (channel > 7) return;
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << channel);  // Enable only one channel at a time
  Wire.endTransmission();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  for (int i = 0; i < 2; i++) {
    tcaSelect(i);
    if (!sensor.begin()) {
      Serial.print("Failed to start VL53L0X on channel ");
      Serial.println(i);
    } else {
      Serial.print("Sensor on channel ");
      Serial.print(i);
      Serial.println(" initialized.");
    }
  }
}

void loop() {
  for (int i = 0; i < 2; i++) {
    tcaSelect(i);
    VL53L0X_RangingMeasurementData_t measure;

    sensor.rangingTest(&measure, false);  // Pass in 'true' to get debug data printout

    Serial.print("Channel ");
    Serial.print(i);
    Serial.print(": ");

    if (measure.RangeStatus != 4) {  // 4 means "Out of range"
      Serial.print(measure.RangeMilliMeter);
      Serial.println(" mm");
    } else {
      Serial.println("Out of range");
    }
  }

  delay(1000);  // Wait 1s before next measurement
}
