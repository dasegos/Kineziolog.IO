# Aiogram imports
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Project imports
from ..text.text import Test
from ..fsm import TestInfo
from ..keyboards import reply_menu_keyboard, found_from_keyboard, commit_keyboard
from ..middlewares.auth_middleware import AutheticationMiddleware
from ..database.stat import StatisticsTable

test_router = Router()
test_router.message.middleware(AutheticationMiddleware(0))

@test_router.message(F.text == 'Пройти тест')
@test_router.message(Command('test'))
async def cmd_test(message: Message):
    statistics_table = StatisticsTable()
    if await statistics_table.has_completed_test(message.from_user.id):
        await message.reply(Test.already_completed_error, parse_mode='html')
    else:
        await message.answer(Test.start, reply_markup=commit_keyboard)

@test_router.callback_query(F.data == 'cancel_test')
async def start_test_1(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(Test.canceled_test, reply_markup=reply_menu_keyboard)

@test_router.callback_query(F.data == 'start_test')
async def start_test_1(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(Test.q1, reply_markup=found_from_keyboard)
    await state.set_state(TestInfo.q1)

@test_router.message(TestInfo.q1)
async def start_test_2(message: Message, state: FSMContext):
    found_from = message.text
    await state.update_data(found_from=found_from)
    await message.answer(Test.q2)
    await state.set_state(TestInfo.q2)

@test_router.message(TestInfo.q2)
async def start_test_3(message: Message, state: FSMContext):
    the_best = message.text
    await state.update_data(the_best=the_best)
    await message.answer(Test.q3)
    await state.set_state(TestInfo.q3)
    
@test_router.message(TestInfo.q3)
async def start_test_4(message: Message, state: FSMContext):
    should_enhance = message.text
    await state.update_data(should_enhance=should_enhance)
    await message.answer(Test.rate, parse_mode='html')
    await state.set_state(TestInfo.rate)

@test_router.message(TestInfo.rate)
async def start_test_5(message: Message, state: FSMContext):
    rate = message.text
    await state.update_data(rate=rate)
    data = await state.get_data()
    await state.clear()
    statistics_table = StatisticsTable()
    await statistics_table.add_stat(message.from_user.id, 
                              data['found_from'], 
                              data['the_best'],
                              data['should_enhance'],
                              data['rate'])
    await message.answer(Test.info_sent, reply_markup=reply_menu_keyboard)