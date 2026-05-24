"""
REX Self-Improvement Engine
"""
import json
import inspect
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from loguru import logger

from config.settings import SELF_IMPROVEMENT_CONFIG, SKILLS_DIR, DATA_DIR


class SelfImprovementEngine:
    """
    Self-Improvement Engine that:
    - Identifies missing skills from user prompts
    - Auto-generates skill code
    - Integrates new skills dynamically
    - Learns from feedback
    """
    
    def __init__(self, engine):
        self.engine = engine
        self.feedback_log = []
        self.improvement_history = []
        self.missing_skills_queue = []
        self.generated_skills = []
        
        self._load_improvement_data()
        logger.info("🔄 Self-improvement engine initialized")
    
    def _load_improvement_data(self):
        """Load improvement history"""
        history_file = DATA_DIR / "improvement_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                self.improvement_history = data.get("history", [])
                self.generated_skills = data.get("generated_skills", [])
            except Exception as e:
                logger.error(f"Failed to load improvement data: {e}")
    
    def _save_improvement_data(self):
        """Save improvement history"""
        history_file = DATA_DIR / "improvement_history.json"
        try:
            data = {
                "history": self.improvement_history[-1000:],
                "generated_skills": self.generated_skills,
                "saved_at": datetime.now().isoformat(),
            }
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save improvement data: {e}")
    
    async def check_improvements(self):
        """Check for potential improvements"""
        # Analyze missing skills from queue
        if self.missing_skills_queue:
            skill_request = self.missing_skills_queue.pop(0)
            await self.generate_skill(
                skill_request["name"],
                skill_request["context"],
                skill_request.get("decision", {})
            )
        
        # Analyze feedback for improvements
        negative_feedback = [f for f in self.feedback_log[-100:] 
                          if f.get("rating", 3) < 3]
        
        if len(negative_feedback) > 10:
            logger.info(f"High negative feedback detected ({len(negative_feedback)}). Analyzing...")
            await self._analyze_improvements(negative_feedback)
    
    async def generate_skill(self, skill_name: str, context: str, 
                            decision: Dict = None) -> Optional[Dict]:
        """
        Auto-generate a new skill based on identified need
        """
        logger.info(f"🔧 Generating new skill: {skill_name}")
        
        # Generate skill code
        skill_code = self._generate_skill_code(skill_name, context)
        
        if not skill_code:
            return None
        
        # Save skill to file
        skill_file = SKILLS_DIR / f"{skill_name}.py"
        
        try:
            with open(skill_file, 'w') as f:
                f.write(skill_code)
            
            # Try to load the new skill
            import importlib
            import sys
            
            module_name = f"skills.{skill_name}"
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            if hasattr(module, "register_skills"):
                module.register_skills(self.engine)
            
            self.generated_skills.append({
                "name": skill_name,
                "file": str(skill_file),
                "generated_at": datetime.now().isoformat(),
                "context": context,
            })
            
            self.improvement_history.append({
                "type": "skill_generated",
                "skill": skill_name,
                "timestamp": datetime.now().isoformat(),
            })
            
            self._save_improvement_data()
            
            logger.info(f"✅ Skill '{skill_name}' generated and loaded!")
            
            return {
                "name": skill_name,
                "file": str(skill_file),
                "status": "active",
            }
            
        except Exception as e:
            logger.error(f"Failed to generate/load skill {skill_name}: {e}")
            return None
    
    def _generate_skill_code(self, skill_name: str, context: str) -> str:
        """Generate Python code for a new skill"""
        
        # Clean skill name
        clean_name = skill_name.replace(" ", "_").replace("-", "_").lower()
        class_name = ''.join(word.capitalize() for word in clean_name.split('_'))
        
        code = f'''"""
Auto-generated Skill: {skill_name}
Generated by REX Self-Improvement Engine
Context: {context}
Generated at: {datetime.now().isoformat()}
"""
from skills.base_skill import BaseSkill


class {class_name}Skill(BaseSkill):
    """
    Skill for handling: {skill_name}
    """
    
    def __init__(self):
        super().__init__(
            name="{clean_name}",
            description="Handles {skill_name} requests",
            version="1.0.0",
            category="auto_generated"
        )
    
    async def execute(self, user_input: str, decision: dict, context: dict) -> dict:
        """Execute the skill"""
        try:
            # Process the request
            result = self._process(user_input, context)
            return {{
                "text": result,
                "actions": [],
                "data": {{"skill": "{clean_name}", "status": "completed"}},
            }}
        except Exception as e:
            return {{
                "text": f"I encountered an issue with {skill_name}: {{str(e)}}",
                "actions": ["retry"],
                "data": {{"error": str(e)}},
            }}
    
    def _process(self, user_input: str, context: dict) -> str:
        """Process the skill-specific logic"""
        # Auto-generated processing logic
        return f"I've processed your {skill_name} request. Here's what I found based on your input."
    
    def get_info(self) -> dict:
        return {{
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "auto_generated": True,
        }}


def register_skills(engine):
    """Register this skill with the REX engine"""
    skill = {class_name}Skill()
    engine.register_skill(
        name="{clean_name}",
        handler=skill.execute,
        description="Handles {skill_name} requests"
    )
'''
        return code
    
    async def _analyze_improvements(self, feedback: List[Dict]):
        """Analyze negative feedback and suggest improvements"""
        # Group by intent
        intent_issues = {}
        for f in feedback:
            intent = f.get("intent", "unknown")
            if intent not in intent_issues:
                intent_issues[intent] = []
            intent_issues[intent].append(f)
        
        for intent, issues in intent_issues.items():
            if len(issues) > 3:
                logger.warning(f"Skill '{intent}' has {len(issues)} negative feedbacks")
                # Queue for improvement
                self.missing_skills_queue.append({
                    "name": f"{intent}_improved",
                    "context": f"Improvement needed for {intent} skill based on user feedback",
                    "feedback": issues,
                })
    
    def collect_feedback(self, user_input: str, response: str, 
                        rating: int, comment: str = ""):
        """Collect user feedback for improvement"""
        feedback = {
            "user_input": user_input,
            "response": response,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        }
        self.feedback_log.append(feedback)
        logger.debug(f"Feedback collected: rating={rating}")
    
    def identify_missing_skill(self, user_input: str, decision: Dict):
        """Identify when a skill is missing and queue it for generation"""
        skill_name = decision.get("skill", "")
        
        if skill_name == "general_response" or skill_name not in self.engine.skill_registry:
            self.missing_skills_queue.append({
                "name": skill_name or "new_skill",
                "context": user_input,
                "decision": decision,
            })
            logger.info(f"Missing skill identified: {skill_name}")
    
    def get_improvement_stats(self) -> Dict:
        """Get improvement statistics"""
        return {
            "total_feedback": len(self.feedback_log),
            "generated_skills": len(self.generated_skills),
            "improvement_history": len(self.improvement_history),
            "pending_skills": len(self.missing_skills_queue),
            "average_rating": (
                sum(f.get("rating", 3) for f in self.feedback_log) / len(self.feedback_log)
                if self.feedback_log else 3.0
            ),
        }
