"""
REX Smart Home Integration Skill
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from loguru import logger

from skills.base_skill import BaseSkill
from config.settings import DATA_DIR


class SmartHomeSkill(BaseSkill):
    """
    Smart Home Integration Skill supporting:
    - Light control
    - Temperature control
    - Security cameras
    - Door locks
    - Appliance control
    - Scene management
    - Automation rules
    """
    
    def __init__(self):
        super().__init__(
            name="smart_home",
            description="Control and automate smart home devices",
            version="1.0.0",
            category="iot"
        )
        self.devices = self._load_devices()
        self.automations = []
        self.scenes = {}
    
    def _load_devices(self) -> Dict:
        """Load device configurations"""
        device_file = DATA_DIR / "smart_home_devices.json"
        if device_file.exists():
            try:
                with open(device_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default devices
        return {
            "living_room_light": {"type": "light", "room": "Living Room", "state": "off", "brightness": 100},
            "bedroom_light": {"type": "light", "room": "Bedroom", "state": "off", "brightness": 100},
            "kitchen_light": {"type": "light", "room": "Kitchen", "state": "off", "brightness": 100},
            "ac": {"type": "thermostat", "room": "Living Room", "state": "off", "temperature": 24},
            "front_door": {"type": "lock", "room": "Entrance", "state": "locked"},
            "garage_door": {"type": "garage", "room": "Garage", "state": "closed"},
            "security_camera": {"type": "camera", "room": "Front Yard", "state": "recording"},
            "fan": {"type": "fan", "room": "Living Room", "state": "off", "speed": "medium"},
        }
    
    def _save_devices(self):
        """Save device configurations"""
        device_file = DATA_DIR / "smart_home_devices.json"
        try:
            with open(device_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save devices: {e}")
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute smart home command"""
        try:
            action = self._detect_action(user_input)
            
            if action == "turn_on":
                result = await self.turn_on(user_input)
            elif action == "turn_off":
                result = await self.turn_off(user_input)
            elif action == "set_temperature":
                result = await self.set_temperature(user_input)
            elif action == "set_brightness":
                result = await self.set_brightness(user_input)
            elif action == "status":
                result = await self.get_status()
            elif action == "scene":
                result = await self.activate_scene(user_input)
            elif action == "lock":
                result = await self.lock_door(user_input)
            elif action == "unlock":
                result = await self.unlock_door(user_input)
            else:
                result = await self.get_status()
            
            self._save_devices()
            
            return {
                "text": result.get("text", "Command executed."),
                "actions": result.get("actions", []),
                "data": result.get("data", {}),
            }
        except Exception as e:
            return {
                "text": f"Smart home error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _detect_action(self, text: str) -> str:
        """Detect smart home action"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["turn on", "switch on", "enable", "start"]):
            return "turn_on"
        elif any(w in text_lower for w in ["turn off", "switch off", "disable", "stop"]):
            return "turn_off"
        elif any(w in text_lower for w in ["temperature", "set temp", "thermostat"]):
            return "set_temperature"
        elif any(w in text_lower for w in ["brightness", "dim", "bright"]):
            return "set_brightness"
        elif any(w in text_lower for w in ["status", "state", "what's", "show"]):
            return "status"
        elif any(w in text_lower for w in ["scene", "mode", "mood"]):
            return "scene"
        elif any(w in text_lower for w in ["lock", "secure"]):
            return "lock"
        elif any(w in text_lower for w in ["unlock", "open door"]):
            return "unlock"
        
        return "status"
    
    def _find_device(self, text: str) -> Optional[str]:
        """Find device name from text"""
        text_lower = text.lower()
        
        device_keywords = {
            "living_room_light": ["living room light", "living room", "hall light"],
            "bedroom_light": ["bedroom light", "bedroom"],
            "kitchen_light": ["kitchen light", "kitchen"],
            "ac": ["ac", "air conditioner", "aircon", "cooling"],
            "front_door": ["front door", "main door", "door"],
            "garage_door": ["garage", "garage door"],
            "security_camera": ["camera", "security camera", "cctv"],
            "fan": ["fan", "ceiling fan"],
        }
        
        for device, keywords in device_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return device
        
        return None
    
    async def turn_on(self, text: str) -> Dict:
        """Turn on a device"""
        device = self._find_device(text)
        
        if not device or device not in self.devices:
            return {"text": f"I couldn't find that device. Available devices: {', '.join(self.devices.keys())}"}
        
        self.devices[device]["state"] = "on"
        
        return {
            "text": f"✅ Turned on {device.replace('_', ' ').title()} in {self.devices[device]['room']}",
            "actions": ["turn_off", "set_brightness"],
            "data": {"device": device, "state": "on"},
        }
    
    async def turn_off(self, text: str) -> Dict:
        """Turn off a device"""
        device = self._find_device(text)
        
        if not device or device not in self.devices:
            return {"text": f"I couldn't find that device."}
        
        self.devices[device]["state"] = "off"
        
        return {
            "text": f"✅ Turned off {device.replace('_', ' ').title()} in {self.devices[device]['room']}",
            "actions": ["turn_on"],
            "data": {"device": device, "state": "off"},
        }
    
    async def set_temperature(self, text: str) -> Dict:
        """Set temperature"""
        import re
        
        temp_match = re.search(r'(\d+)\s*(?:degrees|°|deg)?', text)
        if temp_match:
            temp = int(temp_match.group(1))
            self.devices["ac"]["temperature"] = temp
            self.devices["ac"]["state"] = "on"
            
            return {
                "text": f"🌡️ Set temperature to {temp}°C. AC is now on.",
                "data": {"temperature": temp},
                "actions": [],
            }
        
        return {"text": "Please specify a temperature (e.g., 'set temperature to 22')"}
    
    async def set_brightness(self, text: str) -> Dict:
        """Set light brightness"""
        import re
        
        device = self._find_device(text)
        brightness_match = re.search(r'(\d+)\s*%?', text)
        
        if device and brightness_match:
            brightness = min(int(brightness_match.group(1)), 100)
            self.devices[device]["brightness"] = brightness
            self.devices[device]["state"] = "on"
            
            return {
                "text": f"💡 Set {device.replace('_', ' ').title()} brightness to {brightness}%",
                "data": {"device": device, "brightness": brightness},
                "actions": [],
            }
        
        return {"text": "Please specify device and brightness (e.g., 'set living room light to 50%')"}
    
    async def get_status(self) -> Dict:
        """Get status of all devices"""
        status_lines = []
        
        for device_id, device in self.devices.items():
            state_emoji = "🟢" if device.get("state") in ["on", "recording"] else "🔴"
            name = device_id.replace('_', ' ').title()
            room = device.get("room", "Unknown")
            state = device.get("state", "unknown")
            
            extra = ""
            if device.get("type") == "light" and device.get("brightness"):
                extra = f" (Brightness: {device['brightness']}%)"
            elif device.get("type") == "thermostat" and device.get("temperature"):
                extra = f" ({device['temperature']}°C)"
            
            status_lines.append(f"  {state_emoji} {name} [{room}]: {state}{extra}")
        
        return {
            "text": f"""🏠 **Smart Home Status**

{chr(10).join(status_lines)}

💡 Say 'turn on/off [device]' to control devices""",
            "actions": ["control_device", "create_automation", "create_scene"],
            "data": {"devices": self.devices},
        }
    
    async def activate_scene(self, text: str) -> Dict:
        """Activate a pre-configured scene"""
        scenes = {
            "morning": {
                "description": "Good Morning Scene",
                "actions": [
                    ("bedroom_light", "on", 70),
                    ("ac", "on", 24),
                ]
            },
            "night": {
                "description": "Good Night Scene",
                "actions": [
                    ("living_room_light", "off", 0),
                    ("kitchen_light", "off", 0),
                    ("bedroom_light", "on", 20),
                    ("front_door", "locked", None),
                ]
            },
            "movie": {
                "description": "Movie Mode",
                "actions": [
                    ("living_room_light", "on", 10),
                    ("ac", "on", 22),
                ]
            },
        }
        
        text_lower = text.lower()
        for scene_name, scene_data in scenes.items():
            if scene_name in text_lower:
                for device_id, state, value in scene_data["actions"]:
                    if device_id in self.devices:
                        self.devices[device_id]["state"] = state
                        if value is not None:
                            if "brightness" in self.devices[device_id]:
                                self.devices[device_id]["brightness"] = value
                            elif "temperature" in self.devices[device_id]:
                                self.devices[device_id]["temperature"] = value
                
                return {
                    "text": f"🎬 Activated '{scene_data['description']}' scene!",
                    "data": {"scene": scene_name},
                    "actions": [],
                }
        
        available = ", ".join(scenes.keys())
        return {"text": f"Available scenes: {available}. Say 'activate [scene name]'"}
    
    async def lock_door(self, text: str) -> Dict:
        """Lock a door"""
        self.devices["front_door"]["state"] = "locked"
        return {
            "text": "🔒 Front door is now locked.",
            "data": {"device": "front_door", "state": "locked"},
            "actions": [],
        }
    
    async def unlock_door(self, text: str) -> Dict:
        """Unlock a door"""
        self.devices["front_door"]["state"] = "unlocked"
        return {
            "text": "🔓 Front door is now unlocked. Please ensure safety.",
            "data": {"device": "front_door", "state": "unlocked"},
            "actions": [],
        }


def register_skills(engine):
    """Register skill with REX engine"""
    skill = SmartHomeSkill()
    engine.register_skill(
        name="smart_home",
        handler=skill.execute,
        description=skill.description
    )
