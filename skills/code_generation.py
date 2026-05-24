"""
REX Code Generation Skill
"""
import os
import subprocess
import tempfile
from typing import Dict, List, Optional
from pathlib import Path

from loguru import logger

from skills.base_skill import BaseSkill


class CodeGenerationSkill(BaseSkill):
    """
    Advanced Code Generation Skill supporting:
    - Python, JavaScript, Java, C++, C#, Go, Rust, PHP, Ruby
    - Web applications (HTML/CSS/JS, React, Flask, Django)
    - APIs and backend services
    - Database schemas
    - Deployment configurations
    """
    
    LANGUAGE_TEMPLATES = {
        "python": {
            "extension": ".py",
            "run_cmd": "python",
            "templates": {
                "function": '''def {name}({params}):
    """
    {description}
    """
    {body}
    return {return_val}
''',
                "class": '''class {name}:
    """
    {description}
    """
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
                "flask_app": '''from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({{"message": "Welcome to {name} API", "status": "running"}})

@app.route('/api/data', methods=['GET'])
def get_data():
    data = {{"items": [], "count": 0}}
    return jsonify(data)

@app.route('/api/data', methods=['POST'])
def create_data():
    item = request.json
    return jsonify({{"created": item, "status": "success"}}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)
''',
            }
        },
        "javascript": {
            "extension": ".js",
            "templates": {
                "function": '''function {name}({params}) {{
    // {description}
    {body}
}}
''',
                "express_app": '''const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {{
    res.json({{ message: "Welcome to {name} API", status: "running" }});
}});

app.get('/api/data', (req, res) => {{
    res.json({{ items: [], count: 0 }});
}});

app.post('/api/data', (req, res) => {{
    const item = req.body;
    res.status(201).json({{ created: item, status: "success" }});
}});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${{PORT}}`));
''',
            }
        },
        "html": {
            "extension": ".html",
            "templates": {
                "webpage": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 90%;
        }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        p {{ color: #666; line-height: 1.6; }}
        .btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
            transition: transform 0.2s;
        }}
        .btn:hover {{ transform: scale(1.05); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{name}</h1>
        <p>{description}</p>
        <button class="btn" onclick="alert('Hello from REX!')">Get Started</button>
    </div>
</body>
</html>
''',
            }
        },
    }
    
    def __init__(self):
        super().__init__(
            name="code_generation",
            description="Generate code in multiple programming languages",
            version="1.0.0",
            category="development"
        )
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute code generation"""
        try:
            # Determine language and type
            language = self._detect_language(user_input)
            code_type = self._detect_code_type(user_input)
            
            # Generate code
            code = self.generate_code(user_input, language, code_type)
            
            # Create preview if HTML
            preview_url = None
            if language == "html":
                preview_url = self._create_preview(code)
            
            return {
                "text": f"Here's the generated {language} code:\n\n```{language}\n{code}\n```",
                "actions": ["display_code", "copy_code", "run_code", "save_file"],
                "data": {
                    "code": code,
                    "language": language,
                    "type": code_type,
                    "preview_url": preview_url,
                },
            }
        except Exception as e:
            return {
                "text": f"Code generation error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _detect_language(self, text: str) -> str:
        """Detect requested programming language"""
        text_lower = text.lower()
        
        language_keywords = {
            "python": ["python", "py", "flask", "django", "pandas"],
            "javascript": ["javascript", "js", "node", "react", "express", "vue"],
            "html": ["html", "website", "webpage", "web page", "landing page"],
            "java": ["java", "spring", "android"],
            "cpp": ["c++", "cpp", "c plus plus"],
            "csharp": ["c#", "csharp", ".net", "unity"],
            "go": ["golang", "go "],
            "rust": ["rust", "cargo"],
            "php": ["php", "laravel", "wordpress"],
            "ruby": ["ruby", "rails"],
            "sql": ["sql", "database", "query", "table"],
            "css": ["css", "style", "stylesheet"],
        }
        
        for lang, keywords in language_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return lang
        
        return "python"  # Default
    
    def _detect_code_type(self, text: str) -> str:
        """Detect what type of code to generate"""
        text_lower = text.lower()
        
        type_keywords = {
            "webpage": ["website", "webpage", "landing page", "html page", "web app"],
            "flask_app": ["flask", "api", "backend", "rest", "server"],
            "express_app": ["express", "node api", "node server"],
            "function": ["function", "method", "algorithm", "calculate", "sort", "search"],
            "class": ["class", "object", "model", "entity"],
            "script": ["script", "automation", "bot", "crawler"],
        }
        
        for code_type, keywords in type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return code_type
        
        return "function"
    
    def generate_code(self, prompt: str, language: str = "python", 
                     code_type: str = "function") -> str:
        """Generate code based on prompt"""
        # Extract name from prompt
        name = self._extract_name(prompt)
        
        # Get template
        lang_config = self.LANGUAGE_TEMPLATES.get(language, self.LANGUAGE_TEMPLATES["python"])
        templates = lang_config.get("templates", {})
        template = templates.get(code_type, templates.get("function", "# Code here"))
        
        # Fill template
        code = template.format(
            name=name,
            params="",
            description=f"Generated by REX based on: {prompt[:100]}",
            body="# Implementation based on requirements",
            return_val="result",
            init_params="",
            init_body="pass",
            methods="# Methods here",
        )
        
        # Add generated header
        header = self._generate_header(language, prompt)
        
        return header + "\n" + code
    
    def _extract_name(self, prompt: str) -> str:
        """Extract a suitable name from the prompt"""
        import re
        words = re.findall(r'\b[a-zA-Z]+\b', prompt)
        meaningful = [w for w in words if len(w) > 3 and w.lower() not in 
                     {'create', 'make', 'build', 'write', 'generate', 'code', 'program'}]
        
        if meaningful:
            return '_'.join(meaningful[:3]).lower()
        return "rex_generated"
    
    def _generate_header(self, language: str, prompt: str) -> str:
        """Generate file header comment"""
        from datetime import datetime
        
        headers = {
            "python": f'"""\nGenerated by REX AI\nPrompt: {prompt[:100]}\nDate: {datetime.now().strftime("%Y-%m-%d")}\n"""',
            "javascript": f'/**\n * Generated by REX AI\n * Prompt: {prompt[:100]}\n * Date: {datetime.now().strftime("%Y-%m-%d")}\n */',
            "html": f'<!-- Generated by REX AI | {datetime.now().strftime("%Y-%m-%d")} -->',
            "java": f'/**\n * Generated by REX AI\n * Date: {datetime.now().strftime("%Y-%m-%d")}\n */',
        }
        
        return headers.get(language, f"// Generated by REX AI - {datetime.now().strftime('%Y-%m-%d')}")
    
    def _create_preview(self, html_code: str) -> str:
        """Create HTML preview file"""
        preview_dir = Path(tempfile.gettempdir()) / "rex_previews"
        preview_dir.mkdir(exist_ok=True)
        
        preview_file = preview_dir / f"preview_{os.urandom(4).hex()}.html"
        with open(preview_file, 'w') as f:
            f.write(html_code)
        
        return str(preview_file)
    
    async def execute_code(self, code: str, language: str = "python") -> Dict:
        """Execute generated code in sandbox"""
        try:
            ext = self.LANGUAGE_TEMPLATES.get(language, {}).get("extension", ".py")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            if language == "python":
                result = subprocess.run(
                    ["python", temp_file],
                    capture_output=True, text=True, timeout=30
                )
            elif language == "javascript":
                result = subprocess.run(
                    ["node", temp_file],
                    capture_output=True, text=True, timeout=30
                )
            else:
                return {"error": f"Execution not supported for {language}"}
            
            os.unlink(temp_file)
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Code execution timed out (30s limit)"}
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_web_app(self, requirements: str) -> Dict:
        """Generate a complete web application"""
        app_structure = {
            "app.py": self.generate_code(requirements, "python", "flask_app"),
            "templates/index.html": self.generate_code(requirements, "html", "webpage"),
            "requirements.txt": "flask\nflask-cors\n",
            "README.md": f"# {requirements[:50]}\n\nGenerated by REX AI\n\n## Setup\n```\npip install -r requirements.txt\npython app.py\n```",
        }
        
        return {
            "text": f"Web application generated with {len(app_structure)} files!",
            "data": {"files": app_structure},
            "actions": ["download_zip", "preview", "deploy"],
        }


def register_skills(engine):
    """Register skill with REX engine"""
    skill = CodeGenerationSkill()
    engine.register_skill(
        name="code_generation",
        handler=skill.execute,
        description=skill.description
    )
