# 📚 Documentação da API - VistorIA

## Visão Geral

A API do VistorIA é construída com FastAPI e fornece endpoints para:
- Transcrição de áudio usando Whisper
- Análise de imagens com GPT-4 Vision
- Sumarização de textos
- Geração de relatórios PDF

**Base URL:** `http://localhost:8000`

## 🔐 Autenticação

Atualmente, a API não requer autenticação para o MVP. Em produção, será implementado:
- JWT tokens
- API keys por cliente
- Rate limiting

## 📋 Endpoints

### Health Check

```http
GET /api/health
```

**Resposta:**
```json
{
  "status": "ok",
  "service": "VistorIA API"
}
```

### 🎤 Transcrição de Áudio

Converte áudio em texto usando Whisper da OpenAI.

```http
POST /api/transcribe
Content-Type: multipart/form-data
```

**Parâmetros:**
- `file` (required): Arquivo de áudio (WAV, MP3, M4A, OGG)

**Exemplo de Uso:**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav"
```

**Resposta:**
```json
{
  "text": "A torneira da cozinha apresenta um pequeno vazamento na base"
}
```

**Códigos de Status:**
- `200`: Sucesso
- `422`: Arquivo inválido
- `500`: Erro interno

### 👁️ Análise de Imagem

Analisa imagens e gera descrições usando GPT-4 Vision.

```http
POST /api/vision
Content-Type: multipart/form-data
```

**Parâmetros:**
- `file` (required): Arquivo de imagem (JPG, PNG, WEBP)
- `prompt` (optional): Prompt personalizado (padrão: "Descreva o estado do item na imagem.")

**Exemplo de Uso:**
```bash
curl -X POST "http://localhost:8000/api/vision" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@torneira.jpg" \
  -F "prompt=Analise o estado desta torneira"
```

**Resposta:**
```json
{
  "description": "Torneira cromada em bom estado de conservação, sem sinais visíveis de ferrugem ou vazamentos. O acabamento está brilhante e não há calcário acumulado."
}
```

### 📝 Sumarização de Texto

Resume textos longos mantendo informações importantes.

```http
POST /api/summarize
Content-Type: application/x-www-form-urlencoded
```

**Parâmetros:**
- `text` (required): Texto a ser resumido

**Exemplo de Uso:**
```bash
curl -X POST "http://localhost:8000/api/summarize" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=Observação muito longa sobre o estado do imóvel..."
```

**Resposta:**
```json
{
  "summary": "Imóvel em bom estado geral, necessita pequenos reparos na cozinha e banheiro."
}
```

### 📄 Geração de Relatório

Gera relatório PDF completo da vistoria.

```http
POST /api/report
Content-Type: application/json
```

**Parâmetros (JSON):**
```json
{
  "propertyAddress": "string",
  "landlordName": "string", 
  "tenantName": "string",
  "checklist": [
    {
      "room": "string",
      "item": "string", 
      "status": "ok|danificado|sujo|ausente",
      "notes": "string (optional)",
      "photos": ["array of paths (optional)"],
      "audioTranscripts": ["array of strings (optional)"]
    }
  ],
  "landlordSignature": "string (base64, optional)",
  "tenantSignature": "string (base64, optional)",
  "logoPath": "string (optional)",
  "inspectionDate": "datetime (optional)",
  "inspectionType": "entrada|saida"
}
```

**Exemplo de Uso:**
```bash
curl -X POST "http://localhost:8000/api/report" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "propertyAddress": "Rua das Flores, 123",
    "landlordName": "João Silva",
    "tenantName": "Maria Santos", 
    "checklist": [
      {
        "room": "Cozinha",
        "item": "Torneira",
        "status": "ok",
        "notes": "Em perfeito estado"
      }
    ]
  }'
```

**Resposta:** Arquivo PDF para download

## 🔧 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 400 | Requisição inválida |
| 422 | Dados de entrada inválidos |
| 500 | Erro interno do servidor |

## 📊 Limites e Quotas

### Tamanhos de Arquivo
- **Áudio**: Máximo 25MB
- **Imagem**: Máximo 20MB

### Formatos Suportados
- **Áudio**: WAV, MP3, M4A, OGG, FLAC
- **Imagem**: JPG, JPEG, PNG, WEBP

### Rate Limiting (Produção)
- 100 requisições por minuto por IP
- 1000 requisições por hora por usuário autenticado

## 🧪 Testando a API

### Usando cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Upload de áudio
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@test_audio.wav"

# Upload de imagem  
curl -X POST http://localhost:8000/api/vision \
  -F "file=@test_image.jpg" \
  -F "prompt=Descreva esta imagem"
```

### Usando Python

```python
import requests

# Transcrição de áudio
with open('audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/transcribe',
        files={'file': f}
    )
    print(response.json())

# Análise de imagem
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/vision',
        files={'file': f},
        data={'prompt': 'Analise esta imagem'}
    )
    print(response.json())
```

### Usando JavaScript

```javascript
// Transcrição de áudio
const formData = new FormData();
formData.append('file', audioFile);

fetch('/api/transcribe', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Análise de imagem
const imageFormData = new FormData();
imageFormData.append('file', imageFile);
imageFormData.append('prompt', 'Descreva esta imagem');

fetch('/api/vision', {
  method: 'POST', 
  body: imageFormData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 📖 Documentação Interativa

Acesse `http://localhost:8000/docs` para:
- Documentação Swagger UI interativa
- Teste de endpoints diretamente no navegador
- Esquemas de dados detalhados
- Exemplos de requisições e respostas

## 🐛 Troubleshooting

### Erro: "OpenAI API key not found"
```bash
# Verifique se a variável de ambiente está definida
echo $OPENAI_API_KEY

# Configure no arquivo .env
OPENAI_API_KEY=your_key_here
```

### Erro: "File too large"
- Verifique se o arquivo não excede os limites
- Comprima áudios/imagens antes do upload

### Erro: "Unsupported file format"
- Verifique se o formato está na lista de suportados
- Converta o arquivo para um formato suportado

## 🔄 Versionamento

A API segue versionamento semântico:
- **v1.0.0**: Versão inicial do MVP
- **v1.1.0**: Adição de autenticação
- **v1.2.0**: Melhorias na estrutura de dados

## 📞 Suporte

Para dúvidas sobre a API:
- 📧 Email: api@vistoria.com.br
- 📖 Documentação: `/docs`
- 🐛 Issues: GitHub Issues