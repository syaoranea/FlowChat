# 📋 Instruções de Deploy na Vercel - FlowChat

## 🔴 Problemas Identificados

### 1. Firebase - Erro "File name too long"
**Causa:** O código estava tentando usar o JSON das credenciais como nome de arquivo.

**Solução:** Agora o sistema aceita as credenciais Firebase de duas formas:
- `FIREBASE_CREDENTIALS_PATH`: Caminho para arquivo (desenvolvimento local)
- `FIREBASE_CREDENTIALS_JSON`: JSON completo das credenciais (recomendado para Vercel)

### 2. Modo MOCK ativado
**Causa:** Como o Firebase não inicializava, o sistema entrava em modo MOCK.

**Solução:** Com a correção acima, o Firebase inicializará corretamente.

### 3. Mensagens não enviadas via Twilio
**Causa:** O webhook está retornando TwiML corretamente, mas o Twilio precisa de:
- Credenciais válidas configuradas
- Número de WhatsApp verificado
- Conta Twilio em modo produção ou sandbox configurado

---

## 🔧 Configuração das Variáveis de Ambiente na Vercel

### Passo 1: Obter credenciais do Firebase

1. Acesse o [Firebase Console](https://console.firebase.google.com/)
2. Selecione seu projeto `flowchat-72383`
3. Vá em **Configurações do Projeto** (⚙️) → **Contas de serviço**
4. Clique em **"Gerar nova chave privada"**
5. Baixe o arquivo JSON

### Passo 2: Preparar o JSON para a Vercel

O JSON baixado terá este formato:
```json
{
  "type": "service_account",
  "project_id": "flowchat-72383",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxx@flowchat-72383.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

**IMPORTANTE:** Converta para uma única linha antes de colar na Vercel:
- Abra o arquivo JSON
- Remova todas as quebras de linha (deve ficar tudo em uma linha)
- Ou use este comando no terminal:
  ```bash
  cat firebase-credentials.json | tr -d '\n' | pbcopy  # Mac
  cat firebase-credentials.json | tr -d '\n' | xclip   # Linux
  ```

### Passo 3: Configurar variáveis na Vercel

Acesse: https://vercel.com/dashboard → Seu projeto → Settings → Environment Variables

Configure as seguintes variáveis:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `FIREBASE_PROJECT_ID` | `flowchat-72383` | ID do projeto Firebase |
| `FIREBASE_CREDENTIALS_JSON` | `{"type":"service_account",...}` | JSON completo em uma linha |
| `TWILIO_ACCOUNT_SID` | `ACxxxxxxxxxxxxxxx` | Account SID do Twilio |
| `TWILIO_AUTH_TOKEN` | `xxxxxxxxxxxxxxxx` | Auth Token do Twilio |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` | Número do WhatsApp Sandbox |
| `COMPANY_NAME` | `Sua Empresa` | Nome da empresa |
| `LOG_LEVEL` | `INFO` | Nível de log |

### Passo 4: Configurar Twilio

1. Acesse o [Twilio Console](https://console.twilio.com/)
2. Vá para **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Configure o **Sandbox**:
   - Webhook URL: `https://flow-chat-omega.vercel.app/webhook/whatsapp`
   - HTTP Method: `POST`

4. Para testar, envie a mensagem de ativação do sandbox para o número do Twilio

---

## 🚀 Deploy das Correções

### Opção 1: Via GitHub (Recomendado)

```bash
git add .
git commit -m "fix: Firebase credentials JSON support for Vercel"
git push origin main
```

A Vercel fará o deploy automaticamente.

### Opção 2: Via Vercel CLI

```bash
npm i -g vercel
vercel --prod
```

---

## ✅ Verificação

Após o deploy, teste com:

```bash
curl -X POST https://flow-chat-omega.vercel.app/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+5511999999999&Body=oi"
```

Deve retornar um XML TwiML válido:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>👋 Olá! Seja bem-vindo(a) à...</Message>
</Response>
```

---

## 📝 Resumo das Mudanças

### Arquivos Modificados:

1. **`app/config.py`**
   - Adicionada variável `firebase_credentials_json`

2. **`app/services/firebase_service.py`**
   - Método `_initialize_firebase()` agora:
     - Prioriza `FIREBASE_CREDENTIALS_JSON` (para Vercel)
     - Fallback para `FIREBASE_CREDENTIALS_PATH` (local)
     - Fallback para credenciais padrão do ambiente

3. **`.env.example`**
   - Documentação atualizada com ambas opções

---

## 🔍 Troubleshooting

### Firebase ainda não funciona
- Verifique se o JSON está em uma única linha
- Certifique-se de que não há caracteres extras (espaços, aspas duplicadas)
- Verifique os logs na Vercel: `vercel logs` ou no dashboard

### Twilio não envia mensagens
- Verifique se o número está conectado ao sandbox
- Confirme que o `TWILIO_WHATSAPP_FROM` é o número correto
- Teste a API do Twilio diretamente pelo console

### Erro 500 no webhook
- Verifique os logs da Vercel
- Certifique-se de que todas as variáveis estão configuradas
