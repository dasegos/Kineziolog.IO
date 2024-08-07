# Aiogram imports
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

products_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Кинезио тейпы ⭢', url='https://kineziolog-tape.ru/product-category/kinesio-tape/'), InlineKeyboardButton(text='Кросс тейпы ⭢', url='https://kineziolog-tape.ru/product-category/cross-tape/')],
    [InlineKeyboardButton(text='Другие аксессуары ⭢', url='https://kineziolog-tape.ru/product-category/aksessuary/')]])

study_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Семинары 👤', callback_data='seminars')],
    [InlineKeyboardButton(text='Видео-курсы 📹', callback_data='video-courses')]])

commit_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Хорошо!', callback_data='start_test')],
    [InlineKeyboardButton(text='Позже', callback_data='cancel_test')]])

add_inline_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да', callback_data='add_btn')],
    [InlineKeyboardButton(text='Нет', callback_data='no_btn')]])

start_newsletter = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Начинаем!', callback_data='start_newsletter')],
    [InlineKeyboardButton(text='Отмена', callback_data='cancel_newsletter')]])

faq_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Услуги', callback_data='services')],
    [InlineKeyboardButton(text='Что такое кинезиология?', callback_data='kineziology')],
    [InlineKeyboardButton(text='Что такое акупунктура?', callback_data='acupuncture')],
    [InlineKeyboardButton(text='Подбор стелек', callback_data='insoles')]])

admin_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Новое событие'), KeyboardButton(text='События')],
    [KeyboardButton(text='Статистика'), KeyboardButton(text='Начать рассылку')],
    [KeyboardButton(text='Информация для админа')]], resize_keyboard=True)

reply_menu_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Адрес'), KeyboardButton(text='О центре')],
    [KeyboardButton(text='Продукты'), KeyboardButton(text='Обучение')],
    [KeyboardButton(text='Частые вопросы'), KeyboardButton(text='Свяжитесь со мной')],
    [KeyboardButton(text='Github проекта 😎')]], resize_keyboard=True)

share_contact = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Поделиться', request_contact=True)],
    [KeyboardButton(text='Отмена')]], resize_keyboard=True, one_time_keyboard=True)

found_from_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Друзья / знакомые / родственники')],
    [KeyboardButton(text='Реклама ВК'), KeyboardButton(text='Instagram')],
    [KeyboardButton(text='Другое')]], resize_keyboard=True, one_time_keyboard=True)

async def form_events_keyboard(events: list[tuple[int, str, str, str, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for event in events:
        kb.button(text=f'{event[1]} - {event[2]}', callback_data=f'{event[0]}')
    kb.adjust(1)
    return kb.as_markup()

async def form_option(pk: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Удалить', callback_data=f'delete{pk}')]])
    return kb

async def form_newsletter_keyboard(btn_text: str, btn_link: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, url=btn_link)]])
    return kb
