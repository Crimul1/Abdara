import asyncio
import websockets
import requests
import time

# ========= CONFIG =========
# Tokens y Nombres
TOKEN = "kk7bd8x8qhxeww4x147s1s2rdh0gq6"  # SIN "oauth:" (Tu token de bot)
APP_TOKEN = "epaglgmhskyal8sesozk0egutp7w47"  # Token de App (para la API)
CLIENT_ID = "u4jxn8cgm5ki14grzcmedwc8yh5pr5"

# Info del Canal
BOT_NAME = "crimul_bot"
CHANNEL = "abdara12"
BROADCASTER_ID = "212158819"  # ID numérico del streamer

# URL de Google Apps Script (¡Verifica que sea la tuya!)
GAS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbztCP3mW8PQ7e90UZ5H2iTcK0GIi1oHlI4TefBQ-KX0efxWNC2tpvBqimYab-uvn-3n/exec"

# Tiempo de chequeo de API (en segundos)
POLL_INTERVAL = 300  # 300 segundos = 5 minutos
# ==========================


# Tarea 1: Escuchar el chat de Twitch
async def connect_to_chat():
    uri = "wss://irc-ws.chat.twitch.tv:443"

    while True:  # Bucle de reconexión
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
                        # Extrae el usuario y el texto
                        prefix = msg.split("PRIVMSG", 1)[0]
                        username = prefix.split("display-name=", 1)[1].split(";", 1)[0]
                        text = msg.split("PRIVMSG", 1)[1].split(" :", 1)[1].strip().lower()

                        print(f"  (Chat) {username}: {text}")

                        # --- Lógica de Comandos ---
                        if text.startswith("!asistencia"):
                            print(f"⚡ (Chat) Registrando !asistencia para {username}")
                            try:
                                r = requests.get(GAS_WEBHOOK_URL, params={
                                    "action": "asistencia",
                                    "user": username
                                }, timeout=5)

                                resp = r.text.strip()

                                # 🔒 NUEVO: manejo de límite
                                if resp == "ya_registrado":
                                    print(f"⛔ {username} ya registró asistencia.")
                                elif resp in ("normal", "tarde"):
                                    print(f"✅ Asistencia guardada para {username}: {resp}")
                                else:
                                    print(f"⚠️ Respuesta GAS: {resp}")

                            except requests.RequestException as e:
                                print(f"ERROR al enviar !asistencia: {e}")

                        elif text == "!asistenciaextra":
                            print(f"⚡ (Chat) Registrando !asistenciaextra para {username}")
                            try:
                                r = requests.get(GAS_WEBHOOK_URL, params={
                                    "action": "extra",
                                    "user": username
                                }, timeout=5)

                                resp = r.text.strip()

                                # 🔒 NUEVO: manejo de límite para extra
                                if resp == "extra_ya_registrada":
                                    print(f"⛔ {username} ya registró la asistencia extra.")
                                elif resp == "extra_ok":
                                    print(f"✨ Asistencia EXTRA guardada para {username}")
                                else:
                                    print(f"⚠️ Respuesta GAS: {resp}")

                            except requests.RequestException as e:
                                print(f"ERROR al enviar !asistenciaextra: {e}")

        except websockets.exceptions.ConnectionClosed:
            print(f"⚠️ (Chat) Conexión perdida. Reconectando en 10 segundos...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"⚠️ (Chat) Error inesperado: {e}. Reconectando en 10 segundos...")
            await asyncio.sleep(10)


# Tarea 2: Preguntar a la API si el stream está vivo (Polling)
async def poll_stream_status():
    global stream_is_online  # Variable global para saber el estado

    url_helix = f"https://api.twitch.tv/helix/streams?user_id={BROADCASTER_ID}"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {APP_TOKEN}"
    }

    print(" polling")

    while True:
        try:
            r = requests.get(url_helix, headers=headers, timeout=5)

            if r.status_code == 200:
                data = r.json().get("data", [])

                current_status_is_online = len(data) > 0

                if current_status_is_online and not stream_is_online:
                    print("🔴 (API) STREAM INICIADO. Guardando startTimeUTC...")
                    requests.get(GAS_WEBHOOK_URL, params={"action": "stream_start"}, timeout=5)

                elif not current_status_is_online and stream_is_online:
                    print("⚫ (API) STREAM FINALIZADO. Guardando endTimeUTC...")
                    requests.get(GAS_WEBHOOK_URL, params={"action": "stream_stop"}, timeout=5)

                stream_is_online = current_status_is_online

            elif r.status_code == 401:
                print("Error 401: Token (APP_TOKEN) inválido o expirado.")
            
            print(f"  (API) Chequeo realizado. Próximo chequeo en {POLL_INTERVAL} segundos.")
            await asyncio.sleep(POLL_INTERVAL)

        except requests.RequestException as e:
            print(f"⚠️ (API) Error de conexión al consultar API: {e}. Reintentando en 60s.")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"⚠️ (API) Error inesperado: {e}. Reintentando en 60s.")
            await asyncio.sleep(60)


# Función principal
async def main():
    task_chat = asyncio.create_task(connect_to_chat())
    task_api_poll = asyncio.create_task(poll_stream_status())
    await asyncio.gather(task_chat, task_api_poll)


if __name__ == "__main__":
    stream_is_online = False

    print("=== INICIANDO BOT DE ASISTENCIA (Chat + Polling API) ===")
    print(f"URL de Google Script: {GAS_WEBHOOK_URL}")
    print("Presiona Ctrl+C para detener.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCerrando bot...")


