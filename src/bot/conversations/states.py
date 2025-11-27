"""
Conversation state definitions for the application flow.
"""

from enum import IntEnum, auto


class ApplicationState(IntEnum):
    """States for the main application conversation."""

    # Initial
    POSITION_SELECT = auto()

    # Position-specific questions
    ASKING_QUESTIONS = auto()

    # Personal information
    ASK_NAME = auto()
    ASK_EMAIL = auto()
    ASK_PHONE = auto()
    ASK_SOCIALS = auto()

    # Files
    ASK_CV = auto()
    ASK_PROOF_OF_WORK = auto()

    # End
    CONFIRM = auto()


class QuizState(IntEnum):
    """States for the quiz conversation."""

    QUIZ_START = auto()
    QUIZ_QUESTION = auto()
    QUIZ_END = auto()
