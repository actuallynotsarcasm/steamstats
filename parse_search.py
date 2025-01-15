import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
import time


def parse_weapon(item: dict, parsed_item: dict) -> dict:
    pass


def parse_item(item: dict) -> dict:
    parsed_item = {}
    parsed_item['metadata'] = {}
    parsed_item['hash_name'] = item['hash_name']
    parsed_item['item_url'] = item['link']
    parsed_item['steam_listings'] = item['steam_listings']

    initial_type = item['asset_description']['type']

    rarities = ['Consumer Grade', 'Mil-Spec Grade', 'Industrial Grade', 'Restricted', 'Classified', 'Covert', 'High Grade', 'Base Grade', 
                'Remarkable', 'Superior', 'Distinguished', 'Exceptional', 'Extraordinary', 'Exotic', 'Master', 'Contraband']
    rarity = list(filter(lambda x: x in initial_type, rarities))[0]

    type = initial_type[initial_type.find(rarity) + len(rarity) + 1:]
    if type in ['Equipment', 'Knife', 'Machinegun', 'Pistol', 'Rifle', 'Shotgun', 'SMG', 'Sniper Rifle']:
        type == 'Weapon'
    elif type in ['Gift', 'Tag', 'Tool']:
        parsed_item['metadata']['other_type'] = type
        type = 'Other'
    
    parsed_item['type'] = type
    if type in ['Weapon', 'Sticker', 'Charm', 'Agent', 'Patch', 'Graffity', 'Collectible']:
        parsed_item['metadata']['rarity'] = rarity

    if type == 'Weapon':
        pass


all_items = []

page_count = 100
count_resp = requests.get(f'https://steamcommunity.com/market/search/render/?query=&start=0&count=1&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0').json()
total_count = count_resp['total_count']

for start in tqdm(range(0, total_count, page_count)):
    resp_json = requests.get(f'https://steamcommunity.com/market/search/render/?query=&start={start}&count={page_count}&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=1')
    items_json = resp_json.json()
    resp_html = requests.get(f'https://steamcommunity.com/market/search/render/?query=&start={start}&count={page_count}&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0')
    items_html = resp_html.json()['results_html']
    soup = BeautifulSoup(items_html, features='html.parser')
    item_blocks = soup.findAll('a', class_='market_listing_row_link')
    links = list(map(lambda x: x['href'], item_blocks))
    items = items_json['results']
    for item, link in zip(items, links):
        item['link'] = link
    all_items.extend(items)
    start += page_count

for item in items:
    #parse_item(item)
    break

with open('resp.json', 'w', encoding='utf-16') as f:
    json.dump(all_items, f, indent=4)

with open('resp.html', 'w', encoding='utf-16') as f:
    f.write(resp_html)

#with open('resp_item.html', 'w', encoding='utf-16') as f:
#    f.write(resp_item)