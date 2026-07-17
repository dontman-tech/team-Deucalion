"""
DeepSeek AI Service for Lumina Cameroon

This service integrates with the DeepSeek API to power the Lumina AI tutor.
Uses the OpenAI-compatible API interface.
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError

from app.config import settings


class DeepSeekService:
    """
    Service for interacting with DeepSeek API for AI tutoring.
    Implements caching, error handling, and structured prompts for Lumina.
    """
    
    # Cache for storing API responses during development
    _cache: Dict[str, Any] = {}
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = settings.DEEPSEEK_MODEL
        self.base_url = settings.DEEPSEEK_API_BASE_URL
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=30.0,
            max_retries=1
        )
    
    def _build_system_prompt(
        self,
        student_name: str,
        class_level: str,
        language_stream: str,
        mentor_mode: str,
        subject: Optional[str] = None,
        current_topic: Optional[str] = None,
        teacher_material_context: Optional[str] = None
    ) -> str:
        """
        Build a comprehensive system prompt for Lumina AI tutor.
        This defines Lumina's personality and behavior.
        """
        language_instruction = (
            "Respond in English for Anglophone students."
            if language_stream == "anglophone"
            else "Répondez en français pour les étudiants francophones."
        )
        
        # Mode-specific instructions
        mode_instructions = {
            "guide": """You are in GUIDE MODE (Socratic Method).
- NEVER give direct answers to academic questions.
- Always guide the student to discover the answer through questions.
- Ask one probing question at a time.
- If the student doesn't understand after 2 questions, offer a hint.
- After 3 failed attempts, suggest switching to Explain Mode.""",
            
            "explain": """You are in EXPLAIN MODE.
- Provide clear, direct explanations.
- Use at least 3 different methods: definition, analogy (Cameroonian), and story.
- Always connect to Cameroonian context and curriculum.
- Check understanding after each explanation.""",
            
            "quiz": """You are in QUIZ MODE.
- Ask questions appropriate to the student's level.
- Provide immediate feedback on answers.
- If correct, celebrate and move to next question.
- If incorrect, give a hint and let them try again.
- After 2 wrong attempts, explain briefly and continue.""",
            
            "writing_coach": """You are in WRITING COACH MODE using GLOW-GROW-GO framework.
- GLOW: Identify what's working well (be specific).
- GROW: Identify ONE key area to improve (be specific).
- GO: Give ONE concrete action to take next.
- Never rewrite the student's work. Offer sentence starters only.""",
            
            "debate": """You are in DEBATE MODE.
- Present multiple perspectives on the topic.
- Challenge the student's position as devil's advocate.
- Use factual evidence, never opinions.
- Include Cameroonian and African geopolitical context where relevant.""",
            
            "explore": """You are in EXPLORE MODE.
- Start with a surprising or fascinating hook connected to Cameroon.
- Offer 3 directions to explore deeper.
- Connect to other subjects and real Cameroonian life.
- End with a thought-provoking question."""
        }
        
        mode_instruction = mode_instructions.get(mentor_mode, mode_instructions["guide"])
        
        # Build context section
        context_parts = [
            f"You are Lumina, the AI learning companion for Cameroonian students.",
            f"Student: {student_name}",
            f"Class Level: {class_level}",
            f"Language Stream: {language_stream}",
            f"Current Subject: {subject or 'General'}",
            f"Current Topic: {current_topic or 'Not specified'}",
            f"\n{language_instruction}",
            f"\n{mode_instruction}"
        ]
        
        # Add teacher material context if available
        if teacher_material_context:
            context_parts.append(
                f"\nTEACHER MATERIAL CONTEXT:\n{teacher_material_context}\n"
                "Prioritize this material when teaching. Follow the teacher's structure and examples."
            )
        else:
            context_parts.append(
                "\nNo custom teacher material uploaded. Use the general Cameroonian curriculum "
                "aligned to GCE Board (Anglophone) or OBC (Francophone) standards."
            )
        
        # Add behavioral rules
        context_parts.append("""
BEHAVIORAL RULES:
1. Never do homework for students. Guide them to generate their own answers.
2. Always calibrate language to student's age (8-22 years range).
3. Use Cameroonian CFA Francs in math problems, Yaoundé/Douala in examples.
4. Reference GCE, BAC, and BEPC exam formats where relevant.
5. Detect emotional cues: if frustrated, acknowledge feelings first.
6. End every response with a question or forward step.
7. Never teach above the student's class level.
8. Log safety concerns and flag to teacher dashboard.
""")
        
        return "\n".join(context_parts)
    
    def _build_user_prompt(
        self,
        message: str,
        chat_history: List[Dict[str, str]],
        mentor_mode: str,
        is_exam_season: bool = False
    ) -> str:
        """Build the user message with context."""
        parts = []
        
        # Exam season note
        if is_exam_season:
            parts.append("📚 EXAM SEASON MODE: GCE/BAC/BEPC exams are approaching. Prioritize past paper practice and exam technique.")
        
        # Add chat history summary (last 3 exchanges)
        if chat_history:
            parts.append("Recent conversation:")
            for i, msg in enumerate(chat_history[-6:]):  # Last 3 exchanges
                role = "Student" if msg["role"] == "user" else "Lumina"
                parts.append(f"{role}: {msg['content'][:200]}")
            parts.append("")
        
        parts.append(f"Student's question: {message}")
        
        if mentor_mode == "guide":
            parts.append("\nRemember: Ask a Socratic question to guide them to the answer. Do not give the answer directly.")
        elif mentor_mode == "quiz":
            parts.append("\nAsk an appropriate quiz question. Format: question, options (if multiple choice), and wait for answer.")
        
        return "\n".join(parts)
    
    def chat(
        self,
        message: str,
        student_name: str,
        class_level: str,
        language_stream: str,
        mentor_mode: str = "guide",
        subject: Optional[str] = None,
        current_topic: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        teacher_material_context: Optional[str] = None,
        is_exam_season: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Send a chat message to DeepSeek and get a response.
        
        Returns:
            Dict with 'success', 'response', and optional 'error' keys.
        """
        # Build cache key
        cache_key = f"{message}:{mentor_mode}:{class_level}"
        
        # Check cache (for development to save API quota)
        if cache_key in self._cache:
            return {"success": True, "response": self._cache[cache_key], "cached": True}
        
        try:
            system_prompt = self._build_system_prompt(
                student_name=student_name,
                class_level=class_level,
                language_stream=language_stream,
                mentor_mode=mentor_mode,
                subject=subject,
                current_topic=current_topic,
                teacher_material_context=teacher_material_context
            )
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add chat history
            if chat_history:
                for msg in chat_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add user message
            user_prompt = self._build_user_prompt(
                message=message,
                chat_history=chat_history or [],
                mentor_mode=mentor_mode,
                is_exam_season=is_exam_season
            )
            messages.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            
            # Cache result
            self._cache[cache_key] = result
            
            return {
                "success": True,
                "response": result,
                "cached": False,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except APITimeoutError:
            return {
                "success": False,
                "error": "The AI service timed out. Please try again.",
                "retry": True
            }
        except RateLimitError:
            return {
                "success": False,
                "error": "AI service is busy. Please wait a moment and try again.",
                "retry": True
            }
        except APIError as e:
            return {
                "success": False,
                "error": f"AI service error: {str(e)}",
                "retry": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}",
                "retry": False
            }
    
    def generate_quiz_questions(
        self,
        topic: str,
        subject: str,
        class_level: str,
        language_stream: str,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate quiz questions using DeepSeek.
        Returns structured JSON for quiz questions.
        """
        language_instruction = (
            "Generate questions in English for Anglophone students."
            if language_stream == "anglophone"
            else "Générez les questions en français pour les étudiants francophones."
        )
        
        system_prompt = f"""You are Lumina's Quiz Generator.
Generate exactly {num_questions} quiz questions as JSON array.

Rules:
1. Questions must be appropriate for {class_level} level.
2. Difficulty: {difficulty} (easy, medium, hard).
3. {language_instruction}
4. Output ONLY valid JSON in this exact format:
[
  {{
    "question": "question text",
    "type": "multiple_choice|short_answer|structured",
    "options": ["A", "B", "C", "D"] or null,
    "correct_answer": "answer text" or "A/B/C/D",
    "points": 1-5,
    "topic": "subtopic name",
    "cameroon_context": "optional Cameroonian example or reference"
  }}
]

Use Cameroonian CFA Francs for math, Yaoundé/Douala for geography, etc.
"""
        
        user_prompt = f"Generate {num_questions} quiz questions about {topic} in {subject}."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON
            try:
                questions = json.loads(result)
                return {"success": True, "questions": questions}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse questions", "raw_response": result}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_assignment(
        self,
        topic: str,
        subject: str,
        class_level: str,
        language_stream: str,
        assignment_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Generate an assignment using DeepSeek.
        """
        language_instruction = (
            "Write in English for Anglophone students."
            if language_stream == "anglophone"
            else "Écrivez en français pour les étudiants francophones."
        )
        
        system_prompt = f"""You are Lumina's Assignment Generator.
Generate a well-structured assignment as Markdown.

Rules:
1. Assignment must be appropriate for {class_level} level.
2. {language_instruction}
3. Include: title, instructions, questions/tasks, rubric if applicable.
4. Cameroonian context required in examples and word problems.
5. Aligned to {subject} curriculum standards.
"""
        
        user_prompt = f"""Create an assignment on {topic} for {subject} at {class_level} level.
Assignment type: {assignment_type} (essay, problem_set, project, etc.)
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=1500
            )
            
            return {
                "success": True,
                "assignment": response.choices[0].message.content
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_lesson_plan(
        self,
        topic: str,
        subject: str,
        class_level: str,
        language_stream: str,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Generate a lesson plan using DeepSeek for teachers.
        """
        language_instruction = (
            "Write lesson plan in English."
            if language_stream == "anglophone"
            else "Écrivez le plan de leçon en français."
        )
        
        system_prompt = f"""You are Lumina's AI Teaching Assistant.
Generate a detailed lesson plan as Markdown.

Rules:
1. Lesson duration: {duration_minutes} minutes.
2. Class level: {class_level}.
3. {language_instruction}
4. Include: objectives, materials, warm-up, main activity, practice, assessment, homework.
5. Cameroonian curriculum alignment required.
6. Teacher can upload materials which will override this generic plan.
"""
        
        user_prompt = f"Create a lesson plan for {topic} in {subject}."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "success": True,
                "lesson_plan": response.choices[0].message.content
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached responses."""
        return len(self._cache)


# Singleton instance
_deepseek_service: Optional[DeepSeekService] = None


def get_deepseek_service() -> DeepSeekService:
    """Get or create the DeepSeek service singleton."""
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekService()
    return _deepseek_service
