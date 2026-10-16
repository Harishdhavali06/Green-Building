
import cv2
import json
import os

IMAGE_PATH = r"D:\mini project\lab_frame.jpg"
OUTPUT_PATH = r"D:\mini project\seat_zones.json"

image = cv2.imread(IMAGE_PATH)
if image is None:
    raise SystemExit("lab_frame.jpg nahi mila!")

# 6 tables, 3 chairs each
seat_ids = [
    "A1", "A2", "A3", "B1", "B2", "B3",
    "C1", "C2", "C3", "D1", "D2", "D3",
    "E1", "E2", "E3", "F1", "F2", "F3"
]

zones = []
current = []
index = 0
display = image.copy()

print("Har chair ke around mouse se rectangle draw karo.")
print("Drag = rectangle | Enter = confirm | R = redo | Q = quit")

def mouse(event, x, y, flags, param):
    global current, display, index

    if event == cv2.EVENT_LBUTTONDOWN:
        current.clear()
        current.append((x, y))

    elif event == cv2.EVENT_LBUTTONUP and current:
        current.append((x, y))
        display = image.copy()

        for z in zones:
            x1, y1, x2, y2 = z["box"]
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 200, 0), 2)
            cv2.putText(display, z["id"], (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

        (x1, y1), (x2, y2) = current
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 180, 255), 2)

cv2.namedWindow("Mark Seats", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Mark Seats", mouse)

while index < len(seat_ids):
    display = image.copy()

    for z in zones:
        x1, y1, x2, y2 = z["box"]
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(display, z["id"], (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

    cv2.putText(display, f"Mark seat {seat_ids[index]} ({index+1}/18)",
                (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Mark Seats", display)
    key = cv2.waitKey(20) & 0xFF

    if key in (10, 13) and len(current) == 2:
        (x1, y1), (x2, y2) = current
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        if x2 - x1 >= 5 and y2 - y1 >= 5:
            zones.append({
                "id": seat_ids[index],
                "box": [x1, y1, x2, y2]
            })
            index += 1
            current.clear()

    elif key in (ord("r"), ord("R")):
        current.clear()

    elif key in (ord("q"), ord("Q")):
        break

cv2.destroyAllWindows()


if len(zones) == 18:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(zones, f, indent=2)

    print(f"SUCCESS: {len(zones)} seats saved!")
    print(f"File location: {OUTPUT_PATH}")
else:
    print(f"Only {len(zones)} seats confirmed.")
    print("18 seats complete hone ke baad hi file save hogi.")