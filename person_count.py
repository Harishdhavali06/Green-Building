import cv2
import json
import time
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "occupancy.json"
MODEL_FILE = BASE_DIR / "yolo11n.pt"

CAMERA_URL = "http://192.168.116.55:8080/video"

model = YOLO(str(MODEL_FILE))
cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("Camera open nahi ho raha. Phone camera URL check karo.")
    raise SystemExit(1)

print("EcoTwin YOLO occupancy detection started.")

last_count = None

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Camera feed nahi mil rahi.")
            break

        results = model(frame, verbose=False)

        person_count = 0

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])

                if class_id == 0:
                    person_count += 1

        annotated_frame = (
            results[0].plot() if results else frame.copy()
        )

        cv2.putText(
            annotated_frame,
            f"People detected: {person_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        # Write the latest count to the shared JSON file.
        data = {
            "occupancy": person_count,
            "updated_at": time.time(),
        }

        temp_file = DATA_FILE.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(data),
            encoding="utf-8",
        )
        temp_file.replace(DATA_FILE)

        if person_count != last_count:
            print(f"Live occupancy: {person_count}")
            last_count = person_count

        cv2.imshow(
            "EcoTwin - Occupancy Detection",
            annotated_frame,
        )

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()