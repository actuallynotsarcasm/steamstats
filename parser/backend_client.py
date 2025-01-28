import requests
import json


def transform_item(item: dict) -> dict:
    return {
        "name": item['hash_name'],
        "item_type": item['type'],
        "buy_price": float(item['sell_price_text'][1:].replace(',', '')),
        "sell_price": float(item['sale_price_text'][1:].replace(',', '')),
        "listings": item['sell_listings']
    }


with open('parser_data/items_processed.json', 'r') as f:
    items = json.load(f)

items = list(map(transform_item, items))
url = 'http://localhost:8000/items'
resp = requests.post(url, json=items)
print(resp)