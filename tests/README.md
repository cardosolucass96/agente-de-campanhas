# 🧪 Testes do Agente de Campanhas

Pasta centralizada com todos os testes do sistema.

## 📋 Índice de Testes

### 🔧 Testes de Ferramentas (Tools)

**Tokens e Autenticação:**
- `test_facebook_token.py` - Valida token do Facebook, permissões e acesso às contas

**Insights e Métricas:**
- `test_insights_raw.py` - Teste direto da API de insights do Facebook
- `test_insights_tool.py` - Teste da ferramenta de insights do agente
- `test_all_accounts.py` - Teste de resumo de todas as contas
- `test_scale_ctr_direct.py` - Teste direto do CTR da conta Scale via API
- `test_ctr.py` - Teste end-to-end do agente respondendo sobre CTR

**Comparações:**
- `test_compare_direct.py` - Teste direto da ferramenta de comparação de períodos
- `test_compare_periods.py` - Teste da ferramenta compare_campaign_periods

**Histórico e Atividades:**
- `test_activity_history.py` - Teste da ferramenta de histórico de atividades
- `test_list_accounts.py` - Lista todas as contas disponíveis

### 🤖 Testes do Agente (End-to-End)

**Comportamento Geral:**
- `test_agent.py` - Teste básico do agente
- `test_agent_improved.py` - Teste aprimorado do agente

**Cenários Específicos:**
- `test_agent_comparisons.py` - Testa perguntas sobre comparações
- `test_agent_compare.py` - Teste de comparações específicas
- `test_agent_history_questions.py` - Testa perguntas sobre histórico (5 cenários)
- `test_context_dantas.py` - Testa contexto sobre o gestor Dantas (3 cenários)

**Validação Final:**
- `test_final_validation.py` - Suite completa de validação

### 📱 Testes de Integração WhatsApp

**Sistema de Mensagens:**
- `test_message_stacking.py` - Testa empilhamento de mensagens (debounce 12s)
- `test_mark_as_read.py` - Testa marcação automática como lida (1.5s)

### 📊 Resultados

- `test_results_20251205_193231.json` - Resultados históricos de testes
- `analyze_tests.py` - Script de análise de resultados

## 🚀 Como Executar

### Teste Individual
```powershell
python tests/test_nome_do_arquivo.py
```

### Teste Específico de Ferramenta
```powershell
# Testar histórico de atividades
python tests/test_activity_history.py

# Testar comparação de períodos
python tests/test_compare_direct.py

# Testar CTR
python tests/test_scale_ctr_direct.py
```

### Testes do Agente Completo
```powershell
# Testar perguntas sobre histórico (5 cenários)
python tests/test_agent_history_questions.py

# Testar contexto Dantas (3 cenários)
python tests/test_context_dantas.py

# Validação completa
python tests/test_final_validation.py
```

### Testes WhatsApp
```powershell
# Testar empilhamento de mensagens
python tests/test_message_stacking.py

# Testar marcação como lida
python tests/test_mark_as_read.py
```

## 📝 Convenções

- **test_*_direct.py** - Testes diretos da API/ferramenta (sem agente)
- **test_agent_*.py** - Testes end-to-end com o agente completo
- **test_*.py** - Testes gerais de funcionalidade

## ⚙️ Pré-requisitos

1. Token do Facebook válido no `.env`
2. Servidor Evolution API rodando (para testes WhatsApp)
3. Banco de dados configurado
4. Virtual environment ativado

## 🎯 Testes Recomendados Após Mudanças

**Após mudanças em tools:**
1. `test_activity_history.py`
2. `test_compare_direct.py`
3. `test_scale_ctr_direct.py`

**Após mudanças no agente:**
1. `test_agent_history_questions.py`
2. `test_context_dantas.py`
3. `test_ctr.py`

**Após mudanças no sistema de mensagens:**
1. `test_message_stacking.py`
2. `test_mark_as_read.py`

## 🐛 Debug

Para ver logs detalhados, os testes incluem prints de:
- 📅 Períodos consultados
- 🔧 Fields solicitados
- 🌐 URLs chamadas
- 📊 Métricas calculadas
- 💬 Respostas do agente
