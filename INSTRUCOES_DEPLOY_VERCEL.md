# 📋 Instruções de Deploy na Vercel - FlowChat

## 🔄 Migração: Twilio → Z-API

Este projeto agora usa **Z-API** em vez de Twilio para integração com WhatsApp.

### Por que Z-API?
- ✅ Configuração mais simples e rápida
- ✅ Usa seu próprio número de WhatsApp
- ✅ Sem necessidade de aprovação do Meta
- ✅ Sem restrição de janela de 24h
- ✅ Custo mais previsível (plano mensal)

Para detalhes sobre Z-API, veja: [INSTRUCOES_ZAPI.md](./INSTRUCOES_ZAPI.md)

---

## 🔧 Configuração das Variáveis de Ambiente na Vercel

### Passo 1: Obter credenciais do Firebase

1. Acesse o [Firebase Console](https://console.firebase.google.com/)
2. Selecione seu projeto `flowchat-72383`
3. Vá em **Configurações do Projeto** (⚙️) → **Contas de serviço**
4. Clique em **"Gerar nova chave privada"**
5. Baixe o arquivo JSON

### Passo 2: Preparar o JSON do Firebase para a Vercel

**IMPORTANTE:** Converta o JSON para uma única linha antes de colar na Vercel:

```bash
# Mac
cat firebase-credentials.json | tr -d '\n' | pbcopy

# Linux
cat firebase-credentials.json | tr -d '\n' | xclip -selection clipboard
```

### Passo 3: Obter credenciais da Z-API

1. Acesse [https://z-api.io](https://z-api.io) e faça login
2. Clique na sua instância
3. Copie o **Instance ID** e **Token** da URL da API
4. Vá em **Segurança** e copie o **Client-Token**

Veja mais detalhes em [INSTRUCOES_ZAPI.md](./INSTRUCOES_ZAPI.md)

### Passo 4: Configurar variáveis na Vercel

Acesse: https://vercel.com/dashboard → Seu projeto → Settings → Environment Variables

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `FIREBASE_PROJECT_ID` | `flowchat-72383` | ID do projeto Firebase |
| `FIREBASE_CREDENTIALS_JSON` | `{"type":"service_account",...}` | JSON completo em uma linha |
| `ZAPI_INSTANCE_ID` | `XXXXXXXXXXXX` | Instance ID da Z-API |
| `ZAPI_TOKEN` | `YYYYYYYYYYYY` | Token da Z-API |
| `ZAPI_CLIENT_TOKEN` | `ZZZZZZZZZZZZ` | Client-Token (Security Token) |
| `COMPANY_NAME` | `Sua Empresa` | Nome da empresa |
| `LOG_LEVEL` | `INFO` | Nível de log |

### Passo 5: Configurar Webhook na Z-API

1. Acesse o painel da Z-API
2. Clique na sua instância → **Webhooks**
3. Configure a URL do webhook:
   ```
   https://seu-projeto.vercel.app/webhook/whatsapp
   ```
4. Ative os eventos:
   - ✅ Mensagens recebidas (ReceivedCallback)

---

## 🚀 Deploy

### Opção 1: Via GitHub (Recomendado)

```bash
git add .
git commit -m "feat: migrate from Twilio to Z-API"
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

### 1. Testar endpoint raiz

```bash
curl https://seu-projeto.vercel.app/
```

Deve retornar:
```json
{
  "status": "online",
  "service": "WhatsApp E-commerce Chatbot",
  "version": "2.0.0",
  "provider": "Z-API"
}
```

### 2. Testar processamento de mensagem

```bash
curl -X POST https://seu-projeto.vercel.app/api/test/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511999999999", "message": "oi"}'
```

### 3. Verificar status da Z-API

```bash
curl https://seu-projeto.vercel.app/zapi/status
```

### 4. Simular webhook Z-API

```bash
curl -X POST https://seu-projeto.vercel.app/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "fromMe": false,
    "messageId": "test123",
    "text": {"message": "oi"},
    "type": "ReceivedCallback"
  }'
```

---

## 📝 Estrutura do Projeto

```
flowchat_debug/
├── main.py                      # App FastAPI principal
├── app/
│   ├── config.py                # Configurações (variáveis de ambiente)
│   ├── handlers/
│   │   ├── message_handler.py   # Processador de mensagens
│   │   ├── compras_handler.py   # Fluxo de compras
│   │   ├── orcamento_handler.py # Fluxo de orçamento
│   │   └── posvenda_handler.py  # Fluxo pós-venda
│   ├── models/
│   │   └── conversation.py      # Modelos de dados
│   └── services/
│       ├── firebase_service.py  # Serviço Firebase
│       └── zapi_service.py      # Serviço Z-API (novo!)
├── .env.example                 # Exemplo de variáveis
├── INSTRUCOES_ZAPI.md          # Instruções Z-API
└── INSTRUCOES_DEPLOY_VERCEL.md # Este arquivo
```

---

## 🔍 Troubleshooting

### Z-API não envia mensagens

1. Verifique se a instância está conectada (QR Code escaneado)
2. Confirme que as variáveis `ZAPI_INSTANCE_ID`, `ZAPI_TOKEN` estão corretas
3. Teste o endpoint `/zapi/status` para verificar a conexão
4. Verifique os logs na Vercel

### Webhook não recebe mensagens

1. Confirme que a URL está correta no painel Z-API
2. Verifique se os eventos estão ativados (ReceivedCallback)
3. Teste com o botão "Testar Webhook" no painel Z-API

### Firebase não inicializa

1. Verifique se o JSON está em uma única linha
2. Certifique-se de que não há caracteres extras
3. Verifique os logs na Vercel: `vercel logs`

### Erro 500 no webhook

1. Verifique os logs completos na Vercel
2. Teste localmente com os mesmos dados
3. Confirme que todas as variáveis estão configuradas

---

## 🔐 Segurança

- **Nunca commite** credenciais no repositório
- Use **sempre HTTPS** em produção
- Configure o **Client-Token** da Z-API
- Monitore logs para atividades suspeitas
