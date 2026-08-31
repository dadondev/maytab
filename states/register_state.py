from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    name = State()
    phone = State()
    school_type = State()
    region = State()
    province = State()
    school = State()
    auto_send = State()
