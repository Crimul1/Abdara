import asyncio
import websockets
import requests

# ========= CONFIG =========
TOKEN = "kk7bd8x8qhxeww4x147s1s2rdh0gq6"
APP_TOKEN = "epaglgmhskyal8sesozk0egutp7w47"
CLIENT_ID = "u4jxn8cgm5ki14grzcmedwc8yh5pr5"

BOT_NAME = "crimul_bot"
CHANNEL = "abdara12"
BROADCASTER_ID = "212158819"

GAS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwky0NBGWFlNIl0qU2jYfX-2AjsszZvM2z3d_5lutQO8bspLgG4zgQibtVklN7lz8fX/exec"

POLL_INTERVAL = 60   # 1 minuto
# ==========================


async def connect_to_chat():
    uri = "wss://irc-ws.chat.twitch.tv:443"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(f"PASS oauth:{TOKEN}")
                await ws.send(f"NICK {BOT_NAME}")
                await ws.send("CAP REQ :twitch.tv/commands twitch.tv/tags")
                await ws.send(f"JOIN #{CHANNEL}")
                print(f"✅ (Chat) Conectado a: {CHANNEL}")

                while True:
                    msg = await ws.recv()

                    if msg.startswith("PING"):
                        await ws.send("PONG :tmi.twitch.tv")
                        continue

                    if "PRIVMSG" in msg:
                        prefix = msg.split("PRIVMSG")[0]
                        username = prefix.split("display-name=",1)[1].split(";",1)[0]
                        text = msg.split("PRIVMSG",1)[1].split(" :",1)[1].strip().lower()

                        print(f"  (Chat) {username}: {text}")

                        # --- ASISTENCIA ---
                        if text.startswith("!asistencia"):
                            print(f"⚡ Registrando asistencia de {username}")
                            try:
                                r = requests.get(GAS_WEBHOOK_URL, params={
                                    "action": "asistencia",
                                    "user": username
                                }, timeout=5)

                                resp = r.text.strip()

                                if resp == "ya_registrado":
                                    print(f"⛔ {username} ya registró asistencia.")
                                elif resp in ("normal", "tarde"):
                                    print(f"✅ Asistencia {resp} para {username}")
                                else:
                                    print(f"⚠️ GAS dijo: {resp}")

                            except Exception as e:
                                print(f"ERROR: {e}")

                        # --- EXTRA ---
                        elif text == "!asistenciaextra":
                            print(f"⚡ Registrando extra de {username}")
                            try:
                                r = requests.get(GAS_WEBHOOK_URL, params={
                                    "action": "extra",
                                    "user": username
                                }, timeout=5)

                                resp = r.text.strip()

                                if resp == "extra_ya_registrada":
                                    print(f"⛔ {username} ya registró extra.")
                                elif resp == "extra_ok":
                                    print(f"✨ Extra OK para {username}")
                                else:
                                    print(f"⚠️ GAS dijo: {resp}")

                            except Exception as e:
                                print(f"ERROR: {e}")

        except Exception as e:
            print(f"⚠️ (Chat) Error: {e}. Reintentando...")
            await asyncio.sleep(10)


async def poll_stream_status():
    global stream_is_online

    url = f"https://api.twitch.tv/helix/streams?user_id={BROADCASTER_ID}"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {APP_TOKEN}"
    }

    print("Iniciando polling cada 1 minuto...")

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=5)

            if r.status_code == 200:
                live = len(r.json().get("data", [])) > 0

                if live and not stream_is_online:
                    print("🔴 STREAM INICIADO → Guardando startTimeUTC")
                    requests.get(GAS_WEBHOOK_URL, params={"action": "stream_start"}, timeout=5)

                elif not live and stream_is_online:
                    print("⚫ STREAM FINALIZADO → Guardando endTimeUTC")
                    requests.get(GAS_WEBHOOK_URL, params={"action": "stream_stop"}, timeout=5)

                stream_is_online = live

            elif r.status_code == 401:
                print("❌ Error 401: APP_TOKEN inválido o expirado")

            print("  (API) Siguiente chequeo en 1 minuto...")
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"⚠️ (API) Error: {e}. Reintentando en 60s.")
            await asyncio.sleep(60)


async def main():
    task1 = asyncio.create_task(connect_to_chat())
    task2 = asyncio.create_task(poll_stream_status())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    stream_is_online = False

    print("=== BOT ASISTENCIA v3 ===")
    print(f"URL GAS: {GAS_WEBHOOK_URL}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCerrando bot...")
