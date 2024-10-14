#include <Servo.h>
#include "Motor.h"

// Define motor pins individually (no list usage)
const int enc1A = 9, enc1B = 8, pwm1 = 18;
const int enc2A = 7, enc2B = 6, pwm2 = 21;
const int enc3A = 2, enc3B = 3, pwm3 = 20;
const int enc4A = 5, enc4B = 4, pwm4 = 16;

int value;
unsigned long t0;
unsigned long t1;
long timeInterval = 10;  // 10ms per loop = 100Hz

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

  // Read value from Serial input (simulating the RPi input)
  value = mySerialReadString().toInt();

  // Control Motor1 (extend to other motors as needed)
  if (value != 0) {
    motors[0].controlMotor(value);
  }

  // Print encoder count and speed (RPM and RPS) for each motor
  for (int i = 0; i < 4; i++) {
    Serial.print("Motor ");
    Serial.print(i + 1);
    Serial.print(" Encoder: ");
    Serial.println(motors[i].getEncoderCount());
    
    Serial.print(" Motor ");
    Serial.print(i + 1);
    Serial.print(" Speed (RPM): ");
    Serial.println(motors[i].getRPM());

    Serial.print(" Motor ");
    Serial.print(i + 1);
    Serial.print(" Speed (RPS): ");
    Serial.println(motors[i].getRPS());
  }

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
