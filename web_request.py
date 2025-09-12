import aiohttp
import json
import requests

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return json.dumps({"status": "NG"})

def fetch_sync(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return json.dumps({"status": "NG"})
