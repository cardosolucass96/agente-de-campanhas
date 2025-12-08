"""
Script de teste para verificar se o agente está usando botões e listas corretamente
"""
import asyncio
from agent import run_agent

async def test_agent():
    print("=" * 60)
    print("TESTE 1: Mensagem de desempenho (deve mostrar BOTÕES)")
    print("=" * 60)
    
    # Simular mensagem de desempenho
    response = await run_agent(
        message="Desempenho",
        conversation_id=9999,
        contact_name="Teste"
    )
    
    print("\n📤 RESPOSTA DO AGENTE:")
    print(response)
    
    print("\n" + "=" * 60)
    print("TESTE 2: Cumprimento (deve mostrar LISTA - menu)")
    print("=" * 60)
    
    # Simular cumprimento
    response2 = await run_agent(
        message="Oi, bom dia!",
        conversation_id=9999,
        contact_name="Teste"
    )
    
    print("\n📤 RESPOSTA DO AGENTE:")
    print(response2)
    
    print("\n" + "=" * 60)
    print("TESTE 3: Comparação (deve mostrar BOTÕES)")
    print("=" * 60)
    
    # Simular pedido de comparação
    response3 = await run_agent(
        message="Comparar esta semana com a anterior",
        conversation_id=9999,
        contact_name="Teste"
    )
    
    print("\n📤 RESPOSTA DO AGENTE:")
    print(response3)

if __name__ == "__main__":
    asyncio.run(test_agent())
