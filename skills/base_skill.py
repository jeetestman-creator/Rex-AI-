"""
REX Base Skill Class - All skills inherit from this
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseSkill(ABC):
    """
    Base class for all REX skills.
    All skill modules must inherit from this class.
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0",
                 category: str = "general"):
        self.name = name
        self.description = description
        self.version = version
        self.category = category
        self.created_at = datetime.now().isoformat()
        self.usage_count = 0
        self.success_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """
        Execute the skill's main functionality.
        
        Args:
            user_input: The user's input text
            decision: The decision dictionary from reasoning engine
            context: Current context dictionary
            
        Returns:
            Dict with 'text', 'actions', and 'data' keys
        """
        pass
    
    def get_info(self) -> Dict:
        """Get skill information"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
            "success_rate": (
                self.success_count / max(self.usage_count, 1)
            ),
        }
    
    def record_usage(self, success: bool = True):
        """Record skill usage"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    async def validate_input(self, user_input: str) -> bool:
        """Validate input before processing"""
        return bool(user_input and user_input.strip())
    
    async def preprocess(self, user_input: str, context: Dict) -> str:
        """Preprocess input before execution"""
        return user_input.strip()
    
    async def postprocess(self, result: Dict, context: Dict) -> Dict:
        """Postprocess result after execution"""
        return result
