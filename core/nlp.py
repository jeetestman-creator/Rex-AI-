"""
REX NLP Module - Natural Language Processing
"""
import re
import json
import ssl
import warnings
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import numpy as np
from loguru import logger

# Ignore Python 3.12+ strict regex syntax warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
except ImportError:
    detect = None

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.stem import WordNetLemmatizer
except ImportError:
    nltk = None

from config.settings import NLP_CONFIG, REX_CONFIG


class REXNLP:
    """
    Advanced NLP Processing for REX
    """
    
    # Intent patterns
    INTENT_PATTERNS = {
        "greeting": [r"\b(hello|hi|hey|good morning|good evening|good afternoon|howdy|greetings|sup|what'?s up|vanakkam|வணக்கம்|नमस्ते)\b"],
        "farewell": [r"\b(bye|goodbye|see you|farewell|take care|later|பிரியாவிடை|अलविदा)\b"],
        "question": [r"\b(what|who|where|when|why|how|which|can you|could you|do you|is it|are you)\b.*\?", r".*\?$"],
        "command": [r"\b(open|close|start|stop|run|execute|create|delete|show|hide|play|pause|search|find|send|write|read|calculate|convert|translate)\b"],
        "code_request": [r"\b(code|program|script|function|class|algorithm|implement|develop|build|create.*app|write.*code|generate.*code)\b"],
        "web_search": [r"\b(search|google|look up|find|browse|surf|check online)\b"],
        "weather": [r"\b(weather|temperature|forecast|rain|sunny|cloudy|humidity|wind)\b"],
        "calendar": [r"\b(schedule|calendar|appointment|meeting|reminder|event|date|time)\b"],
        "finance": [r"\b(stock|share|market|invest|trading|crypto|bitcoin|forex|portfolio|mutual fund|nifty|sensex|price|buy|sell)\b"],
        "smart_home": [r"\b(light|fan|ac|temperature|thermostat|door|window|camera|alarm|turn on|turn off|switch)\b"],
        "security": [r"\b(scan|vulnerability|penetration|hack|security|firewall|encrypt|decrypt|password|authentication)\b"],
        "media": [r"\b(image|photo|picture|video|music|song|play|generate.*image|create.*video|edit.*photo)\b"],
        "translation": [r"\b(translate|translation|in tamil|in english|in hindi|convert.*language)\b"],
        "math": [r"\b(calculate|compute|solve|equation|formula|math|add|subtract|multiply|divide)\b", r"\d+\s*[-+*/^]\s*\d+"],
        "self_improvement": [r"\b(learn|improve|upgrade|update|new skill|add capability)\b"],
        "gratitude": [r"\b(thank|thanks|appreciate|grateful|धन्यवाद|நன்றி)\b"],
    }
    
    # Entity patterns (Fully sanitized for Python 3.12+)
    ENTITY_PATTERNS = {
        "email": [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"],
        "url": [r"https?://[^\s]+|www\.[^\s]+"],
        "phone": [r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"],
        "date": [r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"],
        "time": [r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b"],
        "money": [r"\$[\d,]+(?:\.\d{2})?|₹[\d,]+(?:\.\d{2})?|\d+\s*(?:dollars|rupees|euros|USD|INR)"],
        "percentage": [r"\b\d+(?:\.\d+)?%\b"],
        "number": [r"\b\d+(?:\.\d+)?\b"],
    }

    def __init__(self):
        self.lemmatizer = None
        self.stop_words = set()
        
        if nltk:
            self._ensure_nltk_data()
            try:
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
            except Exception as e:
                logger.warning(f"⚠️ NLTK initialization warning: {e}. Using empty fallbacks.")
                self.stop_words = set()
                
        self.compiled_intents = self._compile_patterns(self.INTENT_PATTERNS)
        self.compiled_entities = self._compile_patterns(self.ENTITY_PATTERNS)
        
        self.languages = self._load_languages()
        logger.info("🗣️ NLP module initialized")

    def _ensure_nltk_data(self):
        """Self-healing: Auto-downloads missing NLTK datasets with SSL bypass."""
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        required_datasets = [
            ('tokenizers/punkt', 'punkt'),
            ('corpora/stopwords', 'stopwords'),
            ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
            ('chunkers/maxent_ne_chunker', 'maxent_ne_chunker'),
            ('corpora/words', 'words'),
            ('corpora/wordnet', 'wordnet')
        ]
        
        for path, name in required_datasets:
            try:
                nltk.data.find(path)
            except LookupError:
                logger.info(f"🔄 Self-Healing: Downloading missing NLTK dataset '{name}'...")
                try:
                    nltk.download(name, quiet=True)
                except Exception as e:
                    logger.error(f"Failed to download NLTK dataset {name}: {e}")

    def _compile_patterns(self, patterns: Dict) -> Dict:
        """Compile regex patterns with self-healing for Python 3.12+ strict regex rules."""
        compiled = {}
        for category, pattern_list in patterns.items():
            compiled[category] = []
            for p in pattern_list:
                try:
                    compiled[category].append(re.compile(p, re.IGNORECASE))
                except Exception as e:
                    # SELF-HEALING: Skip invalid regex instead of crashing the engine
                    logger.warning(f"⚠️ Self-Healing: Skipped invalid regex in '{category}': {e}")
        return compiled
    
    def _load_languages(self) -> Dict:
        """Load language configurations"""
        lang_path = Path(__file__).parent.parent / "config" / "languages.json"
        if lang_path.exists():
            with open(lang_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def detect_language(self, text: str) -> str:
        """Detect the language of input text"""
        if detect is None:
            return "en"
        try:
            lang = detect(text)
            return lang if lang in REX_CONFIG["supported_languages"] else "en"
        except Exception:
            return "en"
    
    def analyze(self, text: str, language: str = "en") -> Dict:
        """Perform full NLP analysis on text"""
        return {
            "text": text,
            "language": language,
            "tokens": self.tokenize(text),
            "sentences": self.sent_tokenize(text),
            "pos_tags": self.pos_tag(text),
            "lemmas": self.lemmatize(text),
            "clean_text": self.clean_text(text),
        }
    
    def tokenize(self, text: str) -> List[str]:
        if nltk: return word_tokenize(text)
        return re.findall(r'\b\w+\b', text.lower())
    
    def sent_tokenize(self, text: str) -> List[str]:
        if nltk: return sent_tokenize(text)
        return re.split(r'[.!?]+', text)
    
    def pos_tag(self, text: str) -> List[Tuple[str, str]]:
        if nltk: return pos_tag(word_tokenize(text))
        return []
    
    def lemmatize(self, text: str) -> List[str]:
        if not self.lemmatizer: return self.tokenize(text)
        return [self.lemmatizer.lemmatize(token.lower()) for token in self.tokenize(text)]
    
    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text).strip()
        return re.sub(r'[^\w\s.,!?]', '', text)
    
    def recognize_intent(self, nlp_result: Dict) -> str:
        text = nlp_result.get("text", "")
        scores = {}
        for intent, patterns in self.compiled_intents.items():
            for pattern in patterns:
                if pattern.search(text):
                    scores[intent] = scores.get(intent, 0) + 1
        return max(scores, key=scores.get) if scores else "general"
    
    def extract_entities(self, nlp_result: Dict) -> List[Dict]:
        text = nlp_result.get("text", "")
        entities = []
        for entity_type, patterns in self.compiled_entities.items():
            for pattern in patterns:
                for match in pattern.findall(text):
                    entities.append({"text": match, "type": entity_type, "start": text.find(match), "end": text.find(match) + len(match)})
        return entities
    
    def analyze_sentiment(self, nlp_result: Dict) -> str:
        text = nlp_result.get("text", "")
        if TextBlob:
            try:
                polarity = TextBlob(text).sentiment.polarity
                if polarity > 0.2: return "positive"
                elif polarity < -0.2: return "negative"
                else: return "neutral"
            except Exception: pass
        
        pos_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'happy', 'best', 'awesome', 'nice', 'நல்ல', 'அருமை', 'சூப்பர்'}
        neg_words = {'bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'sad', 'angry', 'disappointed', 'poor', 'useless', 'கெட்ட', 'மோசம்'}
        words = set(text.lower().split())
        if len(words & pos_words) > len(words & neg_words): return "positive"
        elif len(words & neg_words) > len(words & pos_words): return "negative"
        return "neutral"
    
    def paraphrase(self, text: str) -> str:
        return text  # Simplified for stability
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        sentences = self.sent_tokenize(text)
        return text if len(sentences) <= max_sentences else '. '.join(sentences[:max_sentences]) + '.'
    
    def get_response_template(self, intent: str, language: str = "en") -> Dict:
        lang_data = self.languages.get(language, self.languages.get("en", {}))
        prompts = lang_data.get("prompts", {})
        templates = {
            "greeting": prompts.get("greeting", "Hello! How can I help you?"),
            "farewell": lang_data.get("farewells", ["Goodbye!"])[0],
            "gratitude": lang_data.get("confirmations", ["You're welcome!"])[0],
            "error": prompts.get("error", "I encountered an error."),
        }
        return {"text": templates.get(intent, "I understand.")}
