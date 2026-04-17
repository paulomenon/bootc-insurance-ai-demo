import os


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")
AGENTIC_AI_URL = os.getenv("AGENTIC_AI_URL", "http://localhost:8002")
INSURANCE_AI_AGENT_URL = os.getenv("INSURANCE_AI_AGENT_URL", "http://localhost:8003")
OPERATOR_AGENT_URL = os.getenv("OPERATOR_AGENT_URL", "http://localhost:8004")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
