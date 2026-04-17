#!/bin/bash
set -e

echo "=============================================="
echo "  Bootable Container AI Demo"
echo "  Insurance Emergency Response System"
echo "=============================================="
echo ""
echo "Starting services via supervisor (systemd-style)..."
echo ""
echo "  [1] Dummy LLM Service        → :8001"
echo "  [2] Agentic AI                → :8002"
echo "  [3] Insurance Coverage AI Agent  → :8003"
echo "  [4] Emergency Dispatch AI Agent  → :8004"
echo "  [5] Telegram Bot              → polling"
echo ""

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "WARNING: TELEGRAM_BOT_TOKEN is not set."
    echo "The Telegram bot will not be able to connect."
    echo "Set it with: -e TELEGRAM_BOT_TOKEN=your-token"
    echo ""
fi

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
