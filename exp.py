import json
import requests
from pyrogram import Client
from urllib.parse import unquote
import asyncio
from pyrogram.raw.functions.messages import RequestWebView
import time
import random
from fake_useragent import UserAgent

api_id = 28415662
api_hash = 'fcf6dfc9293ee184287b5b27813af309'

# Создаем двух клиентов Telegram
client_1 = Client(name="tg_client_1", api_id=api_id, api_hash=api_hash)
client_2 = Client(name="tg_client_2", api_id=api_id, api_hash=api_hash)

# Асинхронная функция для получения tg_web_app_data
async def get_tg_web_data(client):
    await client.start()
    try:
        web_view = await client.invoke(RequestWebView(
            peer=await client.resolve_peer('notpixel'),
            bot=await client.resolve_peer('notpixel'),
            platform='android',
            from_bot_menu=False,
            url='https://notpx.app/'
        ))
        auth_url = web_view.url
        tg_web_app_data = unquote(auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
        return tg_web_app_data
    finally:
        await client.stop()

# Функция для выполнения запросов claim и repaint
async def send_requests(client):
    while True:
        try:
            tg_web_app_data = await get_tg_web_data(client)
            print("Updated tg_web_app_data:", tg_web_app_data)
            
            headers_claim = {
                "accept": "application/json, text/plain, */*",
                'cache-control': 'no-cache',
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                'content-type': 'application/json',
                "authorization": f"initData {tg_web_app_data}",
                "priority": "u=1, i",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                'user-agent': UserAgent(os='android').random
            }

            # GET запрос к mining/claim
            response_claim = requests.get("https://notpx.app/api/v1/mining/claim", headers=headers_claim)
            print("Claim response:", response_claim.status_code, response_claim.text)

            if response_claim.status_code == 503:
                print("Server overloaded (503). Waiting for 5 minutes...")
                await asyncio.sleep(300)  # Ожидание 5 минут при перегрузке сервера
                continue  # Пропуск текущего цикла и возврат к началу

            # Настройка заголовков для repaint
            data_repaint = {
                "pixelId": 577414,
                "newColor": "#000000"
            }
            while True:
                # Генерация случайного цвета
                x = random.randint(608, 621)
                y = random.randint(370, 420)
                data_repaint["pixelId"] = x * 1000 + y
                print(data_repaint["pixelId"])

                # POST запрос к repaint/start
                response_repaint = requests.post(
                    "https://notpx.app/api/v1/repaint/start",
                    headers=headers_claim,
                    data=json.dumps(data_repaint)
                )

                print("Repaint response:", response_repaint.status_code, response_repaint.text)
                print(f"New pos: {x}{y}")

                if response_repaint.status_code == 400:
                    error_response = response_repaint.json()
                    if error_response.get("code") == 16:  # "insufficient charges amount"
                        print("Insufficient charges, waiting for an hour...")
                        await asyncio.sleep(3060)  # Ждать 1 час
                        break  # Выход из внутреннего цикла, чтобы начать клейминг снова

                elif response_repaint.status_code == 401:
                    error_response = response_repaint.json()
                    if error_response.get("code") == 6:  # "access unauthorized"
                        print("Access unauthorized, updating tg_web_app_data...")
                        break  # Выход из внутреннего цикла, чтобы обновить tgWebData

                elif response_repaint.status_code == 503:
                    print("Server overloaded (503) during repaint. Waiting for 5 minutes...")
                    await asyncio.sleep(300)  # Ожидание 5 минут при перегрузке сервера
                    break  # Прекратить выполнение и начать с нового цикла

        except Exception as e:
            print(f"Error: {e}. Retrying in 5 minutes...")
            await asyncio.sleep(300)  # Ожидание 5 минут в случае ошибки

# Запуск выполнения запросов для нескольких клиентов
async def main():
    await asyncio.gather(
        send_requests(client_1),
        send_requests(client_2)
    )

# Запуск основного процесса без asyncio.run()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
