"""
REX Calendar & Scheduling Skill
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from skills.base_skill import BaseSkill
from config.settings import DATA_DIR


class CalendarSkill(BaseSkill):
    """Calendar and Scheduling Management"""
    
    def __init__(self):
        super().__init__(
            name="calendar",
            description="Calendar management, scheduling, and reminders",
            version="1.0.0",
            category="productivity"
        )
        self.events = self._load_events()
        self.reminders = []
    
    def _load_events(self) -> List[Dict]:
        """Load events from storage"""
        events_file = DATA_DIR / "calendar_events.json"
        if events_file.exists():
            try:
                with open(events_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _save_events(self):
        """Save events to storage"""
        events_file = DATA_DIR / "calendar_events.json"
        try:
            with open(events_file, 'w') as f:
                json.dump(self.events, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save events: {e}")
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute calendar skill"""
        try:
            action = self._detect_action(user_input)
            
            if action == "add_event":
                result = await self.add_event(user_input)
            elif action == "list_events":
                result = await self.list_events(user_input)
            elif action == "remind":
                result = await self.set_reminder(user_input)
            elif action == "delete_event":
                result = await self.delete_event(user_input)
            elif action == "today":
                result = await self.get_today_events()
            else:
                result = await self.get_today_events()
            
            self._save_events()
            
            return {
                "text": result.get("text", "Calendar updated."),
                "actions": result.get("actions", []),
                "data": result.get("data", {}),
            }
        except Exception as e:
            return {
                "text": f"Calendar error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _detect_action(self, text: str) -> str:
        """Detect calendar action"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["schedule", "add event", "create event", "set meeting", "book"]):
            return "add_event"
        elif any(w in text_lower for w in ["list", "show", "what's on", "upcoming", "events"]):
            return "list_events"
        elif any(w in text_lower for w in ["remind", "reminder", "alert"]):
            return "remind"
        elif any(w in text_lower for w in ["delete", "remove", "cancel"]):
            return "delete_event"
        elif any(w in text_lower for w in ["today", "today's"]):
            return "today"
        
        return "today"
    
    async def add_event(self, text: str) -> Dict:
        """Add a new event"""
        import re
        
        # Try to extract date/time
        date_patterns = [
            r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',
            r'(tomorrow|today|next monday|next tuesday|next wednesday)',
        ]
        
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',
            r'at\s+(\d{1,2})\s*(am|pm)',
        ]
        
        # Create event
        event = {
            "id": len(self.events) + 1,
            "title": self._extract_title(text),
            "description": "",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "09:00",
            "duration": 60,
            "created_at": datetime.now().isoformat(),
        }
        
        # Try to parse date
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            ampm = time_match.group(3)
            if ampm and ampm.lower() == 'pm' and hour < 12:
                hour += 12
            event["time"] = f"{hour:02d}:{minute:02d}"
        
        if "tomorrow" in text.lower():
            event["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        self.events.append(event)
        
        return {
            "text": f"📅 Event scheduled: **{event['title']}**\n📆 Date: {event['date']}\n⏰ Time: {event['time']}",
            "data": {"event": event},
            "actions": ["list_events", "set_reminder"],
        }
    
    def _extract_title(self, text: str) -> str:
        """Extract event title from text"""
        import re
        # Remove common scheduling words
        cleaned = re.sub(
            r'(schedule|add|create|set|book|meeting|event|for|on|at|tomorrow|today|\d+[:.]\d+\s*(?:am|pm)?)',
            '', text, flags=re.IGNORECASE
        ).strip()
        
        return cleaned if cleaned else "New Event"
    
    async def list_events(self, text: str = "") -> Dict:
        """List upcoming events"""
        if not self.events:
            return {"text": "📅 No events scheduled. Say 'schedule [event]' to add one."}
        
        # Sort by date and time
        sorted_events = sorted(self.events, key=lambda e: (e.get("date", ""), e.get("time", "")))
        
        lines = []
        for event in sorted_events[:10]:
            lines.append(f"  📌 {event['title']} - {event['date']} at {event['time']}")
        
        return {
            "text": f"📅 **Upcoming Events** ({len(self.events)} total)\n\n" + "\n".join(lines),
            "data": {"events": sorted_events},
            "actions": ["add_event", "delete_event"],
        }
    
    async def get_today_events(self) -> Dict:
        """Get today's events"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = [e for e in self.events if e.get("date") == today]
        
        if not today_events:
            return {
                "text": f"📅 **Today ({today})**: No events scheduled. Enjoy your free day! 🎉",
                "actions": ["add_event"],
                "data": {},
            }
        
        lines = [f"  ⏰ {e['time']} - {e['title']}" for e in today_events]
        
        return {
            "text": f"📅 **Today's Schedule ({today})**\n\n" + "\n".join(lines),
            "data": {"events": today_events},
            "actions": ["add_event", "complete_event"],
        }
    
    async def set_reminder(self, text: str) -> Dict:
        """Set a reminder"""
        reminder = {
            "text": self._extract_title(text),
            "time": datetime.now().isoformat(),
            "active": True,
        }
        self.reminders.append(reminder)
        
        return {
            "text": f"⏰ Reminder set: {reminder['text']}",
            "data": {"reminder": reminder},
            "actions": [],
        }
    
    async def delete_event(self, text: str) -> Dict:
        """Delete an event"""
        if self.events:
            removed = self.events.pop()
            return {
                "text": f"🗑️ Deleted event: {removed['title']}",
                "data": {"deleted": removed},
                "actions": ["undo", "list_events"],
            }
        return {"text": "No events to delete."}


def register_skills(engine):
    """Register skill with REX engine"""
    skill = CalendarSkill()
    engine.register_skill(
        name="calendar",
        handler=skill.execute,
        description=skill.description
    )
