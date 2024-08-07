# Aiogram imports 
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

# Other imports
import asyncio
import aiosqlite

# Project imports
from .database.users import Users, Receivers


class Newsletter:
    '''The class to work with custom newsletter'''

    def __init__(self, bot: Bot):
        '''Initialization'''
        self.bot = bot

    async def send_msg(self, to_chat_id: int, from_chat_id: int, message_id: int, relpy_markup: InlineKeyboardMarkup) -> None:
        '''The method to send a message to a user.\n
            Parameters:\n
            - `to_chat_id` : `int` - target chat id;
            - `from_chat_id` : `int` - newsletter's author (admin's chat id);
            - `message_id` : `int` - newsletter's message id;
            - `relpy_markup` : `InlineKeyboardMarkup` - inline keyboard;\n
            Returns `None`'''
        receivers = Receivers()
        users_table = Users()
        try:
            await self.bot.copy_message(to_chat_id, from_chat_id, message_id, reply_markup=relpy_markup) # copies message from admin's chat to the target chat
        except TelegramRetryAfter as ex: # the sort of scenario when we are making to many requests per second  
            await asyncio.sleep(ex.retry_after)
            return await self.bot.copy_message(to_chat_id, from_chat_id, message_id, reply_markup=relpy_markup)
        except TelegramForbiddenError: # if a user blocked the bot immediately after we copied `users` db
            await users_table.set_status(to_chat_id, 'blocked')
        else:
            user = await users_table.get_user(to_chat_id)
            if user[1] == 'blocked':
                await users_table.set_status(to_chat_id, 'member')
            await receivers.set_success(to_chat_id) # changing receiving status to success (1)

    async def start(self, from_chat_id: int, message_id: int, relpy_markup: InlineKeyboardMarkup = None) -> dict[str, int]:
        '''The initial method that starts the newsletter.\n
            Parameters:\n
            - `from_chat_id` : `int` - newsletter's author (admin's chat id);
            - `message_id` : `int` - newsletter's message id;
            - `relpy_markup` : `InlineKeyboardMarkup` - inline keyboard;\n
            Returns `dict` with two keys: `all` - all receivers & `success` - with exit code success (1)
        '''
        receivers = Receivers()
        try:
            await receivers.fill() # Filling the db with default data
            uids = [receiver[0] for receiver in await receivers.not_received()] # Getting ids of the users who haven't received the newsletter yet (at this stage must be all users' ids)
            for uid in uids:
                await self.send_msg(uid, from_chat_id=from_chat_id, message_id=message_id, relpy_markup=relpy_markup)
                await asyncio.sleep(.05) # So that we don't exceed the Telegram's limit for requests per second
            all = await receivers.receivers()
            success = await receivers.received()
            await receivers.drop_table()
            return {'all' : len(all),
                    'success' : len(success)}
        except aiosqlite.IntegrityError:
            await receivers.drop_table()
            asyncio.sleep(.05)
            await self.start(from_chat_id, message_id, relpy_markup)
