import requests, json
from bs4 import BeautifulSoup as bs

url = 'https://proxycompass.com/free-proxy/'

resp = requests.get(url)
resp_text = resp.text

soup = bs(resp_text, features='html.parser')

script = soup.find()

#proxy_json_url = 'https://proxycompass.com/wp-admin/admin-ajax.php?action=proxylister_download&nonce=7f45be8507&format=json'

resp = requests.get(proxy_json_url)
proxies_json = resp.json()

with open('proxies.json', 'w') as f:
    json.dump(proxies_json, f, indent=4)