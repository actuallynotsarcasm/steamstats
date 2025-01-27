import requests
import json
from bs4 import BeautifulSoup


#hash_name = 'PP-Bizon | Harvester (Minimal Wear)'
#hash_name = '\u2605 Ursus Knife | Urban Masked (Well-Worn)'
#hash_name = 'Prisma%202%20Case'
#hash_name = 'Sticker | MOUZ (Glitter) | Paris 2023'
hash_name = 'AK-47%20%7C%20Redline%20%28Well-Worn%29'


rarity = 0
weapon_type = 0
exterior = 0
collection = 0
stickers = 0
souvenir = 0
stattrak = 0

page_url = f'https://steamcommunity.com/market/listings/730/{hash_name}'

listing_url = f'https://steamcommunity.com/market/listings/730/{hash_name}/render/?query=&start=0&count=100&country=RU&language=english&currency=5'

price_url = f'http://steamcommunity.com/market/priceoverview/?appid=730&currency=5&market_hash_name={hash_name}'

price_resp = requests.get(price_url).text
price_json = json.loads(price_resp)

with open('resp_item_price.json', 'w', encoding='utf-16') as f:
    json.dump(price_json, f, indent=4)

listing_resp = requests.get(listing_url).text
listing_json = json.loads(listing_resp)

with open('resp_item_listings.json', 'w', encoding='utf-16') as f:
    json.dump(listing_json, f, indent=4)

page_resp = requests.get(page_url).text
soup = BeautifulSoup(page_resp, 'html.parser')

parse_data_text = 'var line1='
parse_id_text = 'Market_LoadOrderSpread( '

script = soup.find(lambda tag: tag.name == "script" and parse_data_text in tag.text and parse_id_text in tag.text).text

data_start_ind = script.find(parse_data_text)
if data_start_ind == -1:
    data = ''
else:
    data_end_ind = script.find(';\n', data_start_ind)
    data = script[data_start_ind + len(parse_data_text):data_end_ind]
data = json.loads(data)

id_start_ind = script.find(parse_id_text)
if id_start_ind == -1:
    id = ''
else:
    id_end_ind = script.find(' )', id_start_ind)
    id = script[id_start_ind + len(parse_id_text):id_end_ind]

with open('resp_item_data.json', 'w', encoding='utf-16') as f:
    json.dump(data, f, indent=4)

if id:
    graph_url = f'https://steamcommunity.com/market/itemordershistogram?country=RU&language=english&currency=5&item_nameid={id}'

    resp_graph = requests.get(graph_url).text
    graph_json = json.loads(resp_graph)

    with open('resp_item_graph.json', 'w', encoding='utf-16') as f:
        json.dump(graph_json, f, indent=4)