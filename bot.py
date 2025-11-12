############################################################
#  ASISTENCIA ABDARA12 — BOT TWITCH (FULL PRO, POLLING)
############################################################

import asyncio, time, json
import websockets, requests


# ========= CONFIG (SIN .env) =========
TOKEN = "kk7bd8x8qhxeww4x147s1s2rdh0gq6"   # oauth sin "oauth:"
APP_TOKEN = "epaglgmhskyal8sesozk0egutp7w47"
CLIENT_ID = "u4jxn8cgm5ki14grzcmedwc8yh5pr5"

BOT_NAME = "crimul_bot"
CHANNEL = "abdara12"
BROADCASTER_ID = "930537744"

GAS_URL = "https://script.google.com/macros/s/AKfycbx6WjqODhuetXMwsAtzfvXY539Quj1exnRz7s7J6FQBH2UAlag6Brs6InxPsRS3uq2F/exec"
POLL_SECONDS = 60
# =====================================


def call_gas(params, retries=3, timeout=6):
    """GET con reintentos exponenciales simples."""
    backoff = 1.0
    for i in range(retries):
        try:
            r = requests.get(GAS_URL, params=params, timeout=timeout)
            return r
        except Exception as e:
            if i == retries - 1:
                print("GAS FAIL:", e)
                return None
            time.sleep(backoff)
            backoff *= 2


async def connect_to_chat():
    uri = "wss://irc-ws.chat.twitch.tv:443"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(f"PASS oauth:{TOKEN}")
                await ws.send(f"NICK {BOT_NAME}")
                await ws.send("CAP REQ :twitch.tv/commands twitch.tv/tags")
                await ws.send(f"JOIN #{CHANNEL}")
                print(f"✅ CHAT conectado — {CHANNEL}")

                while True:
                    msg = await ws.recv()
                    if msg.startswith("PING"):
                        await ws.send("PONG :tmi.twitch.tv")
                        continue

                    if "PRIVMSG" in msg:
                        prefix = msg.split("PRIVMSG", 1)[0]
                        try:
                            username = prefix.split("display-name=", 1)[1].split(";", 1)[0]
                        except:
                            username = "anon"
                        text = msg.split("PRIVMSG", 1)[1].split(" :", 1)[1].strip().lower()

                        if text.startswith("!asistencia"):
                            call_gas({"action":"asistencia","user":username})

                        elif text == "!asistenciaextra":
                            call_gas({"action":"extra","user":username})

        except Exception as e:
            print("⚠️ CHAT error, reintentando 10s…", e)
            await asyncio.sleep(10)


async def poll_stream_status():
    """Polling cada 60s: detecta on/off y notifica a GAS (start/stop)."""
    global STREAM_ONLINE
    url = f"https://api.twitch.tv/helix/streams?user_id={BROADCASTER_ID}"
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {APP_TOKEN}"}

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                online = len(r.json().get("data", [])) > 0

                if online and not STREAM_ONLINE:
                    call_gas({"action":"stream_start"})
                    print("🔴 STREAM ON")

                elif not online and STREAM_ONLINE:
                    call_gas({"action":"stream_stop"})
                    print("⚫ STREAM OFF")

                STREAM_ONLINE = online

            elif r.status_code == 401:
                print("⚠️ Helix 401 (token app inválido/expirado).")

            await asyncio.sleep(POLL_SECONDS)

        except Exception as e:
            print("⚠️ Poll error:", e)
            await asyncio.sleep(POLL_SECONDS)


async def main():
    task_chat = asyncio.create_task(connect_to_chat())
    task_poll = asyncio.create_task(poll_stream_status())
    await asyncio.gather(task_chat, task_poll)


if __name__ == "__main__":
    STREAM_ONLINE = False
    print("=== BOT ASISTENCIA — INICIO ===")
    asyncio.run(main())
