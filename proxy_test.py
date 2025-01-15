import requests, json
from bs4 import BeautifulSoup as bs
import pandas as pd
import io

url = 'https://proxycompass.com/free-proxy/'

resp = requests.get(url)
resp_text = resp.text

soup = bs(resp_text, features='html.parser')

script = soup.find('script', {'id': 'proxylister-js-js-extra'}).text

backend_access = json.loads(script[script.find('{'):script.rfind('}')+1])

proxy_json_url = backend_access['ajax_url']

payload = f'nonce={backend_access['nonce']}&action=proxylister_load_filtered&filter[page_size]=100000'

headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

resp = requests.post(proxy_json_url, data=payload, headers=headers)
proxies_json = resp.json()

table_text = '<table>\n' + proxies_json['data']['rows'] + '</table>'
table_buffer = io.StringIO(table_text)

table_pandas = pd.read_html(table_buffer, flavor='lxml')[0]
table_pandas.columns = ['ip_address', 'port', 'protocols', 'anonimity', 'location', 'provider', 'ping', 'bandwidth', 'availability', 'last_checked']
table_pandas['country'] = table_pandas['location'].apply(lambda x: None if type(x) == float else x.split('  ')[0])
table_pandas['city'] = table_pandas['location'].apply(lambda x: None if type(x) == float else x.split('  ')[1])
table_pandas.drop('location', axis=1, inplace=True)

print(len(table_pandas))
print(table_pandas.head())

with open('proxies.json', 'w', encoding='utf-8') as f:
    f.write(table_text)

with open('proxies.csv', 'w', encoding='utf-8') as f:
    table_pandas.to_csv(f, index=False)