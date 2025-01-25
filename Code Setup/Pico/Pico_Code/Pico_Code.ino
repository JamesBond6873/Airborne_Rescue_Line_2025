#include <Servo.h>
#include "myServo.h"
#include "Motor.h"
#include <Adafruit_PWMServoDriver.h>
#include "ArmGrip.h"

// --------------------------- Motor Vars ---------------------------

const int enc1A = 2;
const int enc1B = 3;
const int enc2A = 12;
const int enc2B = 13;
const int enc3A = 21;
const int enc3B = 22;
const int enc4A = 14;
const int enc4B = 15;

Motor motors[4] = {
    Motor(10, enc1A, enc1B),
    Motor(11, enc2A, enc2B),
    Motor(20, enc3A, enc3B),
    Motor(19, enc4A, enc4B)
};

int value;
int startMotorSpeed = 1520; // Default speed for just launched code
int values[4] = {startMotorSpeed,startMotorSpeed,startMotorSpeed,startMotorSpeed};


// --------------------------- Arm Vars ---------------------------

const int leftHandServo = 0; // Channel 0 for the left hand servo
const int rightHandServo = 1; // Channel 1 for the right hand servo
const int leftArmServo = 2; // Channel 2 for the left arm servo
const int rightArmServo = 3; // Channel 3 for the right arm servo

// Create the PCA9685 object
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Create the ArmGrip object with specified channels for servos
ArmGrip Grip(pwm, rightHandServo, leftHandServo, rightArmServo, leftArmServo);


// --------------------------- Time Vars ---------------------------

unsigned long t0;  // control sampling rate (period ini)
unsigned long t1;  // control sampling rate (period end)
long timeInterval = 10;  // 10ms per loop = 100Hz



// ----------------------------------------------------------------
// -----------------  <<<<<<<<  Setup  >>>>>>>>  ------------------
// --------------------------- ----- ------------------------------

void setup() {
  // put your setup code here, to run once:
  for (int i = 0; i < 4; i++) {
    motors[i].getReady();
  }

  Serial.begin(115200);

  t0 = millis();
}



// ---------------------------------------------------------------
// -----------------  <<<<<<<<  Loop  >>>>>>>>  ------------------
// --------------------------- ----- -----------------------------

String message = "";
void loop() {
  t1 = t0 + timeInterval;


  // Read Serial Port
  message = readSerial(); 

  // Act According Message:
  if (message.startsWith("M(") && message.endsWith(")")) { ControlMotor(message); }  // Motor Command | M(x,x)

  else if (message == "PA") { Grip.pickAlive(); }  // Pick Alive Victim Sequence Command | Pick Alive
  else if (message == "PD") { Grip.pickDead(); }  // Pick Dead Victim Sequence Command | Pick Dead

  else if (message == "CL") { cameraLine(); }  // Point Camera Down for Line Following Command | Camera Line
  else if (message == "CE") { cameraDead(); }  // Point Camera Forward for Evactuation Zone Victim Rescue Command | Camera Evacuation

  else if (message == "DA") { dropAlive(); }  // Drop Alive Victims Command | Drop Alive
  else if (message == "DD") { dropAlive(); }  // Drop Dead Victims Command | Drop Dead

  else if (message == "LD") { collectToFData(); }  // Collect ToF Data from All Sensors | Laser Data
  else if (message == "LX") { collectToFDataX(); }  // Collect ToF Data from X Sensor | Laser X - LX,X

  else if (message == "HO") { Grip.openHand(); }  // Open Hand Command | Hand Open
  else if (message == "HC") { Grip.closeHand(); }  // Close Hand Command | Hand Close
  else if (message == "HA") { Grip.moveAlive(); }  // Move Hand to Alive Position Command | Hand Alive
  else if (message == "HD") { Grip.moveDead(); }  // Move Hand to Dead Position Command | Hand Dead

  else if (message == "AD") { Grip.moveDown(); }  // Move Arm Down Command (Catch Position) | Arm Down
  else if (message == "AU") { Grip.moveUp(); }  // Move Arm Up Command (Storage Position) | Arm Up

  else if (message.startsWith("SC,")) { servoControlMessage(message); } // Control Single Servo Command | servoControl
  

  while (millis() <= t1) {
    delay(1);
  }
  t0 = t1;
}



// --------------------------------------------------------------
// --------------  <<<<<<<<  Functions  >>>>>>>>  ---------------
// --------------------------- ----- ----------------------------


// --------------------------------------------------------------
// Function to read the serial port
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


// --------------------------------------------------------------
// Function to control Motors | Command: ControlMotor | M(X,X)
void ControlMotor(String input) {
  // Interpret Motor Controls | Update values list with motor speeds

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

  // Send Motor Control
  /*Serial.print("Motors Values: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(values[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();*/

  for (int i = 0; i < 4; i++) {
    motors[i].controlMotor(values[i]);
  }

}


// --------------------------------------------------------------
// Function to Control Servo to Point Camera Down for Line Following | Command: cameraLine
void cameraLine() {
  // Sill Empty
  // Pass
}


// --------------------------------------------------------------
// Function to Control Servo to Camera Forward for Evactuation Zone Victim Rescue Command | Command: cameraEvactuation
void cameraEvacuation() {
  // Sill Empty
  // Pass
}


// --------------------------------------------------------------
// Function to Control Ball Storage Servo and Drop Alive Victims | Command: dropAlive
void dropAlive() {
  // Sill Empty
  // Pass
}


// --------------------------------------------------------------
// Function to Control Ball Storage Servo and Drop Dead Victims | Command: dropDead
void dropDead() {
  // Sill Empty
  // Pass
}


// --------------------------------------------------------------
// Function to Collect Distance Measurements from ALL Time of Flights | Command: collectToFData
void collectToFData() {
  // Sill Empty
  // Pass
}


// --------------------------------------------------------------
// Function to Collect Distance Measurements from One Specific Time of Flight | Command: collectToFDataX | LX,X
void collectToFDataX() {
  // Sill Empty
  // Pass
}


// --------------------------------------------------------------
// Function to Control Single Servo | Command: ServoControl | SC,X,Angle
void servoControlMessage(String Input) {
  // Parse the command for individual servo control
  int commaIndex1 = input.indexOf(',');
  int commaIndex2 = input.indexOf(',', commaIndex1 + 1);

  if (commaIndex1 != -1 && commaIndex2 != -1) {
    String servoIdStr = input.substring(commaIndex1 + 1, commaIndex2);
    String angleStr = input.substring(commaIndex2 + 1);
    int servoId = servoIdStr.toInt();
    int angle = angleStr.toInt();

    // Validate the servo angle
    if (angle >= 0 && angle <= 180) {
      Serial.print("Set servo ");
      Serial.print(servoId);
      Serial.print(" to ");
      Serial.print(angle);
      Serial.println(" degrees");
      Grip.customServoAngle(servoId, angle);
    } else {
      Serial.println("Invalid angle.");
    }
  } else {
    Serial.println("Invalid command format. Use S4,R,Angle");
  }
}

