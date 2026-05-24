
---

## 25. `skills/ethical_hacking.py`

```python
"""
REX Ethical Hacking Skill - Attack & Defense
"""
import socket
import hashlib
import json
from typing import Dict, List
from datetime import datetime

from loguru import logger

from skills.base_skill import BaseSkill


class EthicalHackingSkill(BaseSkill):
    """
    Ethical Hacking Skill for authorized testing:
    - Attack simulation (authorized)
    - Defense mechanisms
    - Security scanning
    - Vulnerability assessment
    - Password auditing
    - Network analysis
    """
    
    def __init__(self):
        super().__init__(
            name="ethical_hacking",
            description="Ethical hacking tools for authorized security testing",
            version="1.0.0",
            category="security"
        )
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute ethical hacking skill"""
        try:
            action = self._detect_action(user_input)
            
            # Always show disclaimer for attack features
            disclaimer = "⚠️ **IMPORTANT**: Only use these tools on systems you own or have explicit permission to test.\n\n"
            
            if action == "recon":
                result = await self.reconnaissance(user_input)
            elif action == "password_audit":
                result = await self.password_audit(user_input)
            elif action == "network_scan":
                result = await self.network_scan(user_input)
            elif action == "defense":
                result = await self.defense_check(user_input)
            elif action == "web_scan":
                result = await self.web_vulnerability_scan(user_input)
            elif action == "hash":
                result = await self.hash_operations(user_input)
            elif action == "report":
                result = await self.generate_report()
            else:
                result = await self.get_tools_overview()
            
            result["text"] = disclaimer + result.get("text", "")
            return result
            
        except Exception as e:
            return {
                "text": f"Ethical hacking error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _detect_action(self, text: str) -> str:
        """Detect hacking action"""
        text_lower = text.lower()
        
        actions = {
            "recon": ["recon", "reconnaissance", "information gathering", "enumerate", "fingerprint"],
            "password_audit": ["password audit", "password crack", "brute force", "dictionary", "wordlist"],
            "network_scan": ["network scan", "network map", "discover", "arp scan", "host discovery"],
            "defense": ["defense", "harden", "protect", "secure", "firewall check", "ids"],
            "web_scan": ["web scan", "web vulnerability", "xss", "sqli", "web app", "owasp"],
            "hash": ["hash", "md5", "sha", "crack hash", "identify hash"],
            "report": ["report", "summary", "findings"],
        }
        
        for action, keywords in actions.items():
            if any(kw in text_lower for kw in keywords):
                return action
        
        return "overview"
    
    async def reconnaissance(self, text: str) -> Dict:
        """Information gathering / Reconnaissance"""
        import re
        
        # Extract target
        target = None
        ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', text)
        domain_match = re.search(r'\b([\w.-]+\.\w{2,})\b', text)
        
        if ip_match:
            target = ip_match.group(1)
        elif domain_match:
            target = domain_match.group(1)
        
        if not target:
            return {
                "text": "Please specify a target IP or domain for reconnaissance.",
                "actions": ["help"],
                "data": {},
            }
        
        results = []
        
        # DNS Resolution
        try:
            ip_addr = socket.gethostbyname(target)
            results.append(f"🌐 DNS Resolution: {target} → {ip_addr}")
        except Exception:
            results.append(f"❌ Could not resolve: {target}")
            ip_addr = target
        
        # Port scan (top 20)
        open_ports = []
        common_ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 
                       445, 993, 995, 1723, 3306, 3389, 5900, 8080]
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip_addr, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except Exception:
                continue
        
        results.append(f"\n🔓 Open Ports: {open_ports if open_ports else 'None found in top 20'}")
        
        # Banner grabbing
        if 80 in open_ports or 443 in open_ports:
            port = 80 if 80 in open_ports else 443
            try:
                sock = socket.socket()
                sock.settimeout(3)
                sock.connect((ip_addr, port))
                sock.send(b"HEAD / HTTP/1.0\r\nHost: " + target.encode() + b"\r\n\r\n")
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                server_line = [l for l in banner.split('\n') if 'Server:' in l]
                if server_line:
                    results.append(f"\n🏷️ Server Banner: {server_line[0].strip()}")
                sock.close()
            except Exception:
                pass
        
        return {
            "text": f"""**Reconnaissance Report: {target}**

{chr(10).join(results)}

📊 Summary:
- Target: {target}
- Open ports found: {len(open_ports)}
- Scan time: {datetime.now().strftime('%H:%M:%S')}""",
            "actions": ["deep_scan", "vulnerability_check", "exploit_suggestions"],
            "data": {"target": target, "open_ports": open_ports},
        }
    
    async def password_audit(self, text: str) -> Dict:
        """Password strength audit and suggestions"""
        import re
        import string
        import itertools
        
        # Generate common password list
        common_passwords = [
            "123456", "password", "12345678", "qwerty", "abc123",
            "monkey", "master", "dragon", "111111", "baseball",
            "iloveyou", "trustno1", "sunshine", "letmein", "football",
            "shadow", "superman", "michael", "ninja", "mustang",
        ]
        
        # Check strength metrics
        results = []
        
        # Password generation for testing
        strong_password = self._generate_strong_password(16)
        
        results.append(f"""**Password Audit Tools**

🔐 Strong Password Generator:
   `{strong_password}`

📊 Common Passwords to Avoid:
{chr(10).join([f'   ❌ {p}' for p in common_passwords[:10]])}

📋 Password Policy Recommendations:
   • Minimum 12 characters
   • Mix of upper/lower case
   • Include numbers and symbols
   • No dictionary words
   • No personal information
   • Unique for each account
   • Use a password manager

🛡️ Defense Measures:
   • Implement account lockout after 5 attempts
   • Use multi-factor authentication (MFA)
   • Implement rate limiting
   • Hash passwords with bcrypt/argon2
   • Use salt for each password""")
        
        return {
            "text": "\n".join(results),
            "actions": ["generate_password", "check_breach_db"],
            "data": {"generated_password": strong_password},
        }
    
    def _generate_strong_password(self, length: int = 16) -> str:
        """Generate a cryptographically strong password"""
        import secrets
        import string
        
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        return password
    
    async def network_scan(self, text: str) -> Dict:
        """Network discovery and scanning"""
        import subprocess
        
        results = []
        
        # Get local network info
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            results.append(f"🖥️ Host: {hostname}")
            results.append(f"📡 Local IP: {local_ip}")
        except Exception:
            pass
        
        # ARP table (Linux/Mac)
        try:
            import platform
            if platform.system() != "Windows":
                output = subprocess.check_output(["arp", "-a"], text=True, timeout=5)
                results.append(f"\n📋 ARP Table:\n{output[:500]}")
        except Exception:
            results.append("⚠️ ARP scan not available on this system")
        
        return {
            "text": f"""**Network Scan Results**

{chr(10).join(results)}

🔍 To scan a specific subnet, use: 'network scan 192.168.1.0/24'""",
            "actions": ["host_discovery", "service_detection"],
            "data": {},
        }
    
    async def defense_check(self, text: str) -> Dict:
        """Security defense and hardening check"""
        import platform
        import psutil
        
        checks = []
        system = platform.system()
        
        # Firewall check
        checks.append("🔥 Firewall Status:")
        if system == "Linux":
            try:
                import subprocess
                result = subprocess.check_output(["ufw", "status"], text=True, timeout=5)
                checks.append(f"   UFW: {result.strip()}")
            except Exception:
                checks.append("   ⚠️ UFW status unknown")
        elif system == "Windows":
            checks.append("   Check Windows Defender Firewall settings")
        else:
            checks.append("   Check macOS firewall in System Preferences")
        
        # Open connections
        connections = psutil.net_connections()
        listening = [c for c in connections if c.status == 'LISTEN']
        checks.append(f"\n🔌 Listening Services: {len(listening)}")
        
        # Processes
        suspicious = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                name = proc.info['name'].lower() if proc.info['name'] else ''
                if any(s in name for s in ['nc', 'netcat', 'ncat', 'socat']):
                    suspicious.append(proc.info)
            except Exception:
                continue
        
        if suspicious:
            checks.append(f"\n⚠️ Suspicious Processes: {suspicious}")
        else:
            checks.append("\n✅ No obviously suspicious processes found")
        
        # Disk encryption
        checks.append("\n🔒 Recommendations:")
        checks.append("   • Enable full disk encryption")
        checks.append("   • Keep system updated")
        checks.append("   • Use strong passwords")
        checks.append("   • Enable 2FA where possible")
        checks.append("   • Regular security audits")
        checks.append("   • Backup important data")
        
        return {
            "text": f"""**Defense & Hardening Check**

{chr(10).join(checks)}""",
            "actions": ["full_audit", "harden_system"],
            "data": {},
        }
    
    async def web_vulnerability_scan(self, text: str) -> Dict:
        """Web application vulnerability scanning concepts"""
        return {
            "text": """**Web Application Security Testing**

🔍 OWASP Top 10 Vulnerabilities to Test:

1. **Injection (SQLi)**
   - Test input fields with: ' OR '1'='1
   - Use parameterized queries as defense

2. **Broken Authentication**
   - Test for default credentials
   - Check session management

3. **Sensitive Data Exposure**
   - Check for HTTPS
   - Verify data encryption at rest

4. **XML External Entities (XXE)**
   - Test XML parsers with external entities

5. **Broken Access Control**
   - Test for IDOR vulnerabilities
   - Check authorization on all endpoints

6. **Security Misconfiguration**
   - Check for default pages
   - Verify security headers

7. **Cross-Site Scripting (XSS)**
   - Test: <script>alert('XSS')</script>
   - Implement CSP headers

8. **Insecure Deserialization**
   - Avoid deserializing untrusted data

9. **Using Components with Known Vulnerabilities**
   - Keep dependencies updated
   - Use vulnerability scanners

10. **Insufficient Logging & Monitoring**
    - Implement proper logging
    - Set up alerts

🛡️ **Defensive Measures:**
- Input validation and sanitization
- Output encoding
- Security headers (CSP, HSTS, X-Frame-Options)
- Regular security testing
- Web Application Firewall (WAF)""",
            "actions": ["test_xss", "test_sqli", "header_check"],
            "data": {},
        }
    
    async def hash_operations(self, text: str) -> Dict:
        """Hash identification and operations"""
        import re
        
        # Look for hash in text
        hash_patterns = {
            "MD5": r"\b[a-fA-F0-9]{32}\b",
            "SHA1": r"\b[a-fA-F0-9]{40}\b",
            "SHA256": r"\b[a-fA-F0-9]{64}\b",
            "SHA512": r"\b[a-fA-F0-9]{128}\b",
        }
        
        found_hashes = []
        for hash_type, pattern in hash_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                found_hashes.append({"type": hash_type, "value": match})
        
        if found_hashes:
            results = [f"Found {h['type']}: {h['value']}" for h in found_hashes]
            return {
                "text": f"""**Hash Analysis**

{chr(10).join(results)}

💡 Hash identification based on length:
- 32 chars = MD5
- 40 chars = SHA1
- 64 chars = SHA256
- 128 chars = SHA512""",
                "data": {"hashes": found_hashes},
                "actions": [],
            }
        
        # Generate hashes for demonstration
        sample = "REX_AI_2026"
        return {
            "text": f"""**Hash Operations**

Sample text: "{sample}"

Hash values:
- MD5: {hashlib.md5(sample.encode()).hexdigest()}
- SHA1: {hashlib.sha1(sample.encode()).hexdigest()}
- SHA256: {hashlib.sha256(sample.encode()).hexdigest()}
- SHA512: {hashlib.sha512(sample.encode()).hexdigest()[:64]}...

Provide a hash string to identify its type.""",
            "data": {},
            "actions": ["identify_hash", "generate_hash"],
        }
    
    async def generate_report(self) -> Dict:
        """Generate security assessment report"""
        report = {
            "title": "Security Assessment Report",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sections": [
                "1. Executive Summary",
                "2. Scope & Methodology",
                "3. Findings",
                "4. Risk Assessment",
                "5. Recommendations",
                "6. Conclusion",
            ]
        }
        
        return {
            "text": f"""📋 **Security Assessment Report**

Date: {report['date']}
Generated by: REX AI Ethical Hacking Module

{chr(10).join(report['sections'])}

💡 To generate a full report, perform scans and use 'generate report' after testing.""",
            "data": report,
            "actions": ["export_pdf", "export_html"],
        }
    
    async def get_tools_overview(self) -> Dict:
        """Show available tools"""
        return {
            "text": """**🦖 REX Ethical Hacking Toolkit**

📡 **Reconnaissance:**
   • Information gathering
   • DNS enumeration
   • Port scanning
   • Service identification

🔐 **Password Security:**
   • Password strength audit
   • Strong password generation
   • Policy recommendations

🌐 **Network Analysis:**
   • Network discovery
   • Host scanning
   • Service detection

🛡️ **Defense & Hardening:**
   • System security audit
   • Firewall check
   • Hardening recommendations

🕸️ **Web Security:**
   • OWASP Top 10 testing
   • Vulnerability assessment
   • Security header checks

#️⃣ **Cryptography:**
   • Hash identification
   • Hash generation
   • Encryption/Decryption

📋 **Reporting:**
   • Assessment reports
   • Finding summaries
   • Remediation guides

⚠️ **Legal Notice**: Only use these tools on systems you own or have written permission to test.""",
            "actions": ["recon", "defense", "password_audit"],
            "data": {},
        }


def register_skills(engine):
    """Register skill with REX engine"""
    skill = EthicalHackingSkill()
    engine.register_skill(
        name="ethical_hacking",
        handler=skill.execute,
        description=skill.description
    )
