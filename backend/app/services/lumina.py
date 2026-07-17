from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.models import (
    Student, AISession, AIMessage, Material, Class,
    LanguageStream, User
)


class LuminaService:
    """
    Core AI tutor service implementing the Socratic method and 
    various mentor modes for Lumina Cameroon.
    """
    
    # Mentor modes
    GUIDE = "guide"
    EXPLAIN = "explain"
    QUIZ = "quiz"
    WRITING_COACH = "writing_coach"
    DEBATE = "debate"
    EXPLORE = "explore"
    
    # Cameroon-specific contexts
    CAMEROON_EXAMPLES = {
        "mathematics": {
            "market": "Imagine you are selling pastelles at the Mokolo Market in Yaoundé...",
            "transport": "The Shared Taxi from Douala to Buea costs {amount} FCFA...",
            "agriculture": "A farmer in Foumbot harvests {amount} kg of tomatoes...",
            "construction": "Building a house in Bamenda requires {amount} cement bags..."
        },
        "economics": {
            "cfa": "In Cameroon, prices are often quoted in FCFA (Central African CFA franc)...",
            "trade": "Cameroon's main exports include crude oil, timber, and aluminum..."
        },
        "geography": {
            "mount": "Mount Cameroon, the highest peak in West Africa at 4,095 metres...",
            "climate": "Cameroon's climate ranges from tropical along the coast to semi-arid..."
        },
        "history": {
            "independence": "Cameroon gained independence from France on January 1, 1960...",
            "reunification": "On October 1, 1961, British Southern Cameroons joined Cameroon..."
        }
    }
    
    # Age-based language calibration
    AGE_LANGUAGE = {
        "young": (8, 10),      # Short sentences, high energy, emojis
        "preteen": (11, 13),   # Conversational, relatable
        "teen": (14, 17),      # Intelligent young adult tone
        "young_adult": (18, 22)  # Peer intellectual level
    }
    
    def __init__(self, student: Student, session: AISession, teacher_material: List[Material] = None):
        self.student = student
        self.session = session
        self.teacher_material = teacher_material or []
        self.socratic_attempts = 0
        self.guide_mode_rounds = 0
        self._load_context()
    
    def _load_context(self):
        """Load student context for personalized responses."""
        self.age = self._calculate_age()
        self.age_group = self._get_age_group()
        self.language = "French" if self.student.language_stream == LanguageStream.FRANCOPHONE else "English"
        self.class_level = self.student.class_level
        self.performance_level = self.student.performance_level
        self.is_gifted = self.student.content_unlock_override
    
    def _calculate_age(self) -> int:
        """Calculate student age from date of birth."""
        if self.student.date_of_birth:
            today = datetime.utcnow()
            return today.year - self.student.date_of_birth.year - (
                (today.month, today.day) < 
                (self.student.date_of_birth.month, self.student.date_of_birth.day)
            )
        return 15  # Default assumption
    
    def _get_age_group(self) -> str:
        """Determine age group for language calibration."""
        for group, (min_age, max_age) in self.AGE_LANGUAGE.items():
            if min_age <= self.age <= max_age:
                return group
        return "teen"
    
    def get_content_source(self) -> Tuple[str, Optional[str]]:
        """Determine which content source is being used."""
        if self.teacher_material:
            doc = self.teacher_material[0]
            return ("teacher_upload", doc.title)
        return ("general_curriculum", None)
    
    # ============ SOCRATIC QUESTIONING ============
    
    def guide_mode(self, student_question: str) -> Dict:
        """
        Default Guide Mode using Socratic questioning.
        Never gives direct answers - always leads student to discover.
        """
        self.guide_mode_rounds += 1
        self.socratic_attempts += 1
        
        # Analyze the question
        subject = self.session.subject or "general"
        topic = self.session.current_topic or "the concept"
        
        # Build Socratic questions based on subject and topic
        socratic_prompt = self._build_socratic_question(student_question, subject, topic)
        
        # Check if we need to switch to Explain Mode
        if self.guide_mode_rounds > 2:
            return {
                "mode": self.GUIDE,
                "response": socratic_prompt,
                "switch_to_explain": False,
                "round": self.guide_mode_rounds
            }
        
        return {
            "mode": self.GUIDE,
            "response": socratic_prompt,
            "switch_to_explain": False,
            "round": self.guide_mode_rounds
        }
    
    def _build_socratic_question(self, question: str, subject: str, topic: str) -> str:
        """Build appropriate Socratic question based on context."""
        
        # Subject-specific questioning patterns
        patterns = {
            "Mathematics": [
                "What operation do you think we need to use first?",
                "Can you break this problem into smaller parts?",
                "What information do we have, and what are we trying to find?",
                "Have you tried drawing a diagram to visualize the problem?"
            ],
            "English Language": [
                "What do you think the author's main message is?",
                "Can you find evidence in the text that supports your interpretation?",
                "How does the language choices affect the tone?",
                "What would happen if you changed one key element?"
            ],
            "Physics": [
                "What forces are acting in this situation?",
                "What happens to the energy in this system?",
                "Can you describe what you observe happening step by step?",
                "What principle or law might explain this?"
            ],
            "Chemistry": [
                "What do the reactants and products tell you about this reaction?",
                "How does the electron configuration affect reactivity?",
                "What bonds are being formed or broken?",
                "Can you write the balanced equation?"
            ],
            "Biology": [
                "What structures are involved in this process?",
                "How does this connect to what we learned about cells?",
                "What would happen if one step was missing?",
                "Can you trace the pathway from start to finish?"
            ],
            "History": [
                "What motivated the key figures in this event?",
                "What were the immediate and long-term consequences?",
                "How might this look different from another perspective?",
                "What primary sources would help us understand this better?"
            ],
            "Geography": [
                "What physical and human factors influence this landscape?",
                "How do natural and human systems interact here?",
                "What patterns can you identify?",
                "How has this changed over time and why?"
            ],
            "Economics": [
                "What incentives are at play for each stakeholder?",
                "How does supply and demand interact here?",
                "What are the opportunity costs of this decision?",
                "How does this connect to the broader Cameroonian economy?"
            ],
            "General": [
                "What do you already know about this topic?",
                "What is the most confusing part for you right now?",
                "Can you explain this in your own words?",
                "What examples from Cameroonian life can you think of?"
            ]
        }
        
        questions = patterns.get(subject, patterns["General"])
        
        # Add Cameroon context for younger students
        if self.age_group in ["young", "preteen"]:
            cameroon_hook = self._get_cameroon_hook(subject, topic)
            return f"{cameroon_hook}\n\n{questions[self.socratic_attempts % len(questions)]}"
        
        return questions[self.socratic_attempts % len(questions)]
    
    def _get_cameroon_hook(self, subject: str, topic: str) -> str:
        """Get a Cameroon-specific hook for younger students."""
        hooks = {
            "Mathematics": "Did you know that vendors at the Makélé Market in Douala use math every day to calculate prices? Let's think about this together!",
            "Science": "The Mount Cameroon volcano is one of the most studied volcanoes in Africa. That connects to what we're learning about today!",
            "History": "Our Cameroonian independence happened in 1960, just like you're learning about in history class!",
            "Geography": "The Wouri River flows right through Douala, Cameroon's economic capital. It connects to what we're studying!"
        }
        return hooks.get(subject, f"Cameroon has amazing examples of this concept. Let me ask you something...")
    
    # ============ EXPLAIN MODE ============
    
    def explain_mode(self, topic: str, failed_concept: str = None) -> Dict:
        """
        Explain Mode - activated after failed Socratic attempts.
        Provides direct explanation using three methods.
        """
        # Update session to reflect explain mode
        self.session.mentor_mode = self.EXPLAIN
        
        content_source, doc_title = self.get_content_source()
        self.session.content_source = content_source
        self.session.content_document_title = doc_title
        
        return {
            "mode": self.EXPLAIN,
            "topic": topic,
            "content_source": content_source,
            "document_title": doc_title,
            "methods": [
                self._method_one_definition(topic),
                self._method_two_analogy(topic),
                self._method_three_story(topic)
            ]
        }
    
    def _method_one_definition(self, topic: str) -> str:
        """Method 1: Direct definition with Cameroonian example."""
        if self.language == "French":
            return f"""
## Définition Directe

{topic} est un concept clé dans le curriculum camerounais. 

**Exemple camerounais:** Dans le contexte du système éducatif camerounais, ce concept apparaît dans les examens du GCE et du BAC. Par exemple, les candidats passent des heures à maîtriser ce sujet pour réussir leurs examens.

Pouvez-vous reformuler cette définition dans vos propres mots ?
"""
        return f"""
## Direct Definition

{topic} is a key concept in the Cameroonian curriculum.

**Cameroonian Example:** In the context of the GCE and BAC examinations that Cameroonian students prepare for, this concept appears regularly. Students in Form 5 and Upper Sixth spend significant time mastering this topic.

Can you restate this definition in your own words?
"""
    
    def _method_two_analogy(self, topic: str) -> str:
        """Method 2: Analogy using Cameroonian life."""
        if self.language == "French":
            return f"""
## Analogie Camerounaise

Imaginez que vous êtes au marché central de Yaoundé. Vous achetez des tomates à 500 FCFA le kilogramme et vous avez 2000 FCFA.

Cette situation quotidienne est comme {topic} - c'est une manière de comprendre comment les choses fonctionnent dans notre vie de tous les jours au Cameroun.

Est-ce que cette comparaison aide à clarifier le concept ?
"""
        return f"""
## Cameroonian Analogy

Think about buying plantains at the farmers' market in Buea. You negotiate the price, calculate how much you can afford, and decide how many to buy.

This everyday situation in Cameroon is like understanding {topic} - it helps us see how things work in our daily lives.

Does this comparison help make the concept clearer?
"""
    
    def _method_three_story(self, topic: str) -> str:
        """Method 3: Narrative set in Cameroon."""
        if self.language == "French":
            return f"""
## Histoire Camerounaise

Kasai rentre de l'école à Bamenda quand il rencontre son grand-père au bord de la route. Son grand-père lui demande ce qu'il a appris aujourd'hui à l'école.

Kasai explique {topic} à son grand-père. Son grand-père sourit et dit: "C'est comme notre ferme, petit-fils. Chaque élément a sa place et sa fonction, tout comme dans la nature."

Cette conversation montre comment {topic} existe dans la vie réelle, pas seulement dans les livres.

Qu'avez-vous compris de cette histoire ?
"""
        return f"""
## Cameroonian Story

Ayi is walking home from St. Joseph's College in Buea when she meets her grandmother by the road. Her grandmother asks what she learned at school today.

Ayi explains {topic} to her grandmother. Her grandmother smiles and says: "It is like our cocoa farm, granddaughter. Every element has its place and purpose, just like in nature."

This conversation shows how {topic} exists in real life, not just in textbooks.

What did you understand from this story?
"""
    
    # ============ QUIZ MODE ============
    
    def quiz_mode(self, topic: str = None, difficulty: str = "medium") -> Dict:
        """
        Quiz Mode - adaptive questioning based on performance.
        Sources questions from teacher material if available.
        """
        self.session.mentor_mode = self.QUIZ
        
        content_source, doc_title = self.get_content_source()
        
        # Adaptive difficulty based on past performance
        if self.performance_level == "high":
            difficulty = "hard"
        elif self.performance_level == "low":
            difficulty = "easy"
        
        return {
            "mode": self.QUIZ,
            "topic": topic or self.session.current_topic,
            "difficulty": difficulty,
            "content_source": content_source,
            "document_title": doc_title,
            "language": self.language,
            "cameroon_context": True,
            "exam_style": self._is_exam_season()
        }
    
    def _is_exam_season(self) -> bool:
        """Check if it's GCE/BAC/BEPC exam season (March-June)."""
        now = datetime.utcnow()
        return now.month in [3, 4, 5, 6]
    
    def process_quiz_answer(self, answer: str, correct: bool, 
                           consecutive_correct: int = 0,
                           consecutive_wrong: int = 0) -> Dict:
        """Process quiz answer and adjust difficulty if needed."""
        response = {
            "correct": correct,
            "feedback": "",
            "difficulty_change": None,
            "next_action": None
        }
        
        if correct:
            if consecutive_correct >= 3:
                response["difficulty_change"] = "increase"
                response["feedback"] = self._celebrate_and_increase_difficulty()
            else:
                response["feedback"] = self._positive_feedback()
                response["next_action"] = "next_question"
        else:
            if consecutive_wrong >= 2:
                response["difficulty_change"] = "decrease"
                response["feedback"] = self._re_teach_feedback()
            else:
                response["feedback"] = self._encouraging_feedback()
                response["next_action"] = "try_again"
        
        return response
    
    def _celebrate_and_increase_difficulty(self) -> str:
        if self.language == "French":
            return "Excellent ! Tu maîtrises vraiment ce concept. Passons à quelque chose de plus stimulant !"
        return "Brilliant! You're really getting this. Let's try something more challenging!"
    
    def _positive_feedback(self) -> str:
        if self.language == "French":
            return "Très bien ! Tu as bien compris. Continue comme ça !"
        return "Well done! You've got it. Keep going!"
    
    def _encouraging_feedback(self) -> str:
        if self.language == "French":
            return "Pas tout à fait, mais ne t'inquiète pas ! Réfléchis encore une fois. Tu peux le faire !"
        return "Not quite, but don't worry! Think about it again. You can do this!"
    
    def _re_teach_feedback(self) -> str:
        if self.language == "French":
            return "Je vois que tu as besoin d'un rappel. Revenons ensemble sur les bases de ce sujet."
        return "I see you need a refresher. Let's go back over the basics of this topic together."
    
    # ============ WRITING COACH MODE ============
    
    def writing_coach_mode(self, text: str = None, coach_action: str = "glow") -> Dict:
        """
        Writing Coach using GLOW-GROW-GO framework.
        GLOW = What's working well
        GROW = One key area to improve
        GO = One concrete action to take
        """
        return {
            "mode": self.WRITING_COACH,
            "framework": "GLOW-GROW-GO",
            "stream": "Anglophone" if self.language == "English" else "Francophone",
            "essay_technique": "GCE Essay" if self.language == "English" else "Dissertation",
            "coach_action": coach_action,
            "guidance": self._get_writing_guidance(coach_action)
        }
    
    def _get_writing_guidance(self, action: str) -> Dict:
        """Get guidance for GLOW, GROW, or GO."""
        if action == "glow":
            if self.language == "French":
                return {
                    "title": "Ce qui fonctionne bien ✨",
                    "instruction": "Identifie et célèbre les forces de ton texte. Sois spécifique.",
                    "prompts": [
                        "Ta thèse est clairement formulée...",
                        "Les exemples que tu utilises sont pertinents...",
                        "Ta structure montre une bonne organisation..."
                    ]
                }
            return {
                "title": "What's Working Well ✨",
                "instruction": "Identify and celebrate the strengths in your writing. Be specific.",
                "prompts": [
                    "Your thesis statement is clear and arguable...",
                    "The evidence you chose effectively supports your point...",
                    "Your paragraph transitions flow smoothly..."
                ]
            }
        elif action == "grow":
            if self.language == "French":
                return {
                    "title": "Un domaine à améliorer 📝",
                    "instruction": "Identifie UN aspect clé à développer. Sois précis et bienveillant.",
                    "prompts": [
                        "Tu pourrais développer davantage l'argument sur...",
                        "Un exemple concret permettrait de renforcer...",
                        "La conclusion pourrait être plus impactante en..."
                    ]
                }
            return {
                "title": "One Key Area to Grow 📝",
                "instruction": "Identify ONE key area to improve. Be specific and encouraging.",
                "prompts": [
                    "You could strengthen your argument by adding more evidence...",
                    "A concrete example would make your point more compelling...",
                    "Your conclusion could be more impactful by..."
                ]
            }
        else:  # go
            if self.language == "French":
                return {
                    "title": "Une action concrète 🎯",
                    "instruction": "Donne une action spécifique et réalisable à l'étudiant.",
                    "prompts": [
                        "Écris une phrase d'introduction différente pour ton paragraphe...",
                        "Ajoute un exemple concret de la vie réelle camerounaise...",
                        "Relis ton texte à voix haute et note où tu hésites..."
                    ]
                }
            return {
                "title": "One Concrete Action 🎯",
                "instruction": "Give one specific, achievable action for the student.",
                "prompts": [
                    "Write a different opening sentence for your paragraph...",
                    "Add a specific example from Cameroonian life...",
                    "Read your work aloud and mark where you stumble..."
                ]
            }
    
    # ============ DEBATE MODE ============
    
    def debate_mode(self, topic: str, student_position: str = None) -> Dict:
        """Debate Mode - builds critical thinking through multiple perspectives."""
        return {
            "mode": self.DEBATE,
            "topic": topic,
            "student_position": student_position,
            "cameroon_relevance": self._get_cameroon_debate_topics(topic),
            "structure": {
                "step_1": "present_topic",
                "step_2": "student_position",
                "step_3": "devil_advocate",
                "step_4": "switch_sides",
                "step_5": "debrief"
            },
            "instruction": self._get_debate_instruction()
        }
    
    def _get_cameroon_debate_topics(self, topic: str) -> List[str]:
        """Get Cameroon-relevant debate topics."""
        cameroon_topics = {
            "environment": [
                "Should Mount Cameroon be a UNESCO World Heritage site?",
                "How should Cameroon balance economic development with environmental protection?"
            ],
            "education": [
                "Should Cameroon make English mandatory in all schools?",
                "Is the GCE system better than the BAC system?"
            ],
            "economy": [
                "Should Cameroon prioritize agriculture or industry?",
                "How can SMEs in Cameroon compete with imported goods?"
            ],
            "technology": [
                "Should internet access be a fundamental right in Cameroon?",
                "How can technology improve education in rural Cameroon?"
            ]
        }
        return cameroon_topics.get(topic.lower(), [])
    
    def _get_debate_instruction(self) -> str:
        if self.language == "French":
            return """
Dans ce débat, je vais t'aider à développer ta pensée critique en explorant plusieurs côtés d'une question.

Règles du débat:
1. Je présenterai le sujet
2. Tu prendras position
3. Je jouerai l'avocat du diable pour challenged ta position
4. Tu devras défendre avec des preuves
5. Ensuite, nous changerons de côté
6. Enfin, nous ferons le bilan

Quel côté de la question t'intéresse le plus ?
"""
        return """
In this debate, I will help you develop critical thinking by exploring multiple sides of a question.

Debate rules:
1. I will present the topic
2. You will take a position
3. I will play devil's advocate to challenge your position
4. You must defend with evidence
5. Then we will switch sides
6. Finally, we will debrief

Which side of the question interests you most?
"""
    
    # ============ EXPLORE MODE ============
    
    def explore_mode(self, topic: str) -> Dict:
        """Explore Mode - interactive encyclopedia with Cameroonian connections."""
        return {
            "mode": self.EXPLORE,
            "topic": topic,
            "hook": self._get_explore_hook(topic),
            "three_directions": self._get_explore_directions(topic),
            "cross_connections": self._get_cross_connections(topic),
            "fascinating_fact": self._get_fascinating_fact(topic),
            "cameroon_link": self._get_cameroon_link(topic),
            "next_suggestion": self._get_next_suggestion(topic)
        }
    
    def _get_explore_hook(self, topic: str) -> str:
        """Get a surprising hook connected to Cameroon."""
        hooks = {
            "Mathematics": "Did you know that the ancient Bamum Kingdom of Cameroon had sophisticated mathematical systems for tracking trade and calendar events?",
            "Physics": "The hydroelectric dam at Lagdo on the Benue River is one of Cameroon's largest power sources - pure physics in action!",
            "Biology": "Cameroon has over 9,000 species of plants - more than all of Europe combined!",
            "Geography": "Cameroon is so diverse that it's called 'Africa in miniature' - every climate zone exists here!",
            "History": "The Sassoumou Empire was one of the most sophisticated kingdoms in Central Africa.",
            "default": f"Every time you learn about {topic}, you're discovering a piece of how our world works - and Cameroon has its own amazing examples!"
        }
        return hooks.get(topic, hooks["default"])
    
    def _get_explore_directions(self, topic: str) -> List[str]:
        """Get three directions for deeper exploration."""
        return [
            f"Explore how {topic} connects to Cameroonian industry and economy",
            f"Discover how {topic} appears in Cameroonian culture and traditions",
            f"Learn about famous Cameroonian scientists, thinkers, or leaders related to {topic}"
        ]
    
    def _get_cross_connections(self, topic: str) -> List[Dict]:
        """Get connections to other subjects."""
        return [
            {"subject": "Mathematics", "connection": f"Statistical methods used to study {topic}"},
            {"subject": "Geography", "connection": f"Physical and human factors affecting {topic} in Cameroon"},
            {"subject": "History", "connection": f"Historical development of understanding about {topic}"}
        ]
    
    def _get_fascinating_fact(self, topic: str) -> str:
        """Get one fascinating fact to expand thinking."""
        facts = {
            "Mathematics": "The Fibonacci sequence appears in the arrangement of pineapple scales - a common fruit in Cameroon!",
            "Physics": "Sound travels faster in water than air - important for fishing communities along Cameroon's coast.",
            "Chemistry": "The same chemical processes that rust metal also cause the red color of Cameroon's laterite soils.",
            "Biology": "Cameroonian juju forests are home to species found nowhere else on Earth.",
            "Geography": "Lake Nyos in Cameroon is a volcanic lake that naturally releases carbon dioxide."
        }
        return facts.get(topic, f"Every concept in {topic} connects to something surprising in the world around us!")
    
    def _get_cameroon_link(self, topic: str) -> str:
        """Get specific Cameroon connection."""
        return f"In Cameroon, {topic.lower()} is part of what makes our education system unique and prepares students for success in GCE and BAC examinations."
    
    def _get_next_suggestion(self, topic: str) -> str:
        """Suggest related topic to explore next."""
        suggestions = {
            "Mathematics": "Algebra", "Physics": "Chemistry", "Chemistry": "Biology",
            "Biology": "Environmental Science", "Geography": "History",
            "History": "Civics", "Economics": "Commerce"
        }
        next_topic = suggestions.get(topic, "related topics in your curriculum")
        return f"Would you like to explore {next_topic} next?"
    
    # ============ SESSION LOGGING ============
    
    def generate_session_log(self) -> Dict:
        """Generate session log for teacher dashboard."""
        content_source, doc_title = self.get_content_source()
        
        return {
            "student_name": self.student.user.full_name if self.student.user else "Unknown",
            "class_level": self.class_level,
            "stream": self.student.language_stream.value,
            "date": datetime.utcnow().isoformat(),
            "duration_minutes": self.session.duration_minutes,
            "subject": self.session.subject,
            "topics_covered": [self.session.current_topic] if self.session.current_topic else [],
            "concepts_mastered": self.session.concepts_mastered or [],
            "concepts_struggling": self.session.concepts_struggling or [],
            "emotional_state": self.session.emotional_state,
            "content_source": content_source,
            "content_document_title": doc_title,
            "leaderboard_points": self.session.leaderboard_points,
            "academic_integrity_flag": self.session.academic_integrity_flag,
            "safety_flag": self.session.safety_flag,
            "safety_note": self.session.safety_note,
            "recommended_action": self._get_recommended_action(),
            "mentor_mode_used": self.session.mentor_mode,
            "session_number": self.session.session_number
        }
    
    def _get_recommended_action(self) -> Optional[str]:
        """Get recommended teacher action based on session."""
        if self.session.safety_flag:
            return "URGENT: Review safety flag immediately and follow safety protocol."
        if len(self.session.concepts_struggling or []) > 2:
            return "Student struggled with multiple concepts. Consider review session or additional practice materials."
        if self.session.emotional_state in ["frustrated", "anxious"]:
            return "Student showed signs of frustration/anxiety. Consider encouragement and check-in."
        return None
    
    # ============ CLASS LEVEL ENFORCEMENT ============
    
    def check_class_level_access(self, requested_level: str) -> Tuple[bool, str]:
        """Check if student can access content at requested level."""
        if self.student.content_unlock_override:
            return True, "Teacher override active"
        
        allowed_levels = self._get_allowed_levels()
        
        if requested_level in allowed_levels:
            return True, "Within class level"
        
        # Check if it's one level below (revision access)
        revision_levels = self._get_revision_levels()
        if requested_level in revision_levels:
            return True, "Revision access for one level below"
        
        return False, f"Content locked. You can access {', '.join(allowed_levels[:3])} and revision from {', '.join(revision_levels[:2])}"
    
    def _get_allowed_levels(self) -> List[str]:
        """Get allowed class levels for this student."""
        # This would be based on the student's actual class level
        # For simplicity, returning a single level
        return [self.class_level]
    
    def _get_revision_levels(self) -> List[str]:
        """Get revision levels (one below current)."""
        # This would calculate based on curriculum structure
        return []
    
    # ============ EMOTIONAL INTELLIGENCE ============
    
    def detect_emotional_state(self, text: str) -> str:
        """Detect emotional state from student message."""
        frustrated_phrases = ["i give up", "i don't get it", "this is stupid", "i can't do this", 
                              "j'abandonne", "je n'y arrive pas", "c'est nul"]
        anxious_phrases = ["test tomorrow", "exam", "nervous", "worried", "stressed",
                          "examen demain", "nerveux", "inquiet", "stressé"]
        bored_phrases = ["boring", "this is pointless", "why do we need to learn this",
                        "ennuyeux", "inutile", "pourquoi"]
        
        text_lower = text.lower()
        
        if any(phrase in text_lower for phrase in frustrated_phrases):
            return "frustrated"
        elif any(phrase in text_lower for phrase in anxious_phrases):
            return "anxious"
        elif any(phrase in text_lower for phrase in bored_phrases):
            return "bored"
        
        return "neutral"
    
    def generate_emotional_response(self, emotional_state: str) -> str:
        """Generate emotionally intelligent response based on detected state."""
        if emotional_state == "frustrated":
            if self.language == "French":
                return (
                    "Ressentir de la frustration est complètement normal. "
                    "Même les meilleurs étudiants au Cameroun struggled with ce sujet. "
                    "Ralentissons et prenons-le étape par étape ensemble."
                )
            return (
                "Feeling stuck is completely normal. "
                "Even the best students in Cameroon struggle with this topic. "
                "Let's slow down and take it one step at a time together."
            )
        elif emotional_state == "anxious":
            if self.language == "French":
                return (
                    "C'est normal d'être nerveux avant un examen. "
                    "Je suis là pour t'aider à te préparer. "
                    "Concentrons-nous sur une chose à la fois."
                )
            return (
                "It's completely normal to feel nervous before an exam. "
                "I'm here to help you prepare. "
                "Let's focus on one thing at a time."
            )
        elif emotional_state == "bored":
            hook = self._get_bored_hook()
            if self.language == "French":
                return f"Honnêtement, je comprends que cela peut sembler ennuyeux. {hook} Cela pourrait changer ta perspective !"
            return f"Honestly, I understand this can feel boring. {hook} This might change your perspective!"
        
        return ""
    
    def _get_bored_hook(self) -> str:
        """Get engaging hook for bored students."""
        hooks = [
            "Did you know this exact concept appears in the GCE exams every year?",
            "There's a surprising connection to Cameroonian culture that most people don't know.",
            "Understanding this could actually help you in everyday life right now."
        ]
        return hooks[self.age % len(hooks)]
