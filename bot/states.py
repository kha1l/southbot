from aiogram.dispatcher.filters.state import StatesGroup, State


class States(StatesGroup):
    pizza = State()
    post = State()
    working = State()
