import aiohttp
import json

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return json.dumps({"status": "NG"})

async def post(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json.dumps(params), headers={'Content-Type': 'application/json'}) as response:
            if response.status == 200:
                return await response.json()
            else:
                return json.dumps({"status": "NG"})
