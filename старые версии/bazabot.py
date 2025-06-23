import os
import telebot
import requests
import json
import time
import signal
import sys
import urllib3
import tempfile
import base64

# Отключаем предупреждения о небезопасных SSL-соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация
TELEGRAM_TOKEN = "8085023273:AAEEprv8N5caD9Hr75CvNUbvYsOMD3MQfUE"
OPENROUTER_KEY = "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"

# SaluteSpeech OAuth2
SALUTE_CLIENT_ID = "8866814e-605b-4451-b507-c814df61655b"
SALUTE_CLIENT_SECRET = "ODg2NjgxNGUtNjA1Yi00NDUxLWI1MDctYzgxNGRmNjE2NTViOjcxMjgzNTZkLTcxY2ItNGZlYi1iMTNkLWMzZjAyMDVkODkwNA=="
SALUTE_SCOPE = "SALUTE_SPEECH_PERS"

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Создание временной директории
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def signal_handler(signum, frame):
    print("\nПолучен сигнал завершения. Очистка и выход...")
    for file in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, file))
        except Exception as e:
            print(f"Ошибка при удалении файла {file}: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_salute_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_str = f"{SALUTE_CLIENT_ID}:{SALUTE_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = f"scope={SALUTE_SCOPE}&grant_type=client_credentials"
    print("HEADERS:", headers)
    print("DATA:", data)
    response = requests.post(url, headers=headers, data=data, verify=False)
    print("Ответ сервера при получении токена:", response.status_code, response.text)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Ошибка получения токена: {response.text}")

def synthesize_speech(text):
    token = get_salute_token()
    url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "voice": "Oksana",  # Можно выбрать другой голос
        "format": "opus",
        "sampleRateHertz": 48000,
        "emotion": "neutral",
        "speed": 1.0,
        "pitch": 1.0,
        "lang": "ru-RU"
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Ошибка синтеза речи: {response.status_code} {response.text}")

def generate_ai_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://github.com",      
        "Content-Type": "application/json",
        "X-Title": "Telegram Bot"
    }
    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    try:
        print(f"Отправляем запрос к OpenRouter API...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",     
            headers=headers,
            json=data
        )
        print(f"Статус ответа OpenRouter: {response.status_code}")
        print(f"Ответ OpenRouter: {response.text}")
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"Ошибка генерации ответа: {response.text}")
    except Exception as e:
        raise Exception(f"Ошибка при запросе к OpenRouter: {str(e)}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Привет! Я бот, который может отвечать на ваши сообщения голосом. Просто напишите что-нибудь!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        print(f"Получено текстовое сообщение от {message.from_user.username}: {message.text}")
        bot.send_chat_action(message.chat.id, 'typing')
        ai_response = generate_ai_response(message.text)
        print(f"Ответ ИИ: {ai_response}")
        bot.reply_to(message, ai_response)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        bot.reply_to(message, f"⚠️ Произошла ошибка: {str(e)}")

if __name__ == '__main__':
    try:
        print("Бот запущен...")
        bot.remove_webhook()
        time.sleep(1)
        bot.polling(none_stop=True, interval=1, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        print("Завершение работы бота...")
        for file in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, file))
            except Exception as e:
                print(f"Ошибка при удалении файла {file}: {e}")
