# 🛡️ wazuh-whatsapp-alert

Integração customizada que conecta o **Wazuh SIEM** ao **WhatsApp** via Twilio (ou Evolution API).

Quando um alerta de segurança é detectado com nível de criticidade igual ou acima do configurado, uma mensagem formatada é enviada automaticamente para o WhatsApp — sem polling, sem cron job, sem painel aberto.

---

## 📱 Exemplo de mensagem recebida

```
⚠️ ALERTA WAZUH
━━━━━━━━━━━━━━━━━━
🔔 Severidade: 🔴 CRÍTICO (nível 13)
📋 Regra: 5712 — SSH brute force
🖥️ Agente: db-server (192.168.1.50)
🏷️ Grupos: authentication_failed, ssh
🌐 IP Origem: 203.0.113.42
🕐 2024-01-01T14:24:37Z
━━━━━━━━━━━━━━━━━━
```

---

## 🏗️ Arquitetura

```
Wazuh Manager
     │
     │  (evento detectado, nível >= 7)
     ▼
custom-whatsapp.py   ←── /var/ossec/integrations/
     │
     │  (POST via REST API)
     ▼
Twilio WhatsApp API
     │
     ▼
📱 WhatsApp
```

---

## ⚙️ Pré-requisitos

- Wazuh Manager instalado e rodando
- Python 3.8+
- Conta no [Twilio](https://www.twilio.com) (sandbox gratuita disponível)  
  **ou** instância da [Evolution API](https://github.com/EvolutionAPI/evolution-api) (self-hosted)

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/wazuh-whatsapp-alert.git
cd wazuh-whatsapp-alert
```

### 2. Instale as dependências

```bash
# Para Twilio
pip3 install twilio

# Para Evolution API
pip3 install requests
```

Ou instale tudo de uma vez:

```bash
pip3 install -r requirements.txt
```

### 3. Configure o script

Abra o arquivo `custom-whatsapp.py` e edite a seção de configurações no topo:

```python
MIN_LEVEL = 7               # nível mínimo para disparar (7=médio, 10=alto, 13=crítico)
PROVIDER  = "twilio"        # "twilio" ou "evolution"

# Twilio
TWILIO_ACCOUNT_SID = "ACxxxx..."
TWILIO_AUTH_TOKEN  = "xxxx..."
TWILIO_FROM        = "whatsapp:+14155238886"
TWILIO_TO          = "whatsapp:+5511999999999"
```

### 4. Copie para o Wazuh e ajuste permissões

```bash
sudo cp custom-whatsapp.py /var/ossec/integrations/custom-whatsapp
sudo chmod 750 /var/ossec/integrations/custom-whatsapp
sudo chown root:wazuh /var/ossec/integrations/custom-whatsapp
```

### 5. Configure o ossec.conf

Abra `/var/ossec/etc/ossec.conf` e adicione dentro de `<ossec_config>`:

```xml
<integration>
  <name>custom-whatsapp</name>
  <level>7</level>
  <alert_format>json</alert_format>
</integration>
```

> **Dica:** Para filtrar por grupo de regra (ex: só alertas de SSH):
> ```xml
> <integration>
>   <name>custom-whatsapp</name>
>   <level>10</level>
>   <group>sshd</group>
>   <alert_format>json</alert_format>
> </integration>
> ```

### 6. Reinicie o Wazuh Manager

```bash
sudo systemctl restart wazuh-manager
```

---

## 🧪 Testando manualmente

Antes de configurar no Wazuh, teste o script diretamente com o arquivo de exemplo:

```bash
python3 custom-whatsapp.py test_alert.json
```

Se a configuração estiver correta, a mensagem chegará no WhatsApp em menos de 1 segundo.

---

## 🔧 Personalização

| O que mudar | Onde |
|---|---|
| Nível mínimo de criticidade | `MIN_LEVEL` no topo do script |
| Provedor de envio | `PROVIDER = "twilio"` ou `"evolution"` |
| Múltiplos destinatários | Duplicar o bloco `<integration>` no `ossec.conf` com `TWILIO_TO` diferentes |
| Formato da mensagem | Função `format_message()` |

---

## 📊 Níveis de criticidade do Wazuh

| Nível | Severidade | Emoji |
|---|---|---|
| 1 – 6 | Baixo / Informativo | 🟢 ignorado |
| 7 – 9 | Médio | 🟡 |
| 10 – 12 | Alto | 🟠 |
| 13 – 15 | Crítico | 🔴 |

---

## 📁 Estrutura do repositório

```
wazuh-whatsapp-alert/
├── custom-whatsapp.py   # script principal
├── test_alert.json      # alerta de exemplo para testes
├── requirements.txt     # dependências Python
└── README.md
```

---

## 📄 Licença

MIT License — use, modifique e distribua à vontade.

---

## 🤝 Contribuições

Pull requests são bem-vindos! Sugestões de melhorias:

- Suporte a múltiplos números por criticidade
- Templates de mensagem configuráveis
- Integração com outros canais (Telegram, Teams, Slack)
