import requests
import json
import asyncio
import time
from bs4 import BeautifulSoup as bs

from proxy_list import get_proxy_list
from proxy_rotator import ProxyRotator


async def parse_page(start: int, page_count: int, proxy_rotator: ProxyRotator) -> list:
    while True:
        try:
            session = await proxy_rotator.get_session()
            async with session:
                url_json = f'https://steamcommunity.com/market/search/render/?query=&start={start}&count={page_count}&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=1'
                async with session.get(url_json, ssl=False) as resp_json:
                    if resp_json.status == 200:
                        items_json = await resp_json.json()
                    else:
                        continue
                url_html = f'https://steamcommunity.com/market/search/render/?query=&start={start}&count={page_count}&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0'
                async with session.get(url_html, ssl=False) as resp_html:
                    if resp_html.status == 200:
                        items_html = (await resp_html.json())['results_html']
                    else:
                        continue
                soup = bs(items_html, features='html.parser')
                item_blocks = soup.findAll('a', class_='market_listing_row_link')
                links = list(map(lambda x: x['href'], item_blocks))
                items = items_json['results']
                for item, link in zip(items, links):
                    item['link'] = link
            return items
        except Exception as e:
            pass
                

async def resp_success_coroutine(resp):
    return resp.status == 200 and ('{"success":true,"start":' in (await resp.text()))


async def main():
    timer = time.time()

    page_count = 100
    count_url = f'https://steamcommunity.com/market/search/render/?query=&start=0&count=1&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=0'
    count_resp = requests.get(count_url).json()
    total_count = count_resp['total_count']
    print(f'Item count: {total_count}')

    proxy_list = await get_proxy_list()
    proxy_rotator = ProxyRotator(
        proxy_list=proxy_list, 
        proxy_check_workers=300, 
        proxy_check_request=count_url, 
        resp_success_coroutine=resp_success_coroutine,
        check_success_coroutine=resp_success_coroutine,
        cooldown_duration=300,
        list_update_coroutine=get_proxy_list,
        update_period=60
    )
    start_values = range(0, total_count, page_count)
    tasks = list(map(lambda x: asyncio.create_task(parse_page(x, page_count, proxy_rotator)), start_values))
    while len(list(filter(lambda x: x.done(), tasks))) < len(tasks):
        await asyncio.sleep(1)
        tasks_done = len(list(filter(lambda x: x.done(), tasks)))
        print(f'Tasks done: {tasks_done}/{len(tasks)}, time elapsed: {time.time() - timer:.2f}')
    items = await asyncio.gather(*tasks)
    items = sum(items, start=[])
    print(len(items))

    with open('parser/parser_data/items.json', 'w', encoding='utf-16') as f:
        json.dump(items, f, indent=4)


if __name__ == '__main__':
    asyncio.run(main())