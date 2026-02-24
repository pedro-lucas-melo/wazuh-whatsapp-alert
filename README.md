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
     │  (evento detectado, nível >= MIN_LEVEL)
     ▼
custom-whatsapp.py   ←── lê credenciais do .env
     │
     │  (POST via REST API)
     ▼
Twilio WhatsApp API
     │
     ▼
📱 WhatsApp
```

---

## 📁 Estrutura do repositório

```
wazuh-whatsapp-alert/
├── custom-whatsapp.py   # script principal (não editar)
├── .env.example         # modelo de configuração
├── .gitignore           # protege o .env real de subir ao GitHub
├── test_alert.json      # alerta de exemplo para testes
├── requirements.txt     # dependências Python
└── README.md
```

> ⚠️ O arquivo `.env` com suas credenciais reais **nunca sobe para o GitHub** — o `.gitignore` cuida disso automaticamente.

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
pip3 install -r requirements.txt
```

### 3. Configure o arquivo .env

Copie o modelo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Abra o `.env` e edite:

```env
MIN_LEVEL=7
PROVIDER=twilio

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM=whatsapp:+14155238886
TWILIO_TO=whatsapp:+5511999999999
```

> As credenciais do Twilio ficam no painel: https://console.twilio.com

### 4. Copie para o Wazuh e ajuste permissões

```bash
sudo cp custom-whatsapp.py /var/ossec/integrations/custom-whatsapp
sudo cp .env /var/ossec/integrations/.env
sudo chmod 750 /var/ossec/integrations/custom-whatsapp
sudo chown root:wazuh /var/ossec/integrations/custom-whatsapp
sudo chown root:wazuh /var/ossec/integrations/.env
```

### 5. Configure o ossec.conf

Abra `/var/ossec/etc/ossec.conf` e adicione dentro de `<ossec_config>`:

```xml
<integration>
  <n>custom-whatsapp</n>
  <level>7</level>
  <alert_format>json</alert_format>
</integration>
```

> **Dica:** Para filtrar por grupo de regra (ex: só alertas de SSH):
> ```xml
> <integration>
>   <n>custom-whatsapp</n>
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

```bash
python3 custom-whatsapp.py test_alert.json
```

Se o `.env` estiver configurado corretamente, a mensagem chegará no WhatsApp em menos de 1 segundo.

---

## 🔧 Personalizações disponíveis no .env

| Variável | Descrição | Padrão |
|---|---|---|
| `MIN_LEVEL` | Nível mínimo para disparar | `7` |
| `PROVIDER` | Provedor de envio | `twilio` |
| `TWILIO_TO` | Número de destino | — |
| `EVOLUTION_INSTANCE` | Nome da instância Evolution | — |

Para enviar para múltiplos números, duplique o bloco `<integration>` no `ossec.conf` com instâncias diferentes do script.

---

## 📊 Níveis de criticidade do Wazuh

| Nível | Severidade | Emoji |
|---|---|---|
| 1 – 6 | Baixo / Informativo | 🟢 ignorado |
| 7 – 9 | Médio | 🟡 |
| 10 – 12 | Alto | 🟠 |
| 13 – 15 | Crítico | 🔴 |

---

## 📄 Licença

MIT License — use, modifique e distribua à vontade.

---

## 🤝 Contribuições

Pull requests são bem-vindos! Sugestões:

- Suporte a múltiplos números por criticidade
- Templates de mensagem configuráveis via `.env`
- Integração com outros canais (Telegram, Teams, Slack)
