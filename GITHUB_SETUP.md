# 🚀 Setup GitHub e Push

## Passo a Passo

### 1. Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. Nome do repositório: `agente-de-campanhas`
3. Descrição: "Assistente inteligente via WhatsApp para gerenciamento de campanhas Facebook Ads"
4. **Visibilidade**: 
   - 🔒 **Private** (recomendado - contém lógica de negócio)
   - 🌐 Public (se quiser tornar open source)
5. **NÃO** marque:
   - ❌ Add README
   - ❌ Add .gitignore
   - ❌ Add license
6. Clique em **"Create repository"**

### 2. Configurar Remote e Push

```bash
# Adicionar remote (substitua SEU-USUARIO pelo seu username)
git remote add origin https://github.com/SEU-USUARIO/agente-de-campanhas.git

# Verificar
git remote -v

# Push inicial
git push -u origin main
```

### 3. Configurar Secrets para GitHub Actions

Para o workflow de Docker build funcionar, configure no GitHub:

1. Acesse: `Settings` → `Secrets and variables` → `Actions`
2. Clique em `New repository secret`

**Secrets necessários:**

| Secret | Descrição | Onde obter |
|--------|-----------|------------|
| `GITHUB_TOKEN` | ✅ **Já existe automaticamente** | Gerado pelo GitHub |

**O `GITHUB_TOKEN` já tem permissões para:**
- ✅ Fazer push para GitHub Container Registry (ghcr.io)
- ✅ Ler código do repositório
- ✅ Criar packages

### 4. Habilitar GitHub Container Registry

1. Acesse seu perfil → `Settings` → `Developer settings` → `Personal access tokens` → `Tokens (classic)`
2. Ou use o `GITHUB_TOKEN` automático (recomendado - já configurado)

**GHCR será ativado automaticamente no primeiro push!**

### 5. Fazer Push e Verificar Build

```bash
# Push
git push -u origin main

# Verificar no GitHub:
# 1. Aba "Actions" - ver workflow rodando
# 2. Aba "Packages" - ver imagem Docker após build
```

### 6. Usar a Imagem Docker do GitHub

Após o primeiro push bem-sucedido:

```bash
# Login no GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u SEU-USUARIO --password-stdin

# Pull da imagem
docker pull ghcr.io/SEU-USUARIO/agente-de-campanhas:latest

# Ou usar no docker-compose.yml:
```

```yaml
services:
  agente-campanhas:
    image: ghcr.io/SEU-USUARIO/agente-de-campanhas:latest
    # ... resto da config
```

## 📊 Workflows Configurados

### 1. Docker Build (`docker-build.yml`)

**Triggers:**
- ✅ Push na branch `main` ou `master`
- ✅ Push de tags `v*` (ex: v1.0.0)
- ✅ Pull requests

**O que faz:**
- Faz build da imagem Docker
- Push para `ghcr.io/SEU-USUARIO/agente-de-campanhas`
- Suporta multi-plataforma (amd64 + arm64)
- Cache otimizado (GitHub Actions Cache)
- Gera tags automáticas:
  - `latest` (branch main/master)
  - `main` (nome da branch)
  - `sha-abc123` (commit SHA)
  - `v1.0.0` (se tag semver)

### 2. CI Tests (`ci.yml`)

**Triggers:**
- ✅ Push em `main`, `master`, `develop`
- ✅ Pull requests

**O que faz:**
- Testa imports de todas as ferramentas
- Verifica contas padrão configuradas
- Compila agent graph
- Roda calculadora de custos
- Lint com flake8

## 🏷️ Versionamento com Tags

```bash
# Criar tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial Docker setup"

# Push da tag
git push origin v1.0.0

# Isso vai gerar imagem com tags:
# - ghcr.io/SEU-USUARIO/agente-de-campanhas:v1.0.0
# - ghcr.io/SEU-USUARIO/agente-de-campanhas:v1.0
# - ghcr.io/SEU-USUARIO/agente-de-campanhas:v1
# - ghcr.io/SEU-USUARIO/agente-de-campanhas:latest
```

## 🔐 Tornar Imagem Pública

Por padrão, packages são privados. Para tornar público:

1. Acesse: `https://github.com/SEU-USUARIO?tab=packages`
2. Clique no package `agente-de-campanhas`
3. `Package settings` → `Change visibility` → `Public`

## 🐛 Troubleshooting

### Erro: "permission denied"

```bash
# Verificar se está logado
docker login ghcr.io

# Fazer push novamente
git push origin main
```

### Erro: "workflow not found"

Verifique se os arquivos estão em `.github/workflows/`:
```bash
ls .github/workflows/
# Deve mostrar: ci.yml, docker-build.yml
```

### Build falhou no GitHub Actions

1. Acesse aba `Actions` no GitHub
2. Clique no workflow que falhou
3. Veja os logs de cada step
4. Erros comuns:
   - Dockerfile inválido
   - requirements.txt com dependências quebradas
   - Falta de permissões

### Imagem não aparece em Packages

1. Aguarde o workflow completar (pode levar 5-10 min)
2. Verifique se o push foi bem-sucedido na aba Actions
3. Packages aparecem em: `https://github.com/SEU-USUARIO?tab=packages`

## 📝 Comandos Úteis

```bash
# Ver status
git status

# Ver log de commits
git log --oneline

# Ver remotes
git remote -v

# Atualizar remote URL
git remote set-url origin https://github.com/NOVO-USUARIO/agente-de-campanhas.git

# Ver branches
git branch -a

# Criar nova branch
git checkout -b develop

# Voltar para main
git checkout main

# Ver diferenças
git diff

# Ver último commit
git show HEAD
```

## 🎯 Próximos Passos

Após push bem-sucedido:

1. ✅ Verificar workflows na aba Actions
2. ✅ Verificar imagem em Packages
3. ✅ Adicionar README com badges:

```markdown
![Docker Build](https://github.com/SEU-USUARIO/agente-de-campanhas/actions/workflows/docker-build.yml/badge.svg)
![CI](https://github.com/SEU-USUARIO/agente-de-campanhas/actions/workflows/ci.yml/badge.svg)
```

4. ✅ Configurar branch protection rules (Settings → Branches)
5. ✅ Deploy em produção usando imagem do GHCR

---

## 📞 Suporte

**Problemas com GitHub Actions?**
- Documentação: https://docs.github.com/actions
- Logs detalhados na aba Actions do repositório

**Problemas com GHCR?**
- Documentação: https://docs.github.com/packages
- Login: `docker login ghcr.io`
