"""
Calculadora de custo de tokens para conversas com o agente
Baseado nos preços do GPT-4.1-mini
"""

# Preços do GPT-4o-mini (modelo usado: gpt-4.1-mini é alias)
# Fonte: https://openai.com/api/pricing/
PRICE_PER_1M_INPUT_TOKENS = 0.150  # $0.150 por 1M tokens de entrada
PRICE_PER_1M_OUTPUT_TOKENS = 0.600  # $0.600 por 1M tokens de saída

# Cotação dólar (ajustar conforme necessário)
USD_TO_BRL = 6.10


def estimate_tokens(text: str) -> int:
    """
    Estima número de tokens em um texto.
    Regra aproximada: 1 token ≈ 4 caracteres em inglês, ~3 em português
    """
    # Para português, usar fator mais conservador
    return len(text) // 3


def calculate_system_prompt_tokens() -> int:
    """
    Calcula tokens do system prompt (enviado em toda mensagem)
    """
    # O system prompt do agent.py tem aproximadamente:
    # - Instruções gerais: ~500 tokens
    # - Ferramentas descritas: ~800 tokens
    # - Exemplos e contexto: ~700 tokens
    # Total estimado: ~2000 tokens
    return 2000


def calculate_conversation_cost(num_messages: int = 10):
    """
    Calcula custo estimado de uma conversa com N mensagens
    
    Cenário:
    - Usuário envia mensagem (~50 tokens)
    - System prompt é incluído (~2000 tokens)
    - Histórico das últimas 5 mensagens (~300 tokens)
    - Agent responde (~200 tokens)
    - Se usar ferramenta, faz 2 chamadas (tool call + resposta final)
    """
    
    print("=" * 70)
    print("CALCULADORA DE CUSTO - AGENTE DE CAMPANHAS")
    print("=" * 70)
    print(f"\nModelo: gpt-4.1-mini (GPT-4o-mini)")
    print(f"Preço Input: ${PRICE_PER_1M_INPUT_TOKENS} por 1M tokens")
    print(f"Preço Output: ${PRICE_PER_1M_OUTPUT_TOKENS} por 1M tokens")
    print(f"Cotação: R$ {USD_TO_BRL}/USD")
    print()
    
    # Tokens fixos por mensagem
    system_prompt_tokens = calculate_system_prompt_tokens()
    user_message_tokens = 50  # Média de uma pergunta
    history_tokens = 300  # Últimas 5 mensagens de contexto
    agent_response_tokens = 200  # Resposta média
    tool_result_tokens = 500  # Resultado de ferramenta (dados Facebook)
    
    # Cenários
    print("─" * 70)
    print("CENÁRIO 1: Conversa simples (sem ferramentas)")
    print("─" * 70)
    
    total_input_tokens = 0
    total_output_tokens = 0
    
    for i in range(1, num_messages + 1):
        # Cada mensagem do usuário
        msg_input = system_prompt_tokens + user_message_tokens
        msg_output = agent_response_tokens
        
        # A partir da 2ª mensagem, adiciona histórico
        if i > 1:
            msg_input += min(history_tokens, (i-1) * (user_message_tokens + agent_response_tokens))
        
        total_input_tokens += msg_input
        total_output_tokens += msg_output
    
    cost_input_simple = (total_input_tokens / 1_000_000) * PRICE_PER_1M_INPUT_TOKENS
    cost_output_simple = (total_output_tokens / 1_000_000) * PRICE_PER_1M_OUTPUT_TOKENS
    total_cost_simple_usd = cost_input_simple + cost_output_simple
    total_cost_simple_brl = total_cost_simple_usd * USD_TO_BRL
    
    print(f"Total Input Tokens: {total_input_tokens:,}")
    print(f"Total Output Tokens: {total_output_tokens:,}")
    print(f"Custo Input: ${cost_input_simple:.4f}")
    print(f"Custo Output: ${cost_output_simple:.4f}")
    print(f"Custo Total (USD): ${total_cost_simple_usd:.4f}")
    print(f"Custo Total (BRL): R$ {total_cost_simple_brl:.4f}")
    print()
    
    # Cenário com ferramentas
    print("─" * 70)
    print("CENÁRIO 2: Conversa com uso de ferramentas (50% das mensagens)")
    print("─" * 70)
    
    total_input_tokens_tools = 0
    total_output_tokens_tools = 0
    
    for i in range(1, num_messages + 1):
        # Cada mensagem do usuário
        msg_input = system_prompt_tokens + user_message_tokens
        
        # A partir da 2ª mensagem, adiciona histórico
        if i > 1:
            msg_input += min(history_tokens, (i-1) * (user_message_tokens + agent_response_tokens))
        
        # 50% das mensagens usam ferramentas (2 chamadas ao LLM)
        if i % 2 == 0:
            # Primeira chamada: LLM decide usar ferramenta
            total_input_tokens_tools += msg_input
            total_output_tokens_tools += 100  # Tool call (pequeno)
            
            # Segunda chamada: LLM processa resultado da ferramenta
            total_input_tokens_tools += msg_input + tool_result_tokens
            total_output_tokens_tools += agent_response_tokens
        else:
            # Mensagem simples, sem ferramenta
            total_input_tokens_tools += msg_input
            total_output_tokens_tools += agent_response_tokens
    
    cost_input_tools = (total_input_tokens_tools / 1_000_000) * PRICE_PER_1M_INPUT_TOKENS
    cost_output_tools = (total_output_tokens_tools / 1_000_000) * PRICE_PER_1M_OUTPUT_TOKENS
    total_cost_tools_usd = cost_input_tools + cost_output_tools
    total_cost_tools_brl = total_cost_tools_usd * USD_TO_BRL
    
    print(f"Total Input Tokens: {total_input_tokens_tools:,}")
    print(f"Total Output Tokens: {total_output_tokens_tools:,}")
    print(f"Custo Input: ${cost_input_tools:.4f}")
    print(f"Custo Output: ${cost_output_tools:.4f}")
    print(f"Custo Total (USD): ${total_cost_tools_usd:.4f}")
    print(f"Custo Total (BRL): R$ {total_cost_tools_brl:.4f}")
    print()
    
    # Cenário intensivo
    print("─" * 70)
    print("CENÁRIO 3: Conversa intensiva (100% usa ferramentas complexas)")
    print("─" * 70)
    
    total_input_tokens_intensive = 0
    total_output_tokens_intensive = 0
    
    for i in range(1, num_messages + 1):
        msg_input = system_prompt_tokens + user_message_tokens
        
        if i > 1:
            msg_input += min(history_tokens, (i-1) * (user_message_tokens + agent_response_tokens))
        
        # Todas as mensagens usam ferramentas
        # Primeira chamada: Tool decision
        total_input_tokens_intensive += msg_input
        total_output_tokens_intensive += 100
        
        # Segunda chamada: Process tool result
        total_input_tokens_intensive += msg_input + tool_result_tokens
        total_output_tokens_intensive += agent_response_tokens
    
    cost_input_intensive = (total_input_tokens_intensive / 1_000_000) * PRICE_PER_1M_INPUT_TOKENS
    cost_output_intensive = (total_output_tokens_intensive / 1_000_000) * PRICE_PER_1M_OUTPUT_TOKENS
    total_cost_intensive_usd = cost_input_intensive + cost_output_intensive
    total_cost_intensive_brl = total_cost_intensive_usd * USD_TO_BRL
    
    print(f"Total Input Tokens: {total_input_tokens_intensive:,}")
    print(f"Total Output Tokens: {total_output_tokens_intensive:,}")
    print(f"Custo Input: ${cost_input_intensive:.4f}")
    print(f"Custo Output: ${cost_output_intensive:.4f}")
    print(f"Custo Total (USD): ${total_cost_intensive_usd:.4f}")
    print(f"Custo Total (BRL): R$ {total_cost_intensive_brl:.4f}")
    print()
    
    # Resumo
    print("=" * 70)
    print("RESUMO - CUSTO POR MENSAGEM")
    print("=" * 70)
    print(f"Simples (sem ferramentas): R$ {total_cost_simple_brl/num_messages:.4f} por mensagem")
    print(f"Moderado (50% ferramentas): R$ {total_cost_tools_brl/num_messages:.4f} por mensagem")
    print(f"Intensivo (100% ferramentas): R$ {total_cost_intensive_brl/num_messages:.4f} por mensagem")
    print()
    
    # Projeção mensal
    print("=" * 70)
    print("PROJEÇÃO MENSAL (baseado em uso)")
    print("=" * 70)
    
    # Exemplo: 100 conversas/dia, 10 mensagens cada
    conversations_per_day = 100
    messages_per_conversation = num_messages
    days_per_month = 30
    
    monthly_cost_simple = total_cost_simple_brl * conversations_per_day * days_per_month / num_messages * messages_per_conversation
    monthly_cost_moderate = total_cost_tools_brl * conversations_per_day * days_per_month / num_messages * messages_per_conversation
    monthly_cost_intensive = total_cost_intensive_brl * conversations_per_day * days_per_month / num_messages * messages_per_conversation
    
    print(f"Uso: {conversations_per_day} conversas/dia × {messages_per_conversation} msgs × {days_per_month} dias")
    print(f"  Simples: R$ {monthly_cost_simple:.2f}/mês")
    print(f"  Moderado: R$ {monthly_cost_moderate:.2f}/mês")
    print(f"  Intensivo: R$ {monthly_cost_intensive:.2f}/mês")
    print()
    
    print("=" * 70)
    print("OBSERVAÇÕES:")
    print("=" * 70)
    print("• Valores são ESTIMATIVAS baseadas em médias")
    print("• System prompt (~2000 tokens) é enviado em TODA chamada ao LLM")
    print("• Conversas com ferramentas fazem 2+ chamadas ao LLM por mensagem")
    print("• Histórico de conversa aumenta tokens de input progressivamente")
    print("• GPT-4.1-mini é significativamente mais barato que GPT-4")
    print("• Preços podem mudar - verificar: https://openai.com/api/pricing/")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    # Permitir passar número de mensagens como argumento
    num_msgs = 10
    if len(sys.argv) > 1:
        try:
            num_msgs = int(sys.argv[1])
        except:
            print("Uso: python calculate_token_cost.py [num_mensagens]")
            sys.exit(1)
    
    calculate_conversation_cost(num_msgs)
