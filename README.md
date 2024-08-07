# Бот на `aiogram` для студии «Kineziolog»
## Features:
> __1) Создание рассылки:__     

Рассылка в боте реализована следующим образом: Предполагается наличие основой БД `Users`, в которую мы добавляем данные, если пользователь написал боту, нажав на команду `/start`:
```
@all_router.message(Command('start'))  
async def cmd_start(message: Message):   
    load_dotenv()
    kb = None
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
       kb = admin_keyboard
    else: 
       kb = reply_menu_keyboard
       users = Users()
       await users.add_user(message.from_user.id)
    await message.answer(await start_text(message.from_user.first_name), parse_mode='html', reply_markup=kb)
```
Метод класса `Users` `add_user` принимает один аргумент - уникальный идентификатор пользователя в Telegram. Код метода:
```
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
```
Таким образом, если пользователь уже существует, то его статус просто измениться на `member`. Если пользователя нет, то он добавится в БД.   
Доступная админу команда `/set_newsletter` предлагает создать рассылку. В качестве рассылаемого сообщения можно отправить текст или текст с картинкой. Также есть возможность добавить `inline-кнопку`. Если для кнопки будет представлен невалидный `url-адрес` (при выполнении кода возбудится исключение `TelegramBadRequest`), то админа снова попросят ввести ссылку. Как только будет сформировано сообщение, начнется рассылка. Перед этим бот переспросит админа о том, начинать ли рассылку.  
Код реализации рассылки находится в модуле `newsletter`. В нем есть одноименный класс, в котором и реализуются все методы. Код класса:
```
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
```
Поподробнее разберем код. Для создания рассылки нужно запустить метод `start()` у экземляра класса. В него передаются такие параметры: `from_chat_id`, `message_id`, `relpy_markup`. Они представляют собой `id` чата, из которого копируется сообщение, `id` самого сообщения и клавиатура (если такая имеется) соответственно. В начале метод создает экземпляр класса `Receivers`. Через метод `fill()` создается и заполняется новая таблица, в которой будут получатели рассылки. По сути это будут те же пользователи, что и в таблице `users`, но поля у таблицы `receivers` - другие. Появляется колонка `received`, представляющая собой статус отправки сообщения тому или иному пользователю. При заполнении в ней стоит `0`, а при успешной отправке она меняется на `1`. Во втором методе класса `send_msg` есть обраблтка таких исключений, которые могут возбудится при выполнении кода: `TelegramRetryAfter` и `TelegramForbiddenError`. Первое возбудится в том случае, если мы делаем слишком много запросов в секунду (лимит в последней доке - 30). Если это происходит, то мы "спим" указанное в ошибке время секунд:
```
except TelegramRetryAfter as ex: # the sort of scenario when we are making to many requests per second  
    await asyncio.sleep(ex.retry_after)
```
Второе исключение возбудится в том случае, если пользователь заблокировал бота. Тогда в БД `users` мы меняем статус этого пользователя на `blocked`. Если же никаких исключений не было возбуждено, то выполняется этот код:
```
user = await users_table.get_user(to_chat_id)
if user[1] == 'blocked':
    await users_table.set_status(to_chat_id, 'member')
await receivers.set_success(to_chat_id) # changing receiving status to success
```
Тут мы создаем экземпляр класса `Users` и проверяем в БД статус того пользователя, которому только что успешно (!) отправили сообщение. Если он равен `blocked`, то мы меняем его на `member`.   
Это все, что касается рассылки.
> __2) Тест (статистика):__     

Тест в этом боте - это обычный опросник: "откуда вы узнали о студии", "что вам понравилось больше всего" и т.д.. Тест можно проходить раз в три месяца. Это сделано для защиты от нелегитимной информации. Хранение ответов и `user_id` реализовано простейшим образом через БД `redis`. `expire` для каждой записи равно количеству секунд в трех месяццах. Весь код можно посмотреть в `database.stat`.    
Единственный важный момент заключается в том, что в качестве `redis` использовался такой модуль: `import redis.asyncio as aioredis`. Ввиду того, что `aiogram` - асинхронный, хотелось также использовать асинхронную библиотеку для работы с БД (сам `redis` - синхронный).   
Конвертация в файл `.xlsx` также предельно простая - через `pandas` и `dataframe`. Код конвертирующей функции:
```
async def to_excel(values: dict[str, list], path: str) -> str:
    dataframe = pd.DataFrame(values)
    dataframe.to_excel(path, sheet_name='Статистика', index=False)
    return path
```
Отправка файла в `aiogram` делается следущим образом:  
`await message.answer_document(FSInputFile(path=path))`. `FSInputFile` импортируется из `aiogram.types`.
На этом все со статистикой.
> __3) Мидлварь (`Middleware`):__

Код для `middleware` находится в модуле `middlewares.auth_middleware`. Функция этого мидлваря - разделение информации и команд, которые могут получить и использовать админ и пользователи. Код:
```
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
```
При инициализации он принимает один аргумент - `auth_level`, который может принимать два значение: `1` и `0`. `1` значит, что привязанные к мидлварю хэндлеры будут доступны только админу, а `0` - только обычным пользователям. Более того, если переданный `auth_level` не является ни `0`, ни `1`, то возбуждается кастомное исключение `UnknownAuthLevel`. Все кастомные исключение есть в модуле `exceptions`.
> __4) Обратная связь:__

В боте настроено два вида обратной связи: в чат админа и на админский `email`. С чатом все предельно просто:
```
load_dotenv()
text = await ContactMeText.form_request(*data.values())
await bot.send_message(os.getenv('ADMIN_ID'), text)
```
В методе `form_request` формируем текст для обратной связи - информацию о пользователе. С `gmail` почтой все сложнее. Первый нюанс -  в 2022 году компания `gmail` отменила прямую возможность пересылки сообщений через сторонние сервисы с логином и паролем. Теперь необходимо генерировать специальные "пароли приложения" и использовать их для входа. При этом высока вероятность того, что ваши письма попадут в спам и будут помечены как "возможно опасные" и "подозрительные". Отправление реализовано через библиотеки `smtplib` и `email`. Код находится в модуле `utils`:
```
async def send_mail(to: str, text: str):
    load_dotenv()
    login = os.getenv('GMAIL_LOGIN')
    password = os.getenv('GMAIL_PASSWORD')

    email = MIMEText(text, 'plain', 'utf-8')
    email['Subject'] = Header('Поступил запрос на обратную связь!', 'utf-8')
    email['From'] = login
    email['To'] = to

    con = smtplib.SMTP(host='smtp.gmail.com', port=587)
    con.ehlo() # Not necessary
    con.starttls()
    con.ehlo() # Not necessary
    con.login(login, password)
    con.sendmail(email['From'], to, email.as_string())
    con.quit()
```
> __5) События:__

Возможность добавлять события сделана для реализации уведомлений. Админ бота может регестрировать события с определенным названием на определенную дату с точностью до минуты. После этого событие добавляется в таблицу `events`.  
Уведомления необходимо было сделать за день и за три до наступления события. Так как днем проведения может быть первый - третий день месяца, то для получения правильной даты в модуле `utils` реализована функция `process_data`:
```
async def process_data(year: int, month: int, day: int, hour: int, minute: int, rollback: int) -> int:
    if (rollback == 3 and day <= 3) or (rollback == 1 and day <= 1):
        prev_month_days = calendar.monthrange(year, month-1)
        prev_month_day = prev_month_days[1] - abs(day - rollback)
        return int(datetime.timestamp(datetime(year, month-1, prev_month_day, hour, minute)) / 60)
    return int(datetime.timestamp(datetime(year, month, day-rollback, hour, minute)) / 60)
```
Пожалуй, подробное описание работы ф-ции можно опустить. Если есть желание, можно разобраться самостоятельно.  
Итак, вот весь код хэндлера, создающего эвент:
```
@admin_router.message(CreateEvent.time)
async def cmd_create_event_4(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(time=message.text)
    data = await state.get_data()
    await state.clear()
    date = data['date']
    time = data['time']

    year, month, day = (map(int, date.split('/'))) # Split date string

    try:
        hour, minute = (map(int, time.split(':'))) # Split time string
        datetime = f'{date} {time}'
        expired = await process_time(dt.datetime.now(), 
                                     dt.datetime(year, month, day, hour, minute))

        if expired <= 0: # If datetime has passed already
            await message.answer(Admin.event_datetime_passed)

        else:
            # Creating an event 
            # --------------------
            events = Events()
            pk = await events.add_event(data['name'], datetime) # Returning Primary Key
            # --------------------

            if expired > ONE_DAY_SECONDS:
                tasks = Tasks()
                await tasks.enqueue_task(await Admin.notification_text(data['name'], datetime, Admin.one_day),
                                         await process_data(year, month, day, hour, minute, 1),
                                         pk[0])

            if expired > THREE_DAYS_SECONDS:
                tasks = Tasks()
                await tasks.enqueue_task(await Admin.notification_text(data['name'], datetime, Admin.three_days),
                                         await process_data(year, month, day, hour, minute, 3),
                                         pk[0])

            await message.answer(Admin.event_created_successfully) # on success

    except ValueError: # Except invalid time was passed, ex. `abcd`, `12/00`
        await message.answer(Error.invalid_time_passed)
```
В строке ...
```
year, month, day = (map(int, date.split('/'))) # Split date string
```
... мы разделяем дату в формате __'YY:MM:DD'__ на отдельные параметры.   
Далее в блоке `try-except` мы пытаемся разделить время на часы и минуты:
```
hour, minute = (map(int, time.split(':'))) # Split time string
```
Если возбуждается исключение `ValueError`, то было введено невалидное время. В строке ...
```
expired = await process_time(dt.datetime.now(), 
                             dt.datetime(year, month, day, hour, minute))
```
... мы смотрим, какова разница во времени между текущей датой и временем и датой и временем проведения события. Ф-ция `process_time()` возвращает разницу между датами в секундах (также модуль `utils`). Если `expired` меньше или равна нулю, то дата истекла / истекает. Тогда мы не создаем эвент. В противном случае мы его создаем. Далее идет проверка на то, есть ли еще время для создания уведомления. В модуле `config` есть две константы:
```
ONE_DAY_SECONDS = 86400
THREE_DAYS_SECONDS = 259200
```
Первая - кол-во секунд в одном дне, вторая - кол-во секунд в трех днях. Если `expired` больше обеих из них, то таски будут создаваться на две даты: за три и за один день до проведения эвента. Если же `expired` больше только `ONE_DAY_SECONDS`, то смысла для создания таска за три дня нет - создается только таск за один день.   
Важный момент: таски добавляются в таблицу `tasks` одноименного модуля. Они связаны с эвентами посредством внешнего ключа. Разберем структуру таблицы подробнее:
```
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
```
Таблица имеет такие колонки:
>1) __pk__ - первичный ключ
>2) __text__ - текст уведомления
>3) __timestamp__ - временная метка (в минутах!)__*1__ 
>4) __event_id__ - внешний ключ к таблице `events`

__*1__ - в таблицу `tasks` попадает значение классической `timestamp`, разделенное на 60. Таким образом, в таблицу попадает `timestamp` в минутах! Зачем? См. пункт __6)__

__Удаление событий__  
Чтобы удалить событие (я), нужно сначала вызвать хэндлер для просмотра всех событий: `/registered_events`. Он собирает информацию из таблицы `events` и выдает ее в виде `inline-кнопок`:

![пример](/images/scrin1.png)

При нажатии на одну из них выдается более подробная информация об эвенте и кнопка "удалить":

![пример](/images/scrin2.png)

Удаление и показ информации производится через следующие хэндлеры:
```
# II. Getting an event / Получение одного события
# ---------------------------------------------
@admin_router.callback_query(F.data.regexp(r'[\d]+', mode='fullmatch'))
async def event(callback: CallbackQuery):
    events = Events()
    data = await events.get_event(int(callback.data))
    try:
        await callback.message.answer(await Admin.form_event(data[1], data[2]), 
                                      reply_markup=await form_option(int(callback.data)), parse_mode='html')
    except TypeError:
        await callback.message.answer(Admin.event_does_not_exist)
# ---------------------------------------------
```
Возбуждение исключения `TypeError` в данном случае говорит о том, что такого события не существует. `F.data` представляет из себя `id` события и формируется в ф-ции модуля `keyboards` `form_events_keyboard`:
```
async def form_events_keyboard(events: list[tuple[int, str, str, str, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for event in events:
        kb.button(text=f'{event[1]} - {event[2]}', callback_data=f'{event[0]}')
    kb.adjust(1)
    return kb.as_markup()
```
Фильтром хэндлера является регулярное выражение: `F.data.regexp(r'[\d]+', mode='fullmatch')` при получении события и `F.data.regexp(r'delete[\d]+', mode='fullmatch')` при удалении.  
Код удаляющего хэндлера:
```
# DELETE - Deleting an event / Удаление события
# ---------------------------------------------
@admin_router.callback_query(F.data.regexp(r'delete[\d]+', mode='fullmatch'))
async def delete_event(callback: CallbackQuery, bot: Bot):
    events = Events()
    pk = int(callback.data[6:])
    tasks = Tasks()
    event_tasks = await tasks.get_event_tasks(pk)
    if event_tasks:
        for task in event_tasks:
            await tasks.delete_task(task[0])
    await events.delete_event(pk)
    await callback.message.edit_text(Admin.event_deleted_successfully)
# ---------------------------------------------
```
При удалении события мы также удаляем привязанные к нему таски (что логично), если такие имеются.  
Думаю, это все, что можно сказать о событиях. Для более подробного анализа лучше изучить `CRUD` методы таблиц `events` & `tasks`.
> __6) Уведомления:__

Пожалуй, самая интересная и требующая глубокого анализа тема.  

Немного _предыстории..._ 

Так как уведомления являются по сути отложенными событиями, которые ждут своего выполнения, то изначально было принятр решение использовать какую-нибудь библиотеку для реализации отложенных задач с брокером сообщений.   

>Самая первая реализация уведомлений была сделана с помощью нешироко известной библиотеки `arq`. "Префикс" `a` говорит об ее асинхронности. Однако, ее использование было не достаточно успешным, и этого стоило ожидать: много _багов_ (это же были они?), _непонятная и скупая_ дока и т.д..  

>Самая первая проблема - таски некорректно записывались в очередь и "дублировались", если так можно сказать. Плюс были сложности с тем, как их можно отменить. Для метода `abort` надо было "иметь на руках" экземпляр класса `Job`, который возвращал метод `enqueue_job()`. Это, разумеется, невозможно. Для этого в хэндлере удаления надо "вручную" создавать экземпляр класса `Job`, имея при этом `job_id`, который тоже надо где-то хранить. Выход - создание доп. колонок в таблице `events`, но это тоже так себе способ... единственный плюс этой либы в том, что она (как и многие другие этого рода) работает в _другом **потоке**_, что делает ее очень быстрой. К тому же в качестве брокера используется `redis`! Его и тестировать легко, и использовать на практике. Еще один супер заметный минус - почему-то таски дублировались перед удалением...

>Потом было принято решение использовать _крутейший_ `celery` + все тот же `redis` в качестве брокера. `celery` - самая известная библиотека для работы с отложенными и периодическими задачами. Но на сайте доки я прочла такую вещь:  
_"Tasks with eta or countdown are immediately fetched by the worker and until the scheduled time passes, they reside in the worker’s memory. When using those options to schedule lots of tasks for a distant future, those tasks may accumulate in the worker and make a significant impact on the RAM usage.
Moreover, tasks are not acknowledged until the worker starts executing them. If using Redis as a broker, task will get redelivered when countdown exceeds visibility_timeout (see Caveats).
Therefore, using eta and countdown is not recommended for scheduling tasks for a distant future. Ideally, use values no longer than several minutes. For longer durations, consider using database-backed periodic tasks, e.g. with https://pypi.org/project/django-celery-beat/ if using Django (see Using custom scheduler classes)."_  
А это значит то, что, если вкратце, задачи, отложенные надолго, могут занимать много памяти. Более того, если использовать в качестве брокера `redis`, то задачи будут доставлятся ​​повторно, когда обратный отсчет превысит `Visibility_timeout`, равный одному часу. Там также сказано, что идеально не использовать период больше нескольких минут, что вообще не подходит для моей ситуации, когда задачи могут быть отложены на более чем неделю и даже больше.
 
Теперь к реализации... Было принято решение записывать такие таски в БД, а потом периодически их оттуда "доставать". Это можно сделать самыми разными способами. Для менее загруженного бота это можно было бы внедрить так:  
>_При изменении таблицы запускалась бы некая ф-ция __a__, которая бы доставала из нее __ближайшее__ событие, а потом бы "засыпала" на определенное время до ее исполнения, например с помощью `asyncio.sleep()`. Если "сон" не был прерван, начиналась бы рассылка уведомлений, а в противном случае снова бы запускался поиск ближайшего события._

Если же бот более-менее загружен, то проще сделать так: 
>_Каждую минуту запускать некую ф-цию __b__, которая проверяет, есть ли в таблице таски, которые должны произойти прямо сейчас, в данный момент. Если есть, то запускать рассылку уведомлений. Можно сделать через `celery cron` или `apscheduler`._

И хотя данный бот не предполагался нагруженным (сто человек будут писать боту одновременно, да еще и события будут постоянно меняться - удаляться / добавляться), я приняла решение делать через периодические походы в БД через `apscheduler` (второй вариант).  
>*__*1__ - Так как точность создания события - минута, то и `timestamp` тоже должен быть "минутный".*
При запуске бота инициализируем экземпляр класса `AsyncIOScheduler`.
```
...
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(check_events, trigger='interval', seconds=60, kwargs={'bot' : bot}) # Add job to check events
    scheduler.start()
...
```
Добавляем `job` проверки событий с интервалом в 60 секунд. Погрешность при этом может быть равна минимально 1 секунде и максимально 60 секундам, что, впрочем, не имеет значения.

> __7) Файла докера, `gitignore`:__

Все файлы докера и гита (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.gitignore`) есть в корневой папке проекта. `.gitignore` игнорирует все ненужные файлы и папки (например, кэш `__pycache__`) и файлы с конфиденциальной информацией о проекте - `.env`.  
Хотелось бы подробнее описать несколько моментов в `Dockerfile`, а конкретно такие строки:  
### I.
```
RUN apt-get update && \  
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG ru_RU.UTF-8
ENV LC_TIME ru_RU.UTF-8
```
... и такие:
### II.
```
RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN echo 'Europe/Moscow' > /etc/timezone
```
Итак, разберемся с первым случаем.  
В хэндлерах создания события используется специальный `inline-календарь`:
<video src='videos/calendar.MOV' width='400' height='240' controls></video>
>_Ссылка на доку этого календаря на `aiogram`: https://github.com/noXplode/aiogram_calendar. Отличный инструмент и фича для любого бота!_

Вот его использование в моих хэндлерах:
```
...
    await message.answer(text=Admin.select_date, reply_markup=await DialogCalendar(locale='ru_RU.UTF-8').start_calendar())
...
```
```
...
    selected, date = await DialogCalendar(locale='ru_RU.UTF-8').process_selection(callback, callback_data)
...
```
Он принимает такой параметр - `locale`. `locale` отвечает за язык, на котором будет отображен календарь. На локальной машине все будет работать отлично, но в `docker-контейнере` может вылезать такая ошибка:
```
return _setlocale(category, locale)
bot-1    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
bot-1    | locale.Error: unsupported locale setting
```
_"Под капотом"_ в инициализации используется ф-ция `setlocale` модуля `locales`. Такая ошибка говорит о том, что такого параметра `locale` не существует в контейнере. С помощью вышеупомянутых команд можно скачать и установить значение для локали!  

Вторая ситуация связана с уведомлениями, реализация и использование которых описаны в главе __6)__. Дело в том, что время в контейнере (`timestamp`) отличается от времени на локальной машине. Контейнер использует другой - _дефолтный_ - часовой пояс (работа с часовыми поясами в программировании как отдельный вид мазохизма), а с ним уведомления будут работать некорректно. Тем более что при создании экземпляра `AsyncIOScheduler` конкретно прописывается тайм-зона:
```
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
```
Так вот эти строки в `Dockerfile` и нужны для того, чтобы прописать какой часовой пояс будет использоваться в контейнере! Без них бот будет работать некорректно в изолированном пространстве.
## Usage:
>Видео-примеры использования бота!

> Как __админ:__
<video src='videos/admin-usage.mp4' width='400' height='240' controls></video>

> Как __пользователь:__
<video src='videos/user-usage.mp4' width='400' height='240' controls></video>