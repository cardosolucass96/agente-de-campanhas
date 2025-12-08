# Script PowerShell para iniciar o Agente de Campanhas com Docker

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Agente de Campanhas - Docker Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está instalado
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "❌ Docker não está instalado!" -ForegroundColor Red
    Write-Host "   Instale: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker instalado" -ForegroundColor Green

# Verificar se Docker está rodando
try {
    docker ps > $null 2>&1
    Write-Host "✅ Docker está rodando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    Write-Host "   Inicie o Docker Desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar se .env existe
if (-not (Test-Path .env)) {
    Write-Host "⚠️  Arquivo .env não encontrado!" -ForegroundColor Yellow
    Write-Host "   Criando .env a partir de .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env criado - EDITE O ARQUIVO COM SUAS CREDENCIAIS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Edite o arquivo .env e execute este script novamente." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Arquivo .env encontrado" -ForegroundColor Green
Write-Host ""

# Criar diretório data se não existir
if (-not (Test-Path data)) {
    New-Item -ItemType Directory -Path data | Out-Null
    Write-Host "✅ Diretório data criado" -ForegroundColor Green
}

# Build
Write-Host "🐳 Iniciando build do Docker..." -ForegroundColor Cyan
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Build concluído com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Iniciando containers..." -ForegroundColor Cyan
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Aplicação iniciada!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📍 Acesse:" -ForegroundColor Cyan
        Write-Host "   - API: http://localhost:8000" -ForegroundColor White
        Write-Host "   - Health: http://localhost:8000/health" -ForegroundColor White
        Write-Host "   - Docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host ""
        Write-Host "📋 Comandos úteis:" -ForegroundColor Cyan
        Write-Host "   - Ver logs: docker-compose logs -f" -ForegroundColor White
        Write-Host "   - Parar: docker-compose stop" -ForegroundColor White
        Write-Host "   - Restart: docker-compose restart" -ForegroundColor White
        Write-Host "   - Status: docker-compose ps" -ForegroundColor White
        Write-Host ""
        
        # Aguardar e testar health
        Write-Host "⏳ Aguardando aplicação iniciar..." -ForegroundColor Yellow
        Start-Sleep -Seconds 8
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Health check passou!" -ForegroundColor Green
                Write-Host ""
                Write-Host "🎉 Tudo pronto! Aplicação rodando." -ForegroundColor Green
            }
        } catch {
            Write-Host "⚠️  Health check falhou - verificando logs..." -ForegroundColor Yellow
            Write-Host ""
            docker-compose logs --tail=30
        }
    } else {
        Write-Host "❌ Erro ao iniciar containers" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Erro no build do Docker" -ForegroundColor Red
    exit 1
}
