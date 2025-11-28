"""
AI-powered applicant evaluation service.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict

from openai import OpenAI
from config.settings import settings
from models.applicant import Applicant

logger = logging.getLogger(__name__)


class AIEvaluator:
    """
    AI-based evaluation using OpenAI gpt-4.1 with strict JSON output.
    """

    def __init__(self):
        # Correct 1.x SDK usage — ONLY api_key allowed
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4.1"

    def evaluate(self, applicant: Applicant, include_quiz: bool = False) -> Dict[str, Any]:
        prompt = self._build_prompt(applicant, include_quiz)

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert hiring evaluator. "
                                "You MUST respond ONLY with valid JSON. No markdown."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                )

                raw = response.choices[0].message.content
                result = json.loads(raw)

                if (
                    "overall_recommendation" in result
                    and "scores" in result
                    and "short_summary" in result
                    and "red_flags" in result
                ):
                    return result

                logger.warning("Invalid JSON from AI attempt=%s", attempt+1)

            except Exception as e:
                logger.warning("AI evaluation error attempt=%s: %s", attempt+1, e)

        # Fallback result
        return {
            "overall_recommendation": "no",
            "scores": {
                "relevant_skills": 0,
                "english_level": 0,
                "communication": 0,
                "reliability_risk": 10
            },
            "short_summary": "AI evaluation failed.",
            "red_flags": ["AI returned invalid JSON"]
        }

    def _build_prompt(self, applicant: Applicant, include_quiz: bool = False) -> str:
        position = applicant.custom_position if applicant.position == "other" else applicant.position

        data = {
            "position": position,
            "answers": applicant.answers,
            "full_name": applicant.full_name,
            "email": applicant.email,
            "phone": applicant.phone,
            "socials": applicant.socials,
            "cv_file_id": applicant.cv_file_id,
            "portfolio_files": applicant.portfolio_files,
            "submitted_at": applicant.started_at.isoformat()
        }

        if include_quiz:
            data["quiz_answers"] = applicant.quiz_answers
        else:
            data["quiz_answers"] = {}

        return (
            "Return ONLY valid JSON with structure:\n"
            "{\n"
            '  "overall_recommendation": "...",\n'
            '  "scores": { "relevant_skills": int, "english_level": int, "communication": int, "reliability_risk": int },\n'
            '  "short_summary": "...",\n'
            '  "red_flags": []\n'
            "}\n\n"
            f"Applicant data:\n{json.dumps(data)}"
        )


ai_evaluator = AIEvaluator()
