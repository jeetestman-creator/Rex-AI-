"""
REX Security Guardrails - Safety & Ethics
"""
import re
from typing import Dict, List, Optional
from datetime import datetime

from loguru import logger


class SecurityGuardrails:
    """
    Safety and Ethics Guardrails:
    - Content filtering
    - Bias detection
    - Privacy protection
    - Transparency
    - Value alignment
    """
    
    HARMFUL_PATTERNS = [
        r"(?:how to|help me)\s+(?:hack|break into|steal|attack|exploit)\s+(?!own|my|test|learn|ethical)",
        r"(?:make|create|build)\s+(?:bomb|weapon|virus|malware|ransomware)",
        r"(?:buy|sell)\s+(?:illegal|drugs|stolen)",
    ]
    
    SENSITIVE_PATTERNS = [
        r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",  # SSN-like
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
        r"(?:password|passwd|secret)\s*[:=]\s*\S+",  # Passwords
    ]
    
    def __init__(self):
        self.compiled_harmful = [re.compile(p, re.IGNORECASE) for p in self.HARMFUL_PATTERNS]
        self.compiled_sensitive = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]
        self.violations_log = []
        
        logger.info("🛡️ Security guardrails initialized")
    
    def check_input(self, text: str) -> Dict:
        """Check user input for safety"""
        result = {
            "safe": True,
            "warnings": [],
            "filtered_text": text,
        }
        
        # Check for harmful content
        for pattern in self.compiled_harmful:
            if pattern.search(text):
                result["safe"] = False
                result["warnings"].append("Potentially harmful content detected")
                self._log_violation("harmful_content", text)
                break
        
        # Check for sensitive information
        for pattern in self.compiled_sensitive:
            matches = pattern.findall(text)
            if matches:
                result["warnings"].append("Sensitive information detected - please be careful")
                # Redact sensitive info
                result["filtered_text"] = pattern.sub("[REDACTED]", result["filtered_text"])
        
        return result
    
    def check_output(self, text: str) -> Dict:
        """Check AI output for safety"""
        result = {
            "safe": True,
            "warnings": [],
            "filtered_text": text,
        }
        
        # Ensure no harmful instructions
        for pattern in self.compiled_harmful:
            if pattern.search(text):
                result["safe"] = False
                result["filtered_text"] = "I cannot provide that information as it may be harmful."
                break
        
        # Ensure no sensitive data leakage
        for pattern in self.compiled_sensitive:
            result["filtered_text"] = pattern.sub("[PROTECTED]", result["filtered_text"])
        
        return result
    
    def detect_bias(self, text: str) -> Dict:
        """Detect potential bias in text"""
        bias_indicators = {
            "gender": [r"\b(?:all men|all women|boys will be|girls can't)\b"],
            "race": [r"\b(?:all (?:black|white|asian|hispanic) people)\b"],
            "age": [r"\b(?:old people|young people) (?:always|never|can't)\b"],
        }
        
        detected = {}
        for category, patterns in bias_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected[category] = True
        
        return {"biased": bool(detected), "categories": detected}
    
    def ensure_privacy(self, data: Dict) -> Dict:
        """Ensure privacy in data handling"""
        sensitive_keys = ['password', 'ssn', 'credit_card', 'api_key', 'secret']
        
        sanitized = {}
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "[PROTECTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _log_violation(self, violation_type: str, content: str):
        """Log a safety violation"""
        self.violations_log.append({
            "type": violation_type,
            "timestamp": datetime.now().isoformat(),
            "content_preview": content[:50] + "...",
        })
        logger.warning(f"Safety violation: {violation_type}")
    
    def get_report(self) -> Dict:
        """Get guardrails report"""
        return {
            "total_violations": len(self.violations_log),
            "recent_violations": self.violations_log[-10:],
            "status": "active",
        }
