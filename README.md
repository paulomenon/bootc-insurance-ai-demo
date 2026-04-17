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
| Operator Agent | 8004 | Auto-connects to nearest hospital for emergencies, appointments, and dispatch |
| Telegram Bot | — | Receives messages, sends responses |

---

## Use Case Scenario

A user messages the Telegram bot:

> "I had a ski accident in the Alps, I need an ambulance"

The system:

1. Detects the intent (emergency ambulance request)
2. Extracts entities (location: alps, activity: skiing, transport: ambulance)
3. Checks insurance coverage via the **Insurance AI Agent** (ambulance covered under standard plan)
4. The **Operator Agent** auto-connects to the nearest hospital, dispatches an ambulance, and pre-alerts the facility
5. Returns a formatted response with coverage details, hospital connection, ETA, and dispatch info

Another scenario:

> "I want a helicopter"

The system:

1. Detects helicopter request intent
2. **Insurance AI Agent** checks coverage (helicopter NOT covered under standard plan)
3. **Operator Agent** falls back to ground ambulance, auto-connects to nearest hospital
4. Returns response explaining coverage denial + ambulance dispatch with hospital connection

---

## How the Operator Agent Works

The **Operator Agent** is the system's operations hub. After the **Agentic AI** receives a response from the **Insurance AI Agent** confirming (or denying) coverage, it forwards the request to the Operator Agent.

The Operator Agent automatically:

1. **Locates the nearest hospital** — uses the user's location (alps, mountain, city, beach) to find the closest medical facility from its database
2. **Dispatches emergency help** — for emergencies, it dispatches an ambulance or helicopter, generates a unit callsign, calculates an ETA based on severity, and pre-alerts the hospital
3. **Books appointments** — for non-emergency requests, it connects to the nearest hospital that accepts appointments and books a slot
4. **Handles fallbacks** — if the insurance check says helicopter is not covered, the Operator Agent automatically falls back to a ground ambulance

**Flow:**

```
User message → Dummy LLM (intent) → Agentic AI
                                        │
                                        ├──▶ Insurance AI Agent (is it covered?)
                                        │         │
                                        │         ▼
                                        ├──▶ Operator Agent (connect to hospital, dispatch help)
                                        │         │
                                        ▼         ▼
                                    Merge results → Telegram response
```

The Operator Agent endpoint is `/operate` (POST) — it receives the intent, entities, and the insurance decision, then returns the full operation result including hospital name, distance, ETA, unit callsign, and connection status.

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
│  │  AI Agent            │              │  Operator          │    │
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
                                   Insurance AI Agent   Operator Agent
                                   (check coverage)     (connect hospital)
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
| **Agentic AI** | Routes requests to the correct agents based on intent. For emergencies: calls Insurance AI Agent first (coverage check), then Operator Agent (hospital connection + dispatch), then merges results. For greetings: responds directly |
| **Insurance AI Agent** | Checks mock policy rules. Ambulance is covered (10% copay, €50k limit). Helicopter is NOT covered on standard plan (suggests upgrade). Activity and location coverage checks included |
| **Operator Agent** | Automatically locates and connects to the nearest hospital based on the user's location. Handles emergencies (ambulance/helicopter dispatch, hospital pre-alert, ETA), appointments (auto-booking at nearest available facility), and general help requests. Receives the insurance decision from the Agentic AI and acts accordingly — if helicopter is not covered, falls back to ground ambulance |

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
| `INSURANCE_AI_AGENT_URL` | No | `http://localhost:8003` | Insurance AI Agent URL |
| `OPERATOR_AGENT_URL` | No | `http://localhost:8004` | Operator Agent URL |
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
│   ├── agentic-ai/            # Agentic AI — coordinates agents + builds responses
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── insurance-ai-agent/    # Insurance AI Agent — policy coverage checks
│   │   ├── app.py
│   │   └── requirements.txt
│   └── operator-agent/        # Operator Agent — hospital connection, dispatch, appointments
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
PORT=8003 python services/insurance-ai-agent/app.py

# Terminal 3: Operator Agent
PORT=8004 python services/operator-agent/app.py

# Terminal 4: Agentic AI
PORT=8002 INSURANCE_AI_AGENT_URL=http://localhost:8003 OPERATOR_AGENT_URL=http://localhost:8004 python services/agentic-ai/app.py

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
oc -n bootc-insurance-ai start-build operator-agent
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
  --build-arg SERVICE_NAME=insurance-ai-agent --build-arg SERVICE_PORT=8003 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/operator-agent:latest \
  --build-arg SERVICE_NAME=operator-agent --build-arg SERVICE_PORT=8004 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/agentic-ai:latest \
  --build-arg SERVICE_NAME=agentic-ai --build-arg SERVICE_PORT=8002 \
  -f Containerfile.service .

podman build -t bootc-insurance-ai/telegram-bot:latest \
  --build-arg SERVICE_NAME=telegram-bot --build-arg SERVICE_PORT=8005 \
  -f Containerfile.service .

# Load images into Kind cluster
for img in dummy-llm insurance-agent operator-agent agentic-ai telegram-bot; do
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
curl http://localhost:8004/health   # Operator Agent
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
| "I had a ski accident in the Alps, I need an ambulance" | Full flow — insurance approved, Operator Agent connects to nearest hospital, ambulance dispatched |
| "I want a helicopter" | Insurance denies helicopter, Operator Agent falls back to ambulance, connects to nearest hospital |
| "Is my policy covering helicopter transport?" | Coverage inquiry — shows policy details |
| "I fell while hiking and I'm bleeding badly" | Emergency flow with high severity, Operator Agent dispatches ambulance to nearest hospital |

---

## Expected Telegram Responses

### Ambulance Request (Covered)

```
🚨 EMERGENCY RESPONSE ACTIVATED

📋 Insurance Check:
  ✅ Covered — Emergency Ground Transport
  💰 Limit: €50,000 per incident
  📊 Copay: 10%

🏥 Operator Agent — Hospital Connection:
  📍 Operation ID: OP-20260416-A3F2B1
  🚑 Unit: ALPHA-07 (ambulance)
  ⏱ ETA: 12 minutes
  🏥 Hospital: Zermatt Medical Center
  📏 Distance: 3.2 km
  ✅ Connected to hospital
  ✅ Hospital has been pre-alerted

⚠️ This is a simulation — not connected to real emergency services.
```

### Helicopter Request (Not Covered)

```
🚨 EMERGENCY RESPONSE ACTIVATED

📋 Insurance Check:
  ❌ Not Covered — Helicopter transport is not covered under your current Standard plan
  💡 Upgrade to Premium plan (€29.99/month) for helicopter coverage up to €100,000

🏥 Operator Agent — Hospital Connection:
  📍 Operation ID: OP-20260416-7B1C4E
  🚑 Unit: BRAVO-23 (ambulance)
  ⏱ ETA: 15 minutes
  🏥 Hospital: Innsbruck University Hospital
  📏 Distance: 12.5 km
  ✅ Hospital has been pre-alerted
  ⚠️ Helicopter not covered by insurance — dispatching ground ambulance instead
  ✅ Connected to hospital

⚠️ This is a simulation — not connected to real emergency services.
```

---

## How Services Communicate

All communication is via **HTTP REST calls** over the internal container network:

```
Telegram Bot  ──POST /analyze──▶  Dummy LLM (:8001)
Telegram Bot  ──POST /process──▶  Agentic AI (:8002)
Agentic AI    ──POST /check────▶  Insurance AI Agent (:8003)
Agentic AI    ──POST /operate──▶  Operator Agent (:8004)
```

| Endpoint | Method | Service | Description |
|---|---|---|---|
| `/health` | GET | All services | Health check |
| `/analyze` | POST | Dummy LLM | Analyze message text, return intent + entities |
| `/process` | POST | Agentic AI | Full workflow: route to agents, build response |
| `/check` | POST | Insurance AI Agent | Check policy coverage for given intent + entities |
| `/operate` | POST | Operator Agent | Auto-connect to nearest hospital, dispatch emergency help or book appointment |

---

## Disclaimer

This project is a **technical demonstration only**. It is not connected to any real emergency services, insurance systems, or medical infrastructure. All data, policy rules, hospital names, and operator connections are entirely fictional.

**In a real emergency, always call your local emergency number (112 in Europe, 911 in the US).**
