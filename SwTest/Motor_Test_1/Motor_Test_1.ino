#include <Servo.h>

Servo ESC1;
Servo ESC2;
Servo ESC3;
Servo ESC4;

int value;

void setup() {
  // put your setup code here, to run once:
  ESC1.attach(16);
  ESC2.attach(20);
  ESC3.attach(18);
  ESC4.attach(19);

  Serial.begin(9600);

  // Arm:
  kickESC2(2000, 100);
  delay(100);
  kickESC2(1500, 100);
  delay(100);
  //kickESC2(1000, 100);
  //delay(100);
  /*ESC.writeMicroseconds(2000); // Neutral
  delay(100);
  ESC.writeMicroseconds(2000); // Reverse/Brake
  delay(100);
  ESC.writeMicroseconds(1000); // Full Throttle
  delay(100);*/
}

void loop() {
  while (Serial.available() == 0) {
  }
  value = Serial.parseInt();
  if (value != 0) {
    Serial.println(value);
    
    kickESC2(value, 1000);
    //kickESC(value, 1000);
    delay(100);
  }
}

void kickESC2(int val, int duration) { //val is the value sent to the ESP
  unsigned long time = millis();// register the starting time of the one second timing.
  Serial.println(val);
  /*while( millis() < time + duration){
    ESC1.writeMicroseconds(val);
    ESC2.writeMicroseconds(val);
    ESC3.writeMicroseconds(val);
    ESC4.writeMicroseconds(val);

    delay(1);
  }*/
  ESC1.writeMicroseconds(val);
  ESC2.writeMicroseconds(val);
  ESC3.writeMicroseconds(val);
  ESC4.writeMicroseconds(val);
}