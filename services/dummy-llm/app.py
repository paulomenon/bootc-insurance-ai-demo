import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from flask import Flask, request, jsonify
from shared.logger import get_logger

app = Flask(__name__)
log = get_logger("dummy-llm")

INTENT_PATTERNS = {
    "emergency_ambulance": [
        r"accident",
        r"ambulance",
        r"hurt",
        r"injur",
        r"crash",
        r"broke",
        r"fracture",
        r"bleed",
        r"pain",
        r"fall",
        r"fell",
        r"emergency",
    ],
    "emergency_helicopter": [
        r"helicopter",
        r"air\s*lift",
        r"air\s*rescue",
        r"medevac",
        r"chopper",
    ],
    "coverage_inquiry": [
        r"covered",
        r"coverage",
        r"policy",
        r"insurance",
        r"plan",
        r"claim",
    ],
    "greeting": [
        r"\bhello\b",
        r"\bhi\b",
        r"\bhey\b",
        r"good\s*(morning|afternoon|evening)",
    ],
}

LOCATION_PATTERNS = {
    "alps": r"alps|alpine|switzerland|austria|chamonix|zermatt|innsbruck|tyrol",
    "beach": r"beach|coast|shore|seaside|ocean",
    "city": r"city|town|urban|street|road|highway",
    "mountain": r"mountain|hill|peak|summit|slope|ski|skiing|snowboard",
}

ACTIVITY_PATTERNS = {
    "skiing": r"ski|skiing|snowboard|slope|piste",
    "hiking": r"hik|trek|climb|trail",
    "driving": r"driv|car|vehicle|road|highway|crash",
    "cycling": r"cycl|bike|bicycle",
}


def detect_intent(text: str) -> dict:
    text_lower = text.lower()
    scores = {}

    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, text_lower))
        if score > 0:
            scores[intent] = score

    if not scores:
        return {
            "intent": "unknown",
            "confidence": 0.3,
            "routing": "none",
        }

    best_intent = max(scores, key=scores.get)
    max_possible = len(INTENT_PATTERNS[best_intent])
    confidence = min(0.95, 0.5 + (scores[best_intent] / max_possible) * 0.45)

    routing = "agentic_ai"
    if best_intent == "greeting":
        routing = "direct_response"
    elif best_intent == "coverage_inquiry":
        routing = "insurance_agent_only"

    return {
        "intent": best_intent,
        "confidence": round(confidence, 2),
        "routing": routing,
    }


def extract_entities(text: str) -> dict:
    text_lower = text.lower()
    entities = {}

    for loc, pattern in LOCATION_PATTERNS.items():
        if re.search(pattern, text_lower):
            entities["location"] = loc
            break

    for act, pattern in ACTIVITY_PATTERNS.items():
        if re.search(pattern, text_lower):
            entities["activity"] = act
            break

    if re.search(r"helicopter|chopper|air", text_lower):
        entities["requested_transport"] = "helicopter"
    elif re.search(r"ambulance", text_lower):
        entities["requested_transport"] = "ambulance"

    severity_keywords = {
        "critical": r"critical|severe|dying|unconscious|not breathing",
        "high": r"bad|serious|lot of blood|broken|fracture",
        "medium": r"hurt|pain|injur|accident",
        "low": r"minor|small|slight|little",
    }
    for level, pattern in severity_keywords.items():
        if re.search(pattern, text_lower):
            entities["severity"] = level
            break

    return entities


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "dummy-llm"})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")
    log.info(f"Analyzing message: {text[:100]}")

    intent_result = detect_intent(text)
    entities = extract_entities(text)

    response = {
        "intent": intent_result["intent"],
        "confidence": intent_result["confidence"],
        "entities": entities,
        "routing": intent_result["routing"],
        "raw_text": text,
    }

    log.info(f"LLM result: intent={response['intent']}, confidence={response['confidence']}, routing={response['routing']}")
    return jsonify(response)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    log.info(f"Dummy LLM service starting on port {port}")
    app.run(host="0.0.0.0", port=port)
