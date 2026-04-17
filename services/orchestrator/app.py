import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import requests
from flask import Flask, request, jsonify
from shared.config import INSURANCE_AGENT_URL, DISPATCH_AGENT_URL
from shared.logger import get_logger

app = Flask(__name__)
log = get_logger("agentic-ai")

GREETING_RESPONSES = {
    "greeting": (
        "Hello! I'm your Alpine Insurance emergency assistant.\n\n"
        "I can help you with:\n"
        "• Emergency ambulance dispatch\n"
        "• Insurance coverage checks\n"
        "• Emergency helicopter requests\n\n"
        "Describe your situation and I'll coordinate everything for you."
    ),
}


def call_insurance_agent(intent: str, entities: dict) -> dict:
    try:
        resp = requests.post(
            f"{INSURANCE_AGENT_URL}/check",
            json={"intent": intent, "entities": entities},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error(f"Insurance AI Agent call failed: {e}")
        return {"is_covered": False, "reason": "Insurance AI Agent unavailable", "error": True}


def call_dispatch_agent(intent: str, entities: dict, insurance_decision: dict) -> dict:
    try:
        resp = requests.post(
            f"{DISPATCH_AGENT_URL}/dispatch",
            json={
                "intent": intent,
                "entities": entities,
                "insurance_decision": insurance_decision,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error(f"Dispatch AI Agent call failed: {e}")
        return {"status": "failed", "error": str(e)}


def format_response(intent: str, insurance: dict, dispatch: dict) -> str:
    lines = []
    lines.append("🚨 *EMERGENCY RESPONSE ACTIVATED*")
    lines.append("")

    lines.append("📋 *Insurance Check:*")
    if insurance.get("is_covered"):
        lines.append(f"  ✅ Covered — {insurance.get('coverage_type', 'N/A')}")
        lines.append(f"  💰 Limit: {insurance.get('coverage_limit', 'N/A')}")
        copay = insurance.get("copay_percentage", 0)
        if copay > 0:
            lines.append(f"  📊 Copay: {copay}%")
    else:
        lines.append(f"  ❌ Not Covered — {insurance.get('reason', 'N/A')}")
        if insurance.get("upgrade_suggestion"):
            lines.append(f"  💡 {insurance['upgrade_suggestion']}")

    lines.append("")
    lines.append("🚑 *Emergency Dispatch:*")
    if dispatch.get("status") == "dispatched":
        lines.append(f"  📍 Dispatch ID: `{dispatch.get('dispatch_id', 'N/A')}`")
        transport = dispatch.get("transport_type", "ambulance")
        icon = "🚁" if transport == "helicopter" else "🚑"
        lines.append(f"  {icon} Unit: {dispatch.get('unit_callsign', 'N/A')} ({transport})")
        lines.append(f"  ⏱ ETA: {dispatch.get('eta_minutes', '?')} minutes")
        lines.append(f"  🏥 Hospital: {dispatch.get('hospital_name', 'N/A')}")
        lines.append(f"  📏 Distance: {dispatch.get('hospital_distance_km', '?')} km")
        if dispatch.get("hospital_alerted"):
            lines.append("  ✅ Hospital has been pre-alerted")
        if dispatch.get("note"):
            lines.append(f"  ⚠️ {dispatch['note']}")
    else:
        lines.append("  ❌ Dispatch failed — please call local emergency services")

    lines.append("")
    lines.append("⚠️ _This is a simulation — not connected to real emergency services._")

    return "\n".join(lines)


def format_coverage_only(insurance: dict) -> str:
    lines = []
    lines.append("📋 *Insurance Coverage Information*")
    lines.append("")
    lines.append(f"  Policy: `{insurance.get('policy_id', 'N/A')}`")
    lines.append(f"  Type: {insurance.get('coverage_type', 'N/A')}")
    lines.append(f"  Limit: {insurance.get('coverage_limit', 'N/A')}")
    lines.append(f"  Copay: {insurance.get('copay_percentage', 0)}%")
    lines.append("")
    if insurance.get("restrictions"):
        lines.append("  *Conditions:*")
        for r in insurance["restrictions"]:
            lines.append(f"    • {r}")
    lines.append("")
    lines.append("⚠️ _This is a simulation — not real policy data._")
    return "\n".join(lines)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "agentic-ai"})


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    intent = data.get("intent", "unknown")
    entities = data.get("entities", {})
    confidence = data.get("confidence", 0)
    routing = data.get("routing", "agentic_ai")

    log.info(f"Processing: intent={intent}, routing={routing}, confidence={confidence}")

    if routing == "direct_response":
        msg = GREETING_RESPONSES.get(intent, "I'm here to help with insurance emergencies. Describe your situation.")
        return jsonify({"success": True, "intent": intent, "message": msg})

    if routing == "insurance_agent_only":
        insurance = call_insurance_agent(intent, entities)
        msg = format_coverage_only(insurance)
        return jsonify({"success": True, "intent": intent, "insurance": insurance, "message": msg})

    # Full emergency flow: insurance check → dispatch
    log.info("Running full emergency flow: insurance → dispatch")

    insurance = call_insurance_agent(intent, entities)
    log.info(f"Insurance result: covered={insurance.get('is_covered')}")

    dispatch = call_dispatch_agent(intent, entities, insurance)
    log.info(f"Dispatch result: status={dispatch.get('status')}")

    msg = format_response(intent, insurance, dispatch)

    return jsonify({
        "success": True,
        "intent": intent,
        "insurance": insurance,
        "dispatch": dispatch,
        "message": msg,
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    log.info(f"Agentic AI starting on port {port}")
    app.run(host="0.0.0.0", port=port)
