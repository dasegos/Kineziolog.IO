# Aiogram imports
from aiogram.fsm.state import StatesGroup, State

class ContactMe(StatesGroup):
    number = State()
    name = State()
    time = State()

class TestInfo(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    rate = State()

class CreateEvent(StatesGroup):
    name = State()
    date = State()
    time = State()

class CreateNewsletter(StatesGroup):
    text = State()
    decision = State()
    confirmation = State()

class InlineBtn(StatesGroup):
    text = State()
    link = State()