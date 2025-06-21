import logging

from aiogram.client.session import aiohttp


async def get_token(user: str, password: str):
    url = "http://backend:8000/api/token/"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {
        "username": user,
        "password": password
    }
    logging.info(f"{data}, {headers}, {url}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            logging.info(response)
            if response.status == 200:
                return await response.json()  # Возвращает JSON-ответ (например, {"token": "..."})
            elif response.status == 400:
                return "error"
            else:
                raise Exception(f"Ошибка API: {response.status}")


async def register(user: str, password: str):
    url = "http://backend:8000/api/register/"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": user,
        "password": password
    }
    logging.info(f"{data}, {url}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            logging.info(response)
            if response.status == 201:
                return await response.json()  # Возвращает JSON-ответ (например, {"token": "..."})
            else:
                raise Exception(f"Ошибка API: {response.status}")


async def create_task(access_token, name: str, description: str = "", tags: str = "", deadline: str = ""):
    url = "http://backend:8000/api/tasks/"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer "+access_token}
    data = {
        "name": name
    }
    if description is not "":
        data["description"] = description
    if deadline is not "":
        data["deadline"] = deadline
    if tags is not "":
        tags = tags.split(", ")
        data["tags"] = tags
    logging.info(f"{data}, {url}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            logging.info(response)
            if response.status == 201:
                return await response.json()  # Возвращает JSON-ответ (например, {"token": "..."})
            else:
                raise Exception(f"Ошибка API: {response.status}")


async def get_tasks(access_token):
    url = "http://backend:8000/api/tasks/"
    headers = {"Authorization": "Bearer " + access_token}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            logging.info(response)
            if response.status == 200:
                return await response.json()  # Возвращает JSON-ответ (например, {"token": "..."})
            else:
                raise Exception(f"Ошибка API: {response.status}")
