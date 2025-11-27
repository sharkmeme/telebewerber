"""
AI-powered applicant evaluation service.

Uses Claude or OpenAI to evaluate applicant responses and provide ratings.
"""

import logging
from typing import Tuple, Optional

from config.settings import settings
from models.applicant import Applicant

logger = logging.getLogger(__name__)


class AIEvaluator:
    """Evaluates applicants using AI."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.model = settings.AI_MODEL

        if self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")
                self.client = None
        elif self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                logger.error("openai package not installed. Run: pip install openai")
                self.client = None
        else:
            logger.error(f"Unknown AI provider: {self.provider}")
            self.client = None

    def evaluate(self, applicant: Applicant) -> Tuple[float, str]:
        """
        Evaluate an applicant and return (rating, feedback).

        Args:
            applicant: The applicant to evaluate

        Returns:
            Tuple of (rating from 0-10, text feedback)
        """
        if not self.client:
            logger.warning("AI client not configured, returning default rating")
            return 5.0, "AI evaluation unavailable"

        prompt = self._build_evaluation_prompt(applicant)

        try:
            if self.provider == "anthropic":
                rating, feedback = self._evaluate_with_anthropic(prompt)
            elif self.provider == "openai":
                rating, feedback = self._evaluate_with_openai(prompt)
            else:
                return 5.0, "Unknown AI provider"

            logger.info(f"AI evaluation for user {applicant.user_id}: {rating}/10")
            return rating, feedback

        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            return 5.0, f"Evaluation error: {str(e)}"

    def _build_evaluation_prompt(self, applicant: Applicant) -> str:
        """Build the evaluation prompt from applicant data."""
        prompt = f"""Evaluate this job applicant for the position: {applicant.position}

Applicant Information:
- Name: {applicant.full_name}
- Email: {applicant.email}
- Telegram: @{applicant.telegram_username}

Position-Specific Answers:
"""
        for question_id, answer in applicant.answers.items():
            prompt += f"- {question_id}: {answer}\n"

        if applicant.social_links:
            prompt += f"\nSocial/Portfolio Links: {applicant.social_links}\n"

        if applicant.proof_of_work:
            prompt += f"\nProof of Work: {', '.join(applicant.proof_of_work)}\n"

        prompt += """\nProvide:
1. A rating from 0-10 (10 being the best candidate)
2. Brief feedback (2-3 sentences) highlighting strengths and concerns

Format your response as:
RATING: [number]
FEEDBACK: [your feedback]
"""
        return prompt

    def _evaluate_with_anthropic(self, prompt: str) -> Tuple[float, str]:
        """Evaluate using Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        return self._parse_evaluation_response(response_text)

    def _evaluate_with_openai(self, prompt: str) -> Tuple[float, str]:
        """Evaluate using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        response_text = response.choices[0].message.content
        return self._parse_evaluation_response(response_text)

    def _parse_evaluation_response(self, response: str) -> Tuple[float, str]:
        """Parse the AI response to extract rating and feedback."""
        rating = 5.0
        feedback = response

        try:
            # Try to parse RATING: X format
            for line in response.split('\n'):
                if line.startswith('RATING:'):
                    rating_str = line.replace('RATING:', '').strip()
                    rating = float(rating_str)
                elif line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()

        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")

        return rating, feedback


# Global evaluator instance
ai_evaluator = AIEvaluator()
