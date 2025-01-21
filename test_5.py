import asyncio

class MyAsyncObject:
    def __init__(self, name, delay):
        self.name = name
        self.delay = delay
        self.is_changed = False
        self.task = None

    async def schedule_change(self):
        await asyncio.sleep(self.delay)
        print(f"Async object '{self.name}' changed state after {self.delay} seconds.")
        self.is_changed = True

    def start_scheduling(self):
        self.task = asyncio.create_task(self.schedule_change())

    def cancel_scheduling(self):
        if self.task and not self.task.done():
            self.task.cancel()
            print(f"Scheduling for async object '{self.name}' cancelled.")

async def main():
    async_objects = [
        MyAsyncObject("Async Object X", 3),
        MyAsyncObject("Async Object Y", 1),
        MyAsyncObject("Async Object Z", 6),
    ]

    for obj in async_objects:
        obj.start_scheduling()

    # Cancel a task if needed
    async_objects[0].cancel_scheduling()

if __name__ == "__main__":
    asyncio.run(main())