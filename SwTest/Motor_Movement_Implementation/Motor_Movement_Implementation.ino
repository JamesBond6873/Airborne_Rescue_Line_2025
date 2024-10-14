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

Motor motors[4] = {
    Motor(18, enc1A, enc1B),
    Motor(21, enc2A, enc2B),
    Motor(20, enc3A, enc3B),
    Motor(16, enc4A, enc4B)
};

int value;
int values[4];
unsigned long t0;  // control sampling rate (period ini)
unsigned long t1;  // control sampling rate (period end)
long timeInterval = 10;  // 10ms per loop = 100Hz

void setup() {
  // put your setup code here, to run once:
  for (int i = 0; i < 4; i++) {
    motors[i].getReady();
  }

  Serial.begin(115200);

  t0 = millis();
}

void loop() {
  t1 = t0 + timeInterval;

  updateValuesFromSerial();

  Serial.print("Motors Values: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(values[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();

  for (int i = 0; i < 4; i++) {
    motors[i].controlMotor(values[i]);
  }

  while (millis() <= t1) {
    delay(1);
  }


  t0 = t1;
}


// Function to read serial input and update the list
void updateValuesFromSerial() {
  String input = readSerial();

  if (input.startsWith("M(") && input.endsWith(")")) {
    input = input.substring(2, input.length() - 1);

    int commaIndex = input.indexOf(',');
    if (commaIndex != -1) {

      // Get values a and b from the string
      int a = input.substring(0, commaIndex).toInt();
      int b = input.substring(commaIndex + 1).toInt();

      // Update the list with [a, a, b, b]
      values[0] = a;
      values[1] = a;
      values[2] = b;
      values[3] = b;
    } 
  }
}


String readSerial() {
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