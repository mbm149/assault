import asyncio
import time
import os
import requests


def fetch(url):
    """Make the request and return the results"""
    started_at = time.monotonic()
    response = requests.get(url)
    request_time = time.monotonic() - started_at
    return {"status_code": response.status_code, "requests": request_time}


async def worker(name, queue, results):
    """A Function to take  unmake request from a queue and perform th work the add results to the results list"""
    loop = asyncio.get_event_loop()
    while True:
        url = await queue.get()
        if os.getenv("DEBUG"):
            print(f"{name} - Fetching {url}")
        future_result = loop.run_in_executor(None, fetch, url)
        result = await future_result
        results.append(result)
        queue.task_done()


async def distribute_work(url, requests, concurrency, results):
    """Divide up the work into baches and collect the final results"""
    queue = asyncio.Queue()
    for _ in range(requests):
        queue.put_nowait(url)

    tasks = []
    for i in range(concurrency):
        task = asyncio.create_task(worker(f"worker- {i+1}", queue, results))
        tasks.append(task)

    start_at = time.monotonic()
    await queue.join()
    total_time = time.monotonic() - start_at

    for task in tasks:
        task.cancel()

    print("----")
    print(
        f"{concurrency} workers took {total_time:2f} seconds to complete {len(results)} requests"
    )


def assault(url, requests, concurrency):
    """Entrypoint to making  requests"""
    results = []
    asyncio.run(distribute_work(url, requests, concurrency, results))
    print(results)
