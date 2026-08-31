from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    auto_send = State()
