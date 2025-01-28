import json
import asyncio
from bs4 import BeautifulSoup as bs

from proxy_list import get_proxy_list
from proxy_rotator import ProxyRotator


def parse_page(page_text: str) -> dict:
    soup = bs(page_text, features='html.parser')
    script = list(filter(
        lambda x: 'var rgItem = ' in x.text, 
        soup.find_all('script', {'type': 'text/javascript'})
    ))[0].text

    item_data_start_ind = script.find('var rgItem = ') + len('var rgItem = ')
    item_data_end_ind = script.find(';', item_data_start_ind)
    item_data = json.loads(script[item_data_start_ind:item_data_end_ind])

    price_history_start_ind = script.find('var line1=') + len('var line1=')
    price_history_end_ind = script.find(';', price_history_start_ind)
    price_history = json.loads(script[price_history_start_ind:price_history_end_ind])

    item_id_start_ind = script.find('Market_LoadOrderSpread( ') + len('Market_LoadOrderSpread( ')
    item_id_end_ind = script.find(' )', item_id_start_ind)
    item_id = script[item_id_start_ind:item_id_end_ind]
    item_data['order_hist_id'] = item_id
    return {'item_data': item_data, 'price_history': price_history}


async def resp_success_coroutine(resp):
    return resp.status == 200 and ('<div class="item_desc_description">' in (await resp.text()))


def get_urls():
    with open('parser/parser_data/items_processed.json', 'r') as f:
        items = json.load(f)
    urls = {item['hash_name']: item['link'] for item in items}
    return urls


async def main():
    urls = get_urls()
    test_url = 'https://steamcommunity.com/market/search/render/?query=&start=0&count=1&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0'

    proxy_list = await get_proxy_list()
    proxy_rotator = ProxyRotator(
        task_list=list(urls.values()),
        proxy_list=proxy_list,
        max_connections=600, 
        proxy_check_workers=100, 
        proxy_check_request=test_url, 
        resp_success_coroutine=resp_success_coroutine,
        check_success_coroutine=resp_success_coroutine,
        cooldown_duration=300,
        list_update_coroutine=get_proxy_list,
        update_period=60,
        verbose=True
    )
    resps = await proxy_rotator.wait_for_tasks()
    item_pages_data = {}
    for hash_name, url in urls.items():
        item_pages_data[hash_name] = parse_page(await resps[url].text())
    with open('parser/parser_data/item_pages_data.json', 'w') as f:
        json.dump(item_pages_data, f, indent=4)


if __name__ == '__main__':
    asyncio.run(main())