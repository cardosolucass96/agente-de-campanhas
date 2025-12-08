"""
Tool para buscar histórico de atividades/edições de contas, campanhas e conjuntos de anúncios
"""
import httpx
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def get_activity_history(
    ad_account_id: str,
    level: str = "account",
    entity_id: str = None,
    days: int = 7
) -> str:
    """
    Busca histórico de atividades e edições de contas, campanhas ou conjuntos de anúncios.
    Use para verificar se o gestor está acompanhando e otimizando as campanhas.
    
    NÍVEIS DISPONÍVEIS (level):
    - "account": Histórico geral da conta (todas as edições)
    - "campaign": Histórico de uma campanha específica
    - "adset": Histórico de um conjunto de anúncios específico
    
    INFORMAÇÕES RETORNADAS:
    - Data e hora de cada edição
    - Tipo de ação (criação, pausa, ativação, edição de orçamento, etc)
    - Campo alterado e valores antes/depois
    - Quem fez a alteração (usuário)
    - Frequência de otimizações
    
    EXEMPLOS DE USO:
    - "histórico da conta Scale últimos 7 dias" → level="account", days=7
    - "edições da campanha X nos últimos 3 dias" → level="campaign", entity_id="123", days=3
    - "quando foi a última otimização?" → level="account", days=7
    
    Args:
        ad_account_id: ID da conta (ex: act_123456789 ou apenas 123456789)
        level: "account", "campaign" ou "adset"
        entity_id: ID da campanha ou adset (obrigatório se level != "account")
        days: Número de dias para buscar histórico (padrão: 7)
    
    Returns:
        Histórico formatado com todas as atividades e análise de gestão
    """
    try:
        # Garantir que o ad_account_id tenha o prefixo 'act_'
        if not ad_account_id.startswith('act_'):
            ad_account_id = f'act_{ad_account_id}'
        
        # Calcular período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Determinar qual endpoint usar
        if level == "account":
            # Activity log da conta
            url = f"https://graph.facebook.com/v21.0/{ad_account_id}/activities"
        elif level == "campaign":
            if not entity_id:
                return "❌ Para level='campaign', você deve fornecer entity_id (ID da campanha)"
            url = f"https://graph.facebook.com/v21.0/{entity_id}/activities"
        elif level == "adset":
            if not entity_id:
                return "❌ Para level='adset', você deve fornecer entity_id (ID do conjunto de anúncios)"
            url = f"https://graph.facebook.com/v21.0/{entity_id}/activities"
        else:
            return f"❌ Level inválido: {level}. Use: account, campaign ou adset"
        
        params = {
            'access_token': FACEBOOK_ACCESS_TOKEN,
            'since': int(start_date.timestamp()),
            'until': int(end_date.timestamp()),
            'fields': 'event_type,event_time,actor_id,actor_name,object_id,object_name,object_type,translated_event_type,extra_data',
            'limit': 100
        }
        
        print(f"🔍 Buscando atividades: {url}")
        print(f"📅 Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            data = response.json()
        
        if "error" in data:
            error_msg = data['error'].get('message', 'Erro desconhecido')
            # Se o endpoint de activities não existir, tentar via activity log alternativo
            if "Unsupported get request" in error_msg or "does not exist" in error_msg:
                return await _get_activity_via_insights(ad_account_id, level, entity_id, days)
            return f"❌ Erro ao buscar histórico: {error_msg}"
        
        activities = data.get('data', [])
        
        if not activities:
            return (
                f"📋 *Nenhuma atividade encontrada*\n\n"
                f"📅 Período: Últimos {days} dias\n"
                f"🔍 Nível: {level}\n\n"
                f"⚠️ *Isso pode indicar:*\n"
                f"• Conta sem otimizações recentes\n"
                f"• Campanhas no automático sem ajustes manuais\n"
                f"• Gestor não está acompanhando ativamente\n\n"
                f"💡 Recomendação: Verificar se há oportunidades de otimização"
            )
        
        # Agrupar atividades por tipo
        activity_types = {}
        activity_details = []
        actors_count = {}
        billing_count = 0  # Contador de cobranças
        
        for activity in activities:
            event_type = activity.get('event_type', 'unknown')
            event_time = activity.get('event_time', '')
            actor_name = activity.get('actor_name', 'Sistema')
            object_name = activity.get('object_name', '')
            
            # Normalizar nome do gestor
            if actor_name == 'Lucas Dantas Sa':
                actor_name = 'Dantas'
            
            # Pular cobranças para não poluir
            if event_type == 'ad_account_billing_charge':
                billing_count += 1
                continue
            
            # Converter timestamp para data legível
            if event_time:
                try:
                    # Tentar como timestamp
                    if isinstance(event_time, (int, float)):
                        dt = datetime.fromtimestamp(int(event_time))
                    else:
                        # Tentar como ISO format
                        dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%d/%m/%Y %H:%M')
                except:
                    formatted_time = event_time
            else:
                formatted_time = "N/A"
            
            # Mapear tipos de eventos para descrições em português
            event_map = {
                'update_ad_bid': '💰 Atualização de Lance',
                'update_ad_budget': '💵 Atualização de Orçamento',
                'create_campaign': '✨ Criação de Campanha',
                'update_campaign': '✏️ Edição de Campanha',
                'pause_campaign': '⏸️ Pausa de Campanha',
                'unpause_campaign': '▶️ Ativação de Campanha',
                'create_adset': '✨ Criação de Conjunto',
                'update_adset': '✏️ Edição de Conjunto',
                'pause_adset': '⏸️ Pausa de Conjunto',
                'unpause_adset': '▶️ Ativação de Conjunto',
                'create_ad': '✨ Criação de Anúncio',
                'update_ad': '✏️ Edição de Anúncio',
                'pause_ad': '⏸️ Pausa de Anúncio',
                'unpause_ad': '▶️ Ativação de Anúncio',
                'update_ad_set_budget': '💵 Ajuste de Orçamento',
                'ad_account_billing_charge': '💳 Cobrança/Pagamento',
                'ad_account_update_status': '🔄 Atualização de Status',
                'create_audience': '🎯 Criação de Público',
                'update_audience': '🎯 Edição de Público',
                'ad_account_add_user_to_role': '👤 Adição de Usuário',
            }
            
            event_desc = event_map.get(event_type, '📝 ' + event_type.replace('_', ' ').title())
            
            # Contar tipos
            if event_desc not in activity_types:
                activity_types[event_desc] = 0
            activity_types[event_desc] += 1
            
            # Contar atores (apenas ações de otimização, não cobranças)
            if 'Cobrança' not in event_desc and 'Pagamento' not in event_desc and actor_name != 'Sistema':
                if actor_name not in actors_count:
                    actors_count[actor_name] = 0
                actors_count[actor_name] += 1
            
            # Detalhes
            translated_fields = activity.get('translated_fields', {})
            extra_data = activity.get('extra_data', {})
            
            detail = {
                'time': formatted_time,
                'type': event_desc,
                'actor': actor_name,
                'object': object_name,
                'fields': translated_fields,
                'extra': extra_data
            }
            
            activity_details.append(detail)
        
        # Construir resposta
        response_lines = [
            f"📊 *Histórico de Atividades*",
            f"",
            f"📅 Período: Últimos {days} dias ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})",
            f"📈 Total de atividades: {len(activities)}",
            f""
        ]
        
        # Resumo por tipo
        if activity_types:
            response_lines.append("*Resumo de Ações:*")
            for event_type, count in sorted(activity_types.items(), key=lambda x: x[1], reverse=True):
                response_lines.append(f"• {event_type}: {count}x")
            response_lines.append("")
        
        # Resumo de gestores
        if actors_count:
            response_lines.append("*Gestores mais ativos:*")
            for actor, count in sorted(actors_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                response_lines.append(f"• {actor}: {count} otimizações")
            response_lines.append("")
        
        # Mostrar últimas 10 atividades em ordem cronológica reversa
        response_lines.append("*Últimas Atividades:*")
        for i, detail in enumerate(activity_details[:10], 1):
            actor_info = f" por {detail['actor']}" if detail['actor'] != 'Sistema' else ""
            object_info = f" ({detail['object']})" if detail['object'] else ""
            
            response_lines.append(f"{i}. [{detail['time']}] {detail['type']}{actor_info}{object_info}")
            
            if detail['fields']:
                for field, value in list(detail['fields'].items())[:2]:  # Primeiros 2 campos
                    response_lines.append(f"   ↳ {field}: {value}")
        
        # Análise de gestão
        response_lines.append("")
        response_lines.append("*Análise de Gestão:*")
        
        # Filtrar ações de otimização (excluir cobranças automáticas)
        optimization_types = [t for t in activity_types.keys() 
                             if 'Cobrança' not in t and 'Pagamento' not in t]
        optimization_count = sum(activity_types[t] for t in optimization_types)
        
        avg_per_day = optimization_count / days
        
        if avg_per_day >= 3:
            response_lines.append("✅ Gestão ativa - Múltiplas otimizações por dia")
        elif avg_per_day >= 1:
            response_lines.append("⚠️ Gestão moderada - Média de 1-3 otimizações por dia")
        elif optimization_count > 0:
            response_lines.append("⚠️ Gestão baixa - Poucas otimizações no período")
        else:
            response_lines.append("❌ Sem gestão ativa - Nenhuma otimização detectada")
        
        response_lines.append(f"📊 Total: {optimization_count} otimizações em {days} dias ({avg_per_day:.1f}/dia)")
        if billing_count > 0:
            response_lines.append(f"💳 ({billing_count} cobranças ocultas)")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Erro ao buscar histórico: {str(e)}"


async def _get_activity_via_insights(ad_account_id: str, level: str, entity_id: str, days: int) -> str:
    """
    Método alternativo: buscar mudanças via insights diários comparando status
    """
    try:
        # Buscar campanhas com seus status e última atualização
        url = f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns"
        params = {
            'access_token': FACEBOOK_ACCESS_TOKEN,
            'fields': 'name,status,updated_time,created_time,daily_budget,lifetime_budget',
            'limit': 100
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            data = response.json()
        
        if "error" in data:
            return f"❌ Histórico de atividades não disponível para esta conta"
        
        campaigns = data.get('data', [])
        
        # Filtrar campanhas atualizadas no período
        start_date = datetime.now() - timedelta(days=days)
        recent_updates = []
        
        for campaign in campaigns:
            updated_time = campaign.get('updated_time', '')
            if updated_time:
                try:
                    update_dt = datetime.fromisoformat(updated_time.replace('Z', '+00:00'))
                    if update_dt >= start_date:
                        recent_updates.append({
                            'name': campaign.get('name', 'N/A'),
                            'status': campaign.get('status', 'N/A'),
                            'updated': update_dt.strftime('%d/%m/%Y %H:%M'),
                            'budget': campaign.get('daily_budget') or campaign.get('lifetime_budget', 'N/A')
                        })
                except:
                    pass
        
        if not recent_updates:
            return (
                f"📋 *Nenhuma atualização recente detectada*\n\n"
                f"📅 Período: Últimos {days} dias\n\n"
                f"⚠️ *Campanhas sem modificações recentes*\n"
                f"• Nenhuma campanha foi atualizada no período\n"
                f"• Isso pode indicar falta de otimização ativa\n\n"
                f"💡 Recomendação: Verificar oportunidades de melhoria"
            )
        
        # Construir resposta
        response_lines = [
            f"📊 *Campanhas Atualizadas Recentemente*",
            f"",
            f"📅 Período: Últimos {days} dias",
            f"🔄 Total de atualizações: {len(recent_updates)}",
            f"",
            f"*Detalhes:*"
        ]
        
        for i, update in enumerate(recent_updates[:10], 1):
            response_lines.append(f"{i}. {update['name']}")
            response_lines.append(f"   ↳ Atualizado: {update['updated']}")
            response_lines.append(f"   ↳ Status: {update['status']}")
            if update['budget'] != 'N/A':
                budget_formatted = f"R$ {float(update['budget'])/100:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                response_lines.append(f"   ↳ Orçamento: {budget_formatted}")
            response_lines.append("")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Erro ao buscar atualizações: {str(e)}"
