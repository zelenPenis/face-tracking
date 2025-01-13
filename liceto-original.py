#mai pochti raboti brat ne znam pomosht

import cv2
import face_recognition
from threading import Thread
import serial
import time

# Initialize communication with Arduino
arduino = serial.Serial('COM12', 9600)  
time.sleep(2)  # Wait for Arduino

#  multithreading video streamm
class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FPS, 30)  
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 
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

# initialize previous servo positions ?!?!, maybe
prev_servo_x, prev_servo_y = 90, 90

while True:
    frame = video_stream.read()

    small_frame = cv2.resize(frame, (320, 240)) 
    rgb_small_frame = small_frame[:, :, ::-1]

    face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")

    if not face_locations:
        arduino.write("90,90\n".encode('utf-8'))  
        cv2.imshow("Face Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    scale_x = frame.shape[1] / small_frame.shape[1]
    scale_y = frame.shape[0] / small_frame.shape[0]

    for top, right, bottom, left in face_locations:
        top = int(top * scale_y)
        right = int(right * scale_x)
        bottom = int(bottom * scale_y)
        left = int(left * scale_x)

        center_x = (left + right) // 2
        center_y = (top + bottom) // 2

        servo_x = 180 - int((center_x / frame.shape[1]) * 180)  
        servo_y = 180 - int((center_y / frame.shape[0]) * 180)  

        servo_x = max(0, min(180, servo_x))
        servo_y = max(0, min(180, servo_y))


        if abs(servo_x - prev_servo_x) > 2 or abs(servo_y - prev_servo_y) > 2:
            arduino.write(f"{servo_x},{servo_y}\n".encode('utf-8'))
            prev_servo_x, prev_servo_y = servo_x, servo_y
            time.sleep(0.05) 

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, f"X: {servo_x}, Y: {servo_y}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Face Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


video_stream.stop()
cv2.destroyAllWindows()
