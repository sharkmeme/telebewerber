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
    AI-based evaluation service using OpenAI gpt-4.1.
    Produces strict JSON output according to MASTER SPEC.
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4.1"

    def evaluate(self, applicant: Applicant) -> Dict[str, Any]:
        """Evaluate the applicant and return a structured JSON dict."""
        prompt = self._build_prompt(applicant)

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert hiring evaluator. "
                                "You MUST respond ONLY with valid JSON. "
                                "No explanations. No markdown. No comments."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )

                raw = response.choices[0].message.content
                result = json.loads(raw)

                # Validate required fields
                if (
                    "overall_recommendation" in result
                    and "scores" in result
                    and "short_summary" in result
                    and "red_flags" in result
                ):
                    return result

                logger.warning("AI JSON missing required fields, attempt=%s", attempt + 1)

            except Exception as e:
                logger.warning("AI evaluation error on attempt %s: %s", attempt + 1, e)

        # Final fallback if all attempts failed
        return {
            "overall_recommendation": "no",
            "scores": {
                "relevant_skills": 0,
                "english_level": 0,
                "communication": 0,
                "reliability_risk": 10,
            },
            "short_summary": "AI evaluation failed.",
            "red_flags": ["AI returned invalid JSON"],
        }

    def _build_prompt(self, applicant: Applicant) -> str:
        """Builds the full evaluation prompt."""
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
            "submitted_at": applicant.started_at.isoformat(),
        }

        return (
            "Evaluate this job applicant. Return ONLY valid JSON with fields:\n"
            "{\n"
            '  "overall_recommendation": "strong hire" | "hire" | "maybe" | "no",\n'
            '  "scores": {\n'
            '    "relevant_skills": int,\n'
            '    "english_level": int,\n'
            '    "communication": int,\n'
            '    "reliability_risk": int\n'
            "  },\n"
            '  "short_summary": string,\n'
            '  "red_flags": []\n'
            "}\n\n"
            f"Applicant data:\n{json.dumps(data, indent=2)}"
        )


# Singleton instance
ai_evaluator = AIEvaluator()
