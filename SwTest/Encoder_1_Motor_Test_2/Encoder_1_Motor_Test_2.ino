#include <Servo.h>

// Single motor control flag: true for single motor, false for all motors
const bool SINGLE_MOTOR_MODE = true;

// Pin definitions for each motor's encoder and PWM control
const int encPins[4][2] = {{9, 8}, {7, 6}, {2, 3}, {5, 4}};
const int pwmPins[4] = {18, 21, 20, 16};

// Control loop settings
const unsigned long CONTROL_INTERVAL = 10; // Interval in milliseconds (100 Hz)
unsigned long lastUpdateTime = 0;
int targetRPM = 0;

Servo esc[4];
volatile long encoderCounts[4] = {0, 0, 0, 0};
float currentRPMs[4] = {0, 0, 0, 0};
float targetRPMs[4] = {0, 0, 0, 0};
float Kp = 0.2, Ki = 0.01, Kd = 0.1;
float integrals[4] = {0, 0, 0, 0};
float previousErrors[4] = {0, 0, 0, 0};

// Function prototypes
void initializeMotors();
//void handleEncoderInterrupt(int motorIndex);
void handleEncoderInterruptMotor0() { handleEncoderInterrupt(0); }
void handleEncoderInterruptMotor1() { handleEncoderInterrupt(1); }
void handleEncoderInterruptMotor2() { handleEncoderInterrupt(2); }
void handleEncoderInterruptMotor3() { handleEncoderInterrupt(3); }
void calculateRPM(int motorIndex);
void updateSpeed(int motorIndex);
void controlMotor(int motorIndex, int pulse);
void displayMotorData();
String readSerialRPM();

void setup() {
    Serial.begin(115200);
    initializeMotors();
    lastUpdateTime = millis();
}

void loop() {
    // Check if the control loop interval has elapsed
    if (millis() - lastUpdateTime >= CONTROL_INTERVAL) {
        lastUpdateTime = millis();

        // Read target RPM value from serial input
        int newTargetRPM = readSerialRPM().toInt();
        if (newTargetRPM != targetRPM) {
            targetRPM = newTargetRPM;
            if (SINGLE_MOTOR_MODE) {
                targetRPMs[0] = targetRPM; // Only update motor 0 in single motor mode
            } else {
                for (int i = 0; i < 4; i++) {
                    targetRPMs[i] = targetRPM; // Update all motors in multi-motor mode
                }
            }
        }

        // Update motor speed using the PID controller
        if (SINGLE_MOTOR_MODE) {
            updateSpeed(0); // Only update motor 0 in single motor mode
        } else {
            for (int i = 0; i < 4; i++) {
                updateSpeed(i); // Update all motors in multi-motor mode
            }
        }

        // Display the current data for debugging
        displayMotorData();
    }
}

void initializeMotors() {
    for (int i = 0; i < 4; i++) {
        esc[i].attach(pwmPins[i]);
        pinMode(encPins[i][0], INPUT);
        pinMode(encPins[i][1], INPUT);
    }

    attachInterrupt(digitalPinToInterrupt(encPins[0][0]), handleEncoderInterruptMotor0, RISING);
    attachInterrupt(digitalPinToInterrupt(encPins[1][0]), handleEncoderInterruptMotor1, RISING);
    attachInterrupt(digitalPinToInterrupt(encPins[2][0]), handleEncoderInterruptMotor2, RISING);
    attachInterrupt(digitalPinToInterrupt(encPins[3][0]), handleEncoderInterruptMotor3, RISING);

    for (int i = 0; i < 4; i++) {
        controlMotor(i, 1500); // Calibrate to neutral position
    }
}

// Interrupt service routine to handle encoder counts
void handleEncoderInterrupt(int motorIndex) {
    encoderCounts[motorIndex]++;
}

// Function to calculate RPM from encoder counts
void calculateRPM(int motorIndex) {
    unsigned long currentTime = millis();
    unsigned long elapsedTime = currentTime - lastUpdateTime;
    int COUNTS_PER_REVOLUTION = 11;
    if (elapsedTime > 0) {
        currentRPMs[motorIndex] = (encoderCounts[motorIndex] / (float)elapsedTime) * 60000 / COUNTS_PER_REVOLUTION;
        encoderCounts[motorIndex] = 0; // Reset count after RPM calculation
    }
}

// PID control to update the motor speed
void updateSpeed(int motorIndex) {
    calculateRPM(motorIndex);
    float error = targetRPMs[motorIndex] - currentRPMs[motorIndex];
    integrals[motorIndex] += error * CONTROL_INTERVAL;
    float derivative = (error - previousErrors[motorIndex]) / CONTROL_INTERVAL;
    float output = Kp * error + Ki * integrals[motorIndex] + Kd * derivative;

    output = constrain(output, 1500, 2000); // Ensure PWM value is within range
    controlMotor(motorIndex, output);

    previousErrors[motorIndex] = error;
}

// Function to set motor speed using a PWM pulse
void controlMotor(int motorIndex, int pulse) {
    if (pulse >= 1000 && pulse <= 2000) {
        esc[motorIndex].writeMicroseconds(pulse);
    } else {
        Serial.println("Invalid pulse value");
    }
}

// Function to display motor data for debugging
void displayMotorData() {
    Serial.print("Target RPM:\t");
    for (int i = 0; i < (SINGLE_MOTOR_MODE ? 1 : 4); i++) {
        Serial.print(targetRPMs[i]);
        Serial.print("\t");
    }

    Serial.print("Pulse:\t");
    for (int i = 0; i < (SINGLE_MOTOR_MODE ? 1 : 4); i++) {
        Serial.print(esc[i].readMicroseconds());
        Serial.print("\t");
    }

    Serial.print("Encoder Count:\t");
    for (int i = 0; i < (SINGLE_MOTOR_MODE ? 1 : 4); i++) {
        Serial.print(encoderCounts[i]);
        Serial.print("\t");
    }

    Serial.print("Current RPM:\t");
    for (int i = 0; i < (SINGLE_MOTOR_MODE ? 1 : 4); i++) {
        Serial.print(currentRPMs[i]);
        Serial.print("\t");
    }
    Serial.println();
}

// Function to read RPM value from serial input
String readSerialRPM() {
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
