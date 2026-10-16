
import cv2
import json
import time
from ultralytics import YOLO

CAMERA_URL = "http://192.168.116.55:8080/video"
MODEL_PATH = r"D:\mini project\yolo11n.pt"
ZONES_PATH = r"D:\mini project\seat_zones.json"
OUTPUT_PATH = r"D:\mini project\seat_occupancy.json"

model = YOLO(MODEL_PATH)

with open(ZONES_PATH, "r", encoding="utf-8") as f:
    zones = json.load(f)

cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    raise SystemExit("Phone camera connect nahi hua. URL check karo.")

# YOLO COCO class 0 = person
history = {zone["id"]: [] for zone in zones}

print("Seat detection started. Press Q to stop.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Camera frame nahi mila.")
        break

    results = model(frame, classes=[0], conf=0.35, verbose=False)
    detections = []

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = map(int, box)
            # Person ke feet ke paas point
            point = ((x1 + x2) // 2, y2)
            detections.append(point)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 180, 0), 2)

    seat_status = {}

    for zone in zones:
        seat_id = zone["id"]
        x1, y1, x2, y2 = zone["box"]

        # Seat zone ke andar person ka bottom-center point?
        occupied_now = any(
            x1 <= px <= x2 and y1 <= py <= y2
            for px, py in detections
        )

        history[seat_id].append(occupied_now)
        history[seat_id] = history[seat_id][-5:]

        # Last 5 frames mein at least 3 detections
        occupied = sum(history[seat_id]) >= 3

        seat_status[seat_id] = "occupied" if occupied else "empty"

        color = (0, 200, 0) if occupied else (130, 130, 130)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame, f"{seat_id}: {seat_status[seat_id]}",
            (x1, max(20, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "seat_count": len(zones),
            "occupied_count": sum(
                s == "occupied" for s in seat_status.values()
            ),
            "seats": seat_status
        }, f, indent=2)

    cv2.imshow("Live Seat Occupancy", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Seat detector stopped.")
