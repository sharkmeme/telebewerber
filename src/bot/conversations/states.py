"""
Conversation state definitions for the application flow.
"""

from enum import IntEnum, auto


class ApplicationState(IntEnum):
    """
    Main job application states.
    These follow the exact order and naming from the project MASTER SPEC.
    """

    # 1. Choose role
    SELECT_POSITION = auto()

    # 2. If user selects "Other"
    OTHER_POSITION_TEXT = auto()

    # 3. Position-specific Q&A
    POSITION_QUESTIONS = auto()

    # 4. Personal info
    COLLECT_NAME = auto()
    COLLECT_EMAIL = auto()
    COLLECT_PHONE = auto()
    COLLECT_SOCIALS = auto()

    # 5. Files
    UPLOAD_CV = auto()
    UPLOAD_PORTFOLIO = auto()

    # 6. Final confirmation
    CONFIRM_SUBMIT = auto()


class QuizState(IntEnum):
    """
    Quiz flow states (simple for now).
    """

    QUIZ_START = auto()
    QUIZ_QUESTION = auto()
    QUIZ_FINISH = auto()
