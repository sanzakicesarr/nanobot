#!/usr/bin/env python3
"""NanoBot – Gemini 2.5 Flash (1M Kontext, $0)"""
import logging, json, time, urllib.request
from config import TOKEN, GEMINI_KEY, GEMINI_URL, ALLOWED_USERS, MAX_CONTEXT
from tool_system import tool_list_prompt, execute_tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
OFFSET = 0

try:
    with open("/app/data/memory.json") as f:
        MEMORY = json.load(f)
except:
    MEMORY = {"about_user": "", "facts": [], "conversations": []}

def save_memory():
    with open("/app/data/memory.json", 'w') as f:
        json.dump(MEMORY, f, indent=2)

SYSTEM_PROMPT = (
    "Du bist NanoBot, Sans persönlicher KI-Agent. Läufst auf Gemini 2.5 Flash, 1M Kontext, $0 Kosten.\n"
    "Antworte auf Deutsch. Sei ein AGENT: locker, direkt, erledigt Sachen.\n"
    "Du hast PERSÖNLICHKEIT: humorvoll, manchmal frech, aber immer hilfreich.\n"
    f"{tool_list_prompt()}"
)

if MEMORY.get("about_user"):
    SYSTEM_PROMPT += f"\nInfo über den User: {MEMORY['about_user']}"

def gemini(messages):
    """Ruft Gemini API auf"""
    parts = [{"text": m["content"]} for m in messages]
    data = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": m["content"]} for m in messages]}],
        "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.7}
    }).encode()
    
    url = f"{GEMINI_URL}?key={GEMINI_KEY}"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    return result["candidates"][0]["content"]["parts"][0]["text"]

def send(chat_id, text):
    data = json.dumps({"chat_id": chat_id, "text": text[:4000]}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, headers={"Content-Type":"application/json"}), timeout=10)

def typing(chat_id):
    urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendChatAction?chat_id={chat_id}&action=typing", timeout=5)

history = []
logging.info(f"🚀 NanoBot auf Gemini 2.5 Flash (1M Kontext)")

while True:
    try:
        resp = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={OFFSET}&timeout=30", timeout=35).read())
        for u in resp.get("result", []):
            OFFSET = u["update_id"] + 1
            msg = u.get("message", {})
            cid, text = str(msg.get("chat",{}).get("id","")), msg.get("text","")
            if cid not in ALLOWED_USERS or not text:
                continue
            
            typing(int(cid))
            logging.info(f"📨 {text[:50]}")
            history.append({"role": "user", "content": text})
            
            # Gemini Call
            reply = gemini(history)
            
            send(int(cid), reply)
            history.append({"role": "assistant", "content": reply})
            
            MEMORY["conversations"].append({"time": time.time(), "text": text[:100]})
            MEMORY["conversations"] = MEMORY["conversations"][-20:]
            save_memory()
            
            logging.info(f"📬 {len(reply)} Zeichen | History: {len(history)} Messages")
    except Exception as e:
        logging.error(f"🔄 {e}")
        time.sleep(5)
