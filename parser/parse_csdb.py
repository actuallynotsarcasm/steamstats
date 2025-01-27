import requests
import json
import time
from bs4 import BeautifulSoup

proxy_json = 'https://proxycompass.com/wp-admin/admin-ajax.php?action=proxylister_download&nonce=7f45be8507&format=json'

with open('headers.json', 'r') as f:
    headers = json.load(f)

timestamp = int(time.time())
headers['Cookie'] = f'_ga_SDFW078N6F=GS1.1.{timestamp}.1.0.{timestamp}.0.0.0'

url = 'https://www.csgodatabase.com/skins/'
with requests.Session() as session:
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 OPR/115.0.0.0 (Edition Yx 05)"
    }
    #session.cert = 'fiddler_cert_w_key_converted_2.cer'
    resp = session.get(url)
resp_text = resp.text
soup = BeautifulSoup(resp_text, features='html.parser')
skin_table = soup.select('table')
print(resp.status_code)

with open('csdb.html', 'w', encoding='utf_8') as f:
    f.write(resp_text)