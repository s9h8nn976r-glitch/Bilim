from aiogram.fsm.state import State, StatesGroup

class MenuState(StatesGroup):
    language = State()
    class_choice = State()
    other = State()
    subject = State()
    textbook = State()
    menu = State()
    gdz = State()
    konspekt = State()
    presentation = State()
    solve = State()
    bzb = State()
