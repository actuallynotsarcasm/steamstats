import aiohttp
import json
import io
import pandas as pd
from bs4 import BeautifulSoup as bs


async def get_proxy_list():
    async with aiohttp.ClientSession() as session:
        url = 'https://proxycompass.com/free-proxy/'
        async with session.get(url) as resp:
            resp_text = await resp.text()

        soup = bs(resp_text, features='html.parser')
        script = soup.find('script', {'id': 'proxylister-js-js-extra'}).text
        backend_access = json.loads(script[script.find('{'):script.rfind('}')+1])

        proxy_json_url = backend_access['ajax_url']
        payload = f'nonce={backend_access['nonce']}&action=proxylister_load_filtered&filter[page_size]=100000'
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        async with session.post(proxy_json_url, data=payload, headers=headers) as resp:
            proxies_json = await resp.json()

    table_text = '<table>\n' + proxies_json['data']['rows'] + '</table>'
    table_buffer = io.StringIO(table_text)

    table_pandas = pd.read_html(table_buffer, flavor='lxml')[0]
    table_pandas.columns = ['ip_address', 'port', 'protocols', 'anonimity', 'location', 'provider', 'ping', 'bandwidth', 'availability', 'last_checked']
    table_pandas['country'] = table_pandas['location'].apply(lambda x: None if type(x) == float else x.split('  ')[0])
    table_pandas['city'] = table_pandas['location'].apply(lambda x: None if type(x) == float else x.split('  ')[1])
    table_pandas.drop('location', axis=1, inplace=True)

    proxy_list = sum(list(map(
        lambda x: list(map(
            lambda y: f'{y.lower()}://{x[1]['ip_address']}:{x[1]['port']}',
            x[1]['protocols'].replace('"', '').split(', ')
        )), 
        table_pandas.iterrows()
    )), start=[])

    return proxy_list