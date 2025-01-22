from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio
from heapdict import heapdict
from queue import PriorityQueue


class Priority:
    ACTIVE = 0
    UNCHECKED = 1
    INACTIVE = 2
    COOLDOWN = 3


class ProxyQueue(heapdict):
    def __init__(self, proxy_list=[], cooldown_duration=300):
        self.cooldown_duration = cooldown_duration
        self.cooldown_end_queue = asyncio.Queue()
        self.queue_semaphore = asyncio.Semaphore(1)
        self.cooldown_scheduler = asyncio.locks.Event()
        super(ProxyQueue, self).__init__()
        if proxy_list:
            asyncio.run(self.add_new_proxies(proxy_list))

    async def add_new_proxies(self, proxy_list):
        for proxy in proxy_list:
            if not proxy in self:
                self[proxy] = Priority.UNCHECKED

    async def popitem(self):
        async with self.queue_semaphore:
            priority = super(ProxyQueue, self).peekitem()[1]
            if priority == Priority.COOLDOWN:
                delay = await self.cooldown_end_queue.get() + time.time()
                wait_task = asyncio.create_task(self.cooldown_scheduler.wait())
                asyncio.create_task(self._unlock_queue_delayed(delay))
                await wait_task
            item = super(ProxyQueue, self).popitem()[0]
        return item

    def __setitem__(self, key, value):
        if value == Priority.COOLDOWN:
            asyncio.create_task(self._change_priority_delayed(key, Priority.ACTIVE))
            self.cooldown_end_queue.put_nowait(time.time() + self.cooldown_duration)
        elif not self.cooldown_scheduler.is_set():
            self.cooldown_scheduler.set()
        super(ProxyQueue, self).__setitem__(key, value)
    
    async def _change_priority_delayed(self, item, new_priority: Priority):
        await asyncio.sleep(self.cooldown_duration)
        await self.cooldown_end_queue.get()
        self[item] = new_priority

    async def _unlock_queue_delayed(self, delay):
        await asyncio.sleep(delay)
        if not self.cooldown_scheduler.is_set():
            self.cooldown_scheduler.set()



@dataclass(init=False, order=True)
class PrioritizedItem:
    item: str = field(compare=False)

    _priority: int
    @property
    def priority(self):
        return self._priority
    @priority.setter
    def priority(self, value):
        if value == Priority.COOLDOWN:
            print(value, Priority.COOLDOWN)
            print(self)
            asyncio.create_task(self._change_priority_delayed(Priority.ACTIVE))
        self._priority = value

    def __init__(self, priority, item):
        self.COOLDOWN_DURATION = 5
        self.item = item
        self._priority = None
        self.priority = priority

    async def _change_priority_delayed(self, new_priority: Priority):
        await asyncio.sleep(self.COOLDOWN_DURATION)
        self.priority = new_priority


async def main():
    '''
    q = PriorityQueue()
    q.put(PrioritizedItem(Priority.UNCHECKED, 'unch'))
    q.put(PrioritizedItem(Priority.COOLDOWN, 'frg'))
    timer = time.time()
    while time.time() - timer < 10:
        print(q.queue)
        await asyncio.sleep(0.5)
    '''
    q = ProxyQueue([], 10)
    print(q.heap)
    await q.add_new_proxies(['proxy_1', 'proxy_2'])
    print(q.heap)
    print(await q.popitem())
    print(await q.popitem())
    print(q.heap)


if __name__ == '__main__':
    asyncio.run(main())