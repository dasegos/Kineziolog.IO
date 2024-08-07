# Aiogram imports
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

# Other imports
import os
import datetime as dt
from aiogram_calendar import DialogCalendar, DialogCalendarCallback
from dotenv import load_dotenv

# Project imports
from ..fsm import CreateEvent, CreateNewsletter, InlineBtn
from ..text.text import Admin, Error
from ..middlewares.auth_middleware import AutheticationMiddleware
from ..database.stat import StatisticsTable
from ..database.events import Events
from ..database.tasks import Tasks
from ..utils import to_excel, process_data, process_time
from ..keyboards import form_events_keyboard, form_option, form_newsletter_keyboard, add_inline_buttons, start_newsletter
from ..newsletter import Newsletter
from ..config.db_config import THREE_DAYS_SECONDS, ONE_DAY_SECONDS

admin_router = Router()
admin_router.message.middleware(AutheticationMiddleware(1))

# Information for Admin / Информация для админа
# ---------------------------------------------
@admin_router.message(F.text == 'Информация для админа')
@admin_router.message(Command('info'))
async def cmd_info(message: Message):
    await message.answer(Admin.info)
# ---------------------------------------------

# Getting statistics / Получение статистики студии
# ---------------------------------------------
@admin_router.message(F.text == 'Статистика')
@admin_router.message(Command('statistics'))
async def cmd_statistics(message: Message):
    statistics_table = StatisticsTable()
    result = await statistics_table.read_stat()
    path = await to_excel(result, 'stat.xlsx')
    await message.answer_document(FSInputFile(path=path))
# ---------------------------------------------

# Setting a newsletter / Начинаем рассылку
# ---------------------------------------------
@admin_router.message(F.text == 'Начать рассылку')
@admin_router.message(Command('set_newsletter'))
async def cmd_set_newsletter_1(message: Message, state: FSMContext):
    await message.answer(Admin.input_newsletter_text)
    await state.set_state(CreateNewsletter.text)

@admin_router.message(CreateNewsletter.text)
async def cmd_set_newsletter_2(message: Message, state: FSMContext):
    await state.update_data(from_chat=message.from_user.id, msg_id=message.message_id)
    await message.answer(Admin.adding_buttons, reply_markup=add_inline_buttons)
    await state.set_state(CreateNewsletter.decision)

@admin_router.callback_query(CreateNewsletter.decision)
async def cmd_set_newsletter_3(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == 'add_btn':
        await callback.message.answer(Admin.input_btn_text)
        await state.set_state(InlineBtn.text)
    else:
        data = await state.get_data()
        await bot.copy_message(callback.from_user.id, data['from_chat'], data['msg_id'])
        await callback.message.answer(Admin.creating_newsletter, reply_markup=start_newsletter) 
        await state.set_state(CreateNewsletter.confirmation)

@admin_router.message(InlineBtn.text)
async def cmd_set_newsletter_5(message: Message, state: FSMContext):
    await state.update_data(btn_text=message.text)
    await message.answer(Admin.input_link)
    await state.set_state(InlineBtn.link)

@admin_router.message(InlineBtn.link)
async def cmd_set_newsletter_6(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(btn_link=message.text)
    data = await state.get_data()
    try: 
        await bot.copy_message(message.from_user.id, data['from_chat'], data['msg_id'], reply_markup=await form_newsletter_keyboard(data['btn_text'], data['btn_link']))
        await message.answer(Admin.creating_newsletter, reply_markup=start_newsletter)
        await state.set_state(CreateNewsletter.confirmation)
    except TelegramBadRequest:
        await message.answer(Error.invalid_url_passed)

@admin_router.callback_query(CreateNewsletter.confirmation)
async def cmd_set_newsletter_7(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == 'start_newsletter':
        data = await state.get_data()
        await state.clear()
        await callback.message.answer(Admin.newsletter_started_successfully)
        newsletter = Newsletter(bot)
        kb = None
        if data.get('btn_text') and data.get('btn_link'):
            kb = await form_newsletter_keyboard(data['btn_text'], data['btn_link'])
        result = await newsletter.start(data['from_chat'], data['msg_id'], relpy_markup=kb)
        await callback.message.answer(await Admin.newsletter_results(result['all'], result['success']))
    else:
        await callback.message.answer(Admin.newsletter_canceled)
        await state.clear()
# ---------------------------------------------

# CREATE - Creating an event / Создание события
# ---------------------------------------------
@admin_router.message(F.text == 'Новое событие')
@admin_router.message(Command('create_event'))
async def cmd_create_event_1(message: Message, state: FSMContext):
    await message.answer(Admin.input_event_name)
    await state.set_state(CreateEvent.name)

@admin_router.message(CreateEvent.name)
async def cmd_create_event_2(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    load_dotenv()
    await message.answer(text=Admin.select_date, reply_markup=await DialogCalendar(locale='ru_RU.UTF-8').start_calendar())

@admin_router.callback_query(DialogCalendarCallback.filter())
async def cmd_create_event_3(callback: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    selected, date = await DialogCalendar(locale='ru_RU.UTF-8').process_selection(callback, callback_data)
    if selected:
        await state.update_data(date=date.strftime('%Y/%m/%d'))
        await callback.message.answer(Admin.select_time)
        await state.set_state(CreateEvent.time)

@admin_router.message(CreateEvent.time)
async def cmd_create_event_4(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(time=message.text)
    data = await state.get_data()
    await state.clear()
    date = data['date']
    time = data['time']

    year, month, day = (map(int, date.split('/'))) # Split date string

    try:
        hour, minute = (map(int, time.split(':'))) # Split time string
        datetime = f'{date} {time}'
        expired = await process_time(dt.datetime.now(), 
                                     dt.datetime(year, month, day, hour, minute))

        if expired <= 0: # If datetime has passed already
            await message.answer(Admin.event_datetime_passed)

        else:
            # Creating an event 
            # --------------------
            events = Events()
            pk = await events.add_event(data['name'], datetime) # Returning Primary Key
            # --------------------

            if expired > ONE_DAY_SECONDS:
                tasks = Tasks()
                await tasks.enqueue_task(await Admin.notification_text(data['name'], datetime, Admin.one_day),
                                         await process_data(year, month, day, hour, minute, 1),
                                         pk[0])

            if expired > THREE_DAYS_SECONDS:
                tasks = Tasks()
                await tasks.enqueue_task(await Admin.notification_text(data['name'], datetime, Admin.three_days),
                                         await process_data(year, month, day, hour, minute, 3),
                                         pk[0])

            await message.answer(Admin.event_created_successfully) # on success

    except ValueError: # Except invalid time was passed, ex. `abcd`, `12/00`
        await message.answer(Error.invalid_time_passed)
# ---------------------------------------------

# READ 
# I. Getting all events / Получение всех событий
# ---------------------------------------------
@admin_router.message(F.text == 'События')
@admin_router.message(Command('registered_events'))
async def cmd_registered_events(message: Message):
    events = Events()
    events = await events.get_events()
    if events:
        keyboard = await form_events_keyboard(events)
        await message.answer(Admin.events, reply_markup=keyboard)
    else:
        await message.answer(Admin.empty_events_sequence)
# ---------------------------------------------

# II. Getting an event / Получение одного события
# ---------------------------------------------
@admin_router.callback_query(F.data.regexp(r'[\d]+', mode='fullmatch'))
async def event(callback: CallbackQuery):
    events = Events()
    data = await events.get_event(int(callback.data))
    try:
        await callback.message.answer(await Admin.form_event(data[1], data[2]), 
                                      reply_markup=await form_option(int(callback.data)), parse_mode='html')
    except TypeError:
        await callback.message.answer(Admin.event_does_not_exist)
# ---------------------------------------------

# DELETE - Deleting an event / Удаление события
# ---------------------------------------------
@admin_router.callback_query(F.data.regexp(r'delete[\d]+', mode='fullmatch'))
async def delete_event(callback: CallbackQuery, bot: Bot):
    events = Events()
    pk = int(callback.data[6:])
    tasks = Tasks()
    event_tasks = await tasks.get_event_tasks(pk)
    if event_tasks:
        for task in event_tasks:
            await tasks.delete_task(task[0])
    await events.delete_event(pk)
    await callback.message.edit_text(Admin.event_deleted_successfully)
# ---------------------------------------------