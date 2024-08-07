# Aiogram imports
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

# Other imports
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from aiosqlite import IntegrityError

# Project imports
from .database.tasks import Tasks
from .database.users import Receivers, Users

load_dotenv()

async def notificate(bot: Bot, text: str):
    '''The method to start notificating users about forthcoming events'''
    try: 
        receivers = Receivers()
        await receivers.fill()
        users_table = Users()
        uids = [user[0] for user in await receivers.not_received()]
        for uid in uids:
            try:
                await bot.send_message(uid, text)
            except TelegramRetryAfter as ex: # the sort of scenario when we are making to many requests per second  
                await asyncio.sleep(ex.retry_after)
                return await bot.send_message(uid, text)
            except TelegramForbiddenError: # if a user blocked the bot immediately after we copied `users` db
                await users_table.set_status(uid, 'blocked')
            else:
                user = await users_table.get_user(uid)
                if user[1] == 'blocked':
                    await users_table.set_status(uid, 'member')
                await receivers.set_success(uid) # changing receiving status to success (1)
        await receivers.drop_table()
    except IntegrityError: # if the `receivers` table exists for some reason (?)
        await receivers.drop_table()
        asyncio.sleep(.05)
        await notificate(bot, text)

async def check_events(bot: Bot):
    '''The function to check if there are any events currently waiting for execution'''
    tasks = Tasks()
    all_tasks = await tasks.get_tasks()
    if all_tasks:
        for task in all_tasks:
            if task[2] == int(datetime.timestamp(datetime.now()) / 60):
                await notificate(bot, task[1])
                await tasks.delete_task(task[0])