#!/bin/bash

echo "🏠 VistorIA - Starting System..."
echo "=================================="

# Verificar se Redis está rodando
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis não está rodando. Iniciando Redis..."
    redis-server --daemonize yes
    echo "✅ Redis iniciado"
fi

# Verificar se Celery worker já está rodando
if pgrep -f "celery.*worker" > /dev/null; then
    echo "⚠️  Celery worker já está rodando. Parando processo anterior..."
    pkill -f "celery.*worker"
    sleep 2
fi

# Iniciar Celery worker em background
echo "🔄 Iniciando Celery worker..."
celery -A app.background_tasks worker --loglevel=info --detach

# Aguardar um momento para o worker inicializar
sleep 3

# Iniciar servidor FastAPI
echo "🚀 Iniciando servidor VistorIA..."
echo "📱 Interface: http://localhost:8000/vistoria"
echo "📚 API Docs: http://localhost:8000/docs"
echo "💾 Banco de dados será criado automaticamente"
echo ""
echo "Para parar o sistema, pressione Ctrl+C"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup quando o script for interrompido
echo ""
echo "🛑 Parando sistema..."
pkill -f "celery.*worker"
echo "✅ Sistema parado"