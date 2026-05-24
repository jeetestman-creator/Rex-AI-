"""
REX NLP Module - Natural Language Processing
Self-Healing, Python 3.14+ Compatible, Sandbox-Safe
"""
import re
import json
import ssl
import os
import warnings
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import numpy as np
from loguru import logger

# Suppress Python 3.12+ strict regex syntax warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- NLTK Setup & Sandbox Bypass (Based on NLTK Docs) ---
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.stem import WordNetLemmatizer
    
    # 1. Create a local nltk_data folder in the project root to avoid Admin/Sandbox permission errors
    BASE_DIR = Path(__file__).parent.parent
    LOCAL_NLTK_DATA = BASE_DIR / "nltk_data"
    LOCAL_NLTK_DATA.mkdir(parents=True, exist_ok=True)
    
    # 2. Tell NLTK to look in our local folder first
    if str(LOCAL_NLTK_DATA) not in nltk.data.path:
        nltk.data.path.insert(0, str(LOCAL_NLTK_DATA))
        
    NLTK_AVAILABLE = True
except ImportError:
    nltk = None
    NLTK_AVAILABLE = False
    logger.warning("NLTK not installed. NLP will use basic fallbacks.")

# --- Optional NLP Libraries ---
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
except ImportError:
    detect = None

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

from config.settings import NLP_CONFIG, REX_CONFIG


class REXNLP:
    """
    Advanced NLP Processing for REX
    """
    
    # Intent patterns (Strictly sanitized for Python 3.12+ / 3.14)
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
    
    # Entity patterns (Strictly sanitized)
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

    # Hardcoded fallback stop words in case NLTK download completely fails
    FALLBACK_STOP_WORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", 
        "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 
        'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 
        'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
        'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 
        'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 
        'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 
        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 
        'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 
        'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 
        'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', 
        "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', 
        "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 
        'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 
        'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
    }

    def __init__(self):
        self.lemmatizer = None
        self.stop_words = set()
        
        if NLTK_AVAILABLE:
            self._ensure_nltk_data()
            try:
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
            except Exception as e:
                logger.warning(f"⚠️ NLTK initialization warning: {e}. Using hardcoded fallbacks.")
                self.stop_words = self.FALLBACK_STOP_WORDS
        else:
            self.stop_words = self.FALLBACK_STOP_WORDS
                
        self.compiled_intents = self._compile_patterns(self.INTENT_PATTERNS)
        self.compiled_entities = self._compile_patterns(self.ENTITY_PATTERNS)
        
        self.languages = self._load_languages()
        logger.info("🗣️ NLP module initialized")

    def _ensure_nltk_data(self):
        """
        Self-healing NLTK Downloader.
        Uses local project directory to bypass Windows Sandbox / Admin permission errors.
        Includes SSL bypass for restricted networks.
        """
        # 1. SSL Bypass for restricted environments
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        # 2. Required datasets (Including new punkt_tab and eng tagger)
        required_datasets = [
            ('tokenizers/punkt_tab', 'punkt_tab'),
            ('tokenizers/punkt', 'punkt'),
            ('corpora/stopwords', 'stopwords'),
            ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
            ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
            ('chunkers/maxent_ne_chunker', 'maxent_ne_chunker'),
            ('corpora/words', 'words'),
            ('corpora/wordnet', 'wordnet')
        ]
        
        # 3. Check and download to LOCAL_NLTK_DATA
        for path, name in required_datasets:
            try:
                nltk.data.find(path)
            except LookupError:
                logger.info(f"🔄 Self-Healing: Downloading missing NLTK dataset '{name}' to local storage...")
                try:
                    # Download specifically to our local sandbox-safe folder
                    nltk.download(name, download_dir=str(LOCAL_NLTK_DATA), quiet=True)
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
            try:
                with open(lang_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def detect_language(self, text: str) -> str:
        """Detect the language of input text"""
        if detect is None:
            return "en"
        try:
            lang = detect(text)
            return lang if lang in REX_CONFIG.get("supported_languages", ["en"]) else "en"
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
        if NLTK_AVAILABLE: 
            try: return word_tokenize(text)
            except Exception: pass
        return re.findall(r'\b\w+\b', text.lower())
    
    def sent_tokenize(self, text: str) -> List[str]:
        if NLTK_AVAILABLE: 
            try: return sent_tokenize(text)
            except Exception: pass
        return re.split(r'[.!?]+', text)
    
    def pos_tag(self, text: str) -> List[Tuple[str, str]]:
        if NLTK_AVAILABLE: 
            try: return pos_tag(word_tokenize(text))
            except Exception: pass
        return []
    
    def lemmatize(self, text: str) -> List[str]:
        if not self.lemmatizer: return self.tokenize(text)
        try:
            return [self.lemmatizer.lemmatize(token.lower()) for token in self.tokenize(text)]
        except Exception:
            return self.tokenize(text)
    
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
                    entities.append({
                        "text": match, 
                        "type": entity_type, 
                        "start": text.find(match), 
                        "end": text.find(match) + len(match)
                    })
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
