import requests
import json
from bs4 import BeautifulSoup


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


    

count = 100

items_list = []

page = 1
flag = True

count_resp = requests.get(f'https://steamcommunity.com/market/search/render/?query=&start=0&count=1&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0').text
total_count = json.loads(count_resp)['total_count']

while flag:
    #https://steamcommunity.com/market/search/render/?query=&start=10&count=10&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=1
    #https://steamcommunity.com/market/search/render/?search_descriptions=0&sort_column=name&sort_dir=asc&appid=730&norender=1&count={count}
    start = 16900
    count = 100
    resp_json_raw = requests.get(f'https://steamcommunity.com/market/search/render/?query=&start={start}&count={count}&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=1').text
    resp_json = json.loads(resp_json_raw)
    resp_html_raw = requests.get(f'https://steamcommunity.com/market/search/render/?query=&start={start}&count={count}&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0').text
    resp_html = json.loads(resp_html_raw)['results_html']
    soup = BeautifulSoup(resp_html, features='html.parser')
    item_blocks = soup.findAll('a', class_='market_listing_row_link')
    links = list(map(lambda x: x['href'], item_blocks))
    items = resp_json['results']
    for item, link in zip(items, links):
        item['link'] = link
    #base_url = 'http://steamcommunity.com/market/priceoverview/?appid=730&currency=5&market_hash_name='
    #urls = list(map(lambda x: base_url + x, names))
    #items_list.extend(urls)
    #resp_item = requests.get(urls[0]).text
    break

for item in items:
    parse_item(item)
    break

with open('resp.json', 'w', encoding='utf-16') as f:
    json.dump(items, f, indent=4)

with open('resp.html', 'w', encoding='utf-16') as f:
    f.write(resp_html)

#with open('resp_item.html', 'w', encoding='utf-16') as f:
#    f.write(resp_item)