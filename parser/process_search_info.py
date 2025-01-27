import json
from tqdm import tqdm


def parse_item(item: dict) -> dict:
    item['metadata'] = {}

    initial_type = item['asset_description']['type']

    rarities = ['Consumer Grade', 'Mil-Spec Grade', 'Industrial Grade', 'Restricted', 'Classified', 'Covert', 'High Grade', 'Base Grade', 
                'Remarkable', 'Superior', 'Distinguished', 'Exceptional', 'Extraordinary', 'Exotic', 'Master', 'Contraband']
    rarity = list(filter(lambda x: x in initial_type, rarities))[0]

    item_type = initial_type[initial_type.find(rarity) + len(rarity) + 1:]
    if item_type in ['Equipment', 'Knife', 'Machinegun', 'Pistol', 'Rifle', 'Shotgun', 'SMG', 'Sniper Rifle']:
        item['metadata']['weapon_class'] = item_type
        item_type = 'Weapon'
    elif type in ['Gift', 'Tag', 'Tool']:
        item['metadata']['other_type'] = item_type
        item_type = 'Other'
    
    item['type'] = item_type
    if item_type in ['Weapon', 'Sticker', 'Charm', 'Agent', 'Patch', 'Graffity', 'Collectible']:
        item['metadata']['rarity'] = rarity

    return item


if __name__ == '__main__':
    with open('parser/parser_data/items.json', 'r', encoding='utf-16') as f:
        items = json.load(f)
    items = list(map(parse_item, tqdm(items)))
    with open('parser/parser_data/items_processed.json', 'w') as f:
        json.dump(items, f, indent=4)