"""
Tool para buscar insights de campanhas do Facebook Ads
"""
import httpx
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def get_campaign_insights(
    ad_account_id: str, 
    start_date: str = None, 
    end_date: str = None,
    level: str = "campaign",
    metrics: str = None
) -> str:
    """
    Busca dados de desempenho (insights) de campanhas do Facebook Ads.
    Use esta ferramenta para ver como as campanhas estão performando.
    
    SEMPRE inclui: gastos (spend), leads (actions), CPL (custo por lead)
    
    MÉTRICAS ADICIONAIS DISPONÍVEIS (use no parâmetro metrics, separadas por vírgula):
    - impressions: número de vezes que anúncios foram exibidos
    - reach: número de pessoas únicas alcançadas
    - clicks: total de cliques em qualquer lugar do anúncio
    - ctr: taxa de cliques (Click-Through Rate) em %
    - cpc: custo por clique (Cost Per Click)
    - cpm: custo por mil impressões (Cost Per Mille)
    - cpp: custo por pessoa alcançada (Cost Per Person)
    - frequency: frequência média (quantas vezes mesma pessoa viu)
    - conversions: total de conversões (todas as ações)
    - cost_per_conversion: custo médio por conversão
    - video_views: visualizações de vídeo
    
    EXEMPLOS DE USO:
    - "CTR da Scale" → metrics="ctr"
    - "impressões e alcance" → metrics="impressions,reach"
    - "cliques e CPC" → metrics="clicks,cpc"
    
    Args:
        ad_account_id: ID da conta (ex: act_123456789 ou apenas 123456789)
        start_date: Data inicial YYYY-MM-DD - DEIXE VAZIO para últimos 7 dias (padrão automático)
        end_date: Data final YYYY-MM-DD - DEIXE VAZIO para até ontem (padrão automático)
        level: "campaign" (padrão), "adset" (conjunto) ou "ad" (anúncio individual)
        metrics: Métricas adicionais separadas por vírgula (veja lista acima)
    
    IMPORTANTE: 
    - Se usuário pedir métrica específica (CTR, CPC, etc), SEMPRE inclua no parâmetro metrics!
    - NÃO passe start_date/end_date a menos que usuário especifique datas exatas!
    - "última semana" = deixe vazio (usa últimos 7 dias automaticamente)
    """
    try:
        # Definir datas padrão (últimos 7 dias fechados)
        if not end_date:
            yesterday = datetime.now() - timedelta(days=1)
            end_date = yesterday.strftime('%Y-%m-%d')
        
        if not start_date:
            seven_days_ago = datetime.now() - timedelta(days=7)
            start_date = seven_days_ago.strftime('%Y-%m-%d')
        
        # Garantir que o ad_account_id tenha o prefixo 'act_'
        if not ad_account_id.startswith('act_'):
            ad_account_id = f'act_{ad_account_id}'
        
        # Validar nível
        valid_levels = ["campaign", "adset", "ad"]
        if level not in valid_levels:
            level = "campaign"
        
        # Campos base sempre incluídos
        base_fields = "spend,actions,cost_per_action_type"
        
        # Adicionar campo de nome baseado no nível
        if level == "campaign":
            base_fields += ",campaign_name,campaign_id,objective"
        elif level == "adset":
            base_fields += ",adset_name,adset_id,campaign_name"
        else:  # ad
            base_fields += ",ad_name,ad_id,adset_name,campaign_name"
        
        # Métricas adicionais customizadas
        additional_metrics = []
        if metrics:
            # Métricas válidas disponíveis na API
            valid_metrics = [
                "impressions", "reach", "clicks", "ctr", "cpc", "cpp", "cpm", 
                "frequency", "video_views", "video_avg_time_watched_actions",
                "conversions", "conversion_values", "cost_per_conversion"
            ]
            requested = [m.strip() for m in metrics.split(',')]
            additional_metrics = [m for m in requested if m in valid_metrics]
        
        if additional_metrics:
            base_fields += "," + ",".join(additional_metrics)
        
        url = f"https://graph.facebook.com/v21.0/{ad_account_id}/insights"
        
        params = {
            "access_token": FACEBOOK_ACCESS_TOKEN,
            "level": level,
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "fields": base_fields,
            "limit": 100
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            data = response.json()
        
        if "error" in data:
            return f"Erro ao buscar insights: {data['error'].get('message', 'Erro desconhecido')}"
        
        items = data.get("data", [])
        
        if not items:
            return f"📋 *Nenhuma campanha ativa encontrada*\n\n📅 Período consultado: {start_date} a {end_date}\n\n💡 *Sugestões:*\n• Esta conta pode não ter campanhas rodando neste período\n• Tente um período maior (ex: últimos 30 dias)\n• Verifique se há campanhas ativas no Gerenciador de Anúncios"
        
        # Formatar período
        start_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        end_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        # Traduzir nível para português
        level_name = {"campaign": "Campanhas", "adset": "Conjuntos de Anúncios", "ad": "Anúncios"}[level]
        
        result = f"📊 *Insights de {level_name}*\n"
        result += f"📅 Período: {start_formatted} a {end_formatted}\n\n"
        
        total_spend = 0
        total_results = 0
        total_impressions = 0
        total_clicks = 0
        
        for idx, item in enumerate(items[:20], 1):  # Limitar a 20 itens
            # Nome do item baseado no nível
            if level == "campaign":
                name = item.get('campaign_name', 'Sem nome')
            elif level == "adset":
                name = item.get('adset_name', 'Sem nome')
            else:
                name = item.get('ad_name', 'Sem nome')
            
            spend = float(item.get('spend', 0))
            total_spend += spend
            
            # Extrair resultados
            actions = item.get('actions', [])
            results = 0
            
            for action in actions:
                action_type = action.get('action_type', '')
                if action_type in ['purchase', 'lead', 'complete_registration', 'contact', 'add_to_cart']:
                    results += int(action.get('value', 0))
            
            if results == 0:
                for action in actions:
                    action_type = action.get('action_type', '')
                    if action_type in ['link_click', 'post_engagement']:
                        results += int(action.get('value', 0))
            
            total_results += results
            
            # Custo por lead
            cost_per_lead = spend / results if results > 0 else 0
            
            result += f"{idx}. *{name}*\n"
            result += f"   💰 Gasto: R$ {spend:.2f}\n"
            
            if results > 0:
                result += f"   🎯 Leads: {results}\n"
                result += f"   💵 CPL: R$ {cost_per_lead:.2f}\n"
            
            # Métricas adicionais
            if "impressions" in additional_metrics:
                impressions = int(item.get('impressions', 0))
                total_impressions += impressions
                result += f"   👁️ Impressões: {impressions:,}\n"
            
            if "reach" in additional_metrics:
                reach = int(item.get('reach', 0))
                result += f"   👥 Alcance: {reach:,}\n"
            
            if "clicks" in additional_metrics:
                clicks = int(item.get('clicks', 0))
                total_clicks += clicks
                result += f"   🖱️ Cliques: {clicks}\n"
            
            if "ctr" in additional_metrics:
                ctr = float(item.get('ctr', 0))
                result += f"   📊 CTR: {ctr:.2f}%\n"
            
            if "cpc" in additional_metrics:
                cpc = float(item.get('cpc', 0))
                result += f"   💵 CPC: R$ {cpc:.2f}\n"
            
            if "cpm" in additional_metrics:
                cpm = float(item.get('cpm', 0))
                result += f"   💵 CPM: R$ {cpm:.2f}\n"
            
            if "frequency" in additional_metrics:
                frequency = float(item.get('frequency', 0))
                result += f"   🔄 Frequência: {frequency:.2f}\n"
            
            result += "\n"
        
        # Totalizadores
        result += f"*TOTAIS DO PERÍODO:*\n"
        result += f"💰 Investimento: R$ {total_spend:.2f}\n"
        
        if total_results > 0:
            avg_cost = total_spend / total_results
            result += f"🎯 Total de Leads: {total_results}\n"
            result += f"💵 CPL médio: R$ {avg_cost:.2f}\n"
        
        if total_impressions > 0:
            result += f"👁️ Total impressões: {total_impressions:,}\n"
        
        if total_clicks > 0:
            result += f"🖱️ Total cliques: {total_clicks}\n"
        
        if len(items) > 20:
            result += f"\n_Mostrando 20 de {len(items)} itens_"
        
        return result
        
    except Exception as e:
        return f"Erro ao buscar insights: {str(e)}"
