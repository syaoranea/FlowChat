# WhatsApp E-commerce Chatbot 🤖

Backend completo em Python para chatbot WhatsApp de e-commerce, integrado com Firebase/Firestore e Twilio.

## 📋 Funcionalidades

- ✅ Webhook para receber mensagens do WhatsApp via Twilio
- ✅ Gerenciamento de estado da conversa por usuário
- ✅ Integração completa com Firestore (produtos, SKUs, estoque, orçamentos)
- ✅ Fluxos conversacionais completos:
  - **Orçamento**: Navegação por categorias e produtos, seleção de atributos, geração de orçamento
  - **Compras**: Encaminhamento para atendente
  - **Pós-venda**: Coleta de número do pedido e encaminhamento
  - **Falar com Atendente**: Encaminhamento direto

## 🏗️ Arquitetura

```
whatsapp_ecommerce_bot/
├── main.py                     # Aplicação FastAPI principal
├── requirements.txt            # Dependências Python
├── .env.example               # Template de variáveis de ambiente
├── README.md                  # Esta documentação
└── app/
    ├── __init__.py
    ├── config.py              # Configurações via variáveis de ambiente
    ├── models/
    │   ├── __init__.py
    │   └── conversation.py    # Modelos de estado da conversa
    ├── services/
    │   ├── __init__.py
    │   ├── firebase_service.py   # Integração com Firestore
    │   └── twilio_service.py     # Integração com Twilio
    └── handlers/
        ├── __init__.py
        ├── message_handler.py    # Handler principal (orquestra fluxos)
        ├── orcamento_handler.py  # Fluxo de orçamento
        ├── compras_handler.py    # Fluxo de compras
        └── posvenda_handler.py   # Fluxo de pós-venda
```

## 🚀 Instalação e Configuração

### 1. Clone e instale dependências

```bash
cd /home/ubuntu/whatsapp_ecommerce_bot
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=flowchat-72383
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Twilio Configuration
TWILIO_ACCOUNT_SID=seu_account_sid_aqui
TWILIO_AUTH_TOKEN=seu_auth_token_aqui
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# App Configuration
COMPANY_NAME=Minha Empresa
ORCAMENTO_VALIDADE_DIAS=10
LOG_LEVEL=INFO
```

### 3. Configure o Firebase

Baixe o arquivo de credenciais do Firebase Console:
1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Vá em Project Settings > Service Accounts
3. Clique em "Generate new private key"
4. Salve o arquivo como `firebase-credentials.json` na raiz do projeto

### 4. Execute o servidor

```bash
# Modo desenvolvimento (com hot reload)
python main.py

# Ou com uvicorn diretamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

O servidor estará disponível em `http://localhost:8000`

## 🔗 Configuração do Twilio

### Webhook Configuration

1. Acesse [Twilio Console](https://console.twilio.com)
2. Vá em Messaging > Settings > WhatsApp Sandbox Settings
3. Configure o webhook "When a message comes in":
   - URL: `https://seu-dominio.com/webhook/whatsapp`
   - Method: POST

### Para desenvolvimento local

Use ngrok ou similar para expor sua porta local:

```bash
ngrok http 8000
```

Configure a URL do ngrok no Twilio.

## 📡 API Endpoints

### Health Check
```
GET /
GET /health
```

### Webhook WhatsApp (Twilio)
```
POST /webhook/whatsapp
Content-Type: application/x-www-form-urlencoded

From=whatsapp:+5511999999999&Body=Olá
```

### Status Callback (Twilio)
```
POST /webhook/whatsapp/status
```

### Teste de Mensagem (Debug)
```
POST /api/test/message
Content-Type: application/json

{
  "phone": "+5511999999999",
  "message": "Olá"
}
```

### Envio Manual de Mensagem
```
POST /api/send?phone=+5511999999999&message=Olá
```

## 📊 Estrutura do Firestore

### Collections

#### `produtos`
```json
{
  "_id": "prod_001",
  "nome": "Camiseta Básica",
  "descricao": "Camiseta 100% algodão",
  "categoria": "Roupas",
  "ativo": true,
  "atributos": ["Cor", "Tamanho"]
}
```

#### `skus`
```json
{
  "_id": "sku_CAM_PRE_M",
  "produto_id": "prod_001",
  "sku": "CAM-PRE-M",
  "preco": 59.9,
  "estoque": 8,
  "ativo": true,
  "atributos": {
    "Cor": "Preto",
    "Tamanho": "M"
  }
}
```

#### `estoque`
```json
{
  "_id": "estoque_01",
  "sku": "CAM-PRE-M",
  "local": "CD-SP",
  "quantidade": 5
}
```

#### `orcamentos`
```json
{
  "_id": "orc_2026_000123",
  "numero": 123,
  "numero_formatado": "ORC-2026-00123",
  "status": "RASCUNHO",
  "data_criacao": "2026-01-31T14:32:00Z",
  "validade": "2026-02-10",
  "cliente": {
    "nome": "João Silva",
    "telefone": "whatsapp:+5511999999999"
  },
  "valores": {
    "subtotal": 599.0,
    "desconto": 0,
    "frete": 0,
    "total": 599.0
  },
  "itens": [...]
}
```

#### `conversas` (Estado da conversa)
```json
{
  "phone": "whatsapp:+5511999999999",
  "nome": "João",
  "etapa": "menu_principal",
  "fluxo": "nenhum",
  "dados_temporarios": {...},
  "encaminhado_atendente": false,
  "ultima_atualizacao": "2026-02-01T10:30:00Z"
}
```

#### `logs_interacoes`
```json
{
  "phone": "whatsapp:+5511999999999",
  "tipo": "mensagem",
  "mensagem_recebida": "1",
  "mensagem_enviada": "...",
  "etapa": "menu_principal",
  "fluxo": "orcamento",
  "timestamp": "2026-02-01T10:30:00Z"
}
```

## 🔄 Fluxos Conversacionais

### Fluxo Inicial
1. Saudação de boas-vindas
2. Captura do nome do cliente
3. Exibe menu principal

### Menu Principal
```
1️⃣ Orçamento
2️⃣ Compras
3️⃣ Pós-venda
4️⃣ Falar com atendente
```

### Fluxo de Orçamento
1. Lista categorias do Firestore
2. Cliente escolhe categoria
3. Lista produtos com preços
4. Cliente escolhe produto
5. Se múltiplas variações, mostra opções (cor, tamanho, etc.)
6. Pergunta quantidade
7. Adiciona ao orçamento
8. Mostra resumo e opções (adicionar mais / finalizar / atendente)
9. Ao finalizar: gera número ORC-2026-XXXXX

### Comandos Globais
- `menu` ou `0`: Volta ao menu principal
- `voltar`: Volta à etapa anterior (quando disponível)
- `cancelar`: Cancela operação atual

## 🧪 Testando

### Via cURL (endpoint de teste)

```bash
# Primeira mensagem (início)
curl -X POST http://localhost:8000/api/test/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5511999999999", "message": "Olá"}'

# Informar nome
curl -X POST http://localhost:8000/api/test/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5511999999999", "message": "João"}'

# Escolher orçamento
curl -X POST http://localhost:8000/api/test/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "+5511999999999", "message": "1"}'
```

### Swagger UI

Acesse `http://localhost:8000/docs` para interface interativa.

## 📝 Logs

O sistema registra todas as interações em:
- Console (stdout)
- Collection `logs_interacoes` no Firestore

Nível de log configurável via `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)

## 🔒 Segurança

- Credenciais via variáveis de ambiente
- Arquivo `.env` não deve ser commitado
- Validação de Twilio Signature (implementar em produção)

## 📦 Dependências Principais

- **FastAPI**: Framework web assíncrono
- **Uvicorn**: Servidor ASGI
- **firebase-admin**: SDK oficial do Firebase
- **twilio**: SDK oficial do Twilio
- **pydantic**: Validação de dados

## 🚧 Próximos Passos (Sugestões)

- [ ] Validação de assinatura Twilio
- [ ] Cache de produtos (Redis)
- [ ] Integração com sistema de pedidos
- [ ] Notificações para atendentes
- [ ] Métricas e dashboard
- [ ] Testes automatizados

## 📄 Licença

MIT
