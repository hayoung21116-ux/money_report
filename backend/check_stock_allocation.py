import json

# Load ledger data
with open('data/ledger.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

accounts = [acc for acc in data['accounts'] if acc['type'] == '투자' and acc['status'] == 'active' and acc.get('asset_value', 0) > 0]

stock_keywords = ['주식', '증권', '나무', '한국투자', 'ibk', 'ok저축은행']

stock_accounts = []

for acc in accounts:
    name = acc['name']
    name_lower = name.lower()
    img_lower = (acc.get('image_path', '') or '').lower()
    asset_value = acc.get('asset_value', 0)
    
    # Skip if already categorized
    if '연금' in name:
        continue
    elif '부동산' in name_lower or '부동산' in img_lower:
        continue
    elif '코인' in name:
        continue
    elif any(kw in name_lower or kw in img_lower for kw in stock_keywords):
        stock_accounts.append((name, asset_value))

print('주식 계좌 목록:')
total = 0
for name, val in sorted(stock_accounts):
    print(f"  {name}: {val:,.0f}원")
    total += val

print(f"\n주식 합계: {total:,.0f}원")

