import asyncio
import aiohttp.connector
from heapdict import heapdict
import aiohttp
import json
from bs4 import BeautifulSoup as bs
import pandas as pd
import io
from aiohttp_socks import ProxyType, ProxyConnector
import time


class Priority:
    ACTIVE = 0
    UNCHECKED = 1
    INACTIVE = 2
    COOLDOWN = 3


class ProxyQueue(heapdict):
    def __init__(self, proxy_list=[], cooldown_duration=300):
        self.cooldown_duration = cooldown_duration
        self.queue_semaphore = asyncio.Semaphore(1)
        self.get_semaphore = asyncio.Semaphore(1)
        self.get_scheduler = asyncio.locks.Event()
        self.active_semaphore = asyncio.Semaphore(1)
        self.active_scheduler = asyncio.locks.Event()

        super(ProxyQueue, self).__init__()
        if proxy_list:
            asyncio.create_task(self.add_new_proxies(proxy_list))

    async def add_new_proxies(self, proxy_list):
        for proxy in proxy_list:
            if not proxy in self:
                self[proxy] = Priority.UNCHECKED

    async def get(self):
        async with self.get_semaphore:
            if self.heap == []:
                self.get_scheduler.clear()
            else:
                async with self.queue_semaphore:
                    priority = self.peekitem()[1]
                if priority == Priority.COOLDOWN:
                    self.get_scheduler.clear()
            await self.get_scheduler.wait()
            async with self.queue_semaphore:
                item = self.popitem()[0]
                if len(self) > 0:
                    if self.peekitem()[1] != Priority.ACTIVE:
                        self.active_scheduler.clear()
                else:
                    self.active_scheduler.clear()
        return item
    
    async def get_active(self):
        async with self.active_semaphore:
            await self.active_scheduler.wait()
            async with self.queue_semaphore:
                item = self.popitem()[0]
                if len(self) > 0:
                    if self.peekitem()[1] != Priority.ACTIVE:
                        self.active_scheduler.clear()
                else:
                    self.active_scheduler.clear()
        if not self.active_semaphore.locked() and len(self) > 0:
            if self.peekitem()[1] != Priority.COOLDOWN:
                self.get_scheduler.set()
        return item
    
    async def put(self, item, priority):
        async with self.queue_semaphore:
            if priority == Priority.COOLDOWN:
                asyncio.create_task(self._change_priority_delayed(item, Priority.ACTIVE))
            elif priority == Priority.ACTIVE:
                self.active_scheduler.set()
                if self.active_semaphore.locked():
                    self.get_scheduler.clear()
                else:
                    self.get_scheduler.set()
            else:
                self.get_scheduler.set()
            super(ProxyQueue, self).__setitem__(item, priority)

    def __setitem__(self, key, value):
        asyncio.create_task(self.put(key, value))
    
    async def _change_priority_delayed(self, item, new_priority: Priority):
        await asyncio.sleep(self.cooldown_duration)
        self[item] = new_priority


class ProxyRotator:
    def __init__(self, task_list, proxy_list=[], max_connections=500, proxy_check_workers=100, proxy_check_request='google.com', use_direct_connection=False, list_update_coroutine=None, update_period=0):
        self.task_queue = asyncio.Queue()
        self.resp_dict = {}
        self.proxy_queue = ProxyQueue()
        self.proxy_set = set()
        self.proxy_metadata = None
        self.proxy_set_sem = asyncio.Semaphore(1)
        self.resp_dict_sem = asyncio.Semaphore(1)
        self.max_connections = max_connections
        self.proxy_check_workers = proxy_check_workers
        self.proxy_check_request = proxy_check_request
        self.running_flag = False
        self.list_update_coroutine = list_update_coroutine
        self.update_period = update_period

        self.success_counter = 0
        self.used_set = set()
        self.time_started = time.time()
        self.proxies_in_use = 0

        if proxy_list or use_direct_connection:
            if use_direct_connection:
                pass #TODO
            asyncio.create_task(self.add_proxies(proxy_list))
        for task in task_list:
            self.task_queue.put_nowait(task)

    async def add_proxies(self, new_list):
        new_set = set(new_list)
        async with self.proxy_set_sem:
            proxies_to_add = new_set.difference(self.proxy_set)
            self.proxy_set = self.proxy_set.union(proxies_to_add)
        asyncio.create_task(self.proxy_queue.add_new_proxies(proxies_to_add))

    async def _init_proxy_list(self):
        new_list = await self.list_update_coroutine()
        asyncio.create_task(self.add_proxies(new_list))

    async def _regular_update_loop(self):
        if self.list_update_coroutine:
            while self.running_flag:
                await asyncio.sleep(self.update_period)
                new_list = await self.list_update_coroutine()
                await self.add_proxies(new_list)

    def _count_proxy_types(self):
        counts = [0, 0, 0, 0]
        for item in self.proxy_queue.heap:
            proxy_type = item[0]
            counts[proxy_type] += 1
        counts = dict(zip(['active', 'unchecked', 'inactive', 'cooldown'], counts))
        return counts

    def _parse_proxy(self, proxy):
        username, password = None, None
        protocol = proxy[:proxy.find('://')]
        proxy = proxy[proxy.find('://')+3:]
        if '@' in proxy:
            auth, proxy = proxy.split('@')
            username, password = auth.split(':')
        host, port = proxy.split(':')
        port = int(port)
        return protocol, username, password, host, port

    async def _worker(self, objective='task'):
        while (not self.task_queue.empty() and objective == 'task') or (self.running_flag and objective == 'check'):
            if objective == 'task':
                task = await self.task_queue.get()
            else:
                task = self.proxy_check_request
            proxy = await self.proxy_queue.get()

            self.proxies_in_use += 1

            protocol, username, password, host, port = self._parse_proxy(proxy)
            match protocol:
                case 'http': proxy_type = ProxyType.HTTP
                case 'socks4': proxy_type = ProxyType.SOCKS4
                case 'socks5': proxy_type = ProxyType.SOCKS5
            #ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = ProxyConnector(
                proxy_type=proxy_type,
                host=host,
                port=port,
                username=username,
                password=password
                #ssl=ssl_context
            )

            async with aiohttp.ClientSession(proxy=None, connector=connector) as session:
                try:
                    if type(task) == str:
                        request = session.get(task, ssl=False)
                    elif type(task) == dict:
                        request = session.request(**task)
                    else:
                        raise Exception('task should be url or dict of aiohttp session.request() params')
                    
                    async with request as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            if '{"success":true,"start":' in text:
                                #print(f'200, tasks done: {len(self.resp_dict)+1}, time elapsed: {int(time.time() - self.time_started)}')
                                #print(proxy)
                                #print(f'{self.success_counter}/{len(self.used_set)}, time elapsed: {int(time.time() - self.time_started)}, proxy counts: {self._count_proxy_types()}, used: {self.proxies_in_use}, overall: {sum(self._count_proxy_types().values(), start=self.proxies_in_use)}')
                                async with self.resp_dict_sem:
                                    self.resp_dict[task] = resp
                                self.proxy_queue[proxy] = Priority.ACTIVE ###
                            else:
                                self.task_queue.put_nowait(task)
                                self.proxy_queue[proxy] = Priority.INACTIVE
                                #print('Invalid format')
                        elif resp.status == 429:
                            #print('Cooling down')
                            self.task_queue.put_nowait(task)
                            self.proxy_queue[proxy] = Priority.COOLDOWN
                        else:
                            #print(resp.status)
                            self.task_queue.put_nowait(task)
                            self.proxy_queue[proxy] = Priority.INACTIVE
                except Exception as e:
                    #print(e.__class__.__name__)
                    self.task_queue.put_nowait(task)
                    self.proxy_queue[proxy] = Priority.INACTIVE
                finally:
                    self.used_set.add(proxy)
                    self.proxies_in_use -= 1

    async def get_session(self):
        if self.running_flag:
            proxy = await self.proxy_queue.get_active()
            protocol, username, password, host, port = self._parse_proxy(proxy)
            match protocol:
                case 'http': proxy_type = ProxyType.HTTP
                case 'socks4': proxy_type = ProxyType.SOCKS4
                case 'socks5': proxy_type = ProxyType.SOCKS5
            connector = ProxyConnector(
                proxy_type=proxy_type,
                host=host,
                port=port,
                username=username,
                password=password
            )
            session = aiohttp.ClientSession(connector=connector)
            return session
        else:
            raise Exception('cannot get session because rotation has not been started')

    def start(self):
        if not self.running_flag:
            self.running_flag = True
            self.time_started = time.time() ###
            self._workers = []

            self._workers.append(asyncio.create_task(self._regular_update_loop()))

            if self.max_connections == -1:
                num_workers = self.task_queue.qsize()
            else:
                num_workers = min(self.task_queue.qsize(), self.max_connections)

            for _ in range(num_workers):
                self._workers.append(asyncio.create_task(self._worker('task')))

            for _ in range(self.proxy_check_workers):
                self._workers.append(asyncio.create_task(self._worker('check')))

            if len(self.proxy_set) == 0 and self.list_update_coroutine:
                asyncio.create_task(self._init_proxy_list())
        else:
            raise Exception('rotation already started')

    def stop(self):
        if self.running_flag:
            self.running_flag = False
            for worker in self._workers:
                worker.cancel()
            return self.resp_dict
        else:
            raise Exception('cannot stop rotation because it has not been started')
        
    async def wait_for_tasks(self):
        await asyncio.gather(*self._workers)
        self.running_flag = False
        return self.resp_dict
    

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


async def test_request(url, proxy=None, connector=None):
    async with aiohttp.ClientSession(connector=connector, proxy=proxy) as session:
        async with session.get(url, ssl=False) as resp:
            print(resp.status)
            return await resp.text()


async def main():
    '''
    q = ProxyQueue()
    task1 = asyncio.create_task(q.get_active())
    task2 = asyncio.create_task(q.get_active())
    q['proxy1'] = Priority.ACTIVE
    q['proxy2'] = Priority.ACTIVE
    print(await task1)
    print(await task2)
    '''
    url = 'https://steamcommunity.com/market/search/render/?query=&start=0&count=100&search_descriptions=0&sort_column=name&sort_dir=desc&appid=730&norender=1'
    proxy_list = await get_proxy_list()
    print(len(proxy_list))
    #tasks = [url.replace('start=0', f'start={i}') for i in range(10000)]
    rotator = ProxyRotator([], proxy_list, 600, proxy_check_workers=200, proxy_check_request=url, list_update_coroutine=get_proxy_list, update_period=60)
    rotator.start()
    #task = asyncio.create_task(rotator.wait_for_tasks())
    #await task
    session = await rotator.get_session()
    print(session.closed)
    async with session:
        print(session.closed)
        async with session.get(url, ssl=False) as resp:
            print(resp.status)
            print((await resp.text())[:100])
    print(session.closed)
    

try:
    if __name__ == '__main__':
        asyncio.run(main())
except asyncio.exceptions.CancelledError as e:
    pass