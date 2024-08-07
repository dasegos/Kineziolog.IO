# Aiogram imports
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Other imports
from dotenv import load_dotenv
import os

# Project imports
from ..text.text import Info, ContactMeText, start_text
from ..keyboards import admin_keyboard, reply_menu_keyboard, share_contact, study_keyboard, products_keyboard, faq_keyboard
from ..fsm import ContactMe
from ..middlewares.auth_middleware import AutheticationMiddleware
from ..utils import send_mail
from ..database.users import Users

all_router = Router()
other_router = Router()
other_router.message.middleware(AutheticationMiddleware(0))

# Basic Info / Базовая информация
# ------------------------------------
@all_router.message(Command('start'))
async def cmd_start(message: Message):
    load_dotenv()
    kb = None
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        kb = admin_keyboard
    else: 
        users = Users()
        await users.add_user(message.from_user.id)
        kb = reply_menu_keyboard
    await message.answer(await start_text(message.from_user.first_name), parse_mode='html', reply_markup=kb)

@all_router.message(F.text == 'Github проекта 😎')
@all_router.message(Command('github'))
async def cmd_github(message: Message):
    await message.answer(Info.github)

@other_router.message(F.text == 'Адрес')
@other_router.message(Command('address'))
async def cmd_address(message: Message):
    await message.answer(Info.address, parse_mode='html')

@other_router.message(F.text == 'О центре')
@other_router.message(Command('about'))
async def cmd_about(message: Message):
    await message.answer(Info.about, parse_mode='html')

@other_router.message(F.text == 'Продукты')
@other_router.message(Command('products'))
async def cmd_products(message: Message):
    await message.answer(Info.products, reply_markup=products_keyboard)

@other_router.message(F.text == 'Обучение')
@other_router.message(Command('study'))
async def cmd_study(message: Message):
    await message.answer(Info.study, reply_markup=study_keyboard)

@other_router.callback_query(F.data == 'seminars')
async def seminars(callback: CallbackQuery):
    await callback.message.answer(Info.seminars, parse_mode='html')

@other_router.callback_query(F.data == 'video-courses')
async def seminars(callback: CallbackQuery):
    await callback.message.answer(Info.video_courses, parse_mode='html')

@other_router.message(F.text == 'Частые вопросы')
@other_router.message(Command('faq'))
async def faq(message: Message):
    await message.answer(Info.faq, reply_markup=faq_keyboard)
# ------------------------------------

# FAQ / Часто задаваемые вопросы
# ------------------------------------
@other_router.callback_query(F.data == 'services')
async def seminars(callback: CallbackQuery):
    await callback.message.answer(Info.services, parse_mode='html')

@other_router.callback_query(F.data == 'kineziology')
async def seminars(callback: CallbackQuery):
    await callback.message.answer(Info.kineziology, parse_mode='html')

@other_router.callback_query(F.data == 'acupuncture')
async def seminars(callback: CallbackQuery):
    await callback.message.answer(Info.acupuncture, parse_mode='html')

@other_router.callback_query(F.data == 'insoles')
async def seminars(callback: CallbackQuery):
    await callback.message.answer(Info.insoles, parse_mode='html')
# ------------------------------------

# Contact me / Свяжитесь со мной
# ------------------------------------
@other_router.message(F.text == 'Свяжитесь со мной')
@other_router.message(Command('contact_me'))
async def cmd_contact_me_1(message: Message, state: FSMContext):
    await message.answer(ContactMeText.share_contact, reply_markup=share_contact)
    await state.set_state(ContactMe.number)

@other_router.message(ContactMe.number)
async def cmd_contact_me_2(message: Message, state: FSMContext):
    if message.content_type == 'contact':
        await message.answer(ContactMeText.contact_gathered_successfully)
        await state.update_data(phone=message.contact)
        await message.answer(ContactMeText.input_name)
        await state.set_state(ContactMe.name)
    else: 
        await message.answer(ContactMeText.cancel, reply_markup=reply_menu_keyboard)
        await state.clear()

@other_router.message(ContactMe.name)
async def cmd_contact_me_3(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(ContactMeText.input_time)
    await state.set_state(ContactMe.time)

@other_router.message(ContactMe.time)
async def cmd_contact_me_4(message: Message, bot: Bot, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer(ContactMeText.val_success, reply_markup=reply_menu_keyboard)
    data = await state.get_data()
    await state.clear()
    load_dotenv()
    text = await ContactMeText.form_request(*data.values())
    await bot.send_message(os.getenv('ADMIN_ID'), text)
    await send_mail(os.getenv('TARGET_MAIL'), text)
# ------------------------------------
