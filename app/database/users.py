# Other imports
import os
import aiosqlite as aiosql
from dotenv import load_dotenv

# Project imports
from ..exceptions import InvalidStatusPassedError

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

class Users:
    '''This class implements commands for working with the bot's users database'''

    def __init__(self):
        '''Initialization...'''
        self.path = DB_PATH

    async def start(self) -> None:
        '''The method creates a table in the database'''
        request = '''CREATE TABLE IF NOT EXISTS users (
                       user_telegram_id INTEGER PRIMARY KEY NOT NULL,
                       status TEXT NOT NULL)'''
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request)
            await con.commit()

    async def set_status(self, uid: int, status: str) -> None:
        '''The method changes user's status'''
        await self.start()
        if status not in ('member', 'blocked'):
            raise InvalidStatusPassedError()
        request = 'UPDATE users SET status = ? WHERE user_telegram_id = ?'
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request, (status, uid))
            await con.commit()

    async def user_exists(self, uid: int) -> bool:
        '''The method checks if a user is in the table'''
        await self.start()
        request = 'SELECT * FROM users WHERE user_telegram_id = ?'
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request, (uid, ))
            result = await cursor.fetchone()
            if result: return True
            return False
    
    async def add_user(self, uid: int) -> None:
        '''The method adds a user into the table'''
        await self.start()
        if not await self.user_exists(uid):
            request = 'INSERT INTO users(user_telegram_id, status) VALUES(?, ?)'
            async with aiosql.connect(self.path) as con:
                cursor = await con.cursor()
                await cursor.execute(request, (uid, 'member'))
                await con.commit()
        else:
            await self.set_status(uid, 'member')

    async def get_user(self, uid: int) -> tuple[int, str]:
        '''The methos gets a user fron the table by their ID'''
        await self.start()
        request = 'SELECT * FROM users WHERE user_telegram_id = ?'
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request, (uid, ))
            result = await cursor.fetchone()
            return result
            
    async def get_all_users(self) -> list[tuple[int, str]]:
        '''The methos gets all users fron the table by their ID'''
        await self.start()
        request = 'SELECT * FROM users'
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request)
            result = await cursor.fetchall()
            return result

    async def get_members(self) -> list[tuple[int, str]]:
        '''The method returns only users who haven't blocked the bots'''
        await self.start()
        request = 'SELECT * FROM users WHERE status = `member`'
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request)
            result = await cursor.fetchall()
            return result

    async def delete_user(self, uid: int) -> None:
        '''The method deletes user from the table'''
        await self.start()
        request = 'DELETE * FROM users WHERE user_telegram_id = ?'
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            await cursor.execute(request, (uid, ))
            await con.commit()

class Receivers:
    '''This class implements commands for working with the newsletter'''  

    def __init__(self) -> None:
        '''Initialization...'''
        self.path = DB_PATH

    async def start(self) -> None:
        '''The method to create a table in the db if it doesn't exist'''
        async with aiosql.connect(self.path) as con:
            request = '''CREATE TABLE IF NOT EXISTS receivers (
                          user_telegram_id INTEGER PRIMARY KEY NOT NULL,
                          received INTEGER NOT NULL)'''
            await con.execute(request)
            await con.commit()

    async def fill(self) -> None:
        '''The method fills a table with default data'''
        await self.start()
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            request = 'INSERT INTO receivers (user_telegram_id, received) SELECT user_telegram_id, ? FROM users'
            await cursor.execute(request, (0, ))
            await con.commit()

    async def set_success(self, uid: int) -> None:
        '''The method sets status to 1 (success)'''
        await self.start()
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            request = 'UPDATE receivers SET received = ? WHERE user_telegram_id = ?'
            await cursor.execute(request, (1, uid))
            await con.commit()

    async def receivers(self) -> list[tuple[int, int]]:
        '''The method returns all receivers'''
        await self.start()
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            request = 'SELECT * FROM receivers'
            await cursor.execute(request)
            result = await cursor.fetchall()
            return result
    
    async def received(self) -> list[tuple[int, int]]:
        '''The method returns all users who received the newsletter (have value `1` in field `received`)'''
        receivers = await self.receivers()
        result = []
        for receiver in receivers:
            if receiver[1] == 1:
                result.append(receiver)
        return result

    async def not_received(self) -> list[tuple[int, int]]:
        '''The method returns all users who haven't received the newsletter (have value `0` in field `received`)'''
        receivers = await self.receivers()
        result = []
        for receiver in receivers:
            if receiver[1] == 0:
                result.append(receiver)
        return result
    
    async def drop_table(self) -> None:
        '''The method drops a table `receivers` once the newsletter is finished'''
        async with aiosql.connect(self.path) as con:
            cursor = await con.cursor()
            request = 'DROP TABLE IF EXISTS receivers'
            await cursor.execute(request)