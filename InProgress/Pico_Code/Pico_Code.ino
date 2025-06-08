#include <Servo.h>
#include <Wire.h>
#include <VL53L0X.h>
#include <Adafruit_PWMServoDriver.h>
#include "myServo.h"
#include "Motor.h"
#include "ArmGrip.h"
#include "IMU.h"
#include "ToF.h"


// --------------------------- Motor Vars ---------------------------

const int enc1A = 2;
const int enc1B = 3;
const int enc2A = 12;
const int enc2B = 13;
const int enc3A = 1;
const int enc3B = 0;
const int enc4A = 14;
const int enc4B = 15;

Motor motors[4] = {
    Motor(10, enc1A, enc1B),
    Motor(11, enc2A, enc2B),
    Motor(22, enc3A, enc3B),
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


// --------------------------- IMU Vars ---------------------------
IMU myIMU;


// --------------------------- TOF Vars ---------------------------
ToF myToFs(3, 4, 5, 6, 7);  // Setup sensors by mux channels


// --------------------------- LED Vars ---------------------------
const int redLed = 18;
const int greenLed = 17;
const int blueLed = 16;
const int robotLight = 8;

unsigned long ledT0;  // control sampling rate (period ini)
unsigned long ledT1;  // control sampling rate (period end)
long ledTimeInterval = 1000;  // 1s blinks

bool ledState = true;


// --------------------------- Time Vars ---------------------------
unsigned long t0;  // control sampling rate (period ini)
unsigned long t1;  // control sampling rate (period end)
long timeInterval = 2.5;  // 2.5ms per loop = 400Hz



// ----------------------------------------------------------------
// -----------------  <<<<<<<<  Setup  >>>>>>>>  ------------------
// --------------------------- ----- ------------------------------

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  /*// Get Motors Ready
  for (int i = 0; i < 4; i++) {
    motors[i].getReady();
  }*/

  // I2C Communitations
  Wire.begin(); // Bus 0 GPIO 4 and 5
  Wire1.setSDA(6); 
  Wire1.setSCL(7);
  Wire1.begin(); // Bus 1 GPIO 6 and 7


  // Get The Servos Ready - Correct Position
  Grip.begin();
  Grip.defaultPosition(); // Get the Grip to its default/storage Position
  camServo.lineFollowing(); // Get the Camera to point down for line following
  ballStorageServo.close(); // Close Ball Storage

  // Let the Servos Stay Free - Avoid Shaking
  delay(1000);
  Grip.freeAllServos();
  camServo.freeServo();
  ballStorageServo.freeServo();

  // IMU Setup
  myIMU.begin(Wire);

  // ToFs Setup
  myToFs.begin(Wire1);

  // LED
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  
  pinMode(redLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(blueLed, OUTPUT);
  setRGBColor(0,255,0);

  pinMode(robotLight, OUTPUT);
  digitalWrite(robotLight, HIGH);


  ledT0 = millis();
  t0 = millis();
}



// ---------------------------------------------------------------
// -----------------  <<<<<<<<  Loop  >>>>>>>>  ------------------
// --------------------------- ----- -----------------------------

String message = "";
void loop() {
  t1 = t0 + timeInterval;


  // Update Sensors
  myIMU.update10DOF();


  // Read Serial Port
  message = readSerial(); 

  if (message != "") {
    Serial.print("Pico Received: ");
    Serial.println(message);
  }


  // Act According Message:
  if (message.startsWith("M(") && message.endsWith(")")) { ControlMotor(message); }  // Motor Command | M(x,x)

  else if (message == "GR") {   // Arm motors again | Get Ready
    for (int i = 0; i < 4; i++) {
      motors[i].getReady();
    }
    Serial.print("Ok\n");
  }

  else if (message == "PA") { Grip.pickAlive(); Serial.print("Ok\n"); }  // Pick Alive Victim Sequence Command | Pick Alive
  else if (message == "PD") { Grip.pickDead(); Serial.print("Ok\n"); }  // Pick Dead Victim Sequence Command | Pick Dead

  else if (message == "CL") { camServo.lineFollowing(); Serial.print("Ok\n"); }  // Point Camera Down for Line Following Command | Camera Line
  else if (message == "CE") { camServo.EvacuationZone(); Serial.print("Ok\n"); }  // Point Camera Forward for Evactuation Zone Victim Rescue Command | Camera Evacuation

  else if (message == "DA") { ballStorageServo.dropAlive(); Serial.print("Ok\n"); }  // Drop Alive Victims Command | Drop Alive
  else if (message == "DD") { ballStorageServo.dropDead(); Serial.print("Ok\n"); }  // Drop Dead Victims Command | Drop Dead
  else if (message == "BC") { ballStorageServo.close(); Serial.print("Ok\n"); } // Close Ball Storage Command | Ball Close

  else if (message == "HO") { Grip.openHand(); Serial.print("Ok\n"); }  // Open Hand Command | Hand Open
  else if (message == "HC") { Grip.closeHand(); Serial.print("Ok\n"); }  // Close Hand Command | Hand Close
  else if (message == "HA") { Grip.moveAlive(); Serial.print("Ok\n"); }  // Move Hand to Alive Position Command | Hand Alive
  else if (message == "HD") { Grip.moveDead(); Serial.print("Ok\n"); }  // Move Hand to Dead Position Command | Hand Dead

  else if (message == "AD") { Grip.moveDown(); Serial.print("Ok\n"); }  // Move Arm Down Command (Catch Position) | Arm Down
  else if (message == "AU") { Grip.moveUp(); Serial.print("Ok\n"); }  // Move Arm Up Command (Storage Position) | Arm Up

  else if (message.startsWith("SC,")) { servoControlMessage(message); Serial.print("Ok\n"); } // Control Single Servo Command | servoControl

  else if (message.startsWith("SF,")) { servoFreeControl(message); Serial.print("Ok\n"); } //Free a servo | Servo Free

  else if (message == "IMU10") { Serial.print("I10, "); Serial.println(myIMU.getAllString()); } // Print All IMU Data | IMU 10 DOF
  else if (message == "IMUAcc") { Serial.println(myIMU.getAccelString()); } // Print IMU Acceleration Data | IMU Acceleration DOF
  else if (message == "IMUGyro") { Serial.println(myIMU.getGyroString()); } // Print IMU Gyroscope Data | IMU Gyroscope DOF
  else if (message == "IMUMag") { Serial.println(myIMU.getMagString()); } // Print IMU Magnetometer Data | IMU Magnetometer DOF
  else if (message == "IMUTemp") { Serial.println(myIMU.getTempString()); } // Print IMU Temperature Data | IMU Temperature DOF

  else if (message == "ToF5") {
    myToFs.updateToF5();
    String allData = "T5, ";
    allData += myToFs.getAllString(); 
    Serial.println(allData);
  } // Print All ToF Data | ToF 5 Sensors
  else if (message.startsWith("ToFX")) { myToFs.updateToF5(); tofControlMessage(message); } // Print Specific ToF Data | ToF X Sensor

  else if (message == "ITData") {
    myToFs.updateToF5();
    String allData = "D, ";
    allData += myIMU.getAllString();     // e.g., 9 IMU values + temp
    allData += ", ";
    allData += myToFs.getAllString();    // 5 TOF values
    Serial.println(allData);             // One complete line
  }

  else if (message == "L0") { digitalWrite(robotLight, LOW); Serial.print("Ok\n"); }
  else if (message == "L1") { digitalWrite(robotLight, HIGH); Serial.print("Ok\n"); }
  else if (message.startsWith("LX")) { lightControlMessage(message); Serial.print("Ok\n"); }
  
  else if (message.startsWith("RGB,")) { handleRGBCommand(message); Serial.print("Ok\n"); }
  
  else if (message == "Alive") { Serial.println("Yes Alive"); }  // Check if Pico is still alive  | Alive


  // LED Blink
  ledBlinkController(); //Blinks LED every Time Interval (ledTimeInterval = 1s)


  while (millis() <= t1) {
    delay(0.025);
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
// Function to Handle RGB Command | Command: RGB,X,X,X
void handleRGBCommand(String command) {
  if (command.startsWith("RGB,")) {
    int firstComma = command.indexOf(',');              // Position of first comma
    int secondComma = command.indexOf(',', firstComma + 1);
    int thirdComma = command.indexOf(',', secondComma + 1);

    if (firstComma > 0 && secondComma > firstComma && thirdComma > secondComma) {
      int red   = command.substring(firstComma + 1, secondComma).toInt();
      int green = command.substring(secondComma + 1, thirdComma).toInt();
      int blue  = command.substring(thirdComma + 1).toInt();

      setRGBColor(red, green, blue);
    } else {
      Serial.println("Error: Malformed RGB command");
    }
  }
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
// Function to handle ToF read commands | Format: ToFX,Index (1 to 5)
void tofControlMessage(String input) {
  int commaIndex = input.indexOf(',');

  if (commaIndex != -1) {
    String indexStr = input.substring(commaIndex + 1);
    int sensorIndex = indexStr.toInt();

    // Read and print the corresponding sensor value
    switch (sensorIndex) {
      case 1:
        //Serial.print("Back Right: ");
        Serial.println(myToFs.getBackRight());
        break;
      case 2:
        //Serial.print("Front Right: ");
        Serial.println(myToFs.getFrontRight());
        break;
      case 3:
        //Serial.print("Front Center: ");
        Serial.println(myToFs.getFrontCenter());
        break;
      case 4:
        //Serial.print("Front Left: ");
        Serial.println(myToFs.getFrontLeft());
        break;
      case 5:
        //Serial.print("Back Left: ");
        Serial.println(myToFs.getBackLeft());
        break;
      default:
        Serial.println("Invalid ToF sensor index. Use 1 to 5.");
        break;
    }
  } else {
    Serial.println("Invalid ToF command format. Use ToFX,Index (1-5)");
  }
}


// --------------------------------------------------------------
// Function to control the light brightness using PWM | Format: LX,0 to LX,255
void lightControlMessage(String input) {
  int commaIndex = input.indexOf(',');

  if (commaIndex != -1) {
    String pwmValueStr = input.substring(commaIndex + 1);
    int pwmValue = pwmValueStr.toInt();

    // Validate the PWM value (between 0 and 255)
    if (pwmValue >= 0 && pwmValue <= 255) {
      //Serial.print("Setting light brightness to: ");
      //Serial.println(pwmValue);
      
      // Set the PWM value to control brightness
      analogWrite(robotLight, pwmValue);
    } else {
      Serial.println("Invalid PWM value. Please provide a value between 0 and 255.");
    }
  } else {
    Serial.println("Invalid command format. Use LX,Value (0-255)");
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
      //Serial.print("Set servo ");
      //Serial.print(servoId);
      //Serial.println(" to Free Mode");

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


void setRGBColor(int red, int green, int blue) {
  digitalWrite(redLed, red);
  digitalWrite(greenLed, green);
  digitalWrite(blueLed, blue);
}