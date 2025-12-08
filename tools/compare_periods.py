"""
Tool para comparar métricas de campanhas entre diferentes períodos
"""
import httpx
import os
import asyncio
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def compare_campaign_periods(
    ad_account_id: str,
    period_type: str = "week_vs_previous",
    metrics: str = "ctr,cpc,spend,impressions",
    level: str = "campaign"
) -> str:
    """
    Compara métricas de campanhas entre dois períodos diferentes.
    Retorna análise comparativa mostrando crescimento/queda em %.
    
    TIPOS DE COMPARAÇÃO DISPONÍVEIS (period_type):
    - "week_vs_previous": Última semana vs semana anterior
    - "month_vs_previous": Último mês vs mês anterior
    - "week_vs_month": Últimos 7 dias vs 30 dias anteriores
    - "current_vs_last_month": Mês atual vs mês passado
    
    MÉTRICAS DISPONÍVEIS (metrics, separadas por vírgula):
    - ctr: taxa de cliques (%)
    - cpc: custo por clique (R$)
    - cpm: custo por mil impressões (R$)
    - spend: gasto total (R$)
    - impressions: impressões totais
    - reach: alcance (pessoas únicas)
    - clicks: cliques totais
    - conversions: conversões totais
    - frequency: frequência média
    
    EXEMPLOS DE USO:
    - "compare CTR da semana passada com a anterior" → period_type="week_vs_previous", metrics="ctr"
    - "mês passado vs anterior em gastos e CPC" → period_type="month_vs_previous", metrics="spend,cpc"
    - "últimos 7 dias vs 30 dias anteriores" → period_type="week_vs_month", metrics="ctr,spend"
    
    Args:
        ad_account_id: ID da conta (ex: act_123456789 ou apenas 123456789)
        period_type: Tipo de comparação (veja lista acima)
        metrics: Métricas para comparar separadas por vírgula
        level: "campaign" (padrão), "adset" ou "ad"
    
    Returns:
        Análise comparativa formatada com % de crescimento/queda
    """
    try:
        # Garantir que o ad_account_id tenha o prefixo 'act_'
        if not ad_account_id.startswith('act_'):
            ad_account_id = f'act_{ad_account_id}'
        
        # Calcular períodos com base no tipo
        hoje = datetime.now()
        
        if period_type == "week_vs_previous":
            # Última semana (7 dias atrás até ontem)
            period1_end = hoje - timedelta(days=1)
            period1_start = hoje - timedelta(days=7)
            # Semana anterior (14 dias atrás até 8 dias atrás)
            period2_end = hoje - timedelta(days=8)
            period2_start = hoje - timedelta(days=14)
            period1_name = "Última Semana"
            period2_name = "Semana Anterior"
            
        elif period_type == "month_vs_previous":
            # Último mês (30 dias atrás até ontem)
            period1_end = hoje - timedelta(days=1)
            period1_start = hoje - timedelta(days=30)
            # Mês anterior (60 dias atrás até 31 dias atrás)
            period2_end = hoje - timedelta(days=31)
            period2_start = hoje - timedelta(days=60)
            period1_name = "Último Mês"
            period2_name = "Mês Anterior"
            
        elif period_type == "week_vs_month":
            # Últimos 7 dias
            period1_end = hoje - timedelta(days=1)
            period1_start = hoje - timedelta(days=7)
            # 30 dias anteriores
            period2_end = hoje - timedelta(days=8)
            period2_start = hoje - timedelta(days=37)
            period1_name = "Últimos 7 Dias"
            period2_name = "30 Dias Anteriores"
            
        elif period_type == "current_vs_last_month":
            # Mês atual (desde dia 1 até hoje)
            period1_end = hoje
            period1_start = hoje.replace(day=1)
            # Mês passado (todo o mês anterior)
            last_month = hoje.replace(day=1) - timedelta(days=1)
            period2_end = last_month
            period2_start = last_month.replace(day=1)
            period1_name = "Mês Atual"
            period2_name = "Mês Passado"
            
        else:
            return f"❌ Tipo de período inválido: {period_type}. Use: week_vs_previous, month_vs_previous, week_vs_month, current_vs_last_month"
        
        # Formatar datas
        p1_start = period1_start.strftime('%Y-%m-%d')
        p1_end = period1_end.strftime('%Y-%m-%d')
        p2_start = period2_start.strftime('%Y-%m-%d')
        p2_end = period2_end.strftime('%Y-%m-%d')
        
        print(f"📅 Período 1: {p1_start} até {p1_end}")
        print(f"📅 Período 2: {p2_start} até {p2_end}")
        
        # Construir campos para API
        # Sempre incluir campos base necessários para cálculos
        base_fields = ['spend', 'impressions', 'reach', 'clicks']
        
        fields = list(base_fields)  # Começar com campos base
        metrics_list = [m.strip() for m in metrics.split(',')]
        
        # Mapear métricas para campos adicionais da API (além dos base)
        # CTR, CPC, CPM, CPP, Frequency são calculados a partir dos base fields
        metric_to_field = {
            'conversions': 'actions',
            'cost_per_conversion': 'cost_per_action_type'
        }
        
        # Adicionar apenas campos adicionais que não são calculados
        for metric in metrics_list:
            if metric in metric_to_field:
                field = metric_to_field[metric]
                if field not in fields:
                    fields.append(field)
        
        fields_str = ','.join(fields)
        
        print(f"🔧 Fields solicitados: {fields_str}")
        
        # Buscar dados do período 1
        url1 = f"https://graph.facebook.com/v21.0/{ad_account_id}/insights"
        params1 = {
            'access_token': FACEBOOK_ACCESS_TOKEN,
            'level': level,
            'time_range': f'{{"since":"{p1_start}","until":"{p1_end}"}}',
            'fields': fields_str,
            'limit': 1000
        }
        
        print(f"🌐 URL: {url1}")
        print(f"📋 Params: level={level}, time_range={params1['time_range']}, fields={fields_str}")
        
        # Buscar dados do período 2
        url2 = f"https://graph.facebook.com/v21.0/{ad_account_id}/insights"
        params2 = {
            'access_token': FACEBOOK_ACCESS_TOKEN,
            'level': level,
            'time_range': f'{{"since":"{p2_start}","until":"{p2_end}"}}',
            'fields': fields_str,
            'limit': 1000
        }
        
        async with httpx.AsyncClient() as client:
            # Fazer requisições em paralelo
            response1, response2 = await asyncio.gather(
                client.get(url1, params=params1, timeout=30.0),
                client.get(url2, params=params2, timeout=30.0)
            )
            
            if response1.status_code != 200:
                return f"❌ Erro ao buscar período 1: {response1.text}"
            
            if response2.status_code != 200:
                return f"❌ Erro ao buscar período 2: {response2.text}"
            
            data1 = response1.json()
            data2 = response2.json()
        
        print(f"📦 Período 1: {len(data1.get('data', []))} campanhas encontradas")
        print(f"📦 Período 2: {len(data2.get('data', []))} campanhas encontradas")
        
        # Agregar métricas de todos os campaigns/adsets/ads
        def aggregate_metrics(data):
            totals = {
                'spend': 0,
                'impressions': 0,
                'reach': 0,
                'clicks': 0,
                'conversions': 0
            }
            
            for item in data.get('data', []):
                totals['spend'] += float(item.get('spend', 0))
                totals['impressions'] += int(item.get('impressions', 0))
                totals['reach'] += int(item.get('reach', 0))
                totals['clicks'] += int(item.get('clicks', 0))
                
                # Somar conversões
                actions = item.get('actions', [])
                for action in actions:
                    totals['conversions'] += int(action.get('value', 0))
            
            # Calcular métricas derivadas
            if totals['impressions'] > 0:
                totals['ctr'] = (totals['clicks'] / totals['impressions']) * 100
                totals['cpm'] = (totals['spend'] / totals['impressions']) * 1000
            else:
                totals['ctr'] = 0
                totals['cpm'] = 0
            
            if totals['clicks'] > 0:
                totals['cpc'] = totals['spend'] / totals['clicks']
            else:
                totals['cpc'] = 0
            
            if totals['reach'] > 0:
                totals['cpp'] = totals['spend'] / totals['reach']
                totals['frequency'] = totals['impressions'] / totals['reach']
            else:
                totals['cpp'] = 0
                totals['frequency'] = 0
            
            if totals['conversions'] > 0:
                totals['cost_per_conversion'] = totals['spend'] / totals['conversions']
            else:
                totals['cost_per_conversion'] = 0
            
            return totals
        
        metrics1 = aggregate_metrics(data1)
        metrics2 = aggregate_metrics(data2)
        
        print(f"📊 Métricas Período 1: {metrics1}")
        print(f"📊 Métricas Período 2: {metrics2}")
        
        # Verificar se há dados
        if metrics1['spend'] == 0 and metrics2['spend'] == 0:
            return (
                f"📋 *Sem dados de campanhas ativas*\n\n"
                f"📅 *{period1_name}*: {period1_start.strftime('%d/%m')} - {period1_end.strftime('%d/%m')}\n"
                f"📅 *{period2_name}*: {period2_start.strftime('%d/%m')} - {period2_end.strftime('%d/%m')}\n\n"
                f"💡 *Possíveis razões:*\n"
                f"• Nenhuma campanha ativa nos períodos\n"
                f"• Campanhas pausadas ou sem investimento\n"
                f"• Token de acesso expirado\n\n"
                f"🔍 Verifique o Gerenciador de Anúncios"
            )
        
        # Calcular variações
        def calc_variation(val1, val2):
            if val2 == 0:
                return "N/A" if val1 == 0 else "+∞"
            variation = ((val1 - val2) / val2) * 100
            return f"+{variation:.1f}%" if variation >= 0 else f"{variation:.1f}%"
        
        def format_number(value, metric_type):
            if metric_type in ['ctr', 'frequency']:
                return f"{value:.2f}"
            elif metric_type in ['cpc', 'cpm', 'cpp', 'spend', 'cost_per_conversion']:
                return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                return f"{int(value):,}".replace(',', '.')
        
        # Construir resposta formatada
        response_lines = [
            f"📊 *Análise Comparativa*",
            f"",
            f"📅 *{period1_name}*: {period1_start.strftime('%d/%m')} - {period1_end.strftime('%d/%m')}",
            f"📅 *{period2_name}*: {period2_start.strftime('%d/%m')} - {period2_end.strftime('%d/%m')}",
            f"",
            f"*Resultados:*"
        ]
        
        # Formatação de métricas
        metric_names = {
            'spend': ('💰 Investimento', 'spend'),
            'impressions': ('👁️ Impressões', 'impressions'),
            'reach': ('👥 Alcance', 'reach'),
            'clicks': ('🖱️ Cliques', 'clicks'),
            'ctr': ('📈 CTR', 'ctr'),
            'cpc': ('💵 CPC', 'cpc'),
            'cpm': ('📊 CPM', 'cpm'),
            'cpp': ('💸 CPP', 'cpp'),
            'frequency': ('🔄 Frequência', 'frequency'),
            'conversions': ('🎯 Conversões', 'conversions'),
            'cost_per_conversion': ('💰 Custo/Conv', 'cost_per_conversion')
        }
        
        for metric in metrics_list:
            if metric in metric_names:
                label, key = metric_names[metric]
                val1 = metrics1.get(key, 0)
                val2 = metrics2.get(key, 0)
                variation = calc_variation(val1, val2)
                
                response_lines.append(
                    f"{label}: {format_number(val1, key)} vs {format_number(val2, key)} ({variation})"
                )
        
        return "\n".join(response_lines)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Erro ao comparar períodos: {str(e)}"
