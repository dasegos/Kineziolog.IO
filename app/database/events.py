# Other imports
import os
from dotenv import load_dotenv
import aiosqlite as aiosql
from datetime import datetime

# Project imports
from ..config.db_config import *

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

class Events:
     '''This class implements commands for working with the events'''

     def __init__(self) -> None:
          '''Initialization...'''
          self.path = DB_PATH

     async def start(self) -> None:
          '''The method to create a table in the database if it doesn't exist'''
          request = '''CREATE TABLE IF NOT EXISTS events (
                         pk INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL, 
                         datetime TEXT NOT NULL)'''
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request)
               await con.commit()

     async def add_event(self, name: str, datetime: datetime) -> int: # OnChange
         '''The method to create a new event'''
         await self.start()
         request = 'INSERT INTO events (name, datetime) VALUES (?, ?) RETURNING pk'
         async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (name, datetime))
               pk = await cursor.fetchone()
               await con.commit()
               return pk

     async def get_event(self, pk: int) -> tuple[int, str, str]:
         '''The method to get an event'''
         await self.start()
         request = 'SELECT * FROM events WHERE pk = ?'
         async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (pk, ))
               result = await cursor.fetchone()
               return result

     async def get_events(self) -> list[tuple[int, str, str]]:
          '''The method to get all event'''
          await self.start()
          request = 'SELECT * FROM events'
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request)
               result = await cursor.fetchall()
               return result
     
     async def delete_event(self, pk: int) -> None: # OnChange
          '''The method to delete an event by its primary key'''
          await self.start()
          request = 'DELETE FROM events WHERE pk = ?'
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (pk, ))
               await con.commit()
