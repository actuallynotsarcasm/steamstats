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
    def __init__(
        self, 
        task_list=[], 
        proxy_list=[], 
        max_connections=500, 
        proxy_check_workers=100, 
        proxy_check_request='google.com', 
        check_success_coroutine=None,
        resp_success_coroutine=None,
        resp_cooldown_coroutine=None,
        cooldown_duration=60,
        use_direct_connection=False, 
        list_update_coroutine=None, 
        update_period=0
    ):
        self.task_queue = asyncio.Queue()
        self.resp_dict = {}
        self.proxy_queue = ProxyQueue(cooldown_duration=cooldown_duration)
        self.proxy_set = set()
        self.proxy_metadata = None
        self.proxy_set_sem = asyncio.Semaphore(1)
        self.resp_dict_sem = asyncio.Semaphore(1)
        self.max_connections = max_connections
        self.proxy_check_workers = proxy_check_workers
        self.proxy_check_request = proxy_check_request
        self.check_success_coroutine = check_success_coroutine if check_success_coroutine else self._check_success_coroutine
        self.resp_success_coroutine = resp_success_coroutine if resp_success_coroutine else self._resp_success_coroutine
        self.resp_cooldown_coroutine = resp_cooldown_coroutine if resp_cooldown_coroutine else self._resp_cooldown_coroutine
        self.running_flag = False
        self.list_update_coroutine = list_update_coroutine
        self.update_period = update_period

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

    async def _check_success_coroutine(self, resp):
        return resp.status == 200

    async def _resp_success_coroutine(self, resp):
        return resp.status == 200
    
    async def _resp_cooldown_coroutine(self, resp):
        return resp.status == 429
    
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

            async with aiohttp.ClientSession(proxy=None, connector=connector) as session:
                try:
                    if type(task) == str:
                        request = session.get(task, ssl=False)
                    elif type(task) == dict:
                        request = session.request(**task)
                    else:
                        raise Exception('task should be url or dict of aiohttp session.request() params')
                    
                    async with request as resp:
                        success_func = self.resp_success_coroutine if objective == 'task' else self.check_success_coroutine
                        resp_success = await success_func(resp)
                        resp_cooldown = (await self.resp_cooldown_coroutine(resp)) if self.resp_cooldown_coroutine else False
                        if resp_success:
                            async with self.resp_dict_sem:
                                self.resp_dict[task] = resp
                            self.proxy_queue[proxy] = Priority.ACTIVE
                        elif resp_cooldown:
                            self.task_queue.put_nowait(task)
                            self.proxy_queue[proxy] = Priority.COOLDOWN
                        else:
                            self.task_queue.put_nowait(task)
                            self.proxy_queue[proxy] = Priority.INACTIVE
                except Exception:
                    self.task_queue.put_nowait(task)
                    self.proxy_queue[proxy] = Priority.INACTIVE

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