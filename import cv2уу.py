import cv2
import face_recognition
from threading import Thread
import serial
import time
from deepface import DeepFace  # Импортираме DeepFace за разпознаване на пол

# Initialize communication with Arduino
arduino = serial.Serial('COM12', 9600)  # Replace 'COM12' with your Arduino port
time.sleep(2)  # Wait for Arduino to initialize

# Class for multithreading video stream reading
class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FPS, 30)  # Set FPS
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Resolution width
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Resolution height
        self.ret, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# Start video stream
video_stream = VideoStream(src=0).start()

print("Press 'q' to quit.")

# Initialize previous servo positions for smoothing
prev_servo_x, prev_servo_y = 90, 90

while True:
    # Grab the current frame
    frame = video_stream.read()

    # Resize frame to speed up processing
    small_frame = cv2.resize(frame, (320, 240))  # Reduce resolution for faster processing
    rgb_small_frame = small_frame[:, :, ::-1]  # Convert to RGB

    # Detect faces using HOG model
    face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")

    # If no faces are detected, stop the servos
    if not face_locations:
        arduino.write("90,90\n".encode('utf-8'))  # Neutral position
        cv2.imshow("Face Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Calculate scaling factor
    scale_x = frame.shape[1] / small_frame.shape[1]
    scale_y = frame.shape[0] / small_frame.shape[0]

    for top, right, bottom, left in face_locations:
        # Scale face coordinates back to the original resolution
        top = int(top * scale_y)
        right = int(right * scale_x)
        bottom = int(bottom * scale_y)
        left = int(left * scale_x)

        # Calculate the center of the detected face
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2

        # Map face position to servo values
        servo_x = 180 - int((center_x / frame.shape[1]) * 180)  # Invert X-axis logic
        servo_y = 180 - int((center_y / frame.shape[0]) * 180)  # Invert Y-axis logic

        # Constrain values to servo ranges
        servo_x = max(0, min(180, servo_x))
        servo_y = max(0, min(180, servo_y))

        # Only send data if there is a significant change
        if abs(servo_x - prev_servo_x) > 2 or abs(servo_y - prev_servo_y) > 2:
            arduino.write(f"{servo_x},{servo_y}\n".encode('utf-8'))
            prev_servo_x, prev_servo_y = servo_x, servo_y
            time.sleep(0.05)  # Add a short delay to prevent timeout

        # Draw rectangle and display servo positions
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, f"X: {servo_x}, Y: {servo_y}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Crop the face region from the frame for gender detection
        face_crop = frame[top:bottom, left:right]
        
        # Gender recognition using DeepFace
        try:
            analysis = DeepFace.analyze(face_crop, actions=['gender'], enforce_detection=False)
            gender = analysis[0]['gender']
            cv2.putText(frame, f"Gender: {gender}", (left, top - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        except Exception as e:
            print("Error analyzing face:", e)

    # Display the frame with face tracking and gender
    cv2.imshow("Face Tracking", frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop the video stream and close windows
video_stream.stop()
cv2.destroyAllWindows()
