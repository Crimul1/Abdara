import asyncio
import aiohttp
import websockets
import time
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "kk7bd8x8qhxeww4x147s1s2rdh0gq6"       # sin "oauth:"
CLIENT_ID = "u4jxn8cgm5ki14grzcmedwc8yh5pr5"
CLIENT_SECRET = "dkn0m45gm7y7a5ka7e024eay1xxhro"

BOT_NAME = "crimul_bot"
CHANNEL = "abdara12"
BROADCASTER_ID = "212158819"

GAS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbysq-navVJ52ZYo1z5T3gBClLlRNhN07HMo84-dUwtH1-0SEgPF-ph6djJaupGR7bul/exec"

POLL_INTERVAL = 30  # 🔥 30 segundos (recomendado)

# ================= ESTADO =================
stream_is_online = False
processed_msg_ids = set()
user_cooldown = {}

# ================= UTILS =================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def in_cooldown(user, seconds=5):
    now = time.time()
    last = user_cooldown.get(user, 0)
    if now - last < seconds:
        return True
    user_cooldown[user] = now
    return False

def already_processed(msg_id):
    if msg_id in processed_msg_ids:
        return True
    processed_msg_ids.add(msg_id)
    if len(processed_msg_ids) > 2000:
        processed_msg_ids.clear()
    return False

# ================= TWITCH AUTH =================
async def get_app_access_token(session):
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    async with session.post(url, params=params) as r:
        data = await r.json()
        return data["access_token"]

# ================= CHAT =================
async def connect_to_chat():
    uri = "wss://irc-ws.chat.twitch.tv:443"
    delay = 5

    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(f"PASS oauth:{BOT_TOKEN}")
                await ws.send(f"NICK {BOT_NAME}")
                await ws.send("CAP REQ :twitch.tv/commands twitch.tv/tags")
                await ws.send(f"JOIN #{CHANNEL}")
                log(f"✅ Chat conectado a #{CHANNEL}")
                delay = 5

                async for msg in ws:
                    if msg.startswith("PING"):
                        await ws.send("PONG :tmi.twitch.tv")
                        continue

                    if "RECONNECT" in msg:
                        log("🔄 Twitch pidió RECONNECT")
                        break

                    if "PRIVMSG" not in msg:
                        continue

                    # ID del mensaje
                    msg_id = None
                    if "@id=" in msg:
                        msg_id = msg.split("@id=", 1)[1].split(";", 1)[0]
                        if already_processed(msg_id):
                            continue

                    prefix, content = msg.split("PRIVMSG", 1)
                    username = "unknown"
                    if "display-name=" in prefix:
                        username = prefix.split("display-name=", 1)[1].split(";", 1)[0].lower()

                    text = content.split(" :", 1)[1].strip().lower()
                    log(f"{username}: {text}")

                    if in_cooldown(username):
                        continue

                    async with aiohttp.ClientSession() as session:
                        if text.startswith("!asistencia"):
                            async with session.get(GAS_WEBHOOK_URL, params={
                                "action": "asistencia",
                                "user": username
                            }) as r:
                                resp = await r.text()
                                log(f"GAS → {resp}")

                        elif text == "!asistenciaextra":
                            async with session.get(GAS_WEBHOOK_URL, params={
                                "action": "extra",
                                "user": username
                            }) as r:
                                resp = await r.text()
                                log(f"GAS → {resp}")

        except Exception as e:
            log(f"⚠ Chat error: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 300)

# ================= STREAM POLLING =================
async def poll_stream_status():
    global stream_is_online
    async with aiohttp.ClientSession() as session:
        access_token = await get_app_access_token(session)
        log("🔑 App Access Token obtenido")

        url = f"https://api.twitch.tv/helix/streams?user_id={BROADCASTER_ID}"

        while True:
            try:
                headers = {
                    "Client-ID": CLIENT_ID,
                    "Authorization": f"Bearer {access_token}"
                }

                async with session.get(url, headers=headers) as r:
                    if r.status == 401:
                        log("🔄 Token expirado, renovando")
                        access_token = await get_app_access_token(session)

                    elif r.status == 200:
                        data = await r.json()
                        live = len(data.get("data", [])) > 0

                        if live and not stream_is_online:
                            log("🔴 STREAM INICIADO")
                            await session.get(GAS_WEBHOOK_URL, params={"action": "stream_start"})

                        elif not live and stream_is_online:
                            log("⚫ STREAM FINALIZADO")
                            await session.get(GAS_WEBHOOK_URL, params={"action": "stream_stop"})

                        stream_is_online = live

                await asyncio.sleep(POLL_INTERVAL)

            except Exception as e:
                log(f"⚠ API error: {e}")
                await asyncio.sleep(60)

# ================= MAIN =================
async def main():
    log("=== BOT ASISTENCIA v4 — ESTABLE ===")
    await asyncio.gather(
        connect_to_chat(),
        poll_stream_status()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("🛑 Bot detenido")
