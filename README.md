# Bootable Container AI Demo — Insurance Emergency System

A **bootable container-based AI demo** that simulates an insurance company emergency response workflow via Telegram. Built with a multi-agent architecture running inside a single bootable container or as distributed microservices.

> **This is a simulation system only.** No real emergency services, no real medical decisions, no real LLM. Everything is mock/fictional logic designed to demonstrate architecture patterns.

---

## What Is a Bootable Container?

A **bootable container** (inspired by Red Hat's image mode / bootc concept) is an OS-level container image that packages an entire system — not just one application, but a full set of services, process management, and configuration — into a single immutable image.

Think of it as:

```
Traditional container:  1 image = 1 process
Bootable container:     1 image = entire system (multiple services, managed like an OS)
```

In this project, the bootable container runs **5 services** managed by `supervisord` (simulating systemd-style process management):

| Service | Port | Role |
|---|---|---|
| Dummy LLM | 8001 | Intent detection and entity extraction |
| Agentic AI | 8002 | Coordinates agents, builds responses |
| Insurance AI Agent | 8003 | Checks policy coverage |
| Dispatch AI Agent | 8004 | Simulates ambulance/helicopter dispatch |
| Telegram Bot | — | Receives messages, sends responses |

---

## Use Case Scenario

A user messages the Telegram bot:

> "I had a ski accident in the Alps, I need an ambulance"

The system:

1. Detects the intent (emergency ambulance request)
2. Extracts entities (location: alps, activity: skiing, transport: ambulance)
3. Checks insurance coverage (ambulance covered under standard plan)
4. Dispatches an ambulance to the nearest hospital
5. Returns a formatted response with coverage details, dispatch info, ETA, and hospital name

Another scenario:

> "I want a helicopter"

The system:

1. Detects helicopter request intent
2. Checks insurance (helicopter NOT covered under standard plan)
3. Falls back to ambulance dispatch
4. Returns response explaining coverage denial + ambulance dispatch instead

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BOOTABLE CONTAINER                               │
│                    (supervisord / systemd-style)                     │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐    │
│  │              │    │              │    │                    │    │
│  │  Telegram    │───▶│  Dummy LLM   │    │   Agentic AI       │    │
│  │  Bot         │    │  Service     │    │                    │    │
│  │              │    │  :8001       │    │   :8002            │    │
│  └──────┬───────┘    └──────────────┘    └─────┬──────┬──────┘    │
│         │                                      │      │           │
│         │            ┌─────────────────────────┘      │           │
│         │            │                                │           │
│         ▼            ▼                                ▼           │
│  ┌──────────────────────┐              ┌────────────────────┐    │
│  │                      │              │                    │    │
│  │  Insurance Coverage  │              │  Emergency         │    │
│  │  AI Agent            │              │  Dispatch AI Agent │    │
│  │  :8003               │              │  :8004             │    │
│  │                      │              │                    │    │
│  └──────────────────────┘              └────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Flow

```
User (Telegram) → Bot → Dummy LLM (analyze) → Agentic AI (coordinate)
                                                    │
                                          ┌─────────┴─────────┐
                                          ▼                   ▼
                                   Insurance AI Agent   Dispatch AI Agent
                                   (check coverage)     (send ambulance)
                                          │                   │
                                          └─────────┬─────────┘
                                                    ▼
                                            Response Builder
                                                    │
                                                    ▼
                                          User (Telegram reply)
```

### Component Details

| Component | What It Does |
|---|---|
| **Telegram Bot** | Long-polls the Telegram API for messages, sends them through the pipeline, returns formatted responses |
| **Dummy LLM** | Pattern-based intent detection (no real AI). Classifies messages as emergency_ambulance, emergency_helicopter, coverage_inquiry, or greeting. Extracts entities: location, activity, transport type, severity |
| **Agentic AI** | Routes requests to the correct agents based on intent. For emergencies: calls Insurance AI Agent first, then Dispatch AI Agent, then merges results. For greetings: responds directly |
| **Insurance AI Agent** | Checks mock policy rules. Ambulance is covered (10% copay, €50k limit). Helicopter is NOT covered on standard plan (suggests upgrade). Activity and location coverage checks included |
| **Dispatch AI Agent** | Simulates emergency dispatch. Selects nearest hospital from a mock database. Generates ETA, unit callsign, dispatch ID. Pre-alerts the hospital. Falls back to ambulance if helicopter isn't covered |

---

## Prerequisites

### Python

```bash
python3 --version   # 3.10 or higher
```

### Podman (for container deployment)

```bash
# macOS
brew install podman-desktop
podman machine init && podman machine start

# Verify
podman --version
```

### Telegram Bot Token

You need a Telegram bot token from **BotFather**:

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name (e.g. "Insurance AI Demo")
4. Choose a username (must end in `bot`, e.g. `insurance_ai_demo_bot`)
5. BotFather gives you a token like: `7123456789:AAH...`
6. Save this token — you'll need it for the `TELEGRAM_BOT_TOKEN` env var

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Token from BotFather |
| `LLM_SERVICE_URL` | No | `http://localhost:8001` | Dummy LLM service URL |
| `AGENTIC_AI_URL` | No | `http://localhost:8002` | Agentic AI service URL |
| `INSURANCE_AGENT_URL` | No | `http://localhost:8003` | Insurance agent URL |
| `DISPATCH_AGENT_URL` | No | `http://localhost:8004` | Dispatch agent URL |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## Project Structure

```
bootc-insurance-ai-demo/
├── Containerfile              # Bootable container (all services + supervisor)
├── Containerfile.service      # Individual service image (for microservices mode)
├── supervisord.conf           # Process manager config (systemd-style)
├── entrypoint.sh              # Startup script
├── .env.example               # Environment variable template
│
├── shared/                    # Shared utilities
│   ├── config.py              # Environment-based configuration
│   ├── models.py              # Data models (dataclasses)
│   └── logger.py              # Structured logging
│
├── services/
│   ├── telegram-bot/          # Telegram integration (polling)
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── dummy-llm/             # Intent detection + entity extraction
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── orchestrator/          # Agentic AI — coordinates agents + builds responses
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── insurance-agent/       # Policy coverage checks
│   │   ├── app.py
│   │   └── requirements.txt
│   └── dispatch-agent/        # Emergency dispatch simulation
│       ├── app.py
│       └── requirements.txt
│
├── deploy/
│   ├── podman/                # Podman Compose files
│   │   ├── bootc-single.yml   # Single bootable container
│   │   └── microservices.yml  # Separate service containers
│   ├── openshift/             # OpenShift manifests (BuildConfig + ImageStream)
│   │   └── bootc-insurance-ai.yml
│   └── kubernetes/            # Kubernetes manifests
│       └── bootc-insurance-ai.yml
│
└── README.md
```

---

## Setup & Running

### Option 1: Bootable Container (Single Container — Recommended)

This runs all 5 services inside one container, managed by supervisord.

```bash
# Build the bootable container image
podman build -t bootc-insurance-ai .

# Run with your Telegram bot token
podman run -d \
  --name bootc-insurance-ai \
  -p 8001:8001 \
  -p 8002:8002 \
  -p 8003:8003 \
  -p 8004:8004 \
  -e TELEGRAM_BOT_TOKEN=your-token-here \
  bootc-insurance-ai
```

Or with Podman Compose:

```bash
cd deploy/podman
TELEGRAM_BOT_TOKEN=your-token-here podman-compose -f bootc-single.yml up -d
```

### Option 2: Microservices (Separate Containers)

Each service runs in its own container, communicating over a Podman network.

```bash
cd deploy/podman
TELEGRAM_BOT_TOKEN=your-token-here podman-compose -f microservices.yml up -d
```

### Option 3: Run Locally Without Containers

```bash
# Install dependencies
pip install flask requests

# Terminal 1: Dummy LLM
PORT=8001 python services/dummy-llm/app.py

# Terminal 2: Insurance AI Agent
PORT=8003 python services/insurance-agent/app.py

# Terminal 3: Dispatch AI Agent
PORT=8004 python services/dispatch-agent/app.py

# Terminal 4: Agentic AI
PORT=8002 INSURANCE_AGENT_URL=http://localhost:8003 DISPATCH_AGENT_URL=http://localhost:8004 python services/orchestrator/app.py  # Agentic AI

# Terminal 5: Telegram Bot
TELEGRAM_BOT_TOKEN=your-token LLM_SERVICE_URL=http://localhost:8001 AGENTIC_AI_URL=http://localhost:8002 python services/telegram-bot/app.py
```

---

## Deploying to OpenShift

```bash
# Log in to your cluster
oc login -u developer -p developer https://api.crc.testing:6443

# Apply all resources (namespace, builds, deployments, services, routes)
oc apply -f deploy/openshift/bootc-insurance-ai.yml

# Update the Telegram bot token secret
oc -n bootc-insurance-ai create secret generic telegram-bot-token \
  --from-literal=TELEGRAM_BOT_TOKEN=your-actual-token \
  --dry-run=client -o yaml | oc apply -f -

# Start builds for all services
oc -n bootc-insurance-ai start-build dummy-llm
oc -n bootc-insurance-ai start-build insurance-agent
oc -n bootc-insurance-ai start-build dispatch-agent
oc -n bootc-insurance-ai start-build agentic-ai
oc -n bootc-insurance-ai start-build telegram-bot

# Watch the builds
oc -n bootc-insurance-ai get builds -w

# Check pods
oc -n bootc-insurance-ai get pods

# Get the Agentic AI route (for external API access)
oc -n bootc-insurance-ai get route agentic-ai
```

---

## Deploying to Kubernetes

```bash
# Build all service images
podman build -t bootc-insurance-ai/dummy-llm:latest \
  --build-arg SERVICE_NAME=dummy-llm --build-arg SERVICE_PORT=8001 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/insurance-agent:latest \
  --build-arg SERVICE_NAME=insurance-agent --build-arg SERVICE_PORT=8003 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/dispatch-agent:latest \
  --build-arg SERVICE_NAME=dispatch-agent --build-arg SERVICE_PORT=8004 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/agentic-ai:latest \
  --build-arg SERVICE_NAME=orchestrator --build-arg SERVICE_PORT=8002 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/telegram-bot:latest \
  --build-arg SERVICE_NAME=telegram-bot --build-arg SERVICE_PORT=8005 \
  -f Containerfile.service .

# Load images into Kind cluster
for img in dummy-llm insurance-agent dispatch-agent agentic-ai telegram-bot; do
  kind load docker-image bootc-insurance-ai/$img:latest --name python-samples
done

# Update the secret with your real token
kubectl -n bootc-insurance-ai create secret generic telegram-bot-token \
  --from-literal=TELEGRAM_BOT_TOKEN=your-actual-token \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply manifests
kubectl apply -f deploy/kubernetes/bootc-insurance-ai.yml

# Check status
kubectl -n bootc-insurance-ai get pods
kubectl -n bootc-insurance-ai get services
```

---

## How to Test

### Test 1: Health Checks

```bash
# Check all services are running
curl http://localhost:8001/health   # Dummy LLM
curl http://localhost:8002/health   # Agentic AI
curl http://localhost:8003/health   # Insurance AI Agent
curl http://localhost:8004/health   # Dispatch AI Agent
```

### Test 2: Ambulance Request (Covered)

Send this via Telegram or curl:

```bash
# Via curl (directly to the LLM)
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I had a ski accident in the Alps, I need an ambulance"}'
```

Expected LLM response:

```json
{
  "intent": "emergency_ambulance",
  "confidence": 0.73,
  "entities": {
    "location": "alps",
    "activity": "skiing",
    "requested_transport": "ambulance",
    "severity": "medium"
  },
  "routing": "agentic_ai"
}
```

Full flow via Agentic AI:

```bash
curl -X POST http://localhost:8002/process \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "emergency_ambulance",
    "confidence": 0.73,
    "entities": {
      "location": "alps",
      "activity": "skiing",
      "requested_transport": "ambulance",
      "severity": "medium"
    },
    "routing": "agentic_ai"
  }'
```

### Test 3: Helicopter Request (NOT Covered)

```bash
curl -X POST http://localhost:8002/process \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "emergency_helicopter",
    "confidence": 0.85,
    "entities": {
      "location": "alps",
      "activity": "skiing",
      "requested_transport": "helicopter",
      "severity": "high"
    },
    "routing": "agentic_ai"
  }'
```

### Test 4: Via Telegram

Send these messages to your bot:

| Message | Expected Behavior |
|---|---|
| "Hello" | Greeting response with available commands |
| "I had a ski accident in the Alps, I need an ambulance" | Full emergency flow — ambulance dispatched, insurance approved |
| "I want a helicopter" | Helicopter denied (not covered), ambulance dispatched as fallback |
| "Is my policy covering helicopter transport?" | Coverage inquiry — shows policy details |
| "I fell while hiking and I'm bleeding badly" | Emergency flow with high severity, ambulance dispatched |

---

## Expected Telegram Responses

### Ambulance Request (Covered)

```
🚨 EMERGENCY RESPONSE ACTIVATED

📋 Insurance Check:
  ✅ Covered — Emergency Ground Transport
  💰 Limit: €50,000 per incident
  📊 Copay: 10%

🚑 Emergency Dispatch:
  📍 Dispatch ID: DSP-20260416-A3F2B1
  🚑 Unit: ALPHA-07 (ambulance)
  ⏱ ETA: 12 minutes
  🏥 Hospital: Zermatt Medical Center
  📏 Distance: 3.2 km
  ✅ Hospital has been pre-alerted

⚠️ This is a simulation — not connected to real emergency services.
```

### Helicopter Request (Not Covered)

```
🚨 EMERGENCY RESPONSE ACTIVATED

📋 Insurance Check:
  ❌ Not Covered — Helicopter transport is not covered under your current Standard plan
  💡 Upgrade to Premium plan (€29.99/month) for helicopter coverage up to €100,000

🚑 Emergency Dispatch:
  📍 Dispatch ID: DSP-20260416-7B1C4E
  🚑 Unit: BRAVO-23 (ambulance)
  ⏱ ETA: 15 minutes
  🏥 Hospital: Innsbruck University Hospital
  📏 Distance: 12.5 km
  ✅ Hospital has been pre-alerted
  ⚠️ Helicopter not covered by insurance — dispatching ground ambulance instead

⚠️ This is a simulation — not connected to real emergency services.
```

---

## How Services Communicate

All communication is via **HTTP REST calls** over the internal container network:

```
Telegram Bot  ──POST /analyze──▶  Dummy LLM (:8001)
Telegram Bot  ──POST /process──▶  Agentic AI (:8002)
Agentic AI    ──POST /check────▶  Insurance AI Agent (:8003)
Agentic AI    ──POST /dispatch─▶  Dispatch AI Agent (:8004)
```

| Endpoint | Method | Service | Description |
|---|---|---|---|
| `/health` | GET | All services | Health check |
| `/analyze` | POST | Dummy LLM | Analyze message text, return intent + entities |
| `/process` | POST | Agentic AI | Full workflow: route to agents, build response |
| `/check` | POST | Insurance AI Agent | Check policy coverage for given intent + entities |
| `/dispatch` | POST | Dispatch AI Agent | Dispatch emergency transport |

---

## Disclaimer

This project is a **technical demonstration only**. It is not connected to any real emergency services, insurance systems, or medical infrastructure. All data, policy rules, hospital names, and dispatch information are entirely fictional.

**In a real emergency, always call your local emergency number (112 in Europe, 911 in the US).**
