"""
services/ai_service.py
─────────────────────
AI service for LLM calls (OpenAI integration).
Provides chatbot functionality and AI-powered insights.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    AI service for LLM calls using OpenAI API.
    Provides chatbot functionality and AI-powered insights.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.is_configured = bool(self.api_key)

    async def generate_chat_response(
        self,
        message: str,
        context: str | None = None,
        role: str = "faculty"
    ) -> str:
        """
        Generate a chat response using OpenAI API.
        
        Args:
            message: User's message
            context: Optional context about the student/situation
            role: User role (faculty, student, admin)
            
        Returns:
            AI-generated response
        """
        if not self.is_configured:
            logger.warning("OpenAI API key not configured, returning fallback response")
            return self._get_fallback_response(message, role)
        
        try:
            import openai
            openai.api_key = self.api_key
            
            # Build system prompt based on role
            system_prompt = self._build_system_prompt(role, context)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {exc}")
            return self._get_fallback_response(message, role)

    def _build_system_prompt(self, role: str, context: str | None) -> str:
        """
        Build system prompt based on user role and context.
        """
        base_prompt = (
            "You are an AI assistant for a JEE coaching institute's dropout prediction system. "
            "You help faculty, students, and administrators understand dropout risk factors "
            "and provide actionable advice."
        )
        
        role_specific = {
            "faculty": "You are talking to a faculty member. Focus on practical interventions and student support strategies.",
            "student": "You are talking to a student. Be encouraging and provide study tips and stress management advice.",
            "admin": "You are talking to an administrator. Focus on system-wide insights and institutional improvements."
        }
        
        prompt = base_prompt + "\n" + role_specific.get(role, "")
        
        if context:
            prompt += f"\n\nContext: {context}"
        
        return prompt

    def _get_fallback_response(self, message: str, role: str) -> str:
        """
        Get a fallback response when AI is not available.
        """
        fallback_responses = {
            "faculty": (
                "I'm currently unable to provide AI-powered insights. "
                "Please review the student's risk assessment data and consider "
                "scheduling a one-on-one counseling session if risk levels are elevated."
            ),
            "student": (
                "I'm currently unable to provide personalized advice. "
                "Focus on maintaining consistent study habits, getting adequate sleep, "
                "and don't hesitate to reach out to your faculty if you're feeling overwhelmed."
            ),
            "admin": (
                "AI insights are currently unavailable. "
                "Please review the system analytics and risk reports for institutional-level insights."
            )
        }
        
        return fallback_responses.get(role, fallback_responses["faculty"])

    async def generate_counselor_summary(
        self,
        student_data: dict[str, Any],
        risk_factors: list[dict[str, Any]]
    ) -> str:
        """
        Generate a counselor summary using AI.
        
        Args:
            student_data: Student information
            risk_factors: List of risk factors from SHAP analysis
            
        Returns:
            AI-generated counselor summary
        """
        if not self.is_configured:
            return self._get_fallback_summary(student_data, risk_factors)
        
        try:
            import openai
            openai.api_key = self.api_key
            
            prompt = self._build_counselor_prompt(student_data, risk_factors)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational counselor. Provide concise, actionable recommendations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.6
            )
            
            return response.choices[0].message.content
            
        except Exception as exc:
            logger.error(f"OpenAI API call failed for counselor summary: {exc}")
            return self._get_fallback_summary(student_data, risk_factors)

    def _build_counselor_prompt(
        self,
        student_data: dict[str, Any],
        risk_factors: list[dict[str, Any]]
    ) -> str:
        """Build prompt for counselor summary generation."""
        prompt = f"Student: {student_data.get('full_name', 'Unknown')}\n"
        prompt += f"Risk Level: {student_data.get('risk_level', 'Unknown')}\n"
        prompt += f"Risk Score: {student_data.get('risk_score', 0)}/100\n\n"
        prompt += "Top Risk Factors:\n"
        
        for factor in risk_factors[:5]:
            prompt += f"- {factor.get('feature', 'Unknown')}: {factor.get('impact', 0)}\n"
        
        prompt += "\nProvide 3-4 specific, actionable recommendations for this student."
        
        return prompt

    def _get_fallback_summary(
        self,
        student_data: dict[str, Any],
        risk_factors: list[dict[str, Any]]
    ) -> str:
        """Get fallback counselor summary."""
        risk_level = student_data.get('risk_level', 'Unknown')
        
        if risk_level in ['High', 'Critical']:
            return (
                "Student requires immediate attention. Schedule one-on-one counseling session, "
                "review study plan, and consider reducing syllabus load temporarily. "
                "Monitor attendance and stress levels closely."
            )
        elif risk_level == 'Medium':
            return (
                "Student shows moderate risk indicators. Recommend bi-weekly progress reviews, "
                "encourage peer study groups, and provide stress management resources."
            )
        else:
            return (
                "Student is on track. Continue current approach and encourage participation "
                "in advanced problem sessions."
            )


# Global AI service instance
ai_service = AIService()
