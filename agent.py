"""
Agente de Campanhas usando LangGraph
"""
from typing import TypedDict, Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import os
import traceback
from dotenv import load_dotenv

from tools import AGENT_TOOLS

load_dotenv()


class AgentState(TypedDict):
    """Estado do agente"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    conversation_id: int
    contact_name: str


# Inicializar o modelo
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Bind tools ao modelo
llm_with_tools = llm.bind_tools(AGENT_TOOLS)


def should_continue(state: AgentState):
    """Decide se deve continuar ou encerrar"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Se a última mensagem não tem tool calls, vai para formatação
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "format"
    
    return "continue"


def call_model(state: AgentState):
    """Chama o modelo LLM"""
    messages = state["messages"]
    contact_name = state.get("contact_name")
    
    print(f"🔵 call_model: {len(messages)} mensagens no estado")
    print(f"🔵 Última mensagem: {messages[-1].content[:100] if messages else 'VAZIO'}...")
    
    # Adicionar system prompt se não houver SystemMessage ainda
    from langchain_core.messages import SystemMessage
    from datetime import datetime
    has_system = any(isinstance(msg, SystemMessage) for msg in messages)
    
    if not has_system:
        # Data atual
        hoje = datetime.now()
        data_atual = hoje.strftime('%d/%m/%Y')
        dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][hoje.weekday()]
        
        # Adicionar nome do contato ao prompt se disponível
        name_context = f"\n\n**Informação do contato:**\nVocê está conversando com {contact_name}. Use o nome da pessoa quando apropriado para tornar a conversa mais pessoal." if contact_name else ""
        
        system_msg = SystemMessage(content=f"""Você é um assistente de campanhas do Grupo Vorp, especializado em gerenciamento de anúncios no Facebook.

**DATA E HORA ATUAL:**
Hoje é {dia_semana}, {data_atual}

**Sobre você:**
- Trabalha no Grupo Vorp (empresa de marketing digital)
- Comunica-se via WhatsApp de forma objetiva e profissional
- Especialista em dados de campanhas publicitárias do Facebook
- Sempre apresenta informações de forma resumida e clara para WhatsApp

**CONTEXTO DA EQUIPE:**
- *Lucas Dantas Sa* é o gestor de tráfego principal (pode chamá-lo apenas de "Dantas")
- Ele é o único gestor da equipe, então a maioria das otimizações são feitas por ele
- Quando mencionar "Lucas Dantas Sa" no histórico, refira-se como "Dantas"
- Ações da "Meta" são automáticas do sistema do Facebook

**Suas responsabilidades:**
- Consultar e apresentar dados de contas de anúncio do Facebook
- Fornecer informações sobre saldo, status e desempenho de campanhas
- Responder dúvidas sobre as contas publicitárias da Vorp
- Manter contexto da conversa e se referir a mensagens anteriores quando relevante
- **SER PROATIVO E ANALÍTICO** - não apenas mostrar dados, mas analisar e sugerir próximos passos

**IMPORTANTE - Seja Proativo e Analítico:**

Quando responder, SEMPRE inclua:
1. **Dados principais** (resposta direta à pergunta)
2. **Análise rápida** (o que isso significa? está bom/ruim?)
3. **1 sugestão de próximo passo** (pergunta relevante para continuar)

Exemplos de sugestões contextuais:

*Após mostrar desempenho:*
- "Quer que eu compare com a semana passada?"
- "Vamos ver qual anúncio está performando melhor?"
- "Quer checar se o Dantas otimizou recentemente?"

*Após mostrar CTR/CPC:*
- "Quer comparar com o mês anterior?"
- "Vamos analisar por conjunto de anúncios?"
- "Quer ver a evolução diária?"

*Após mostrar histórico:*
- "Quer ver o impacto dessas mudanças no desempenho?"
- "Vamos comparar antes e depois das otimizações?"
- "Quer que eu monitore por alguns dias?"

*Após comparações:*
- "Quer ver quais anúncios causaram essa mudança?"
- "Vamos checar o histórico de otimizações nesse período?"
- "Quer que eu analise os públicos?"

**Menu Inicial (quando usuário cumprimentar):**
Se usuário disser "oi", "olá", "bom dia", "boa tarde" etc, você DEVE usar a ferramenta send_whatsapp_list para criar um menu interativo com opções como:
- ID 1: "📊 Desempenho" - CTR, CPC e gastos
- ID 2: "📈 Comparações" - Hoje vs ontem, semana vs mês  
- ID 3: "🔍 Histórico" - Ver otimizações
- ID 4: "💰 Saldos" - Status de todas as contas

Chame a ferramenta com body_text cumprimentando o usuário, button_text como "Ver opções" e as options acima.

**IMPORTANTE - Usar Botões Interativos em Sugestões:**
Após apresentar dados/análise, use send_whatsapp_buttons para oferecer 1-2 ações rápidas!

**Quando usar botões (send_whatsapp_buttons):**
✅ Após mostrar desempenho → oferecer 1-2 análises rápidas
✅ Após comparações → oferecer próximos insights
✅ Após histórico → oferecer análise de impacto
✅ Quando há 2-3 opções simples de escolha

**REGRAS CRÍTICAS para botões:**
⚠️ NUNCA escreva botões como texto tipo [Ver conta] [Detalhar] - isso está ERRADO!
✅ SEMPRE use a ferramenta send_whatsapp_buttons para criar botões clicáveis
✅ Máximo 3 botões por mensagem
✅ Use 1-2 botões normalmente (3 apenas se essencial)
✅ Título do botão: máximo 20 caracteres
✅ Texto curto e direto (use emojis)

**Como usar corretamente:**
ERRADO ❌: "Quer ver mais? [Ver CTR] [Comparar]"
CERTO ✅: Chamar send_whatsapp_buttons com body_text="Quer ver mais?" e buttons=[...] 

**Exemplos de uso correto da ferramenta:**

*Após mostrar desempenho geral:*
SEMPRE chame: send_whatsapp_buttons
  - body_text: "Quer analisar algo específico?"
  - buttons: [id="1" title="📊 Ver CTR/CPC", id="2" title="📈 Comparar"]

*Após mostrar desempenho de uma conta:*
SEMPRE chame: send_whatsapp_buttons
  - body_text: "Quer ver mais detalhes?"
  - buttons: [id="1" title="🔍 Ver otimizações", id="2" title="📊 Outra conta"]

*Após mostrar comparação:*
SEMPRE chame: send_whatsapp_buttons
  - body_text: "Performance mudou. Investigar?"
  - buttons: [id="1" title="🎯 Ver anúncios", id="2" title="🔧 Otimizações"]

*Após mostrar histórico:*
SEMPRE chame: send_whatsapp_buttons
  - body_text: "Ver impacto das mudanças?"
  - buttons: [id="1" title="📈 Antes vs Depois"]

**FLUXO COM FERRAMENTAS DE INTERAÇÃO (Listas/Botões):**
Quando usar send_whatsapp_list ou send_whatsapp_buttons:
1. Chame a ferramenta PRIMEIRO com as opções
2. O sistema processará e enviará a interface interativa
3. DEPOIS, escreva UMA mensagem curta (1-2 linhas) confirmando ou contextualizando

**IMPORTANTE:**
- SEMPRE use a FERRAMENTA send_whatsapp_buttons após apresentar dados
- NUNCA escreva botões como texto entre colchetes []
- Se você quer sugerir opções, DEVE usar a ferramenta
- Não use listas (send_whatsapp_list) para sugestões, apenas no menu inicial!
- SEMPRE escreva uma mensagem de acompanhamento após chamar ferramentas de interação

**Análise Inteligente:**
- Se CTR > 2%: "Excelente! CTR acima da média"
- Se CTR < 1%: "CTR baixo, talvez valha revisar criativos"
- Se CPC subiu muito: "CPC aumentou bastante, pode ser saturação"
- Sem otimizações 7+ dias: "Conta sem otimizações há mais de uma semana"
- Muitas otimizações: "Dantas está acompanhando bem"

**FERRAMENTAS DISPONÍVEIS - USE A FERRAMENTA CERTA:**

1. **get_facebook_ad_accounts** - Lista contas com status e saldo
   Use quando: "quais contas", "liste as contas", "me mostre as contas"
   NÃO use para: dados de campanhas ou desempenho

2. **find_account_by_name** - Encontra ID da conta pelo nome
   Use quando: usuário menciona nome da conta mas você precisa do ID
   SEMPRE use antes de get_campaign_insights quando tiver só o nome!

3. **get_campaign_insights** - Busca dados de UMA conta específica
   Use quando: "como está a conta X", "campanhas da conta Y", "desempenho de Z"
   Precisa do ID da conta (use find_account_by_name se tiver só o nome)

4. **get_all_accounts_insights** - Resumo de TODAS as contas
   Use quando: "como estão as campanhas", "visão geral", "todas as contas", "resumo geral"
   É a ferramenta ideal para começar!

5. **compare_campaign_periods** - Comparar métricas entre períodos
   Use quando: "compare semana passada", "vs mês anterior", "crescimento/queda"
   Tipos: week_vs_previous, month_vs_previous, week_vs_month, current_vs_last_month
   SEMPRE use quando usuário pedir comparação ou vs entre períodos!

6. **get_activity_history** - Histórico de edições e atividades
   Use quando: "histórico da conta", "últimas edições", "o que mudou", "gestor está acompanhando"
   Mostra otimizações, pausas, mudanças de orçamento, criações
   Útil para avaliar se há gestão ativa da conta!

7. **get_facebook_business_info** - Info do Business Manager
8. **calculate_ad_budget** - Calcular orçamento
9. **send_whatsapp_message** - Enviar mensagem
10. **send_whatsapp_list** - Enviar lista interativa com botões (USE para cumprimentos e menus de opções!)
   Use quando: usuário cumprimentar ("oi", "olá", "bom dia") ou quando precisar dar múltiplas opções
   SEMPRE use para menu inicial após cumprimento!

**IMPORTANTE - Formatação:**
- Use APENAS formatação do WhatsApp: *negrito*, _itálico_, ~tachado~
- NUNCA use Markdown (##, ###, **, `, etc)
- Use emojis quando apropriado (📊, ✅, ⚠️, 💰)
- Formate números monetários como R$ 123,45
- Mantenha respostas CONCISAS e bem estruturadas

**IMPORTANTE - Estrutura das Respostas:**
Para manter mensagens limpas e objetivas:
1. Dados principais (1-2 linhas)
2. Análise rápida (1-2 linhas) 
3. 1 sugestão de próximo passo (sem cabeçalho)

Exemplo BOM:
"O CTR da Scale está em 1,57%.

*Análise:* CTR baixo, vale revisar criativos.

Quer comparar com o mês anterior?"

Exemplo RUIM (muito verboso):
"Olá! Vou te mostrar o CTR da conta Scale... [texto longo]
O CTR está em 1,57% e isso significa que... [explicação longa]
Quer que eu compare com o período anterior para você poder ver se..."

**Seja direto, objetivo e organize bem a informação!**

**IMPORTANTE - Datas:**
Hoje é {dia_semana}, {data_atual}

PERÍODO PADRÃO: Sempre use os ÚLTIMOS 7 DIAS (sem passar start_date/end_date)
- NUNCA invente ou calcule datas manualmente
- Para "última semana", "como estão as campanhas", "desempenho", etc → NÃO passe start_date/end_date
- As ferramentas calculam automaticamente baseado na data de HOJE ({data_atual})
- Só passe datas se o usuário especificar uma data exata (ex: "desde 01/11")

IMPORTANTE: Os dados são sempre dos últimos 7 dias completos (até ontem).

**IMPORTANTE - Saldos das Contas:**
O campo "saldo" (balance) retornado pela API do Facebook é o SALDO DEVEDOR.
- Todas as contas estão configuradas com CARTÃO DE CRÉDITO
- Saldo R$ 0,00 = Tudo está pago, não há dívidas pendentes ✅
- Saldo R$ 500,00 = Há R$ 500,00 devedor a pagar ⚠️
- NUNCA interprete saldo zerado como problema! Saldo zero é o ideal (significa conta em dia)

Seja prestativo e sempre confirme as ações realizadas.{name_context}""")
        messages = [system_msg] + messages
    
    print(f"🔵 Invocando LLM com {len(messages)} mensagens...")
    try:
        response = llm_with_tools.invoke(messages)
        print(f"🔵 LLM respondeu: {type(response)}")
        
        # Debug detalhado do response
        if hasattr(response, 'content'):
            content_str = str(response.content) if response.content else "VAZIO"
            print(f"🔵 Conteúdo (len={len(content_str)}): {content_str[:100]}...")
        else:
            print(f"🔵 Response não tem 'content'")
            
        if hasattr(response, 'tool_calls'):
            print(f"🔵 Tem tool_calls: {len(response.tool_calls) > 0}")
            if response.tool_calls:
                print(f"🔵 Tool calls: {[tc['name'] for tc in response.tool_calls]}")
        
        # Se response vazio, logar tudo
        if not response.content and (not hasattr(response, 'tool_calls') or not response.tool_calls):
            print(f"❌ RESPONSE COMPLETAMENTE VAZIO!")
            print(f"❌ Response completo: {response}")
            print(f"❌ Response dict: {response.dict() if hasattr(response, 'dict') else 'N/A'}")
            
    except Exception as e:
        print(f"❌ Erro ao invocar LLM: {e}")
        print(f"❌ Tipo do erro: {type(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    return {"messages": [response]}


def format_for_whatsapp(state: AgentState):
    """Formata a mensagem final para WhatsApp"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage) and not hasattr(last_message, "tool_calls"):
        content = last_message.content
        
        # Converter Markdown para WhatsApp
        import re
        
        # DETECTAR E CONVERTER BOTÕES ESCRITOS COMO TEXTO EM BOTÕES REAIS
        # Padrões aceitos:
        # - [texto do botão]
        # - [emoji texto]
        # - Geralmente aparecem no final da mensagem, em sequência
        
        # Procurar por 1-3 botões seguidos no final ou na última linha
        button_pattern = r'\[([^\]]{1,50})\]'
        
        # Encontrar todas as ocorrências de botões
        buttons_found = re.findall(button_pattern, content)
        
        # Filtrar apenas os últimos botões (provavelmente são sugestões)
        # Pegar os últimos 2-3 colchetes encontrados
        if buttons_found and 1 <= len(buttons_found) <= 3:
            # Verificar se há quebra de linha após a última ocorrência ou se estão no final
            last_bracket_pos = content.rfind(']')
            text_after_bracket = content[last_bracket_pos+1:].strip()
            
            # Se não há texto significativo após os colchetes, são botões
            if len(text_after_bracket) < 10:  # Pouco ou nenhum texto depois
                print(f"🔧 Detectados {len(buttons_found)} botões no final: {buttons_found}")
                
                # Encontrar onde começam os botões no texto
                first_bracket_pos = content.find('[' + buttons_found[0] + ']')
                
                # Separar texto principal dos botões
                main_text = content[:first_bracket_pos].strip()
                
                # Criar botões reais
                import tools.whatsapp_buttons
                
                buttons = []
                for i, btn_text in enumerate(buttons_found[:3], 1):  # Máximo 3
                    clean_btn = btn_text.strip()
                    # Truncar se muito longo
                    if len(clean_btn) > 20:
                        clean_btn = clean_btn[:17] + "..."
                    buttons.append({
                        "id": str(i),
                        "title": clean_btn
                    })
                
                # Definir botões pendentes
                tools.whatsapp_buttons.pending_buttons = {
                    "type": "button",
                    "body": {"text": main_text},
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": btn["id"],
                                    "title": btn["title"]
                                }
                            }
                            for btn in buttons
                        ]
                    }
                }
                
                print(f"✅ Criados {len(buttons)} botões: {[b['title'] for b in buttons]}")
                
                # Atualizar conteúdo sem os colchetes
                last_message.content = main_text
                return {"messages": messages}
        
        # Se não encontrou padrão de botões, manter colchetes
        # (podem ser parte legítima do texto, ex: [Vorp Scale])
        # Apenas remover se houver múltiplos colchetes vazios/suspeitos consecutivos
        # Por ora, não remover nada - deixar como está
        
        # Headers ## -> negrito
        content = re.sub(r'###?\s+(.*?)(?:\n|$)', r'*\1*\n', content)
        
        # Markdown bold ** -> WhatsApp bold *
        content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)
        
        # Markdown code ` -> remover
        content = re.sub(r'`(.*?)`', r'\1', content)
        
        # Remover links markdown [texto](url) -> texto (url)
        # Cuidado para não remover se já removemos botões
        if '(' in content and ')' in content:
            content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', content)
        
        # Limpar quebras de linha excessivas (mais de 2 seguidas)
        content = re.sub(r'\n{3,}', r'\n\n', content)
        
        # Limpar espaços no final de linhas
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # Atualizar a mensagem
        last_message.content = content.strip()
    
    return {"messages": messages}




async def call_tools(state: AgentState):
    """Execute tools based on the agent's tool calls (async support)"""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_calls = last_message.tool_calls if hasattr(last_message, 'tool_calls') else []
    tool_messages = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        # Find and execute the tool
        tool = next((t for t in AGENT_TOOLS if t.name == tool_name), None)
        if tool:
            try:
                # Use ainvoke for async invocation (required in newer LangChain versions)
                result = await tool.ainvoke(tool_args)
                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_id)
                )
            except Exception as e:
                print(f"❌ Erro ao executar tool {tool_name}: {e}")
                traceback.print_exc()
                tool_messages.append(
                    ToolMessage(content=f"Error: {str(e)}", tool_call_id=tool_id)
                )
    
    return {"messages": tool_messages}


# Criar o grafo
workflow = StateGraph(AgentState)

# Adicionar nós
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
workflow.add_node("format_whatsapp", format_for_whatsapp)

# Definir o ponto de entrada
workflow.set_entry_point("agent")

# Adicionar edges condicionais
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "format": "format_whatsapp"
    }
)

# Adicionar edge da tool de volta para o agente
workflow.add_edge("tools", "agent")

# Adicionar edge final após formatação
workflow.add_edge("format_whatsapp", END)

# Compilar o grafo
agent_graph = workflow.compile()


async def run_agent(message: str, conversation_id: int = None, previous_messages: list = None, contact_name: str = None) -> str:
    """
    Executa o agente com uma mensagem
    
    Args:
        message: Mensagem atual do usuário
        conversation_id: ID da conversação
        previous_messages: Lista de mensagens anteriores do banco de dados (últimas 5)
        contact_name: Nome do contato para personalização
    
    Returns:
        Resposta do agente
    """
    # Construir histórico de mensagens
    messages = []
    
    # Adicionar mensagens anteriores ao contexto
    if previous_messages:
        for msg in previous_messages:
            if msg.direction == "incoming":
                messages.append(HumanMessage(content=msg.text))
            elif msg.direction == "outgoing":
                messages.append(AIMessage(content=msg.text))
    
    # Adicionar mensagem atual
    messages.append(HumanMessage(content=message))
    
    initial_state = {
        "messages": messages,
        "conversation_id": conversation_id,
        "contact_name": contact_name
    }
    
    result = await agent_graph.ainvoke(initial_state)
    
    # Retornar a última mensagem do agente
    last_message = result["messages"][-1]
    response = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Validar resposta não vazia
    if not response or not response.strip():
        print("⚠️ Agente retornou resposta vazia, usando fallback")
        return "Desculpe, não consegui processar sua solicitação. Pode reformular a pergunta?"
    
    return response


# NOTA: O system prompt real está implementado dentro da função call_model() (linhas ~64-261)
# Ele é inserido dinamicamente em cada chamada ao LLM com contexto atualizado (data, nome do contato, etc)
