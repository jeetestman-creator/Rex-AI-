"""
REX Weather Skill
"""
import json
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from loguru import logger

try:
    import requests
except ImportError:
    requests = None

from skills.base_skill import BaseSkill
from config.settings import DATA_DIR, CACHE_DIR


class WeatherSkill(BaseSkill):
    """Weather information and forecasting"""
    
    def __init__(self):
        super().__init__(
            name="weather",
            description="Weather information, forecasts, and alerts",
            version="1.0.0",
            category="information"
        )
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute weather skill"""
        try:
            location = self._extract_location(user_input)
            if not location:
                location = "Chennai"  # Default
            
            # Check cache
            cache_key = f"weather_{location}"
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if (datetime.now() - cached["timestamp"]).seconds < self.cache_duration:
                    return cached["result"]
            
            # Fetch weather
            result = await self.get_weather(location)
            
            # Cache result
            self.cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now(),
            }
            
            return result
            
        except Exception as e:
            return {
                "text": f"Weather error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text"""
        import re
        
        # Remove weather-related words
        cleaned = re.sub(
            r'(weather|temperature|forecast|in|at|for|what\'?s|is|the|today|tomorrow)',
            '', text, flags=re.IGNORECASE
        ).strip()
        
        if cleaned:
            return cleaned
        
        return None
    
    async def get_weather(self, location: str) -> Dict:
        """Get weather for a location using wttr.in (free, no API key)"""
        if not requests:
            return self._get_mock_weather(location)
        
        try:
            # Use wttr.in - free weather API
            response = requests.get(
                f"https://wttr.in/{location}?format=j1",
                timeout=10,
                headers={"User-Agent": "REX-AI/1.0"}
            )
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_condition", [{}])[0]
                forecast = data.get("weather", [])
                
                temp_c = current.get("temp_C", "N/A")
                temp_f = current.get("temp_F", "N/A")
                feels_like = current.get("FeelsLikeC", "N/A")
                humidity = current.get("humidity", "N/A")
                description = current.get("weatherDesc", [{}])[0].get("value", "N/A")
                wind_speed = current.get("windspeedKmph", "N/A")
                wind_dir = current.get("winddir16Point", "")
                visibility = current.get("visibility", "N/A")
                uv_index = current.get("uvIndex", "N/A")
                
                # Forecast
                forecast_text = ""
                if forecast:
                    forecast_text = "\n\n📅 **Forecast:**"
                    for day in forecast[:3]:
                        date = day.get("date", "")
                        max_temp = day.get("maxtempC", "N/A")
                        min_temp = day.get("mintempC", "N/A")
                        desc = day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "")
                        forecast_text += f"\n  📆 {date}: {min_temp}°C - {max_temp}°C ({desc})"
                
                return {
                    "text": f"""🌤️ **Weather in {location.title()}**

🌡️ Temperature: {temp_c}°C ({temp_f}°F)
🤔 Feels Like: {feels_like}°C
💧 Humidity: {humidity}%
🌬️ Wind: {wind_speed} km/h {wind_dir}
👁️ Visibility: {visibility} km
☀️ UV Index: {uv_index}
📝 Condition: {description}{forecast_text}

_Last updated: {datetime.now().strftime('%H:%M:%S')}_""",
                    "data": {
                        "location": location,
                        "temperature": temp_c,
                        "humidity": humidity,
                        "description": description,
                    },
                    "actions": ["detailed_forecast", "weather_alerts"],
                }
            
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return self._get_mock_weather(location)
    
    def _get_mock_weather(self, location: str) -> Dict:
        """Fallback weather data"""
        return {
            "text": f"""🌤️ **Weather in {location.title()}**

⚠️ Unable to fetch live weather data. Please check your internet connection.

📍 Location: {location}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

💡 Tip: Try again later or check weather.com""",
            "data": {"location": location, "source": "fallback"},
            "actions": ["retry"],
        }


def register_skills(engine):
    """Register skill with REX engine"""
    skill = WeatherSkill()
    engine.register_skill(
        name="weather",
        handler=skill.execute,
        description=skill.description
    )
