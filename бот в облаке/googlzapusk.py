import telebot
import requests
import tempfile
import os
import sys
import time
import signal
from gtts import gTTS
import re
from dotenv import load_dotenv

# Загружаем переменные из dev.env
load_dotenv(os.path.join(os.path.dirname(__file__), 'dev.env'))

# Получаем ключи из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

# Используем новую бесплатную модель
MODEL_NAME = "deepseek/deepseek-r1-0528-qwen3-8b:free"

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Создание временной директории
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def signal_handler(signum, frame):
    print("Получен сигнал завершения, корректно завершаем работу...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def generate_ai_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://github.com",
        "Content-Type": "application/json",
        "X-Title": "Telegram Bot"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    try:
        print(f"Отправляем запрос к OpenRouter API... Модель: {MODEL_NAME}")
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
    from datetime import datetime

    user_text = message.text.lower()
    if 'время' in user_text or 'который час' in user_text:
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        response = f'Сейчас {time_str}'
        # Озвучка и отправка времени
        tts = gTTS(response, lang='ru')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=TEMP_DIR) as tmp_file:
            tts.write_to_fp(tmp_file)
            tmp_file_path = tmp_file.name
        with open(tmp_file_path, "rb") as audio:
            bot.send_voice(message.chat.id, audio)
        os.remove(tmp_file_path)
        bot.send_message(message.chat.id, response)
        return  # Не отправлять запрос в AI

    try:
        print(f"Получено текстовое сообщение от {message.from_user.username}: {message.text}")
        bot.send_chat_action(message.chat.id, 'typing')
        ai_response = generate_ai_response(message.text)
        print(f"Ответ ИИ: {ai_response}")

        # Очищаем текст от *, #, кавычек, тире и других нежелательных символов
        clean_response = re.sub(r'[\-*#"""«»—–]+', '', ai_response)

        # Синтез речи через gTTS
        tts = gTTS(clean_response, lang='ru')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=TEMP_DIR) as tmp_file:
            tts.write_to_fp(tmp_file)
            tmp_file_path = tmp_file.name

        with open(tmp_file_path, "rb") as audio:
            bot.send_voice(message.chat.id, audio)

        os.remove(tmp_file_path)

        # Затем отправляем очищенный текстовый ответ
        bot.send_message(message.chat.id, clean_response)

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
        print(f"Произошла ошибка: {e}")
        sys.exit(1)