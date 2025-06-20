import os
import telebot
import requests
import json
import time
import signal
import sys
import tempfile
from gtts import gTTS
import logging
from datetime import datetime
import re

# Конфигурация
TELEGRAM_TOKEN = "8085023273:AAEEprv8N5caD9Hr75CvNUbvYsOMD3MQfUE"
OPENROUTER_KEY = "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"

# Настройка логирования
logging.basicConfig(
    filename='/home/grigson69/mytelegrambot/bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Создание временной директории
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def signal_handler(signum, frame):
    print("Получен сигнал завершения, корректно завершаем работу...")
    sys.exit(0)

# Регистрируем обработчик сигналов
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

        # Очищаем текст от *, #, кавычек и других нежелательных символов
        clean_response = re.sub(r'[*#"“"«»]', '', ai_response)

        # Сначала отправляем очищенный текстовый ответ
        bot.send_message(message.chat.id, clean_response)

        # Синтез речи через gTTS
        tts = gTTS(clean_response, lang='ru')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=TEMP_DIR) as tmp_file:
            tts.write_to_fp(tmp_file)
            tmp_file_path = tmp_file.name

        with open(tmp_file_path, "rb") as audio:
            bot.send_voice(message.chat.id, audio)

        os.remove(tmp_file_path)

    except Exception as e:
        print(f"Ошибка: {str(e)}")
        bot.reply_to(message, f"⚠️ Произошла ошибка: {str(e)}")

if __name__ == '__main__':
    try:
        logging.info("Бот запущен")
        print("Бот запущен...")
        bot.remove_webhook()
        time.sleep(1)
        bot.polling(none_stop=True, interval=1, timeout=60, long_polling_timeout=60)
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        sys.exit(1)