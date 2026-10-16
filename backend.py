import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="EcoTwin API")

@app.get("/api/seats")
def get_seats():
    path = r"D:\mini project\seat_occupancy.json"

    if not os.path.exists(path):
        return {
            "seat_count": 18,
            "occupied_count": 0,
            "seats": {}
        }

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).resolve().parent / "occupancy.json"


@app.get("/api/occupancy")
def get_occupancy():
    if not DATA_FILE.exists():
        return JSONResponse(
            content={
                "occupancy": None,
                "status": "waiting",
            },
            headers={"Cache-Control": "no-store"},
        )

    try:
        data = json.loads(
            DATA_FILE.read_text(encoding="utf-8")
        )

        count = int(data["occupancy"])

        if count < 0:
            raise ValueError("Invalid occupancy")

        return JSONResponse(
            content={
                "occupancy": count,
                "status": "live",
                "updated_at": data.get("updated_at"),
            },
            headers={"Cache-Control": "no-store"},
        )

    except (
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        OSError,
    ):
        return JSONResponse(
            content={
                "occupancy": None,
                "status": "waiting",
            },
            headers={"Cache-Control": "no-store"},
        )






import json
import os
import urllib.request
import urllib.error
import requests
from fastapi import HTTPException, Body

from fastapi import HTTPException
from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    live_occupancy: int | None = None
    camera_status: str = "Unknown"
    rooms: list[dict] = []


@app.post("/api/recommendations")
def get_recommendations(payload: RecommendationRequest):
    api_key = os.getenv("AQ.Ab8RN6IgV8xGZb0L69z4LnqvbywwUryZ7wbDxyS0PFekCKixBg")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is not configured. Set GEMINI_API_KEY and restart the backend."
        )

    prompt = f"""
You are EcoTwin, an assistant for a green-building hackathon prototype.
Analyse the supplied building data and suggest 3 practical energy-efficiency actions.
Some room values are illustrative, not live sensor measurements. Do not claim
measured energy savings, carbon reductions, or verified room-level occupancy.
Clearly distinguish suggestions from facts. Be concise and useful for a college campus.

Camera status: {payload.camera_status}
Overall people count in camera frame: {payload.live_occupancy}
Room data: {json.dumps(payload.rooms)}

Return ONLY valid JSON in this format:
{{
  "recommendations": [
    {{
      "title": "Short action",
      "reason": "Why this could help and what should be checked"
    }}
  ]
}}
"""

    body = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))

        text = result["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        return {"recommendations": parsed.get("recommendations", [])}

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API error ({error.code}): {details[:300]}"
        )
    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(status_code=502, detail="Could not reach Gemini API.")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="Gemini returned an unexpected response.")



import os
import requests
from fastapi import HTTPException

@app.get("/api/recommendations")
def get_recommendations():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured"
        )

    prompt = """
    You are EcoTwin, a green-building energy advisor.
    Give 3 practical energy-saving recommendations for a laboratory.
    Keep the answer short and actionable.
    """

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": api_key},
            json={
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            },
            timeout=30
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error: {response.text[:500]}"
            )

        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        return {"recommendations": answer}

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini connection failed: {str(error)}"
        )

@app.post("/api/recommendations")
def get_recommendations(payload: dict = Body(...)):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is missing"
        )

    prompt = f"""
    You are EcoTwin, an intelligent green-building advisor.

    Current occupancy: {payload.get('live_occupancy', 'Unknown')}
    Camera status: {payload.get('camera_status', 'Unknown')}
    Room data: {payload.get('rooms', [])}

    Give 3 practical recommendations to reduce energy waste.
    Explain the reason for each recommendation.
    Do not claim actual energy savings without measured data.
    """

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": api_key},
            json={
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            },
            timeout=30
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error: {response.text[:500]}"
            )

        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        return {"recommendations": answer}

    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail=str(error))