#!/usr/bin/env python3
"""NanoBot – Lokaler AI-Agent mit Tool-System"""
import logging, json, time, urllib.request
from config import TOKEN, OLLAMA_URL, MODEL, ALLOWED_USERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
OFFSET = 0
NAME = "NanoBot"

SYSTEM = {"role": "system", "content": f"Du bist {NAME}, lokaler AI-Assistent. Läufst auf {MODEL}, null Kosten. Antworte auf Deutsch, kurz."}

def ollama(messages):
    data = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read())["message"]["content"]

def send(chat_id, text):
    data = json.dumps({"chat_id": chat_id, "text": text}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, headers={"Content-Type":"application/json"}), timeout=10)

logging.info(f"🤖 {NAME} gestartet")
while True:
    try:
        resp = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={OFFSET}&timeout=30", timeout=35).read())
        for u in resp.get("result", []):
            OFFSET = u["update_id"] + 1
            msg = u.get("message", {})
            cid, text = str(msg.get("chat",{}).get("id","")), msg.get("text","")
            if cid in ALLOWED_USERS and text:
                logging.info(f"📨 {text[:50]}")
                reply = ollama([SYSTEM, {"role":"user","content":text}])
                send(int(cid), reply)
                logging.info(f"📬 {len(reply)} Zeichen")
    except Exception as e:
        logging.error(f"🔄 {e}")
        time.sleep(5)
