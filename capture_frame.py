
import cv2

PHONE_CAMERA = "http://192.168.116.55:8080/video"

cap = cv2.VideoCapture(PHONE_CAMERA)

if not cap.isOpened():
    print("Camera connect nahi hua. Phone stream URL check karo.")
else:
    ok, frame = cap.read()

    if ok:
        cv2.imwrite("lab_frame.jpg", frame)
        print("Saved: lab_frame.jpg")
    else:
        print("Frame read nahi hua.")

cap.release()
