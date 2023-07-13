from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData


class Keyboard:
    set_callback = CallbackData('s', 'func_id')

    post = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f'Стоп-ингредиентов',
                callback_data=set_callback.new(func_id='stop')
            )
        ],
        [
            InlineKeyboardButton(
                text=f'Оценки МП',
                callback_data=set_callback.new(func_id='grade')
            )],
        [
            InlineKeyboardButton(
                text=f'Метрики',
                callback_data=set_callback.new(func_id='metrics')
            )],
        [
            InlineKeyboardButton(
                text=f'Метрики доставки',
                callback_data=set_callback.new(func_id='delivery')
            )],
        [
            InlineKeyboardButton(
                text=f'Выход',
                callback_data='exit'
            )]
    ])
