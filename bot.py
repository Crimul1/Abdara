############################################################
#       ✅ ASISTENCIA ABDARA — BOT TWITCH (POLLING)
############################################################

import asyncio
import websockets
import requests
import time


# ========= CONFIG =========
TOKEN = "kk7bd8x8qhxeww4x147s1s2rdh0gq6"
APP_TOKEN = "epaglgmhskyal8sesozk0egutp7w47"
CLIENT_ID = "u4jxn8cgm5ki14grzcmedwc8yh5pr5"

BOT_NAME = "crimul_bot"
CHANNEL = "abdara12"
BROADCASTER_ID = "930537744"

GAS_URL = "https://script.google.com/macros/s/AKfycbwsV6Ken1I38qcRsKrYCqa0r5qozVFp0yhGFThe8MiJ0WASFdup5pn0Myxbp-AJ9zR6/exec"
# ==========================



# helper
def call_gas(params):
    try:
        return requests.get(GAS_URL, params=params, timeout=5)
    except:
        return None



# =============== CHAT LISTENER ===============
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
                        prefix = msg.split("PRIVMSG",1)[0]
                        username = prefix.split("display-name=",1)[1].split(";",1)[0]
                        text = msg.split("PRIVMSG",1)[1].split(" :",1)[1].strip().lower()

                        # === LOGICA ===
                        if text.startswith("!asistencia"):
                            call_gas({"action":"asistencia","user":username})

                        elif text == "!asistenciaextra":
                            call_gas({"action":"extra","user":username})

        except Exception as e:
            print("⚠️ CHAT error, reintentando 10s…", e)
            await asyncio.sleep(10)



# =============== STREAM POLLING ===============
async def poll_stream_status():
    global stream_online
    url = f"https://api.twitch.tv/helix/streams?user_id={BROADCASTER_ID}"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {APP_TOKEN}"
    }

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                online = len(r.json().get("data",[])) > 0

                if online and not stream_online:
                    call_gas({"action":"stream_start"})
                    print("🔴 STREAM ON")

                elif not online and stream_online:
                    call_gas({"action":"stream_stop"})
                    print("⚫ STREAM OFF")

                stream_online = online

            await asyncio.sleep(60)

        except:
            await asyncio.sleep(60)



# MAIN
async def main():
    task1 = asyncio.create_task(connect_to_chat())
    task2 = asyncio.create_task(poll_stream_status())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    stream_online = False
    print("=== BOT ASISTENCIA ===")
    asyncio.run(main())
