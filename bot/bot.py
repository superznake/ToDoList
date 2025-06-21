import asyncio
import os
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram_dialog import Dialog, DialogManager, Window, StartMode, setup_dialogs
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Back, Row, Column
from aiogram_dialog.widgets.text import Const, Format, Text

from api import get_token, register, create_task, get_tasks

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
    task_name_input = State()
    task_description_input = State()
    task_tags_input = State()
    task_deadline_input = State()
    task_confirm = State()


async def get_username_data(dialog_manager: DialogManager, **kwargs):
    return {"username": dialog_manager.dialog_data.get("username", "Аноним")}


async def get_password_data(dialog_manager: DialogManager, **kwargs):
    return {"password": dialog_manager.dialog_data.get("password", "error")}


async def get_task_data(dialog_manager: DialogManager, **kwargs):
    result = {
        "task_name": dialog_manager.dialog_data.get("task_name")
    }
    for key in ["task_description", "task_tags", "task_deadline"]:
        if key in dialog_manager.dialog_data:
            result[key] = dialog_manager.dialog_data.get(key)
    return result


async def confirm_getter(dialog_manager: DialogManager, **kwargs):
    result = {
        "task_name": dialog_manager.dialog_data.get("task_name"),
        "task_description": dialog_manager.dialog_data.get("task_description", "Не указано"),
        "task_tags": dialog_manager.dialog_data.get("task_tags", "Не указаны"),
        "task_deadline": dialog_manager.dialog_data.get("task_deadline", "Не указан"),
    }
    return result


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


async def on_all_tasks_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    tasks = await get_tasks(access_token=users[callback.message.chat.id])
    for task in tasks:
        text = "Название задачи: " + task["name"]
        if task["description"] != "":
            text += "\nОписание: " + task["description"]
        if task["deadline"] is not None:
            text += "\nСрок: " + task["deadline"]
        if task["tags_info"] != []:
            text += "\nТеги: " + ", ".join(tag["name"] for tag in task["tags_info"])
        text += "\n\nЗадача создана: " + datetime.fromisoformat(task["created_at"]).strftime("%d.%m.%Y %H:%M")
        await callback.message.answer(text=text)


async def on_skip_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def on_task_name_entered(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["task_name"] = message.text
    await dialog_manager.next()


async def on_task_description_entered(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["task_description"] = message.text
    await dialog_manager.next()


async def on_task_tags_entered(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["task_tags"] = message.text
    await dialog_manager.next()


async def on_task_deadline_entered(message: types.Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["task_deadline"] = message.text
    await dialog_manager.next()


async def on_create_task_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(DialogStates.task_name_input)


async def on_confirm_click(callback: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = await get_task_data(dialog_manager)
    await create_task(access_token=users[callback.message.chat.id],
                      name=data["task_name"],
                      description=data.get("task_description", ""),
                      tags=data.get("task_tags", ""),
                      deadline=data.get("task_deadline", ""))
    await dialog_manager.switch_to(DialogStates.menu)


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
    Window(  # Главное меню
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
    Window(  # Создание задачи
        Const("Введите название задачи:"),
        Back(Const("↩️ Назад")),
        MessageInput(on_task_name_entered),
        state=DialogStates.task_name_input),
    Window(  # Создание задачи
        Const("Введите описание"),
        Column(
            Back(Const("↩️ Назад")),
            Button(
                Const("Пропустить этап"),
                id="skip",
                on_click=on_skip_click,
            )
        ),
        MessageInput(on_task_description_entered),
        state=DialogStates.task_description_input
    ),
    Window(  # Создание задачи
        Const("Введите теги через запятую"),
        Column(
            Back(Const("↩️ Назад")),
            Button(
                Const("Пропустить этап"),
                id="skip",
                on_click=on_skip_click,
            )
        ),
        MessageInput(on_task_tags_entered),
        state=DialogStates.task_tags_input
    ),
    Window(  # Создание задачи
        Const("Введите дедлайн в формате YYYY-MM-DD"),
        Column(
            Back(Const("↩️ Назад")),
            Button(
                Const("Пропустить этап"),
                id="skip",
                on_click=on_skip_click,
            )
        ),
        MessageInput(on_task_deadline_entered),
        state=DialogStates.task_deadline_input
    ),
    Window(  # Создание задачи
        Format(
            "Задача: {task_name}\n"
            "Описание: {task_description}\n"
            "Теги: {task_tags}\n"
            "Дедлайн: {task_deadline}\n"),
        Column(
            Back(Const("↩️ Назад")),
            Button(
                Const("Подтвердить"),
                id="confirm",
                on_click=on_confirm_click,
            )
        ),
        getter=confirm_getter,
        state=DialogStates.task_confirm
    ),
)


async def start_cmd(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogStates.main, mode=StartMode.RESET_STACK)


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
