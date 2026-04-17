from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class UserMessage:
    chat_id: int
    text: str
    user_name: str = "Unknown"

    def to_dict(self):
        return asdict(self)


@dataclass
class LLMResult:
    intent: str
    confidence: float
    entities: dict = field(default_factory=dict)
    routing: str = ""
    raw_text: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class InsuranceDecision:
    policy_id: str = "POL-2025-SKI-001"
    is_covered: bool = True
    coverage_type: str = ""
    coverage_limit: str = ""
    copay_percentage: int = 0
    reason: str = ""
    restrictions: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class DispatchResult:
    dispatch_id: str = ""
    transport_type: str = ""
    unit_callsign: str = ""
    eta_minutes: int = 0
    hospital_name: str = ""
    hospital_distance_km: float = 0.0
    hospital_alerted: bool = False
    coordinates: dict = field(default_factory=dict)
    status: str = "dispatched"

    def to_dict(self):
        return asdict(self)


@dataclass
class AgenticAIResponse:
    success: bool = True
    intent: str = ""
    insurance: Optional[dict] = None
    dispatch: Optional[dict] = None
    message: str = ""

    def to_dict(self):
        return asdict(self)
