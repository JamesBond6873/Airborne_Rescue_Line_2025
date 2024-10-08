#include <Servo.h>

Servo myServo;  // Create a servo object

const int servoPin = 16;  // Define the pin the servo is attached to

void setup() {
  Serial.begin(9600);  // Start serial communication at 9600 baud
  myServo.attach(servoPin);  // Attach the servo to the defined pin
  Serial.println("Enter the angle (0-180) to move the servo:");
}

void loop() {
  if (Serial.available() > 0) {
    int angle = Serial.parseInt();  // Read the angle from the serial monitor

    // Check if the entered angle is within the valid range
    if (angle >= 0 && angle <= 180) {
      myServo.write(angle);  // Move the servo to the specified angle
      Serial.print("Servo moved to ");
      Serial.print(angle);
      Serial.println(" degrees.");
    } else {
      Serial.println("Please enter a valid angle between 0 and 180.");
    }

    // Clear the serial buffer
    while (Serial.available() > 0) {
      Serial.read();
    }
  }
}
