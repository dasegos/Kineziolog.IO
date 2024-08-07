# Aiogram imports
from aiogram import Dispatcher, Bot
from app.handlers import main_router

# Other imports
import asyncio, os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Project imports
from app.scheduler import check_events


load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

async def main():
    '''START BOT'''
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(check_events, trigger='interval', seconds=60, kwargs={'bot' : bot}) # Add job to check events
    scheduler.start()
    dp.include_router(main_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
