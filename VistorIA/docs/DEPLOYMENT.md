# 🚀 Guia de Deploy - VistorIA

## Visão Geral

Este guia cobre as opções de deploy para o VistorIA, desde desenvolvimento local até produção em nuvem.

## 🏠 Desenvolvimento Local

### Pré-requisitos
- Python 3.9+
- Git
- Conta OpenAI com API Key

### Setup Rápido
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/vistoria.git
cd vistoria

# Configure ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instale dependências
pip install -r VistorIA/requirements.txt

# Configure variáveis de ambiente
cp VistorIA/env.example VistorIA/.env
# Edite VistorIA/.env com sua OPENAI_API_KEY

# Execute o servidor
cd VistorIA
./dev.sh
```

Acesse: `http://localhost:8000`

## ☁️ Deploy em Nuvem

### 1. Heroku (Recomendado para MVP)

#### Preparação
```bash
# Instale Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login no Heroku
heroku login

# Crie o app
heroku create vistoria-app-nome-unico
```

#### Configuração
```bash
# Configure variáveis de ambiente
heroku config:set OPENAI_API_KEY=your_key_here
heroku config:set APP_NAME=VistorIA
heroku config:set DEBUG=False

# Configure Python version
echo "python-3.9.18" > runtime.txt

# Configure Procfile
echo "web: cd VistorIA && uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

#### Deploy
```bash
# Commit mudanças
git add .
git commit -m "Configure for Heroku"

# Deploy
git push heroku main

# Abra o app
heroku open
```

### 2. Railway

#### Setup
```bash
# Instale Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicialize projeto
railway init

# Configure variáveis
railway variables set OPENAI_API_KEY=your_key_here
railway variables set APP_NAME=VistorIA
```

#### Deploy
```bash
# Deploy automático via GitHub
railway connect  # Conecte ao repositório GitHub
railway up       # Deploy manual
```

### 3. Render

#### Configuração via Dashboard
1. Conecte seu repositório GitHub
2. Configure:
   - **Build Command**: `pip install -r VistorIA/requirements.txt`
   - **Start Command**: `cd VistorIA && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9

#### Variáveis de Ambiente
```
OPENAI_API_KEY=your_key_here
APP_NAME=VistorIA
DEBUG=False
PYTHONPATH=VistorIA
```

### 4. DigitalOcean App Platform

#### app.yaml
```yaml
name: vistoria
services:
- name: api
  source_dir: /
  github:
    repo: seu-usuario/vistoria
    branch: main
  run_command: cd VistorIA && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: OPENAI_API_KEY
    value: your_key_here
  - key: APP_NAME
    value: VistorIA
  - key: DEBUG
    value: "False"
  - key: PYTHONPATH
    value: VistorIA
```

## 🐳 Docker

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY VistorIA/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY VistorIA/ .

# Criar diretórios necessários
RUN mkdir -p static/uploads

# Expor porta
EXPOSE 8000

# Comando de execução
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  vistoria:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - APP_NAME=VistorIA
      - DEBUG=False
    volumes:
      - ./uploads:/app/static/uploads
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - vistoria
    restart: unless-stopped
```

### Build e Run
```bash
# Build da imagem
docker build -t vistoria .

# Run do container
docker run -d \
  --name vistoria-app \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -v $(pwd)/uploads:/app/static/uploads \
  vistoria

# Usando docker-compose
docker-compose up -d
```

## 🔧 Configuração de Produção

### Variáveis de Ambiente Essenciais
```env
# OpenAI
OPENAI_API_KEY=your_production_key

# App
APP_NAME=VistorIA
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your_super_secret_key_here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Files
MAX_FILE_SIZE=52428800  # 50MB
PDF_OUTPUT_DIR=/app/static/uploads

# Logging
LOG_LEVEL=INFO
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # File upload size
    client_max_body_size 50M;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 📊 Monitoramento

### Health Checks
```bash
# Endpoint de health
curl https://yourdomain.com/api/health

# Resposta esperada
{"status":"ok","service":"VistorIA API"}
```

### Logs
```bash
# Heroku
heroku logs --tail

# Docker
docker logs -f vistoria-app

# Railway
railway logs

# Render
# Via dashboard web
```

### Métricas Importantes
- **Response Time**: < 2s para uploads
- **Uptime**: > 99.9%
- **Error Rate**: < 1%
- **File Processing**: Success rate > 95%

## 🔒 Segurança

### SSL/TLS
```bash
# Certbot (Let's Encrypt)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Rate Limiting
```python
# Adicionar ao main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/transcribe")
@limiter.limit("10/minute")
async def api_transcribe(request: Request, file: UploadFile = File(...)):
    # ...
```

### Firewall
```bash
# UFW (Ubuntu)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## 🔄 CI/CD

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r VistorIA/requirements.txt
    
    - name: Run tests
      run: |
        pytest
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "your-app-name"
        heroku_email: "your-email@example.com"
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Heroku
heroku ps:scale web=3

# Docker Swarm
docker service scale vistoria_app=3

# Kubernetes
kubectl scale deployment vistoria --replicas=3
```

### Database (Futuro)
```yaml
# Para quando adicionar PostgreSQL
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: vistoria
      POSTGRES_USER: vistoria
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. "Module not found"
```bash
# Verificar PYTHONPATH
export PYTHONPATH=VistorIA
```

#### 2. "OpenAI API Error"
```bash
# Verificar API key
echo $OPENAI_API_KEY
# Verificar quotas no dashboard OpenAI
```

#### 3. "File upload failed"
```bash
# Verificar permissões de diretório
chmod 755 VistorIA/static/uploads
```

#### 4. "PDF generation error"
```bash
# Instalar dependências de sistema (Ubuntu)
sudo apt-get install libffi-dev python3-dev
```

## 📞 Suporte

Para problemas de deploy:
- 📧 Email: devops@vistoria.com.br
- 📖 Docs: `/docs`
- 🐛 Issues: GitHub Issues
- 💬 Discord: [VistorIA Community](https://discord.gg/vistoria)