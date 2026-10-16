
import cv2
import json

CAMERA_URL = "http://192.168.116.55:8080/video"

cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("Phone camera connect nahi hua. URL check karo.")
    raise SystemExit

print("Camera open ho raha hai. 's' = save frame, 'q' = quit")

while True:
    ok, frame = cap.read()

    if not ok:
        print("Frame read nahi hua.")
        break

    cv2.imshow("Seat Zone Calibration", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        cv2.imwrite("lab_frame.jpg", frame)
        print("Saved: D:\\mini project\\lab_frame.jpg")
        break

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
