# Other imports
import redis.asyncio as aioredis

# Project imports
from ..config.db_config import *

class StatisticsTable:
     '''The class implements commands for working with `Redis DB` to store users' answers to the test.\n
        As for `aiogram` library being asynchronous we do not use `redis` but `aioredis`
     '''
          
     async def add_stat(self, uid: int, found_from: str, the_best: str, should_enhance: str, rate: str) -> None:
         '''The method creates a hashset in `Redis DB`. Doesn't return anything.
            1) `uid` -> user_telegram_id, unique identifier;\n
            Other params imply users' answers for test questions.
            To learn more, check out `app.text.text.Test` and `app.handlers.test_handlers`\n
            All hashsets are to expire in `SECONDS_BEFORE_EXPIRE` seconds. See the value of this 
            constant in `app.config.db_config`
         '''      
         async with aioredis.Redis(host='redis', port='6379', db=2, decode_responses=True) as client:
             await client.hset(uid, mapping={
                         'found_from' : found_from,
                         'the_best' : the_best,
                         'should_enhance' : should_enhance,
                         'rate' : rate
                    })
             await client.expire(uid, SECONDS_BEFORE_EXPIRE)
              
     async def has_completed_test(self, uid: int) -> bool:
          '''The method checks if uid is in the database. 
             If it is, returns True. Otherwise returns False.     
            1) `uid` -> user_telegram_id, unique identifier;
          '''
          async with aioredis.Redis(host='redis', port='6379', db=2, decode_responses=True) as client:
              result = await client.hgetall(uid)
              if result: return True
              return False

     async def read_stat(self) -> dict[str, list]:
          '''The method `scans` all hashlists and receives their values.\n
             Returns a dict with keys `found_from`, `the_best`, `should_enhance`, `rate`\n
             `WARNING!` The returned information is thought to be furtherly pushed into `excel` file
          '''
          found_from = []
          the_best = []
          should_enhance = []
          rate = []
          async with aioredis.Redis(host='redis', port='6379', db=2, decode_responses=True) as client:
               coroutine = await client.scan()
               hashsets = coroutine[1]
               for hash in hashsets:
                    result = await client.hgetall(hash)
                    found_from.append(result['found_from'])
                    the_best.append(result['the_best'])
                    should_enhance.append(result['should_enhance'])
                    rate.append(result['rate'])
               return {'found_from' : found_from, 'the_best' : the_best, 'should_enhance' : should_enhance, 'rate' : rate}
