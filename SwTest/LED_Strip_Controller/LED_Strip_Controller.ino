#include <FastLED.h>

#define LED_PIN     1
#define NUM_LEDS    8

CRGB leds[NUM_LEDS];

void setup() {

  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  pinMode(LED_BUILTIN, OUTPUT);
  
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
  leds[0] = CRGB(255, 0, 0);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);  
  leds[1] = CRGB(0, 255, 0);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, HIGH);
  leds[2] = CRGB(0, 0, 255);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  leds[3] = CRGB(255, 0, 0);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, HIGH);
  leds[4] = CRGB(255, 0, 0);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  leds[5] = CRGB(255, 0, 0);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, HIGH);
  leds[6] = CRGB(255, 0, 0);
  FastLED.show();
  delay(500);
}