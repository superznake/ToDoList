import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram_dialog import Dialog, DialogManager, Window, StartMode, setup_dialogs
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Back, Row, Column
from aiogram_dialog.widgets.text import Const, Format

import logging

logging.basicConfig(level=logging.INFO)
# --- Конфиг ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
users = {0: ""}


# --- States (Состояния диалога) ---
class DialogStates(StatesGroup):
    main = State()
    in_username_input = State()
    in_password_input = State()
    in_password_check = State()
    up_username_input = State()
    up_password_input = State()
    up_password_check = State()
    fast_in = State()
    menu = State()
    task_name = State()
    task_description = State()
    task_tags = State()
    task_deadline = State()
    addd = State()


async def get_username_data(dialog_manager: DialogManager, **kwargs):
    return {"username": dialog_manager.dialog_data.get("username", "Аноним")}


async def get_password_data(dialog_manager: DialogManager, **kwargs):
    return {"password": dialog_manager.dialog_data.get("password", "error")}


# Обработчик нажатия на кастомную кнопку
async def on_show_date_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.message.answer(f"📅 Текущая дата: {datetime.now().strftime('%d.%m.%Y')}")


async def on_sign_in_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    # dialog_manager.dialog_data["username"] = callback.message.text
    await dialog_manager.next()


async def on_sign_up_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    # dialog_manager.dialog_data["username"] = callback.message.text
    await dialog_manager.switch_to(DialogStates.up_username_input)


# Обработчик ввода имени
async def on_username_entered(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["username"] = message.text
    await dialog_manager.next()


async def on_password_entered(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["password"] = message.text
    await message.delete()
    await dialog_manager.next()


async def on_in_password_repeated(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    if dialog_manager.dialog_data.get("password", "error") == message.text:
        access_token = await get_token(dialog_manager.dialog_data.get("username"),
                                       dialog_manager.dialog_data.get("password"))
        if access_token == "error":
            await message.answer("error")
            await dialog_manager.back()
        else:
            access_token = access_token.get("access")
            users[message.chat.id] = access_token
            await message.answer("Успешный вход")
            await dialog_manager.switch_to(DialogStates.menu)
    else:
        await message.answer("error")
        await dialog_manager.back()
    await message.delete()


async def on_up_password_repeated(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    if dialog_manager.dialog_data.get("password", "error") == message.text:
        check = await register(dialog_manager.dialog_data.get("username"),
                               dialog_manager.dialog_data.get("password"))
        if check == "error":
            await message.answer("error")
            await dialog_manager.back()
        else:
            check = check.get("username")
            await message.answer(f"Пользователь {check}, зарегистрирован")
            await dialog_manager.next()

            
async def on_fast_in_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    access_token = await get_token(dialog_manager.dialog_data.get("username"),
                                   dialog_manager.dialog_data.get("password"))
    if access_token == "error":
        await callback.message.answer("error")
    else:
        access_token = access_token.get("access")
        users[callback.message.chat.id] = access_token
        await callback.message.answer("Успешный вход")
        await dialog_manager.switch_to(DialogStates.menu)


async def on_all_tasks_click():
    ...


async def on_create_task_click():
    ...


# Создаем диалог
dialog = Dialog(
    Window(  #Стартовый экран
        Const("Для начала необходимо авторизоваться или зарегистрироваться"),
        Row(Button(
            Const("Авторизоваться"),
            id="sign_in",
            on_click=on_sign_in_click
        ),
            Button(
                Const("Зарегистрироваться"),
                id="sign_up",
                on_click=on_sign_up_click
            )
        ),
        state=DialogStates.main,
    ),
    Window(  #Авторизация
        Const("Введите логин:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_username_entered),
        state=DialogStates.in_username_input
    ),
    Window(  #Авторизация
        Format("Логин: {username}. Введите пароль:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_password_entered),
        getter=get_username_data,
        state=DialogStates.in_password_input,
    ),
    Window(  #Авторизация
        Format("Логин: {username}. Повторите пароль:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_in_password_repeated),
        getter=get_username_data,
        state=DialogStates.in_password_check,
    ),
    Window(  #Регистрация
        Const("Введите логин:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_username_entered),
        state=DialogStates.up_username_input
    ),
    Window(  #Регистрация
        Format("Логин: {username}. Введите пароль:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_password_entered),
        getter=get_username_data,
        state=DialogStates.up_password_input,
    ),
    Window(  #Регистрация
        Format("Логин: {username}. Повторите пароль:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_up_password_repeated),
        getter=get_username_data,
        state=DialogStates.up_password_check,
    ),
    Window(  #Авторизация после регистрации
        Format("Авторизоваться?"),
        Button(
            Const("Авторизоваться"),
            id="fast_in",
            on_click=on_fast_in_click,
        ),
        getter=get_username_data,
        state=DialogStates.fast_in,
    ),
    Window( # Главное меню
        Const("Главное меню"),
        Column(
            Button(
                Const("Посмотреть задачи"),
                id="all_tasks",
                on_click=on_all_tasks_click
            ),
            Button(
                Const("Создать задачу"),
                id="create_task",
                on_click=on_create_task_click,
            )
        ),
        state=DialogStates.menu
    ),
    Window(
        Const("sada"),
        Row(
            Back(Const("↩️ Назад")),
            Button(
                Const("📅 Показать дату"),
                id="show_date",
                on_click=on_show_date_click
            )),
        state=DialogStates.addd
    )
)


# Хендлер команды /start
async def start_cmd(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogStates.main, mode=StartMode.RESET_STACK)


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
    logging.info(f"{user}:{password}, {url}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            logging.info(response)
            if response.status == 201:
                return await response.json()  # Возвращает JSON-ответ (например, {"token": "..."})
            else:
                raise Exception(f"Ошибка API: {response.status}")


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрируем диалог
    dp.include_router(dialog)

    # Настраиваем систему диалогов
    setup_dialogs(dp)

    # Регистрируем команду
    dp.message.register(start_cmd, Command("start"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
