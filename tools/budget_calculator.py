"""
Tool para cálculos de orçamento de campanhas
"""
from langchain_core.tools import tool


@tool
async def calculate_ad_budget(daily_budget: float, days: int, currency: str = "BRL") -> str:
    """
    Calcula o orçamento total de uma campanha de anúncios.
    
    Args:
        daily_budget: Orçamento diário em reais
        days: Número de dias da campanha
        currency: Moeda (padrão: BRL)
    
    Returns:
        String com o cálculo do orçamento total
    """
    total = daily_budget * days
    return f"Orçamento total: {currency} {total:.2f} (Diário: {currency} {daily_budget:.2f} x {days} dias)"
