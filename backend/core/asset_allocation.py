"""Portfolio-style asset totals by category (same rules as /stats/asset-allocation)."""
from typing import Dict, List

from models.domain import Account

ASSET_CATEGORY_KEYS = ("현금", "부동산", "코인", "주식", "연금", "기타")


def compute_asset_allocation_categories(accounts: List[Account]) -> Dict[str, float]:
    categories = {k: 0.0 for k in ASSET_CATEGORY_KEYS}
    for acc in accounts:
        if acc.status == "dead":
            continue
        if acc.type == "투자":
            investment_value = getattr(acc, "asset_value", 0) or 0
            if investment_value <= 0:
                continue
            account_name = acc.name
            account_name_lower = account_name.lower()
            image_path_lower = acc.image_path.lower() if acc.image_path else ""
            if "연금" in account_name:
                categories["연금"] += investment_value
            elif "부동산" in account_name_lower or "부동산" in image_path_lower:
                categories["부동산"] += investment_value
            elif "코인" in account_name:
                categories["코인"] += investment_value
            elif any(
                keyword in account_name_lower or keyword in image_path_lower
                for keyword in ["주식", "증권", "나무", "한국투자", "ibk", "ok저축은행"]
            ):
                categories["주식"] += investment_value
            else:
                categories["기타"] += investment_value
        elif acc.type == "현금":
            balance = acc.balance()
            if balance > 0:
                categories["현금"] += balance
    return categories
