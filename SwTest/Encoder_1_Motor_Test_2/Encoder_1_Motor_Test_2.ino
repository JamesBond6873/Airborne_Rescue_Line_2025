#include <Servo.h>
#include "Motor.h"

const int enc1A = 9, enc1B = 8, pwm1 = 18;
const int enc2A = 7, enc2B = 6, pwm2 = 21;
const int enc3A = 2, enc3B = 3, pwm3 = 20;
const int enc4A = 5, enc4B = 4, pwm4 = 16;

int value;
unsigned long t0;  
unsigned long t1;
long timeInterval = 10;  // Sampling rate: 100Hz

Motor motors[4] = {
  Motor(pwm1, enc1A, enc1B),
  Motor(pwm2, enc2A, enc2B),
  Motor(pwm3, enc3A, enc3B),
  Motor(pwm4, enc4A, enc4B)
};

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < 4; i++) {
    motors[i].getReady();
  }

  t0 = millis();
}

void loop() {
  t1 = t0 + timeInterval;

  // Read value from Serial input (simulating RPi input)
  value = mySerialReadString().toInt();

  // Control each motor with the same input value
  for (int i = 0; i < 4; i++) {
    if (value != 0) {
      motors[i].controlMotor(value);  // Apply control to all motors
    }
  }

  // Print encoder counts and RPM for all motors in one line with tabs
  Serial.print("Motor Encoders: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(motors[i].getEncoderCount());
    Serial.print("\t");
  }
  Serial.print("Motor RPM: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(motors[i].getRPM());
    Serial.print("\t");
  }
  Serial.println();

  // Wait for the next cycle
  while (millis() <= t1) {
    delay(1);
  }

  t0 = t1;
}

// Helper function to read serial input
String mySerialReadString() {
  int c;
  String str = "";

  if (Serial.available() <= 0) {
    return str;
  }

  while (1) {
    c = Serial.read();
    if (c == 0 || c == 0x0A || c == 0x0D) break;
    str = str + String(char(c));
    if (Serial.available() <= 0) {
      delay(1);
      if (Serial.available() <= 0) break;
    }
  }

  return str;
}
