from skills.base_skill import BaseSkill
from loguru import logger

class MyCustomSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="my_custom_skill",
            description="Does amazing things",
            version="1.0.0",
            category="custom"
        )
    
    async def execute(self, user_input, decision, context):
        try:
            # Your logic here
            result = self._process(user_input)
            
            return {
                "text": result,
                "actions": ["action1", "action2"],
                "data": {"key": "value"},
            }
        except Exception as e:
            logger.error(f"Skill error: {e}")
            return {
                "text": f"Error: {e}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _process(self, user_input):
        return f"Processed: {user_input}"


def register_skills(engine):
    skill = MyCustomSkill()
    engine.register_skill(
        name="my_custom_skill",
        handler=skill.execute,
        description=skill.description
    )
