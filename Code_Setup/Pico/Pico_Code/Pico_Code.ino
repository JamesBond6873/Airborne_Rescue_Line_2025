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


// ----------------------- Other Servo Vars -----------------------
const int camServoChannel = 4; // Channel 4 for the Camera Tilt Servo
const int ballStorageServoChannel = 5; // Channel 5 for the Ball Storage Servo

myServo camServo(camServoChannel, pwm, true, false);
myServo ballStorageServo(ballStorageServoChannel, pwm, false, true);


// --------------------------- LED Vars ---------------------------
unsigned long ledT0;  // control sampling rate (period ini)
unsigned long ledT1;  // control sampling rate (period end)
long ledTimeInterval = 1000;  // 1s blinks

bool ledState = true;


// --------------------------- Time Vars ---------------------------
unsigned long t0;  // control sampling rate (period ini)
unsigned long t1;  // control sampling rate (period end)
long timeInterval = 10;  // 10ms per loop = 100Hz



// ----------------------------------------------------------------
// -----------------  <<<<<<<<  Setup  >>>>>>>>  ------------------
// --------------------------- ----- ------------------------------

void setup() {
  // put your setup code here, to run once:
  // Let Raspberry Pi Pico wake up
  delay(5000);

  // Get Motors Ready
  for (int i = 0; i < 4; i++) {
    motors[i].getReady();
  }

  // Get The Servos Ready - Correct Position
  Grip.begin();
  Grip.defaultPosition(); // Get the Grip to its default/storage Position
  camServo.lineFollowing(); // Get the Camera to point down for line following
  ballStorageServo.close(); // Close Ball Storage

  // Let the Servos Stay Free - Avoid Shaking
  delay(10);
  Grip.freeAllServos();
  camServo.freeServo();
  ballStorageServo.freeServo();

  // LED
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Serial Communication with RPi
  Serial.begin(115200);

  ledT0 = millis();
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

  else if (message == "PA") { Grip.pickAlive(); respondCommand("Ok");}  // Pick Alive Victim Sequence Command | Pick Alive
  else if (message == "PD") { Grip.pickDead(); respondCommand("Ok");}  // Pick Dead Victim Sequence Command | Pick Dead

  else if (message == "CL") { camServo.lineFollowing(); respondCommand("Ok");}  // Point Camera Down for Line Following Command | Camera Line
  else if (message == "CE") { camServo.EvacuationZone(); respondCommand("Ok");}  // Point Camera Forward for Evactuation Zone Victim Rescue Command | Camera Evacuation

  else if (message == "DA") { ballStorageServo.dropAlive(); respondCommand("Ok");}  // Drop Alive Victims Command | Drop Alive
  else if (message == "DD") { ballStorageServo.dropDead(); respondCommand("Ok");}  // Drop Dead Victims Command | Drop Dead
  else if (message == "BC") { ballStorageServo.close(); respondCommand("Ok");} // Close Ball Storage Command | Ball Close

  else if (message == "LD") { collectToFData(); respondCommand("Ok");}  // Collect ToF Data from All Sensors | Laser Data
  else if (message == "LX") { collectToFDataX(); respondCommand("Ok");}  // Collect ToF Data from X Sensor | Laser X - LX,X

  else if (message == "HO") { Grip.openHand(); respondCommand("Ok");}  // Open Hand Command | Hand Open
  else if (message == "HC") { Grip.closeHand(); respondCommand("Ok");}  // Close Hand Command | Hand Close
  else if (message == "HA") { Grip.moveAlive(); respondCommand("Ok");}  // Move Hand to Alive Position Command | Hand Alive
  else if (message == "HD") { Grip.moveDead(); respondCommand("Ok");}  // Move Hand to Dead Position Command | Hand Dead

  else if (message == "AD") { Grip.moveDown(); respondCommand("Ok");}  // Move Arm Down Command (Catch Position) | Arm Down
  else if (message == "AU") { Grip.moveUp(); respondCommand("Ok");}  // Move Arm Up Command (Storage Position) | Arm Up

  else if (message.startsWith("SC,")) { servoControlMessage(message); respondCommand("Ok");} // Control Single Servo Command | servoControl

  else if (message.startsWith("SF,")) { servoFreeControl(message); respondCommand("Ok");} //Free a servo | Servo Free
  
  else if (message == "Alive") { Serial.println("Yes Alive"); }  // Check if Pico is still alive  | Alive


  // LED Blink
  ledBlinkController(); //Blinks LED every Time Interval (ledTimeInterval = 1s)

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

void respondCommand(String response) {
  Serial.flush();
  Serial.println(response);
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
void servoControlMessage(String input) {
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
      if (servoId >= 0 && servoId <= 3) { Grip.customServoAngle(servoId, angle); } // Inside ArmGrip Class
      else if (servoId == camServoChannel) { camServo.setAngle(angle); } // Camera Servo
      else if (servoId == ballStorageServoChannel) { ballStorageServo.setAngle(angle); } // Ball Storage Servo
      
    } else {
      Serial.println("Invalid angle.");
    }
  } else {
    Serial.println("Invalid command format. Use SC,R,Angle");
  }
}


// --------------------------------------------------------------
// Function to Control Single Servo | Command: ServoControl | SC,X,Angle
void servoFreeControl(String input) {
  // Parse the command for individual servo control
  int commaIndex1 = input.indexOf(',');
  int commaIndex2 = input.indexOf(',', commaIndex1 + 1);

  if (commaIndex1 != -1 && commaIndex2 != -1) {
    String servoIdStr = input.substring(commaIndex1 + 1, commaIndex2);
    String situationStr = input.substring(commaIndex2 + 1);
    int servoId = servoIdStr.toInt();

    // Validate the servo angle
    if ( situationStr == "F") {
      Serial.print("Set servo ");
      Serial.print(servoId);
      Serial.println(" to Free Mode");

      if (servoId < 0) { Grip.freeAllServos(); } // -1
      else if (servoId >= 0 && servoId <= 3) { Grip.freeXServo(servoId); } // Inside ArmGrip Class
      else if (servoId == camServoChannel) { camServo.freeServo(); } // Camera Servo
      else if (servoId == ballStorageServoChannel) { ballStorageServo.freeServo(); } // Ball Storage Servo
      
    } else {
      Serial.println("Invalid Mode (Only Free Available).");
    }
  } else {
    Serial.println("Invalid command format. Use SC,R,Free");
  }
}

// --------------------------------------------------------------
// Function to Control Single Servo | Command: ServoControl | SC,X,Angle
void ledBlinkController() {
  ledT1 = ledT0 + ledTimeInterval;
  if (millis() >= ledT1) {
    ledState = !ledState;
    if (ledState == true) {
      digitalWrite(LED_BUILTIN, HIGH);
    }
    else {
      digitalWrite(LED_BUILTIN, LOW);
    }
    ledT0 = ledT1;
  }
}