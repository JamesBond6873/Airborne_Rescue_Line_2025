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


// String mySerialReadString() { return Serial.readString(); }

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


// the real code to study
void loop() {

  if (Serial.available() > 0) {
    ss.eventStore(0);

    digitalWrite(ledPin, HIGH);
    String incomingString = mySerialReadString();
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