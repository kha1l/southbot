from config.conf import Config
from aiogram import executor, types
from aiogram.dispatcher.filters import Command
from bot.states import States
from aiogram.dispatcher import FSMContext
from database.psql import Database
from bot.keyboard import Keyboard
from bot.update_tokens import token
from function.stops import stops
from function.tickets import send_tickets
from function.metrics_rest import metrics
from function.metrics_delivery import delivery_stats
from datetime import datetime


Config.scheduler.add_job(token, 'cron', day_of_week='*', hour=13, minute=0)
Config.scheduler.add_job(stops, 'interval', minutes=5, start_date=datetime(2023, 7, 13, 20, 55, 0))
Config.scheduler.add_job(send_tickets, 'interval', minutes=5, start_date=datetime(2023, 7, 13, 20, 56, 0))
Config.scheduler.add_job(metrics, 'cron', day_of_week="*", hour='12-22/2', minute=1)
Config.scheduler.add_job(delivery_stats, 'cron', day_of_week="*", hour='12-22/2', minute=2)


@Config.dp.message_handler(Command(commands=["start"]))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(f'Привет, <strong>{message.from_user.full_name}</strong>!\U0001F44B\n')


@Config.dp.message_handler(Command(commands=["add"]))
async def add_rest(message: types.Message):
    await message.answer(f'Укажите название ресторана или ресторанов')
    await States.pizza.set()


@Config.dp.message_handler(Command(commands=["rest"]))
async def func_rest(message: types.Message):
    await message.answer(f'Собираю отчет метрик ресторана')
    await metrics()


@Config.dp.message_handler(Command(commands=["delivery"]))
async def func_delivery(message: types.Message):
    await message.answer(f'Собираю отчет метрик доставки')
    await delivery_stats()


@Config.dp.message_handler(state=States.pizza)
async def auth_pizza(message: types.Message, state: FSMContext):
    db = Database()
    stationary = {}
    uuid = []
    catalog = []
    rest = message.text.replace(' ', '').title().replace('На', 'на').split(',')
    units = db.get_rest()
    value = True
    for unit in units:
        stationary[unit[0]] = [unit[1], unit[2]]
    for i in rest:
        if i not in stationary:
            value = False
        else:
            uuid.append(stationary[i][0])
            catalog.append(stationary[i][1])
    if value:
        await state.update_data(name=[uuid, catalog])
        await message.answer(f'Отчеты', reply_markup=Keyboard.post)
        await States.post.set()
    else:
        await message.answer(f'Пиццерии нет в списке!')
        await state.finish()


@Config.dp.callback_query_handler(Keyboard.set_callback.filter(), state=States.post)
async def choice(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    db = Database()
    await call.answer()
    chat = call.message.chat.id
    await state.update_data(chat_id=chat, post=callback_data.get('func_id'))
    callback = await state.get_data()
    chat = str(callback['chat_id'])
    post = callback['post']
    if post == 'grade':
        uuid = callback['name'][1]
    else:
        uuid = callback['name'][0]
    order = db.check_order(chat, post)
    if order:
        db.update_order(chat, uuid, post)
    else:
        db.add_orders(chat, uuid, post)
    await call.message.answer(f'Вы подписались!')


@Config.dp.message_handler(Command(commands=['del']))
async def drop_orders(message: types.Message):
    db = Database()
    chat = message.chat.id
    db.drop_orders(str(chat))
    await message.answer('Ваши подписки на отчеты успешно удалены')


@Config.dp.callback_query_handler(text='exit', state=[States.post, States.pizza])
async def exit_work(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer(f'До свидания')
    await state.finish()


if __name__ == '__main__':
    Config.scheduler.start()
    executor.start_polling(Config.dp)
