#include <Wire.h>
#include <VL53L0X.h>

#define TCAADDR 0x70
#define NUM_SENSORS 5
const uint8_t channels[NUM_SENSORS] = {3, 4, 5, 6, 7};

VL53L0X sensors[NUM_SENSORS];

void tcaSelect(uint8_t channel) {
  Wire1.beginTransmission(TCAADDR);
  Wire1.write(1 << channel);
  Wire1.endTransmission();
  delay(5);  // Let it settle
}

void setup() {
  Serial.begin(115200);
  Wire1.setSDA(6);
  Wire1.setSCL(7);
  Wire1.begin();

  for (int i = 0; i < NUM_SENSORS; i++) {
    tcaSelect(channels[i]);
    sensors[i].setBus(&Wire1);   // ✔ Works in Pololu lib
    if (!sensors[i].init()) {
      Serial.print("Failed to init sensor on channel ");
      Serial.println(channels[i]);
    } else {
      sensors[i].setTimeout(500);
      sensors[i].setMeasurementTimingBudget(20000);  // ✅ Fast mode
      sensors[i].startContinuous();
      Serial.print("Sensor ");
      Serial.print(channels[i]);
      Serial.println(" started.");
    }
  }
}

void loop() {
  for (int i = 0; i < NUM_SENSORS; i++) {
    tcaSelect(channels[i]);
    uint16_t distance = sensors[i].readRangeContinuousMillimeters();
    Serial.print("Channel ");
    Serial.print(channels[i]);
    Serial.print(": ");
    Serial.print(distance);
    if (sensors[i].timeoutOccurred()) Serial.print(" TIMEOUT");
    Serial.print("\t");
  }
  Serial.println();
  delay(300);
}
