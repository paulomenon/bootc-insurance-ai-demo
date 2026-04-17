import sys
import os
import random
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from flask import Flask, request, jsonify
from shared.logger import get_logger

app = Flask(__name__)
log = get_logger("operator-agent")

HOSPITALS = {
    "alps": [
        {"name": "Innsbruck University Hospital", "distance_km": 12.5, "specialties": ["trauma", "orthopedics"], "emergency": True, "appointments": True},
        {"name": "Zermatt Medical Center", "distance_km": 3.2, "specialties": ["emergency", "sports medicine"], "emergency": True, "appointments": True},
        {"name": "Chamonix Hospital Centre", "distance_km": 8.7, "specialties": ["trauma", "emergency"], "emergency": True, "appointments": False},
    ],
    "mountain": [
        {"name": "Alpine Emergency Clinic", "distance_km": 15.0, "specialties": ["trauma", "altitude medicine"], "emergency": True, "appointments": False},
        {"name": "Mountain Rescue Hospital", "distance_km": 22.3, "specialties": ["orthopedics", "emergency"], "emergency": True, "appointments": True},
    ],
    "city": [
        {"name": "Central City Hospital", "distance_km": 2.1, "specialties": ["emergency", "general"], "emergency": True, "appointments": True},
        {"name": "University Medical Center", "distance_km": 5.4, "specialties": ["trauma", "surgery"], "emergency": True, "appointments": True},
    ],
    "beach": [
        {"name": "Coastal Medical Center", "distance_km": 4.8, "specialties": ["emergency", "general"], "emergency": True, "appointments": True},
        {"name": "Seaside Trauma Hospital", "distance_km": 8.1, "specialties": ["trauma", "emergency"], "emergency": True, "appointments": False},
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


def find_nearest_hospital(location: str, need_appointments: bool = False) -> dict:
    """Auto-locate the nearest hospital based on the user's location."""
    hospitals = HOSPITALS.get(location, HOSPITALS["city"])
    if need_appointments:
        candidates = [h for h in hospitals if h.get("appointments")]
        if not candidates:
            candidates = hospitals
    else:
        candidates = hospitals
    return min(candidates, key=lambda h: h["distance_km"])


def handle_emergency(intent: str, entities: dict, insurance_decision: dict) -> dict:
    """Handle emergency requests: dispatch ambulance/helicopter to nearest hospital."""
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

    hospital = find_nearest_hospital(location)

    coords = COORDINATES.get(location, COORDINATES["city"])
    coords = {
        "lat": round(coords["lat"] + random.uniform(-0.05, 0.05), 4),
        "lng": round(coords["lng"] + random.uniform(-0.05, 0.05), 4),
    }

    operation_id = f"OP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    result = {
        "operation_id": operation_id,
        "operation_type": "emergency",
        "transport_type": transport_type,
        "unit_callsign": unit_template.format(random.randint(1, 99)),
        "eta_minutes": eta_minutes,
        "hospital_name": hospital["name"],
        "hospital_distance_km": hospital["distance_km"],
        "hospital_specialties": hospital["specialties"],
        "hospital_connected": True,
        "hospital_pre_alerted": True,
        "coordinates": coords,
        "severity": severity,
        "status": "dispatched",
        "timestamp": datetime.now().isoformat(),
    }

    if fallback:
        result["note"] = "Helicopter not covered by insurance — dispatching ground ambulance instead"
        result["fallback"] = True

    return result


def handle_appointment(entities: dict, insurance_decision: dict) -> dict:
    """Auto-connect to nearest hospital and book an appointment."""
    location = entities.get("location", "city")
    hospital = find_nearest_hospital(location, need_appointments=True)

    appointment_date = datetime.now() + timedelta(days=random.randint(1, 5))
    appointment_time = f"{random.randint(8, 16):02d}:{random.choice(['00', '15', '30', '45'])}"

    operation_id = f"OP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    return {
        "operation_id": operation_id,
        "operation_type": "appointment",
        "hospital_name": hospital["name"],
        "hospital_distance_km": hospital["distance_km"],
        "hospital_specialties": hospital["specialties"],
        "hospital_connected": True,
        "appointment_date": appointment_date.strftime("%Y-%m-%d"),
        "appointment_time": appointment_time,
        "status": "booked",
        "timestamp": datetime.now().isoformat(),
    }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "operator-agent"})


@app.route("/operate", methods=["POST"])
def operate():
    """
    Main endpoint — receives intent, entities, and insurance decision from the
    Agentic AI. Automatically connects to the nearest hospital and either
    dispatches emergency help or books an appointment.
    """
    data = request.get_json()
    intent = data.get("intent", "")
    entities = data.get("entities", {})
    insurance_decision = data.get("insurance_decision", {})

    log.info(f"Operator request: intent={intent}, entities={entities}")

    if intent in ("emergency_ambulance", "emergency_helicopter"):
        result = handle_emergency(intent, entities, insurance_decision)
        log.info(f"Emergency dispatched: {result['unit_callsign']} → {result['hospital_name']} (ETA: {result['eta_minutes']}min)")
    else:
        result = handle_appointment(entities, insurance_decision)
        log.info(f"Appointment booked: {result['hospital_name']} on {result['appointment_date']} at {result['appointment_time']}")

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    log.info(f"Operator Agent starting on port {port}")
    app.run(host="0.0.0.0", port=port)
