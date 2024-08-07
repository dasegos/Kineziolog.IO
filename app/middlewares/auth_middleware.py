# Aiogram imports
from aiogram.types import Message, CallbackQuery
from aiogram import BaseMiddleware

# Other imports
from typing import Callable, Awaitable, Dict, Any
from dotenv import load_dotenv
import os

# Project imports
from ..text.text import Admin, Info, Error
from ..exceptions import UnknownAuthLevel

class AutheticationMiddleware(BaseMiddleware):
    '''Middleware to check if user is admin or not'''
    
    def __init__(self, auth_level: int):
     '''Auth_level stands for:
        1) `0` commands available only for users;
        2) `1` commands available only for admin;
     '''
     if auth_level in (0, 1): self.auth_level = auth_level
     else: raise UnknownAuthLevel(auth_level)

    async def __call__(self, 
                handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
                event: Message | CallbackQuery,
                data: Dict[str, Any]) -> Any:
       
       load_dotenv()
       ADMIN_ID = int(os.getenv('ADMIN_ID'))

       if self.auth_level == 0:
          if event.from_user.id != ADMIN_ID:
             return await handler(event, data)
          else: 
             await event.answer(Error.unrecognized_command_error)
             await event.answer(Admin.admin_commands)
       else:
          if event.from_user.id == ADMIN_ID:
             return await handler(event, data)
          else: 
             await event.answer(Error.unrecognized_command_error)
             await event.answer(Info.user_commands)