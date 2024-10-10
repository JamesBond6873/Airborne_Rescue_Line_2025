#include <Servo.h>
#include "Motor.h"

const int enc1A = 9;
const int enc1B = 8;
const int enc2A = 7;
const int enc2B = 6;
const int enc3A = 2;
const int enc3B = 3;
const int enc4A = 5;
const int enc4B = 4;

int value;
unsigned long t0;  // control sampling rate (period ini)
unsigned long t1;  // control sampling rate (period end)
long timeInterval = 10;  // 10ms per loop = 100Hz

Motor Motor1(18, enc1A, enc1B);
Motor Motor2(21, enc2A, enc2B);
Motor Motor3(20, enc3A, enc3B);
Motor Motor4(16, enc4A, enc4B);

void setup() {
  Serial.begin(115200);

  Motor1.getReady();
  Motor2.getReady();
  Motor3.getReady();
  Motor4.getReady();

  t0 = millis();
}

void loop() {
  t1 = t0 + timeInterval;

  // Read value from Serial input (simulating the RPi input)
  value = mySerialReadString().toInt();

  // Send continuous control signals to Motor1 based on input value
  if (value != 0) {
    Motor1.controlMotor(value);  // Example control on Motor1, you can extend to others
  }

  // Print encoder count for each motor
  Serial.print("Motor1 Encoder: ");
  Serial.println(Motor1.getEncoderCount());

  /*Serial.print("Motor2 Encoder: ");
  Serial.println(Motor2.getEncoderCount());

  Serial.print("Motor3 Encoder: ");
  Serial.println(Motor3.getEncoderCount());

  Serial.print("Motor4 Encoder: ");
  Serial.println(Motor4.getEncoderCount());*/

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
