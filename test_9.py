hash_names = [
    'AK-47%20%7C%20Redline%20%28Well-Worn%29',
    'PP-Bizon | Harvester (Minimal Wear)'
]
urls = {name: f'https://steamcommunity.com/market/listings/730/{name}' for name in hash_names}
print(list(urls.values()))