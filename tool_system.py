"""NanoBot Tool-System – basiert auf Claude Code Architektur"""
import json, urllib.request, subprocess, os, glob as glob_mod
from pathlib import Path

# ─── Tool Registry ───────────────────────────────────
class Tool:
    def __init__(self, name, description, prompt, fn):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.fn = fn

TOOLS = []

def register(name, description, prompt):
    def decorator(fn):
        TOOLS.append(Tool(name, description, prompt, fn))
        return fn
    return decorator

# ─── Built-in Tools ──────────────────────────────────
@register(
    "read_file", 
    "Lese eine Datei vom Server",
    "Nutze dieses Tool wenn der User fragt was in einer Datei steht."
)
def read_file(path):
    try:
        with open(path) as f:
            return f.read()[:2000]
    except Exception as e:
        return f"Fehler: {e}"

@register(
    "write_file",
    "Schreibe eine Datei auf den Server",
    "Nutze dieses Tool wenn der User will dass du eine Datei erstellst."
)
def write_file(path, content):
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return f"✅ {path} geschrieben ({len(content)} Zeichen)"
    except Exception as e:
        return f"Fehler: {e}"

@register(
    "list_files",
    "Liste Dateien in einem Verzeichnis",
    "Nutze dieses Tool um zu sehen was in einem Ordner ist."
)
def list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files[:30])
    except Exception as e:
        return f"Fehler: {e}"

@register(
    "shell",
    "Führe einen Shell-Befehl aus",
    "Nutze dieses Tool wenn der User Systembefehle ausführen will. ACHTUNG: Nur lesende Befehle!"
)
def shell(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        out = result.stdout + result.stderr
        return out[:2000]
    except subprocess.TimeoutExpired:
        return "Timeout (30s)"
    except Exception as e:
        return f"Fehler: {e}"

def tool_list_prompt():
    """Generiert die Tool-Beschreibung fürs LLM"""
    lines = ["", "## Verfügbare Tools:", ""]
    for t in TOOLS:
        lines.append(f"- {t.name}: {t.description}")
        lines.append(f"  {t.prompt}")
        lines.append("")
    return "\n".join(lines)

def execute_tool(tool_name, **kwargs):
    for t in TOOLS:
        if t.name == tool_name:
            return t.fn(**kwargs)
    return f"Unbekanntes Tool: {tool_name}"
