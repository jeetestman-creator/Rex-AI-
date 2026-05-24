"""
REX AI Engine - Core Processing Unit
"""
import time
import json
import asyncio
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from collections import deque

import numpy as np
from loguru import logger

from config.settings import (
    REX_CONFIG, NLP_CONFIG, MEMORY_CONFIG,
    SELF_IMPROVEMENT_CONFIG, DATA_DIR
)
from core.memory import REXMemory
from core.nlp import REXNLP
from core.reasoning import REXReasoning
from core.self_healing import SelfHealingEngine
from core.self_improvement import SelfImprovementEngine


class REXEngine:
    """
    Main AI Engine for REX - Orchestrates all subsystems
    """
    
    def __init__(self):
        self.name = REX_CONFIG["name"]
        self.version = REX_CONFIG["version"]
        self.is_running = False
        self.conversation_history = deque(maxlen=1000)
        self.active_skills: Dict[str, Any] = {}
        self.skill_registry: Dict[str, Callable] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.context: Dict[str, Any] = {
            "user_name": None,
            "session_start": None,
            "mood": "neutral",
            "task_queue": [],
            "active_tasks": [],
        }
        
        # Initialize subsystems
        logger.info("🦖 Initializing REX Engine...")
        self.memory = REXMemory()
        self.nlp = REXNLP()
        self.reasoning = REXReasoning()
        self.self_healing = SelfHealingEngine(self)
        self.self_improvement = SelfImprovementEngine(self)
        
        # Load skills
        self._load_skills()
        
        logger.info(f"✅ REX Engine initialized with {len(self.skill_registry)} skills")
    
    def _load_skills(self):
        """Load all available skill modules"""
        skills_dir = Path(__file__).parent.parent / "skills"
        
        if not skills_dir.exists():
            logger.warning("Skills directory not found")
            return
        
        import importlib
        import sys
        
        sys.path.insert(0, str(skills_dir.parent))
        
        for skill_file in skills_dir.glob("*.py"):
            if skill_file.name.startswith("_"):
                continue
            
            try:
                module_name = f"skills.{skill_file.stem}"
                module = importlib.import_module(module_name)
                
                if hasattr(module, "register_skills"):
                    module.register_skills(self)
                    logger.info(f"✅ Loaded skill: {skill_file.stem}")
            except Exception as e:
                logger.error(f"❌ Failed to load skill {skill_file.stem}: {e}")
                self.self_healing.report_error(f"skill_load_{skill_file.stem}", e)
    
    def register_skill(self, name: str, handler: Callable, description: str = ""):
        """Register a new skill with the engine"""
        self.skill_registry[name] = {
            "handler": handler,
            "description": description,
            "registered_at": datetime.now().isoformat(),
            "usage_count": 0,
            "success_rate": 1.0,
        }
        logger.debug(f"Registered skill: {name}")
    
    def on_event(self, event_type: str, callback: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(callback)
    
    def emit_event(self, event_type: str, data: Any = None):
        """Emit an event to all registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
    
    async def process(self, user_input: str, context: Dict = None) -> Dict:
        """
        Main processing pipeline for user input
        """
        start_time = time.time()
        
        try:
            # Step 1: Pre-processing
            self.emit_event("pre_process", user_input)
            
            # Step 2: Language Detection & NLP
            lang = self.nlp.detect_language(user_input)
            nlp_result = self.nlp.analyze(user_input, lang)
            
            # Step 3: Intent Recognition
            intent = self.nlp.recognize_intent(nlp_result)
            entities = self.nlp.extract_entities(nlp_result)
            sentiment = self.nlp.analyze_sentiment(nlp_result)
            
            # Step 4: Context Update
            self.context.update({
                "last_input": user_input,
                "last_intent": intent,
                "last_sentiment": sentiment,
                "language": lang,
                "timestamp": datetime.now().isoformat(),
            })
            
            # Step 5: Memory Retrieval
            relevant_memories = await self.memory.retrieve_relevant(
                user_input, intent, entities
            )
            
            # Step 6: Reasoning & Decision
            decision = self.reasoning.decide(
                intent=intent,
                entities=entities,
                context=self.context,
                memories=relevant_memories,
                sentiment=sentiment
            )
            
            # Step 7: Skill Execution
            response = await self._execute_skill(decision, user_input, context)
            
            # Step 8: Post-processing
            processing_time = time.time() - start_time
            
            # Step 9: Store in memory
            await self.memory.store_interaction(
                user_input=user_input,
                response=response,
                intent=intent,
                entities=entities,
                sentiment=sentiment,
                processing_time=processing_time
            )
            
            # Step 10: Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat(),
                "intent": intent,
            })
            self.conversation_history.append({
                "role": "rex",
                "content": response.get("text", ""),
                "timestamp": datetime.now().isoformat(),
            })
            
            self.emit_event("post_process", response)
            
            return {
                "text": response.get("text", ""),
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment,
                "language": lang,
                "processing_time": processing_time,
                "actions": response.get("actions", []),
                "data": response.get("data", {}),
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            healed_response = await self.self_healing.handle_error(e, user_input)
            return healed_response
    
    async def _execute_skill(self, decision: Dict, user_input: str, context: Dict) -> Dict:
        """Execute the decided skill"""
        skill_name = decision.get("skill", "general_response")
        
        if skill_name in self.skill_registry:
            skill_info = self.skill_registry[skill_name]
            handler = skill_info["handler"]
            
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(user_input, decision, self.context)
                else:
                    result = handler(user_input, decision, self.context)
                
                # Update skill stats
                skill_info["usage_count"] += 1
                
                return result
                
            except Exception as e:
                logger.error(f"Skill execution error ({skill_name}): {e}")
                skill_info["success_rate"] *= 0.95
                return await self.self_healing.handle_error(e, user_input)
        else:
            # Try to auto-generate skill
            if SELF_IMPROVEMENT_CONFIG["auto_skill_generation"]:
                new_skill = await self.self_improvement.generate_skill(
                    skill_name, user_input, decision
                )
                if new_skill:
                    return await self._execute_skill(decision, user_input, context)
            
            return self._generate_general_response(user_input, decision)
    
    def _generate_general_response(self, user_input: str, decision: Dict) -> Dict:
        """Generate a general conversational response"""
        responses = [
            f"I understand you're asking about: {user_input}. Let me help you with that.",
            f"That's an interesting question! Here's what I think about '{user_input}'.",
            f"I'm processing your request: {user_input}. Here's my response.",
        ]
        
        return {
            "text": responses[0],
            "actions": [],
            "data": {},
        }
    
    async def start(self):
        """Start the REX engine"""
        self.is_running = True
        self.context["session_start"] = datetime.now().isoformat()
        
        # Start background tasks
        asyncio.create_task(self._background_tasks())
        
        self.emit_event("engine_started")
        logger.info("🚀 REX Engine started!")
    
    async def stop(self):
        """Stop the REX engine"""
        self.is_running = False
        self.emit_event("engine_stopped")
        logger.info("🛑 REX Engine stopped")
    
    async def _background_tasks(self):
        """Run background maintenance tasks"""
        while self.is_running:
            try:
                # Memory consolidation
                await self.memory.consolidate()
                
                # Self-improvement check
                if SELF_IMPROVEMENT_CONFIG["enabled"]:
                    await self.self_improvement.check_improvements()
                
                # Self-healing check
                await self.self_healing.health_check()
                
                await asyncio.sleep(MEMORY_CONFIG["consolidation_interval"])
                
            except Exception as e:
                logger.error(f"Background task error: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            "name": self.name,
            "version": self.version,
            "is_running": self.is_running,
            "skills_loaded": len(self.skill_registry),
            "conversation_length": len(self.conversation_history),
            "memory_stats": self.memory.get_stats(),
            "uptime": self.context.get("session_start", "N/A"),
        }
