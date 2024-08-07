# Other imports
import os
from dotenv import load_dotenv
import aiosqlite as aiosql

# Project imports
from ..config.db_config import *

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

class Tasks:
     '''This class implements commands for working with the tasks'''

     def __init__(self) -> None:
          '''Initialization...'''
          self.path = DB_PATH

     async def start(self) -> None:
          '''The method to create a table in the database if it doesn't exist'''
          request = '''CREATE TABLE IF NOT EXISTS tasks (
                         pk INTEGER PRIMARY KEY AUTOINCREMENT,
                         text TEXT NOT NULL,
                         timestamp INTEGER NOT NULL, 
                         event_id INTEGER NOT NULL,
                         FOREIGN KEY (event_id) REFERENCES events (pk))'''
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request)
               await con.commit()

     async def enqueue_task(self, text: str, timestamp: int | float, event_id: int) -> None:
         '''The method to create a new task'''
         await self.start()
         request = 'INSERT INTO tasks (text, timestamp, event_id) VALUES (?, ?, ?)'
         async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (text, int(timestamp), event_id))
               await con.commit()

     async def get_task(self, pk: int) -> tuple[int, str, int, int]:
         '''The method to get a task specified by its primary key'''
         await self.start()
         request = 'SELECT * FROM tasks WHERE pk = ?'
         async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (pk, ))
               result = await cursor.fetchone()
               return result

     async def get_tasks(self) -> list[tuple[int, str, int, int]]:
          '''The method to get all enquequed tasks'''
          await self.start()
          request = 'SELECT * FROM tasks'
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request)
               result = await cursor.fetchall()
               return result
          
     async def get_event_tasks(self, event_id: int) -> list[tuple[int, str, int, int]]:
          '''The method to get all tasks registered for a specified event'''
          await self.start()
          request = 'SELECT * FROM tasks WHERE event_id = ?'
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (event_id, ))
               result = await cursor.fetchall()
               return result
     
     async def delete_task(self, pk: int) -> None:
          '''The method to delete a tasks specified by its primary key'''
          await self.start()
          request = 'DELETE FROM tasks WHERE pk = ?'
          async with aiosql.connect(self.path) as con:
               cursor = await con.cursor()
               await cursor.execute(request, (pk, ))
               await con.commit()
