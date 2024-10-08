#include "my_sys_state.h"
const int ledPin = LED_BUILTIN;

// RGB Led
#if 1
// RPi-Pico pins
const int RLed = 16;
const int GLed = 17;  
const int BLed = 18;  
#else
// WeMos D1 R1 pins
const int RLed = D3;  
const int GLed = D4;  
const int BLed = D5;  
#endif


// ----------- FUNCTIONS ----------------------


void setColor(int redValue, int greenValue, int blueValue) {
  analogWrite(RLed, 255 - redValue);
  analogWrite(GLed, 255 - greenValue);
  analogWrite(BLed, 255 - blueValue);
}


// ----------- MAIN CODE ----------------------


void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(RLed, OUTPUT);
  pinMode(GLed, OUTPUT);
  pinMode(BLed, OUTPUT);

  setColor(255, 0, 0);
  delay(1000);
  setColor(0, 0, 0);

  Serial.begin(115200);
}


// the SysState "ss" object is declared here:
MySysState ss;

#if 0
// debug of data logging

void loop() {
  // do just ONCE the exp, and do it after 5sec of reboot
  static int loopMode = 1;
  if (!loopMode || millis() < 5000) { return; }

  // this runs after 5sec:
  Serial.println("start exp");
  loopMode = 0;  // disable more runs
  for (int i = 0; i < 10; i++) {
    Serial.println("--- i=" + String(i));
    ss.showAllEvents();
    ss.eventStore(i);
  }
  Serial.println("\nend exp");

}

#else
// the real code to study
void loop() {

  if (Serial.available() > 0) {
    ss.eventStore(0);

    digitalWrite(ledPin, HIGH);
    String incomingString = Serial.readString();
    ss.eventStore(1);
    incomingString.trim();
    ss.eventStore(2);

    if (incomingString == "<") {
      ss.showAllEvents();
      ss.eventStore(101);
    }
    else if (incomingString == "L1") {
      Serial.println("Ok. L1");
      ss.eventStore(11);
      setColor(255, 0, 0);
      ss.eventStore(12);
      digitalWrite(ledPin, LOW);
      ss.eventStore(13);
    }
    else if (incomingString == "L2") {
      Serial.println("Ok. L2");
      ss.eventStore(21);
      setColor(0, 0, 255);
      ss.eventStore(22);
      digitalWrite(ledPin, LOW);
      ss.eventStore(23);
    }
    else {
      setColor(0, 255, 0);
      ss.eventStore(31);
      digitalWrite(ledPin, LOW);
      ss.eventStore(32);
      Serial.println("u there?");
      ss.eventStore(33);
    }
  }
}
#endif
