"""
Job position definitions and configurations.
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class QuestionType(Enum):
    """Type of question."""
    TEXT = "text"  # Free text response
    CHOICE = "choice"  # Multiple choice (single selection)
    MULTI_CHOICE = "multi_choice"  # Multiple choice (multiple selections)


@dataclass
class Question:
    """A question to ask the applicant."""
    id: str
    text: str
    question_type: QuestionType
    choices: List[str] = None  # For CHOICE and MULTI_CHOICE types

    def __post_init__(self):
        if self.choices is None:
            self.choices = []


@dataclass
class Position:
    """Job position configuration."""
    id: str
    name: str
    description: str
    questions: List[Question]
    requires_cv: bool = True
    requires_proof_of_work: bool = False
    proof_of_work_description: str = ""


# Define available positions
POSITIONS: Dict[str, Position] = {
    "developer": Position(
        id="developer",
        name="Software Developer",
        description="Build and maintain our applications",
        questions=[
            Question("exp_years", "How many years of experience do you have?", QuestionType.TEXT),
            Question("tech_stack", "What technologies are you most comfortable with?", QuestionType.TEXT),
            Question("github", "Please share your GitHub profile or portfolio link", QuestionType.TEXT),
        ],
        requires_cv=True,
        requires_proof_of_work=True,
        proof_of_work_description="Please share links to your best projects or GitHub repositories"
    ),
    "designer": Position(
        id="designer",
        name="UI/UX Designer",
        description="Design beautiful and intuitive user interfaces",
        questions=[
            Question("exp_years", "How many years of design experience do you have?", QuestionType.TEXT),
            Question("tools", "Which design tools do you use?", QuestionType.CHOICE,
                    ["Figma", "Adobe XD", "Sketch", "Other"]),
            Question("portfolio", "Please share your portfolio link", QuestionType.TEXT),
        ],
        requires_cv=True,
        requires_proof_of_work=True,
        proof_of_work_description="Please upload images or links to your design work"
    ),
    "marketing": Position(
        id="marketing",
        name="Marketing Specialist",
        description="Drive growth and brand awareness",
        questions=[
            Question("exp_years", "How many years of marketing experience do you have?", QuestionType.TEXT),
            Question("channels", "Which marketing channels have you worked with?", QuestionType.TEXT),
            Question("campaign", "Describe a successful campaign you've run", QuestionType.TEXT),
        ],
        requires_cv=True,
        requires_proof_of_work=False,
    ),
    "other": Position(
        id="other",
        name="Other Position",
        description="Tell us about the role you're interested in",
        questions=[
            Question("position_name", "What position are you applying for?", QuestionType.TEXT),
            Question("why", "Why do you want to join our team?", QuestionType.TEXT),
            Question("relevant_exp", "What relevant experience do you have?", QuestionType.TEXT),
        ],
        requires_cv=True,
        requires_proof_of_work=False,
    ),
}


def get_position(position_id: str) -> Position:
    """Get position by ID."""
    return POSITIONS.get(position_id)


def get_all_positions() -> List[Position]:
    """Get all available positions."""
    return list(POSITIONS.values())
