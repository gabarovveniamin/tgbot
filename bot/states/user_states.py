from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """FSM states for regular user flows."""

    waiting_for_content = State()
