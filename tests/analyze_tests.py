"""
Script de análise dos resultados dos testes
Avalia qualidade das respostas e identifica melhorias necessárias
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def load_test_results(filename):
    """Carrega resultados de um arquivo JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {filename}")
        return None


def analyze_response_quality(result):
    """
    Analisa a qualidade de uma resposta
    Retorna um score de 0-10 e observações
    """
    if result['status'] == 'error':
        return 0, ["ERRO na execução"]
    
    response = result['response']
    observations = []
    score = 10  # Começa com pontuação máxima
    
    # Critério 1: Resposta não vazia
    if not response or len(response.strip()) < 10:
        score -= 5
        observations.append("⚠️ Resposta muito curta ou vazia")
    
    # Critério 2: Formatação WhatsApp (não deve ter Markdown)
    markdown_indicators = ['##', '###', '```', '**', '`']
    has_markdown = any(indicator in response for indicator in markdown_indicators)
    if has_markdown:
        score -= 2
        observations.append("⚠️ Contém formatação Markdown (deveria ser WhatsApp)")
    
    # Critério 3: Uso de emojis (positivo)
    if any(char in response for char in ['📊', '💰', '✅', '❌', '📈', '👥', '🖱️', '💵']):
        observations.append("✅ Usa emojis apropriadamente")
    else:
        score -= 1
        observations.append("⚠️ Poderia usar mais emojis")
    
    # Critério 4: Formatação WhatsApp (*negrito*, _itálico_)
    if '*' in response or '_' in response:
        observations.append("✅ Usa formatação WhatsApp")
    else:
        observations.append("ℹ️ Sem formatação de texto")
    
    # Critério 5: Tamanho apropriado (não muito longo para WhatsApp)
    if len(response) > 2000:
        score -= 1
        observations.append("⚠️ Resposta muito longa para WhatsApp")
    
    # Critério 6: Responde à pergunta
    question = result['question'].lower()
    response_lower = response.lower()
    
    # Verificar palavras-chave relevantes
    if 'conta' in question and 'conta' not in response_lower:
        score -= 2
        observations.append("⚠️ Pergunta sobre contas, mas resposta não menciona")
    
    if 'campanha' in question and 'campanha' not in response_lower:
        score -= 2
        observations.append("⚠️ Pergunta sobre campanhas, mas resposta não menciona")
    
    # Critério 7: Tempo de resposta
    duration = result.get('duration_seconds', 0)
    if duration > 10:
        score -= 1
        observations.append(f"⚠️ Tempo de resposta longo: {duration:.2f}s")
    elif duration < 5:
        observations.append(f"✅ Resposta rápida: {duration:.2f}s")
    
    # Critério 8: Uso de dados numéricos quando apropriado
    if any(word in question for word in ['quanto', 'valor', 'custo', 'resultado', 'desempenho']):
        if any(char.isdigit() for char in response):
            observations.append("✅ Inclui dados numéricos")
        else:
            score -= 2
            observations.append("⚠️ Deveria incluir dados numéricos")
    
    return max(0, score), observations


def generate_detailed_report(results):
    """Gera relatório detalhado com análise de cada resposta"""
    
    print("\n" + "="*100)
    print("📋 RELATÓRIO DETALHADO DE ANÁLISE")
    print("="*100 + "\n")
    
    categories = {}
    all_scores = []
    
    for result in results:
        category = result['category']
        if category not in categories:
            categories[category] = []
        
        score, observations = analyze_response_quality(result)
        all_scores.append(score)
        
        categories[category].append({
            'result': result,
            'score': score,
            'observations': observations
        })
    
    # Análise por categoria
    for category, items in categories.items():
        print(f"\n{'─'*100}")
        print(f"📁 CATEGORIA: {category.upper()}")
        print(f"{'─'*100}\n")
        
        avg_score = sum(item['score'] for item in items) / len(items)
        print(f"Score médio da categoria: {avg_score:.1f}/10\n")
        
        for idx, item in enumerate(items, 1):
            result = item['result']
            score = item['score']
            observations = item['observations']
            
            print(f"\n[{idx}] Pergunta: {result['question']}")
            print(f"    Score: {score}/10")
            print(f"    Tempo: {result.get('duration_seconds', 0):.2f}s")
            print(f"    Status: {result['status']}")
            
            if observations:
                print(f"    Observações:")
                for obs in observations:
                    print(f"      - {obs}")
            
            # Mostrar resposta resumida
            if result['status'] == 'success':
                response_preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                print(f"    Resposta: {response_preview}")
            else:
                print(f"    Erro: {result.get('error', 'Desconhecido')}")
    
    # Resumo geral
    print(f"\n\n{'='*100}")
    print("📊 RESUMO GERAL")
    print(f"{'='*100}\n")
    
    avg_overall = sum(all_scores) / len(all_scores) if all_scores else 0
    print(f"Score médio geral: {avg_overall:.1f}/10")
    print(f"Total de testes: {len(results)}")
    print(f"Sucessos: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"Erros: {sum(1 for r in results if r['status'] == 'error')}")
    
    # Distribuição de scores
    print(f"\nDistribuição de scores:")
    score_ranges = {
        "Excelente (9-10)": sum(1 for s in all_scores if s >= 9),
        "Bom (7-8)": sum(1 for s in all_scores if 7 <= s < 9),
        "Regular (5-6)": sum(1 for s in all_scores if 5 <= s < 7),
        "Ruim (0-4)": sum(1 for s in all_scores if s < 5),
    }
    
    for range_name, count in score_ranges.items():
        percentage = (count / len(all_scores) * 100) if all_scores else 0
        print(f"  {range_name}: {count} ({percentage:.1f}%)")


def identify_improvements(results):
    """Identifica melhorias necessárias baseadas nos resultados"""
    
    print(f"\n\n{'='*100}")
    print("🔧 MELHORIAS RECOMENDADAS")
    print(f"{'='*100}\n")
    
    improvements = []
    
    # Analisar problemas comuns
    markdown_count = 0
    slow_responses = 0
    long_responses = 0
    missing_data = 0
    errors = 0
    
    for result in results:
        if result['status'] == 'error':
            errors += 1
            continue
        
        response = result['response']
        duration = result.get('duration_seconds', 0)
        
        if any(indicator in response for indicator in ['##', '###', '```', '**', '`']):
            markdown_count += 1
        
        if duration > 10:
            slow_responses += 1
        
        if len(response) > 2000:
            long_responses += 1
        
        question = result['question'].lower()
        if any(word in question for word in ['quanto', 'valor', 'custo']) and not any(char.isdigit() for char in response):
            missing_data += 1
    
    # Gerar recomendações
    if errors > 0:
        improvements.append(f"❌ {errors} erros durante execução - verificar logs e tratamento de exceções")
    
    if markdown_count > len(results) * 0.2:
        improvements.append(f"⚠️ {markdown_count} respostas com Markdown - melhorar nó de formatação WhatsApp")
    
    if slow_responses > len(results) * 0.3:
        improvements.append(f"🐌 {slow_responses} respostas lentas (>10s) - otimizar chamadas à API")
    
    if long_responses > len(results) * 0.2:
        improvements.append(f"📏 {long_responses} respostas muito longas - implementar quebra de mensagens")
    
    if missing_data > len(results) * 0.2:
        improvements.append(f"📊 {missing_data} respostas sem dados numéricos quando esperado - verificar tools")
    
    if not improvements:
        print("✅ Nenhuma melhoria crítica identificada!")
        print("   O agente está funcionando bem nos testes.")
    else:
        print("Melhorias identificadas:\n")
        for idx, improvement in enumerate(improvements, 1):
            print(f"{idx}. {improvement}")
    
    print()


if __name__ == "__main__":
    # Buscar arquivo de resultados mais recente ou usar argumento
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Buscar arquivo mais recente
        test_files = sorted(Path('.').glob('test_results_*.json'), reverse=True)
        if not test_files:
            print("❌ Nenhum arquivo de resultados encontrado!")
            print("Execute primeiro: python test_agent.py")
            sys.exit(1)
        filename = str(test_files[0])
        print(f"📂 Usando arquivo mais recente: {filename}\n")
    
    results = load_test_results(filename)
    
    if results:
        generate_detailed_report(results)
        identify_improvements(results)
        
        # Salvar relatório em arquivo
        report_file = filename.replace('.json', '_report.txt')
        print(f"\n💾 Relatório completo pode ser salvo em: {report_file}")
