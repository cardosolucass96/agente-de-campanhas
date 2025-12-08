"""
Teste para verificar detecção de botões em diferentes formatos
"""
import re

def test_button_detection():
    test_cases = [
        # Caso 1: Botões no final separados
        """O CTR da conta Vorp Scale está em 1,54% e o CPC médio é R$ 5,38.

Análise: CTR abaixo de 2%, indicando que pode valer a pena revisar os criativos.

Quer ver o histórico de otimizações?

[🔍 Ver histórico] [📈 Comparar períodos]""",
        
        # Caso 2: Botões juntos
        """Todas as contas estão ativas.

[📊 Desempenho por conta] [🔍 Ver histórico]""",
        
        # Caso 3: 3 botões
        """Resumo das contas:

[📊 Ver CTR] [📈 Comparar] [🔍 Histórico]""",
        
        # Caso 4: Não deve detectar (muito texto depois)
        """Use [isso aqui] para testar, e depois continue lendo muito mais texto aqui."""
    ]
    
    button_pattern = r'\[([^\]]{1,50})\]'
    
    for i, content in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TESTE {i}")
        print(f"{'='*60}")
        print(f"Conteúdo:\n{content[:100]}...")
        
        buttons_found = re.findall(button_pattern, content)
        print(f"\nBotões encontrados: {buttons_found}")
        print(f"Quantidade: {len(buttons_found)}")
        
        # Verificar se estão no final
        last_bracket_pos = content.rfind(']')
        text_after = content[last_bracket_pos+1:].strip()
        print(f"Texto após último ]: '{text_after}' (tamanho: {len(text_after)})")
        
        if buttons_found and 1 <= len(buttons_found) <= 3:
            if len(text_after) < 10:
                print("✅ DETECTARIA COMO BOTÕES")
                
                # Simular criação
                first_bracket_pos = content.find('[' + buttons_found[0] + ']')
                main_text = content[:first_bracket_pos].strip()
                print(f"\nTexto principal (sem botões):\n{main_text}")
            else:
                print("❌ NÃO detectaria (muito texto depois)")
        else:
            print("❌ NÃO detectaria (quantidade inválida)")

if __name__ == "__main__":
    test_button_detection()
