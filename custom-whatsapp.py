#!/usr/bin/env python3
"""
wazuh-whatsapp-alert
====================
Integração customizada Wazuh → WhatsApp via Twilio (ou Evolution API).

Quando o Wazuh detecta um alerta com nível >= MIN_LEVEL, este script
é chamado automaticamente e envia uma mensagem formatada via WhatsApp.

Instalação:
  Ver README.md

Uso manual (teste):
  python3 custom-whatsapp.py test_alert.json
"""

import sys
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────
#  CARREGA VARIÁVEIS DO ARQUIVO .env
# ──────────────────────────────────────────────

def load_env():
    """Carrega o .env da mesma pasta do script."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print(f"[ERRO] Arquivo .env não encontrado em: {env_path}")
        print("       Copie o .env.example para .env e preencha suas credenciais.")
        sys.exit(1)

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

load_env()

# ──────────────────────────────────────────────
#  CONFIGURAÇÕES — lidas do .env
# ──────────────────────────────────────────────

MIN_LEVEL = int(os.environ.get("MIN_LEVEL", "7"))
PROVIDER  = os.environ.get("PROVIDER", "twilio")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM        = os.environ.get("TWILIO_FROM", "")
TWILIO_TO          = os.environ.get("TWILIO_TO", "")

EVOLUTION_API_URL  = os.environ.get("EVOLUTION_API_URL", "")
EVOLUTION_API_KEY  = os.environ.get("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "")
EVOLUTION_TO       = os.environ.get("EVOLUTION_TO", "")

# ──────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────

logging.basicConfig(
    filename="/var/ossec/logs/integrations.log",
    level=logging.INFO,
    format="%(asctime)s [wazuh-whatsapp] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  FORMATAÇÃO DA MENSAGEM
# ──────────────────────────────────────────────

def get_severity_label(level: int) -> str:
    if level >= 13:
        return "🔴 CRÍTICO"
    elif level >= 10:
        return "🟠 ALTO"
    elif level >= 7:
        return "🟡 MÉDIO"
    return "🟢 BAIXO"


def format_message(alert: dict) -> str:
    rule      = alert.get("rule", {})
    agent     = alert.get("agent", {})
    data      = alert.get("data", {})

    level       = rule.get("level", 0)
    rule_id     = rule.get("id", "N/A")
    description = rule.get("description", "Sem descrição")
    agent_name  = agent.get("name", "N/A")
    agent_ip    = agent.get("ip", "N/A")
    groups      = ", ".join(rule.get("groups", [])) or "N/A"
    timestamp   = alert.get("timestamp", datetime.utcnow().isoformat())
    src_ip      = data.get("srcip", data.get("src_ip", ""))

    src_line = f"\n🌐 *IP Origem:* {src_ip}" if src_ip else ""

    return (
        f"⚠️ *ALERTA WAZUH*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔔 *Severidade:* {get_severity_label(level)} (nível {level})\n"
        f"📋 *Regra:* {rule_id} — {description}\n"
        f"🖥️ *Agente:* {agent_name} ({agent_ip})\n"
        f"🏷️ *Grupos:* {groups}"
        f"{src_line}\n"
        f"🕐 *Horário:* {timestamp}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


# ──────────────────────────────────────────────
#  ENVIO — TWILIO
# ──────────────────────────────────────────────

def send_via_twilio(message: str) -> bool:
    try:
        from twilio.rest import Client
    except ImportError:
        logger.error("Twilio não instalado. Execute: pip3 install twilio")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM,
            to=TWILIO_TO,
        )
        logger.info(f"Mensagem enviada via Twilio — SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Erro Twilio: {e}")
        return False


# ──────────────────────────────────────────────
#  ENVIO — EVOLUTION API
# ──────────────────────────────────────────────

def send_via_evolution(message: str) -> bool:
    try:
        import requests
    except ImportError:
        logger.error("requests não instalado. Execute: pip3 install requests")
        return False

    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
    }
    payload = {
        "number": EVOLUTION_TO,
        "options": {"delay": 0},
        "textMessage": {"text": message},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Mensagem enviada via Evolution API — {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Erro Evolution API: {e}")
        return False


# ──────────────────────────────────────────────
#  DISPATCHER
# ──────────────────────────────────────────────

def send_whatsapp(message: str) -> bool:
    if PROVIDER == "twilio":
        return send_via_twilio(message)
    elif PROVIDER == "evolution":
        return send_via_evolution(message)
    else:
        logger.error(f"PROVIDER inválido: '{PROVIDER}'. Use 'twilio' ou 'evolution'.")
        return False


# ──────────────────────────────────────────────
#  PONTO DE ENTRADA
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: custom-whatsapp.py <alert_file.json>")
        sys.exit(1)

    alert_file = sys.argv[1]

    try:
        with open(alert_file, "r") as f:
            alert = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler alerta '{alert_file}': {e}")
        sys.exit(1)

    level = alert.get("rule", {}).get("level", 0)

    if level < MIN_LEVEL:
        logger.debug(f"Alerta nível {level} ignorado (mínimo: {MIN_LEVEL})")
        sys.exit(0)

    logger.info(f"Alerta nível {level} detectado — Regra {alert.get('rule', {}).get('id')}")

    message = format_message(alert)
    success = send_whatsapp(message)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
