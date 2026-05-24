"""
REX Reasoning Engine - Decision Making & Logic
"""
import random
from typing import Any, Dict, List, Optional
from datetime import datetime

from loguru import logger


class REXReasoning:
    """
    Advanced Reasoning Engine with:
    - Causal Reasoning
    - Decision Analysis
    - Logic-Based Problem Solving
    - Multi-Constraint Optimization
    - Analogical Reasoning
    """
    
    # Intent to Skill mapping
    SKILL_MAP = {
        "greeting": "conversation",
        "farewell": "conversation",
        "gratitude": "conversation",
        "question": "knowledge_qa",
        "command": "task_execution",
        "code_request": "code_generation",
        "web_search": "web_scraping",
        "weather": "weather",
        "calendar": "calendar",
        "finance": "investment",
        "smart_home": "smart_home",
        "security": "cybersecurity",
        "media": "media_generation",
        "translation": "translation",
        "math": "math_solver",
        "self_improvement": "self_improvement",
    }
    
    def __init__(self):
        self.rules = self._init_rules()
        self.causal_graph = {}
        self.analogy_bank = []
        
        logger.info("🧩 Reasoning engine initialized")
    
    def _init_rules(self) -> List[Dict]:
        """Initialize reasoning rules"""
        return [
            {
                "condition": lambda ctx: ctx.get("last_sentiment") == "negative",
                "action": "empathize_first",
                "priority": 10,
            },
            {
                "condition": lambda ctx: ctx.get("last_intent") == "greeting" and not ctx.get("user_name"),
                "action": "ask_name",
                "priority": 8,
            },
            {
                "condition": lambda ctx: len(ctx.get("task_queue", [])) > 0,
                "action": "process_queue",
                "priority": 7,
            },
            {
                "condition": lambda ctx: ctx.get("last_intent") in self.SKILL_MAP,
                "action": "execute_skill",
                "priority": 5,
            },
        ]
    
    def decide(self, intent: str, entities: List, context: Dict, 
               memories: List, sentiment: str) -> Dict:
        """
        Main decision-making function
        """
        # Step 1: Apply rules
        rule_action = self._apply_rules(context)
        
        # Step 2: Map intent to skill
        skill = self.SKILL_MAP.get(intent, "general_response")
        
        # Step 3: Causal reasoning
        causal_factors = self._causal_analysis(intent, context)
        
        # Step 4: Check for analogies
        analogous_situation = self._find_analogy(intent, context, memories)
        
        # Step 5: Decision under uncertainty
        confidence = self._calculate_confidence(intent, entities, memories)
        
        # Step 6: Multi-constraint optimization
        optimal_response = self._optimize_response(
            skill=skill,
            intent=intent,
            entities=entities,
            context=context,
            sentiment=sentiment,
            confidence=confidence
        )
        
        return {
            "skill": skill,
            "action": rule_action or "execute_skill",
            "confidence": confidence,
            "causal_factors": causal_factors,
            "analogy": analogous_situation,
            "parameters": optimal_response,
        }
    
    def _apply_rules(self, context: Dict) -> Optional[str]:
        """Apply rule-based reasoning"""
        applicable_rules = []
        for rule in self.rules:
            try:
                if rule["condition"](context):
                    applicable_rules.append(rule)
            except Exception:
                continue
        
        if applicable_rules:
            # Return highest priority rule
            applicable_rules.sort(key=lambda r: r["priority"], reverse=True)
            return applicable_rules[0]["action"]
        return None
    
    def _causal_analysis(self, intent: str, context: Dict) -> List[str]:
        """Analyze cause-effect relationships"""
        factors = []
        
        # Time-based causality
        hour = datetime.now().hour
        if hour < 12 and intent == "greeting":
            factors.append("morning_context")
        elif hour > 18 and intent == "greeting":
            factors.append("evening_context")
        
        # Sequential causality
        last_intent = context.get("last_intent")
        if last_intent:
            factors.append(f"follows_{last_intent}")
        
        return factors
    
    def _find_analogy(self, intent: str, context: Dict, memories: List) -> Optional[Dict]:
        """Find analogous past situations"""
        for memory in memories:
            if memory.get("source") == "episodic" and memory.get("relevance", 0) > 0.8:
                return {
                    "text": memory.get("text"),
                    "similarity": memory.get("relevance"),
                }
        return None
    
    def _calculate_confidence(self, intent: str, entities: List, memories: List) -> float:
        """Calculate confidence in the decision"""
        confidence = 0.5  # Base confidence
        
        # More entities = higher confidence
        if entities:
            confidence += min(len(entities) * 0.1, 0.3)
        
        # Relevant memories boost confidence
        if memories:
            max_relevance = max(m.get("relevance", 0) for m in memories)
            confidence += max_relevance * 0.2
        
        # Known intent = higher confidence
        if intent in self.SKILL_MAP:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _optimize_response(self, skill: str, intent: str, entities: List,
                          context: Dict, sentiment: str, confidence: float) -> Dict:
        """Optimize response parameters"""
        params = {
            "skill": skill,
            "verbosity": "medium",
            "tone": "friendly",
            "include_examples": confidence < 0.7,
            "language": context.get("language", "en"),
        }
        
        # Adjust based on sentiment
        if sentiment == "negative":
            params["tone"] = "empathetic"
            params["verbosity"] = "concise"
        elif sentiment == "positive":
            params["tone"] = "enthusiastic"
        
        # Adjust based on intent
        if intent == "code_request":
            params["verbosity"] = "detailed"
            params["include_examples"] = True
        elif intent in ["greeting", "farewell"]:
            params["verbosity"] = "concise"
        
        return params
    
    def solve_problem(self, problem: str, constraints: List = None) -> Dict:
        """Logic-based problem solving"""
        # Simple constraint satisfaction
        solution = {
            "approach": "analytical",
            "steps": [],
            "confidence": 0.7,
        }
        
        # Break down problem
        steps = problem.split(".")
        for i, step in enumerate(steps):
            if step.strip():
                solution["steps"].append({
                    "step": i + 1,
                    "action": step.strip(),
                    "status": "planned",
                })
        
        return solution
    
    def predict(self, context: Dict, horizon: int = 5) -> List[Dict]:
        """Predict future states based on current context"""
        predictions = []
        
        for i in range(horizon):
            predictions.append({
                "time_step": i + 1,
                "predicted_intent": "continuation",
                "confidence": max(0.5 - i * 0.1, 0.1),
            })
        
        return predictions
