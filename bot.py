#!/usr/bin/env python3
"""NanoBot – mit Tool-System (Claude Code inspiriert)"""
import logging, json, time, urllib.request
from config import TOKEN, OLLAMA_URL, MODEL, ALLOWED_USERS
from tool_system import TOOLS, tool_list_prompt, execute_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
OFFSET = 0

SYSTEM = {
    "role": "system",
    "content": (
        "Du bist NanoBot, ein lokaler AI-Assistent auf Sans Server. "
        "Läufst auf llama3.1:8b lokal, null Kosten. "
        "Antworte auf Deutsch, kurz und hilfreich.\n\n"
        "WENN der User eine Datei lesen/schreiben/auflisten oder "
        "einen Befehl ausführen will, antworte NUR mit:\n"
        "TOOL: tool_name\nparam1=wert1\nparam2=wert2\n\n"
        "Dann wird das Tool ausgeführt und du kriegst das Ergebnis."
        f"{tool_list_prompt()}"
    )
}

def ollama(messages):
    data = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read())["message"]["content"]

def send(chat_id, text):
    data = json.dumps({"chat_id": chat_id, "text": text[:4000]}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, headers={"Content-Type":"application/json"}), timeout=10)

history = [SYSTEM]
logging.info("🤖 NanoBot mit Tool-System gestartet")

while True:
    try:
        resp = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={OFFSET}&timeout=30", timeout=35).read())
        for u in resp.get("result", []):
            OFFSET = u["update_id"] + 1
            msg = u.get("message", {})
            cid, text = str(msg.get("chat",{}).get("id","")), msg.get("text","")
            if cid not in ALLOWED_USERS or not text:
                continue
            
            logging.info(f"📨 {text[:50]}")
            history.append({"role":"user","content":text})
            
            # LLM antwortet
            reply = ollama(history)
            
            # Prüfen ob Tool-Call
            if reply.strip().startswith("TOOL:"):
                lines = reply.strip().split("\n")
                tool_name = lines[0].replace("TOOL:","").strip()
                kwargs = {}
                for l in lines[1:]:
                    if "=" in l:
                        k, v = l.split("=", 1)
                        kwargs[k.strip()] = v.strip()
                logging.info(f"🔧 Tool: {tool_name} {kwargs}")
                result = execute_tool(tool_name, **kwargs)
                history.append({"role":"assistant","content":f"Tool-Ergebnis: {result}"})
                # LLM bekommt das Ergebnis zur Antwort
                reply = ollama(history)
            
            send(int(cid), reply)
            history.append({"role":"assistant","content":reply})
            # History kurz halten
            if len(history) > 10:
                history = [SYSTEM] + history[-8:]
            logging.info(f"📬 {len(reply)} Zeichen")
    except Exception as e:
        logging.error(f"🔄 {e}")
        time.sleep(5)
