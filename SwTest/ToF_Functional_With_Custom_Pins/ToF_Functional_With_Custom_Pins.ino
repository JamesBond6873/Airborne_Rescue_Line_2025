#include <Wire.h>
#include <Adafruit_VL53L0X.h>

#define TCAADDR 0x70  // Default I2C address for TCA9548A

Adafruit_VL53L0X sensor;

int ToFData[2] = {-1, -1};

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

      //sensor.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_DEFAULT);       // Balanced (default) — ~33ms timing budget
      //sensor.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_LONG_RANGE);    // Long range — less accuracy, more range
      sensor.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_HIGH_SPEED);    // Fast mode — ~20ms timing, less accuracy
      //sensor.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_HIGH_ACCURACY); // Slow, most precise — ~200ms timing

    }
  }
}

void loop() {
  for (int i = 0; i < 2; i++) {
    tcaSelect(i);
    VL53L0X_RangingMeasurementData_t measure;

    sensor.rangingTest(&measure, false);  // Pass in 'true' to get debug data printout
  
    if (measure.RangeStatus != 4) {
      ToFData[i] = measure.RangeMilliMeter;
    }
    else {
      ToFData[i] = 2345; // Default number for out of range from now on
    }
  }

  Serial.println();
  Serial.print("Channel 0: ");
  Serial.print(ToFData[0]);
  Serial.print("\t Channel 1: ");
  Serial.println(ToFData[1]);
  Serial.println();

  delay(1000);  // Wait 1s before next measurement
}


/* Range Status Meaning:
0	✅ Valid measurement
1	Sigma fail (too much noise)
2	Signal fail (weak return signal)
3	Min range clipped
4	❌ Out of range
5+	Hardware/processing errors
*/