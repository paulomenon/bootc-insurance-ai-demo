import sys
import os
import random
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from flask import Flask, request, jsonify
from shared.logger import get_logger

app = Flask(__name__)
log = get_logger("dispatch-ai-agent")

HOSPITALS = {
    "alps": [
        {"name": "Innsbruck University Hospital", "distance_km": 12.5, "specialties": ["trauma", "orthopedics"]},
        {"name": "Zermatt Medical Center", "distance_km": 3.2, "specialties": ["emergency", "sports medicine"]},
        {"name": "Chamonix Hospital Centre", "distance_km": 8.7, "specialties": ["trauma", "emergency"]},
    ],
    "mountain": [
        {"name": "Alpine Emergency Clinic", "distance_km": 15.0, "specialties": ["trauma", "altitude medicine"]},
        {"name": "Mountain Rescue Hospital", "distance_km": 22.3, "specialties": ["orthopedics", "emergency"]},
    ],
    "city": [
        {"name": "Central City Hospital", "distance_km": 2.1, "specialties": ["emergency", "general"]},
        {"name": "University Medical Center", "distance_km": 5.4, "specialties": ["trauma", "surgery"]},
    ],
    "beach": [
        {"name": "Coastal Medical Center", "distance_km": 4.8, "specialties": ["emergency", "general"]},
        {"name": "Seaside Trauma Hospital", "distance_km": 8.1, "specialties": ["trauma", "emergency"]},
    ],
}

AMBULANCE_UNITS = [
    "ALPHA-{:02d}",
    "BRAVO-{:02d}",
    "CHARLIE-{:02d}",
    "DELTA-{:02d}",
    "ECHO-{:02d}",
]

HELICOPTER_UNITS = [
    "HELI-RED-{:02d}",
    "HELI-BLUE-{:02d}",
    "AIR-RESCUE-{:02d}",
]

COORDINATES = {
    "alps": {"lat": 46.8182, "lng": 8.2275},
    "mountain": {"lat": 47.2692, "lng": 11.3933},
    "city": {"lat": 48.2082, "lng": 16.3738},
    "beach": {"lat": 43.5528, "lng": 7.0174},
}


def dispatch_emergency(intent: str, entities: dict, insurance_decision: dict) -> dict:
    location = entities.get("location", "city")
    severity = entities.get("severity", "medium")

    is_helicopter = intent == "emergency_helicopter" or entities.get("requested_transport") == "helicopter"
    transport_type = "helicopter" if is_helicopter else "ambulance"

    if is_helicopter and not insurance_decision.get("is_covered", False):
        transport_type = "ambulance"
        fallback = True
    else:
        fallback = False

    if transport_type == "helicopter":
        unit_template = random.choice(HELICOPTER_UNITS)
        base_eta = random.randint(8, 20)
    else:
        unit_template = random.choice(AMBULANCE_UNITS)
        base_eta = random.randint(5, 25)

    severity_modifier = {"critical": 0.7, "high": 0.85, "medium": 1.0, "low": 1.2}
    eta_minutes = int(base_eta * severity_modifier.get(severity, 1.0))

    hospitals = HOSPITALS.get(location, HOSPITALS["city"])
    hospital = min(hospitals, key=lambda h: h["distance_km"])

    coords = COORDINATES.get(location, COORDINATES["city"])
    coords = {
        "lat": round(coords["lat"] + random.uniform(-0.05, 0.05), 4),
        "lng": round(coords["lng"] + random.uniform(-0.05, 0.05), 4),
    }

    dispatch_id = f"DSP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    result = {
        "dispatch_id": dispatch_id,
        "transport_type": transport_type,
        "unit_callsign": unit_template.format(random.randint(1, 99)),
        "eta_minutes": eta_minutes,
        "hospital_name": hospital["name"],
        "hospital_distance_km": hospital["distance_km"],
        "hospital_specialties": hospital["specialties"],
        "hospital_alerted": True,
        "coordinates": coords,
        "severity": severity,
        "status": "dispatched",
        "timestamp": datetime.now().isoformat(),
    }

    if fallback:
        result["note"] = "Helicopter not covered by insurance — dispatching ground ambulance instead"
        result["fallback"] = True

    return result


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "dispatch-ai-agent"})


@app.route("/dispatch", methods=["POST"])
def dispatch():
    data = request.get_json()
    intent = data.get("intent", "")
    entities = data.get("entities", {})
    insurance_decision = data.get("insurance_decision", {})

    log.info(f"Dispatch request: intent={intent}, entities={entities}")
    result = dispatch_emergency(intent, entities, insurance_decision)
    log.info(f"Dispatched: {result['unit_callsign']} → {result['hospital_name']} (ETA: {result['eta_minutes']}min)")

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    log.info(f"Emergency Dispatch AI Agent starting on port {port}")
    app.run(host="0.0.0.0", port=port)
