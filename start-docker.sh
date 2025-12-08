#!/bin/bash

# Script de inicialização do Agente de Campanhas

echo "======================================"
echo "  Agente de Campanhas - Docker Setup"
echo "======================================"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    echo "   Instale: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado!"
    exit 1
fi

echo "✅ Docker instalado"
echo "✅ Docker Compose instalado"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "   Criando .env a partir de .env.example..."
    cp .env.example .env
    echo "✅ .env criado - EDITE O ARQUIVO COM SUAS CREDENCIAIS!"
    echo ""
    echo "   Edite o arquivo .env e execute este script novamente."
    exit 1
fi

echo "✅ Arquivo .env encontrado"
echo ""

# Criar diretório data se não existir
mkdir -p data

echo "🐳 Iniciando build do Docker..."
docker-compose build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build concluído com sucesso!"
    echo ""
    echo "🚀 Iniciando containers..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Aplicação iniciada!"
        echo ""
        echo "📍 Acesse:"
        echo "   - API: http://localhost:8000"
        echo "   - Health: http://localhost:8000/health"
        echo "   - Docs: http://localhost:8000/docs"
        echo ""
        echo "📋 Comandos úteis:"
        echo "   - Ver logs: docker-compose logs -f"
        echo "   - Parar: docker-compose stop"
        echo "   - Restart: docker-compose restart"
        echo ""
        
        # Aguardar 5 segundos e testar health
        echo "⏳ Aguardando aplicação iniciar..."
        sleep 5
        
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Health check passou!"
        else
            echo "⚠️  Health check falhou - verifique os logs"
            docker-compose logs --tail=50
        fi
    else
        echo "❌ Erro ao iniciar containers"
        exit 1
    fi
else
    echo "❌ Erro no build do Docker"
    exit 1
fi
