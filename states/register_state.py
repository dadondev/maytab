from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    name = State()
    phone = State()
    auto_send = State()
