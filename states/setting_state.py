from aiogram.fsm.state import State, StatesGroup

class SettingsState(StatesGroup):
    mode = State()
    file_path = State()
    date = State()
    broadcast_message = State()
    security_select_user = State()
    contact_admin_message = State()
    admin_reply = State()