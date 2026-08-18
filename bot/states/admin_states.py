from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """FSM states for admin flows."""

    waiting_for_reply = State()
