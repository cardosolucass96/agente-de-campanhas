"""
Tool para buscar insights de TODAS as 5 contas de anúncio padrão configuradas
"""
import httpx
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv
from default_accounts import DEFAULT_ACCOUNT_IDS, DEFAULT_AD_ACCOUNTS, get_account_name

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def get_all_accounts_insights(
    start_date: str = None,
    end_date: str = None
) -> str:
    """
    Busca resumo de desempenho de TODAS as 5 contas de anúncio padrão configuradas.
    Use esta ferramenta quando o usuário perguntar sobre "todas as contas" ou "visão geral".
    
    IMPORTANTE: Esta ferramenta mostra um resumo consolidado de todas as contas!
    
    Args:
        start_date: Data inicial YYYY-MM-DD (padrão: últimos 7 dias)
        end_date: Data final YYYY-MM-DD (padrão: ontem)
    
    Retorna resumo com: nome da conta, status, gastos totais, leads e CPL de cada conta.
    """
    try:
        # Definir datas padrão (últimos 7 dias fechados)
        if not end_date:
            yesterday = datetime.now() - timedelta(days=1)
            end_date = yesterday.strftime('%Y-%m-%d')
        
        if not start_date:
            seven_days_ago = datetime.now() - timedelta(days=7)
            start_date = seven_days_ago.strftime('%Y-%m-%d')
        
        print(f"📅 Período de consulta: {start_date} até {end_date}")
        print(f"📅 Hoje: {datetime.now().strftime('%Y-%m-%d')}")
        
        # 1. SEMPRE usar contas padrão (não buscar da API do Facebook)
        print(f"📊 Usando contas padrão configuradas ({len(DEFAULT_ACCOUNT_IDS)} contas)")
        accounts = [
            {
                "id": f"act_{acc_id}",
                "name": info["name"],
                "account_status": 1,  # Ativa
                "currency": "BRL",
                "balance": 0
            }
            for acc_id, info in DEFAULT_AD_ACCOUNTS.items()
        ]
        
        # Formatar período
        start_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        end_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        result = f"📊 *Resumo de Todas as Contas*\n"
        result += f"📅 Período: {start_formatted} a {end_formatted}\n"
        result += f"🏢 Business: Grupo Vorp\n"
        result += f"📁 Total de contas: {len(accounts)}\n\n"
        
        accounts_with_data = []
        accounts_without_data = []
        total_spend_all = 0
        total_results_all = 0
        
        # 2. Buscar insights de cada conta
        async with httpx.AsyncClient() as client:
            for account in accounts:
                acc_id = account['id']
                acc_name = account['name']
                
                # Buscar insights
                url = f"https://graph.facebook.com/v21.0/{acc_id}/insights"
                params = {
                    "access_token": FACEBOOK_ACCESS_TOKEN,
                    "level": "account",
                    "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
                    "fields": "spend,actions"
                }
                
                try:
                    response = await client.get(url, params=params, timeout=30.0)
                    insights_data = response.json()
                    
                    print(f"📊 Consultando {acc_name} ({acc_id})")
                    if "error" in insights_data:
                        print(f"   ❌ Erro: {insights_data['error'].get('message', 'Unknown')}")
                    elif not insights_data.get("data"):
                        print(f"   ⚠️ Sem dados no período")
                    else:
                        print(f"   ✅ Dados encontrados")
                    
                    if "error" not in insights_data and insights_data.get("data"):
                        # Conta com dados
                        insight = insights_data["data"][0]
                        spend = float(insight.get('spend', 0))
                        
                        # Contar resultados
                        actions = insight.get('actions', [])
                        results = 0
                        
                        for action in actions:
                            action_type = action.get('action_type', '')
                            if action_type in ['purchase', 'lead', 'complete_registration', 
                                             'contact', 'add_to_cart', 
                                             'offsite_complete_registration_add_meta_leads']:
                                results += int(action.get('value', 0))
                        
                        if results == 0:
                            for action in actions:
                                action_type = action.get('action_type', '')
                                if action_type in ['link_click', 'post_engagement']:
                                    results += int(action.get('value', 0))
                        
                        cpr = spend / results if results > 0 else 0
                        
                        accounts_with_data.append({
                            'name': acc_name,
                            'id': acc_id,
                            'spend': spend,
                            'results': results,
                            'cpr': cpr
                        })
                        
                        total_spend_all += spend
                        total_results_all += results
                    else:
                        # Conta sem dados
                        accounts_without_data.append({
                            'name': acc_name,
                            'id': acc_id
                        })
                
                except Exception as e:
                    accounts_without_data.append({
                        'name': acc_name,
                        'id': acc_id
                    })
        
        # 3. Montar resposta
        if accounts_with_data:
            result += "✅ *Contas Ativas:*\n\n"
            
            # Ordenar por gasto (maior primeiro)
            accounts_with_data.sort(key=lambda x: x['spend'], reverse=True)
            
            for idx, acc in enumerate(accounts_with_data, 1):
                result += f"{idx}. *{acc['name']}*\n"
                result += f"   💰 Gasto: R$ {acc['spend']:.2f}\n"
                result += f"   🎯 Resultados: {acc['results']:,.0f}\n"
                result += f"   📊 CPR: R$ {acc['cpr']:.2f}\n"
                result += f"   🆔 `{acc['id']}`\n\n"
            
            result += "━━━━━━━━━━━━━━━━━━━\n"
            result += f"💵 *Total Investido:* R$ {total_spend_all:.2f}\n"
            result += f"🎯 *Total de Resultados:* {total_results_all:,}\n"
            
            if total_results_all > 0:
                avg_cpr = total_spend_all / total_results_all
                result += f"📊 *CPR Médio:* R$ {avg_cpr:.2f}\n"
        
        if accounts_without_data:
            result += f"\n⚠️ *{len(accounts_without_data)} conta(s) sem campanhas ativas neste período:*\n"
            for acc in accounts_without_data:
                result += f"• {acc['name']}\n"
        
        return result
    
    except Exception as e:
        return f"Erro ao buscar insights: {str(e)}"
