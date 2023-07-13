import aiohttp
import asyncio
from pyrus import client
from config.conf import Config
from aiohttp.client_exceptions import ContentTypeError


async def get_public_api(url) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                response = await response.json()
                return response
            except ContentTypeError:
                return {}


async def post_api(url, access, **kwargs) -> dict:
    data = {}
    retry_limit = 5
    retry_delay = 30
    for key, value in kwargs.items():
        if key == '_from':
            data['from'] = value
        else:
            data[key] = value
    headers = {
        "user-agent": 'DodoSouth',
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {access}"
    }
    async with aiohttp.ClientSession() as session:
        for i in range(retry_limit):
            async with session.get(url, headers=headers, params=data) as response:
                try:
                    if response.status == 200:
                        response = await response.json()
                        return response
                    elif response.status == 429 or response.status == 503:
                        await asyncio.sleep(retry_delay)
                    else:
                        break
                except ContentTypeError:
                    return {}
        return {}


class PyrusApi:
    def __init__(self):
        cfg = Config()
        pyrus_client = client.PyrusAPI(login=cfg.bot_pyrus, security_key=cfg.key)
        response = pyrus_client.auth()
        self.access = response.access_token


async def pyrus_api(url, *args):
    pyrus = PyrusApi()
    headers = {
        "Authorization": f'Bearer {pyrus.access}',
        "Content-Type": "application/json",
        "user-agent": 'DodoSouth'
    }
    async with aiohttp.ClientSession() as session:
        if args:
            async with session.post(url, json=args[0], headers=headers) as response:
                try:
                    response = await response.json()
                    return response
                except ContentTypeError:
                    return {}
        else:
            async with session.get(url, headers=headers) as response:
                try:
                    response = await response.json()
                    return response
                except ContentTypeError:
                    return {}


async def update_tokens(**kwargs) -> dict:
    cfg = Config()
    data = {
        'grant_type': 'refresh_token',
        'redirect_uri': cfg.redirect,
        'code_verifier': cfg.verifier,
        'refresh_token': kwargs['refresh']
    }
    headers = {
        "user-agent": 'DodoSouth',
        "Content-Type": "application/x-www-form-urlencoded",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(kwargs['url'], headers=headers, data=data, allow_redirects=False,
                                auth=aiohttp.BasicAuth(cfg.client, cfg.secret)) as response:
            try:
                response = await response.json()
                return response
            except ContentTypeError:
                return {}
            