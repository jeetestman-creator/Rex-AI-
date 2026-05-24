"""
REX Voice Module - Speech Recognition
"""
import queue
import threading
from typing import Optional, Callable

from loguru import logger

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyaudio
except ImportError:
    pyaudio = None

from config.settings import VOICE_CONFIG


class REXSpeechRecognition:
    """
    Advanced Speech Recognition with:
    - Real-time listening
    - Wake word detection
    - Multi-language support
    - Noise reduction
    """
    
    def __init__(self, language: str = "en-IN"):
        self.language = language
        self.is_listening = False
        self.recognizer = sr.Recognizer() if sr else None
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.callbacks = []
        self.wake_word = "hey rex"
        self._listen_thread = None
        
        if self.recognizer:
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
        
        self._init_microphone()
        logger.info("🎤 Speech recognition initialized")
    
    def _init_microphone(self):
        """Initialize microphone"""
        if sr is None:
            logger.warning("SpeechRecognition not available")
            return
        
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("✅ Microphone initialized")
        except Exception as e:
            logger.error(f"Microphone init error: {e}")
    
    def start_listening(self, callback: Callable = None):
        """Start continuous listening"""
        if self.is_listening:
            return
        
        self.is_listening = True
        if callback:
            self.callbacks.append(callback)
        
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        logger.info("🎤 Listening started")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=3)
        logger.info("🎤 Listening stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.is_listening:
            try:
                if not self.microphone:
                    break
                
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=30
                    )
                
                self.audio_queue.put(audio)
                self._process_audio(audio)
                
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Listen loop error: {e}")
                continue
    
    def _process_audio(self, audio):
        """Process captured audio"""
        text = self.recognize(audio)
        
        if text:
            logger.info(f"🗣️ Heard: {text}")
            
            # Check for wake word
            if self.wake_word.lower() in text.lower():
                logger.info("🦖 Wake word detected!")
                self._notify_callbacks(text, wake_word=True)
            else:
                self._notify_callbacks(text, wake_word=False)
    
    def recognize(self, audio=None) -> Optional[str]:
        """Recognize speech from audio"""
        if self.recognizer is None:
            return None
        
        try:
            if audio is None:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=30)
            
            # Try Google Speech Recognition (free, no API key needed for basic usage)
            text = self.recognizer.recognize_google(
                audio, 
                language=self.language
            )
            return text
            
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            # Fallback: try offline recognition
            return self._offline_recognize(audio)
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return None
    
    def _offline_recognize(self, audio) -> Optional[str]:
        """Offline speech recognition fallback"""
        if self.recognizer is None:
            return None
        
        try:
            # Try Sphinx (offline)
            text = self.recognizer.recognize_sphinx(audio)
            return text
        except Exception:
            return None
    
    def recognize_from_file(self, file_path: str) -> Optional[str]:
        """Recognize speech from audio file"""
        if self.recognizer is None:
            return None
        
        try:
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(source)
            return self.recognize(audio)
        except Exception as e:
            logger.error(f"File recognition error: {e}")
            return None
    
    def set_language(self, language: str):
        """Set recognition language"""
        self.language = language
        logger.info(f"Language set to: {language}")
    
    def on_speech(self, callback: Callable):
        """Register a callback for speech events"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, text: str, wake_word: bool = False):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(text, wake_word)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def get_supported_languages(self) -> Dict:
        """Get supported languages"""
        return {
            "en-IN": "English (India)",
            "en-US": "English (US)",
            "en-GB": "English (UK)",
            "ta-IN": "Tamil (India)",
            "hi-IN": "Hindi (India)",
            "es-ES": "Spanish",
            "fr-FR": "French",
            "de-DE": "German",
            "ja-JP": "Japanese",
            "zh-CN": "Chinese",
            "ar-SA": "Arabic",
        }
