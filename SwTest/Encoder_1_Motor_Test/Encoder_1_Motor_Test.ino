#include <Servo.h>
#include "Motor.h"

//Servo ESC1;
//Servo ESC2;
//Servo ESC3;
//Servo ESC4;

const int enc1A = 9;
const int enc1B = 8;
const int enc2A = 7;
const int enc2B = 6;
const int enc3A = 2;
const int enc3B = 3;
const int enc4A = 5;
const int enc4B = 4;

int value;

unsigned long t0; // control sampling rate (period ini)
unsigned long t1; // control sampling rate (period end)
long timeInterval = 500; // 10ms per loop = 100Hz

Motor Motor1(18, enc1A, enc1B);

void setup() {
  // put your setup code here, to run once:

  Serial.begin(115200);

  Motor1.getReady();

  t0 = millis();
}

void loop() {
    t1 = t0 + timeInterval;

    // Read value from Serial input (simulating the RPi input)
    value = mySerialReadString().toInt();

    // Send continuous control signals to Motor2
    if (value != 0) {
      kickESC2(value);  // Keep sending the control pulse
    }

    Motor1.updateCounter();

    Serial.print("1: ");
    Serial.print(millis());
    Serial.print("\t2: ");
    Serial.print(Motor1.encoderStateA());
    Serial.print("\t1: ");
    Serial.println(Motor1.getEncoderCount());

    // Wait for the next cycle
    while (millis() <= t1) {
        delay(0.1);
    }

    t0 = t1;
}



String mySerialReadString() {
  // read till the end of the buffer or a terminating chr
  int c;
  String str= "";

  if (Serial.available() <= 0) {
    return str;
  }

  while (1) {
    c= Serial.read();
    if (c==0 || c==0x0A || c==0x0D) break;
    //if (c==0) break;
    str= str + String(char(c));
    if (Serial.available() <= 0) {
      // delay(10); // 10milliseconds = 96bits / 9600bits/sec
      // delay(10); // 10 millisec * 115200 bits/sec = 1152 bits
      delay(1); // 1 millisec * 115200 bits/sec = 115.2 bits (14.4 characters)
      if (Serial.available() <= 0) break;
    }
  }

  //Serial.print("Str: ");
  //Serial.println(str);
  return str;
}


void kickESC2(int val) {
  //Serial.println(val);

  //ESC1.writeMicroseconds(val);
  //ESC2.writeMicroseconds(val);
  //ESC3.writeMicroseconds(val);
  //ESC4.writeMicroseconds(val);

  Motor1.controlMotor(val);
  /*Motor2.controlMotor(val);
  Motor3.controlMotor(val);
  Motor4.controlMotor(val);*/
}
