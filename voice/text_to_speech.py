"""
REX Voice Module - Text to Speech
"""
import threading
import queue
from typing import Optional

from loguru import logger

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from gtts import gTTS
    import io
except ImportError:
    gTTS = None

from config.settings import VOICE_CONFIG, REX_CONFIG


class REXTextToSpeech:
    """
    Advanced Text-to-Speech with:
    - Natural human-like voice
    - Multi-language support
    - Speed and pitch control
    - Queue-based speaking
    """
    
    def __init__(self):
        self.engine = None
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self._speak_thread = None
        
        self._init_engine()
        logger.info("🔊 Text-to-Speech initialized")
    
    def _init_engine(self):
        """Initialize TTS engine"""
        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', VOICE_CONFIG.get('sample_rate', 175))
                self.engine.setProperty('volume', VOICE_CONFIG.get('voice_volume', 1.0))
                
                # Set voice (prefer female voice if available)
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                
                logger.info("✅ pyttsx3 engine initialized")
            except Exception as e:
                logger.error(f"pyttsx3 init error: {e}")
                self.engine = None
    
    def speak(self, text: str, language: str = "en", blocking: bool = False):
        """
        Speak the given text
        
        Args:
            text: Text to speak
            language: Language code
            blocking: If True, wait until speech is complete
        """
        if not text:
            return
        
        self.speech_queue.put({"text": text, "language": language})
        
        if not self._speak_thread or not self._speak_thread.is_alive():
            self._speak_thread = threading.Thread(target=self._speak_loop, daemon=True)
            self._speak_thread.start()
        
        if blocking:
            self.speech_queue.join()
    
    def _speak_loop(self):
        """Process speech queue"""
        while True:
            try:
                item = self.speech_queue.get(timeout=5)
                self._do_speak(item["text"], item["language"])
                self.speech_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Speak loop error: {e}")
                self.speech_queue.task_done()
    
    def _do_speak(self, text: str, language: str = "en"):
        """Actually speak the text"""
        self.is_speaking = True
        
        try:
            if self.engine:
                self.engine.say(text)
                self.engine.runAndWait()
            elif gTTS:
                self._speak_gtts(text, language)
            else:
                logger.warning("No TTS engine available")
        except Exception as e:
            logger.error(f"Speech error: {e}")
        finally:
            self.is_speaking = False
    
    def _speak_gtts(self, text: str, language: str = "en"):
        """Speak using Google TTS (gTTS)"""
        if gTTS is None:
            return
        
        try:
            lang_map = {
                "en": "en",
                "ta": "ta",
                "hi": "hi",
                "es": "es",
                "fr": "fr",
                "de": "de",
                "ja": "ja",
                "zh": "zh-CN",
                "ar": "ar",
            }
            
            tts = gTTS(text=text, lang=lang_map.get(language, "en"), slow=False)
            tts.save("/tmp/rex_speech.mp3")
            
            # Play the audio
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", "/tmp/rex_speech.mp3"])
            elif system == "Linux":
                subprocess.run(["aplay", "/tmp/rex_speech.mp3"], 
                             capture_output=True)
            elif system == "Windows":
                import winsound
                winsound.PlaySound("/tmp/rex_speech.mp3", winsound.SND_FILENAME)
                
        except Exception as e:
            logger.error(f"gTTS error: {e}")
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        if self.engine:
            self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        if self.engine:
            self.engine.setProperty('volume', volume)
    
    def set_voice(self, voice_id: str):
        """Set voice by ID"""
        if self.engine:
            self.engine.setProperty('voice', voice_id)
    
    def get_voices(self) -> list:
        """Get available voices"""
        if self.engine:
            voices = self.engine.getProperty('voices')
            return [{"id": v.id, "name": v.name, "languages": v.languages} 
                    for v in voices]
        return []
    
    def stop(self):
        """Stop current speech"""
        if self.engine:
            self.engine.stop()
        self.is_speaking = False
    
    def save_speech(self, text: str, file_path: str, language: str = "en"):
        """Save speech to file"""
        if gTTS:
            try:
                tts = gTTS(text=text, lang=language, slow=False)
                tts.save(file_path)
                logger.info(f"Speech saved to: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Save speech error: {e}")
        return False
