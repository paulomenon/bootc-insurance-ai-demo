import sys
import os
import random
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from flask import Flask, request, jsonify
from shared.logger import get_logger

app = Flask(__name__)
log = get_logger("insurance-agent")

POLICY_RULES = {
    "ambulance": {
        "covered": True,
        "coverage_type": "Emergency Ground Transport",
        "coverage_limit": "€50,000 per incident",
        "copay_percentage": 10,
        "conditions": [
            "Must be within policy coverage area",
            "Pre-existing conditions may affect coverage",
        ],
    },
    "helicopter": {
        "covered": False,
        "coverage_type": "Emergency Air Transport",
        "coverage_limit": "€0 (not included in standard plan)",
        "copay_percentage": 100,
        "conditions": [
            "Air transport requires Premium or Platinum plan",
            "Standard plan covers ground transport only",
        ],
        "upgrade_suggestion": "Upgrade to Premium plan (€29.99/month) for helicopter coverage up to €100,000",
    },
}

ACTIVITY_COVERAGE = {
    "skiing": {"covered": True, "note": "Winter sports covered under Adventure Rider"},
    "hiking": {"covered": True, "note": "Covered under standard outdoor activities"},
    "driving": {"covered": True, "note": "Covered under motor vehicle clause"},
    "cycling": {"covered": True, "note": "Covered under standard outdoor activities"},
}

LOCATION_COVERAGE = {
    "alps": {"covered": True, "region": "Europe - Alpine Region", "network": "Alpine Rescue Network"},
    "beach": {"covered": True, "region": "Europe - Coastal", "network": "Coast Guard Network"},
    "city": {"covered": True, "region": "Europe - Urban", "network": "City Emergency Network"},
    "mountain": {"covered": True, "region": "Europe - Mountain", "network": "Mountain Rescue Network"},
}


def check_coverage(intent: str, entities: dict) -> dict:
    transport = entities.get("requested_transport", "ambulance")
    if intent == "emergency_helicopter":
        transport = "helicopter"
    elif intent == "emergency_ambulance":
        transport = "ambulance"

    policy = POLICY_RULES.get(transport, POLICY_RULES["ambulance"])
    activity = entities.get("activity", "unknown")
    location = entities.get("location", "unknown")

    activity_info = ACTIVITY_COVERAGE.get(activity, {"covered": True, "note": "General coverage applies"})
    location_info = LOCATION_COVERAGE.get(location, {"covered": True, "region": "Europe - General", "network": "General Emergency Network"})

    is_covered = policy["covered"] and activity_info["covered"] and location_info["covered"]

    result = {
        "policy_id": f"POL-{random.randint(2020, 2026)}-{activity.upper()[:3]}-{random.randint(100, 999):03d}",
        "is_covered": is_covered,
        "coverage_type": policy["coverage_type"],
        "coverage_limit": policy["coverage_limit"],
        "copay_percentage": policy["copay_percentage"],
        "transport_requested": transport,
        "activity_coverage": activity_info,
        "location_coverage": location_info,
        "restrictions": policy.get("conditions", []),
    }

    if not policy["covered"]:
        result["reason"] = f"{transport.title()} transport is not covered under your current Standard plan"
        result["upgrade_suggestion"] = policy.get("upgrade_suggestion", "")
    elif not is_covered:
        result["reason"] = "Coverage denied due to policy restrictions"
    else:
        result["reason"] = f"{transport.title()} transport approved under {policy['coverage_type']}"

    return result


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "insurance-agent"})


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()
    intent = data.get("intent", "")
    entities = data.get("entities", {})

    log.info(f"Checking coverage: intent={intent}, entities={entities}")
    result = check_coverage(intent, entities)
    log.info(f"Coverage decision: covered={result['is_covered']}, type={result['coverage_type']}")

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    log.info(f"Insurance Coverage Agent starting on port {port}")
    app.run(host="0.0.0.0", port=port)
