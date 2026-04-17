import os


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8002")
INSURANCE_AGENT_URL = os.getenv("INSURANCE_AGENT_URL", "http://localhost:8003")
DISPATCH_AGENT_URL = os.getenv("DISPATCH_AGENT_URL", "http://localhost:8004")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
