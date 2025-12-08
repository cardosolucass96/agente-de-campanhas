import httpx
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('FACEBOOK_ACCESS_TOKEN')
account_id = 'act_611132268404060'  # Vorp Scale

from datetime import datetime, timedelta

# Últimos 7 dias
end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

url = f'https://graph.facebook.com/v21.0/{account_id}/insights'
params = {
    'access_token': token,
    'level': 'account',
    'time_range': f'{{"since":"{start_date}","until":"{end_date}"}}',
    'fields': 'spend,actions,impressions,clicks,ctr,cpc'
}

print(f"🔍 Testando API do Facebook para {account_id}")
print(f"📅 Período: {start_date} a {end_date}\n")

try:
    response = httpx.get(url, params=params, timeout=30.0)
    data = response.json()
    
    print("📊 Resposta da API:")
    print(f"Status: {response.status_code}")
    
    if 'error' in data:
        print(f"\n❌ ERRO: {data['error'].get('message', 'Unknown')}")
        print(f"Código: {data['error'].get('code', 'N/A')}")
        print(f"Type: {data['error'].get('type', 'N/A')}")
    elif 'data' in data and len(data['data']) > 0:
        print(f"\n✅ SUCESSO - Dados encontrados!")
        insight = data['data'][0]
        print(f"\n💰 Gastos: R$ {float(insight.get('spend', 0)):.2f}")
        print(f"👁️  Impressões: {insight.get('impressions', 0)}")
        print(f"🖱️  Cliques: {insight.get('clicks', 0)}")
        if insight.get('actions'):
            print(f"🎯 Ações: {len(insight['actions'])} tipos")
    else:
        print("\n⚠️  Resposta vazia - sem dados no período")
        print(f"Data completo: {data}")
        
except Exception as e:
    print(f"\n❌ ERRO na requisição: {str(e)}")
