#include <Servo.h>

Servo servoX;  // Continuous rotation servo for X-axis
Servo servoY;  // Standard servo for Y-axis

// Constants for continuous rotation servo
const int NEUTRAL_X = 1500;  // Neutral position (stop rotation)
const int MAX_SPEED_X = 1600;  // Speed for left rotation
const int MIN_SPEED_X = 1400;  // Speed for right rotation

// Dead zone for X-axis
const int DEAD_ZONE_X = 10;  // Degrees within which the servo won't move

// Variables for smoothing the Y servo
int currentY = 90;  // Start at the center
const int SMOOTHING_STEP = 2;  // Smaller step for slower, smoother movement

void setup() {
  servoX.attach(10);  // Attach continuous rotation servo to pin 10
  servoY.attach(9);   // Attach standard servo to pin 9

  servoX.writeMicroseconds(NEUTRAL_X);  // Stop the X servo initially
  servoY.write(currentY);  // Center the Y servo initially

  Serial.begin(9600);  // Start serial communication
}

void loop() {
  // Check for incoming serial data
  while (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');  // Read incoming data
    int delimiterIndex = data.indexOf(',');
    if (delimiterIndex > 0) {
      String xStr = data.substring(0, delimiterIndex);   // Extract X position
      String yStr = data.substring(delimiterIndex + 1); // Extract Y position
      
      int posX = xStr.toInt();  // Target position for X-axis
      int targetY = yStr.toInt();  // Target position for Y-axis

      // Control the continuous rotation servo (X-axis)
      int pulseWidthX = NEUTRAL_X;  // Default to stop
      if (abs(posX - 90) > DEAD_ZONE_X) {  // Move only if outside dead zone
        if (posX > 90) {
          pulseWidthX = map(posX, 90, 180, NEUTRAL_X, MAX_SPEED_X);  // Rotate left
        } else if (posX < 90) {
          pulseWidthX = map(posX, 0, 90, MIN_SPEED_X, NEUTRAL_X);  // Rotate right
        }
      }
      servoX.writeMicroseconds(pulseWidthX);

      // Smoothly move the Y servo to the target position
      targetY = constrain(targetY, 0, 180);  // Ensure Y position is valid
      if (currentY < targetY) {
        currentY = min(currentY + SMOOTHING_STEP, targetY);
      } else if (currentY > targetY) {
        currentY = max(currentY - SMOOTHING_STEP, targetY);
      }
      servoY.write(currentY);

      // Debugging information (optional)
      Serial.print("Servo X Pulse Width: ");
      Serial.println(pulseWidthX);
      Serial.print("Servo Y Position: ");
      Serial.println(currentY);
    }
  }
}
