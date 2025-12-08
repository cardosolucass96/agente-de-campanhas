# ✅ Checklist - Deploy e GitHub

## Antes do Push

- [x] Código testado localmente
- [x] Dockerfile criado e validado
- [x] docker-compose.yml configurado
- [x] requirements.txt gerado
- [x] .gitignore configurado
- [x] .env.example criado (sem credenciais)
- [x] .env adicionado ao .gitignore
- [x] Documentação completa (README, DOCKER.md, DEPLOY.md)
- [x] GitHub Actions workflows criados
- [x] Scripts de inicialização (start-docker.ps1/sh)
- [x] Tests básicos funcionando

## Criar Repositório GitHub

- [ ] Acessar https://github.com/new
- [ ] Nome: `agente-de-campanhas`
- [ ] Descrição preenchida
- [ ] Visibilidade escolhida (Private/Public)
- [ ] NÃO adicionar README/gitignore/license
- [ ] Repositório criado

## Configurar e Push

- [ ] Remote adicionado: `git remote add origin https://github.com/SEU-USUARIO/agente-de-campanhas.git`
- [ ] Remote verificado: `git remote -v`
- [ ] Push realizado: `git push -u origin main`
- [ ] Push bem-sucedido (sem erros)

## Verificar GitHub Actions

- [ ] Acessar aba "Actions" no repositório
- [ ] Workflow "Build and Push Docker Image" rodando
- [ ] Workflow "CI - Tests and Linting" rodando
- [ ] Ambos workflows completados com sucesso ✅
- [ ] Ver logs de build (se houver erro)

## Verificar Imagem Docker

- [ ] Acessar aba "Packages" no perfil
- [ ] Imagem `agente-de-campanhas` apareceu
- [ ] Tags geradas corretamente:
  - [ ] `latest`
  - [ ] `main`
  - [ ] `sha-xxxxxxx`
- [ ] Imagem disponível em: `ghcr.io/SEU-USUARIO/agente-de-campanhas:latest`

## Configurar Visibilidade (Opcional)

- [ ] Acessar package settings
- [ ] Mudar para Public (se desejado)
- [ ] Link do package conectado ao repositório

## Adicionar Badges ao README

- [ ] Copiar badges do BADGES.md
- [ ] Substituir `SEU-USUARIO` pelo username real
- [ ] Adicionar badges no topo do README.md
- [ ] Commit: `git commit -am "docs: Add badges to README"`
- [ ] Push: `git push origin main`
- [ ] Verificar badges funcionando

## Testar Imagem do GHCR

- [ ] Login no GHCR: `docker login ghcr.io -u SEU-USUARIO`
- [ ] Pull da imagem: `docker pull ghcr.io/SEU-USUARIO/agente-de-campanhas:latest`
- [ ] Imagem baixada com sucesso
- [ ] Testar run: `docker run --env-file .env -p 8000:8000 ghcr.io/SEU-USUARIO/agente-de-campanhas:latest`

## Configurar Branch Protection (Recomendado)

- [ ] Acessar: Settings → Branches → Add branch protection rule
- [ ] Branch name pattern: `main`
- [ ] Configurações recomendadas:
  - [ ] Require pull request reviews before merging
  - [ ] Require status checks to pass before merging
    - [ ] Build and Push Docker Image
    - [ ] CI - Tests and Linting
  - [ ] Require branches to be up to date before merging
  - [ ] Include administrators (opcional)
- [ ] Salvar regras

## Deploy em Produção

- [ ] Servidor VPS configurado
- [ ] Docker instalado no servidor
- [ ] Repositório clonado no servidor
- [ ] .env configurado com credenciais de produção
- [ ] docker-compose up -d --build executado
- [ ] Aplicação rodando e health check OK
- [ ] Nginx configurado como reverse proxy
- [ ] SSL/HTTPS configurado (Let's Encrypt)
- [ ] Webhooks WhatsApp/Facebook configurados
- [ ] Firewall configurado (portas 80, 443, 22)
- [ ] Backup automático configurado

## Monitoramento

- [ ] Logs funcionando: `docker-compose logs -f`
- [ ] Health check respondendo: `curl https://seu-dominio.com/health`
- [ ] Uptime Robot configurado (opcional)
- [ ] Alertas configurados (email/SMS)

## Documentação Final

- [ ] README.md atualizado com instruções de uso
- [ ] Link para documentação completa (DOCKER.md, DEPLOY.md)
- [ ] Exemplos de uso documentados
- [ ] API endpoints documentados
- [ ] Troubleshooting guide criado
- [ ] Changelog iniciado (opcional)

## Segurança

- [ ] .env não está no repositório
- [ ] Secrets sensíveis não estão expostos
- [ ] Webhook signatures validadas
- [ ] Rate limiting configurado (se necessário)
- [ ] CORS configurado corretamente
- [ ] Logs não expõem dados sensíveis

## Performance

- [ ] Custos de tokens monitorados
- [ ] Limites de uso definidos
- [ ] Cache configurado (se necessário)
- [ ] Database otimizado

## Testes em Produção

- [ ] Enviar mensagem teste via WhatsApp
- [ ] Verificar lista interativa funciona
- [ ] Verificar botões funcionam
- [ ] Testar consulta de campanhas
- [ ] Testar comparações
- [ ] Testar histórico
- [ ] Verificar logs de erro

---

## 🎉 Conclusão

Quando todos os itens estiverem marcados:
- ✅ Aplicação está no GitHub
- ✅ CI/CD configurado
- ✅ Imagem Docker disponível
- ✅ Deploy em produção funcionando
- ✅ Documentação completa

**Parabéns! Seu projeto está pronto para uso em produção! 🚀**

---

## 📊 Status do Projeto

| Componente | Status |
|------------|--------|
| Código | ✅ Completo |
| Docker | ✅ Configurado |
| GitHub | ⏳ Pendente push |
| CI/CD | ✅ Configurado |
| Docs | ✅ Completa |
| Deploy | ⏳ Pendente |
| Testes | ✅ OK |

**Última atualização:** 08/12/2025
