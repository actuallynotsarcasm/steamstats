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
        self.blocked = False
        self.cooldown_end_timestamps = []
        super(ProxyQueue, self).__init__()
        if proxy_list:
            self.add_proxies(proxy_list)

    def add_proxies(self, proxy_list):
        for proxy in proxy_list:
            if not proxy in self:
                self[proxy] = Priority.UNCHECKED

    def popitem(self, key):
        priority = super(ProxyQueue, self).peekitem(key)[1]
        if priority == Priority.COOLDOWN:
            asyncio.run()
        return item

    def __setitem__(self, key, value):
        if value == Priority.COOLDOWN:
            asyncio.create_task(self._change_priority_delayed(key, Priority.ACTIVE))
            self.cooldown_end_timestamps.append(time.time() + self.cooldown_duration)
        super(ProxyQueue, self).__setitem__(key, value)
    
    async def _change_priority_delayed(self, item, new_priority: Priority):
        await asyncio.sleep(self.cooldown_duration)
        self.cooldown_end_timestamps.pop(0)
        self[item] = new_priority



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
    q = PriorityQueue()
    q.put(PrioritizedItem(Priority.UNCHECKED, 'unch'))
    q.put(PrioritizedItem(Priority.COOLDOWN, 'frg'))
    timer = time.time()
    while time.time() - timer < 10:
        print(q.queue)
        q.
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    asyncio.run(main())