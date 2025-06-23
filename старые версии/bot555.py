import os
import telebot
import requests
import json
import time
import shutil
import datetime
import subprocess
import signal
import sys
import urllib3

# Отключаем предупреждения о небезопасных SSL-соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Токены напрямую
BOT_TOKEN = "8085023273:AAEEprv8N5caD9Hr75CvNUbvYsOMD3MQfUE"
SALUTE_TOKEN = "ODg2NjgxNGUtNjA1Yi00NDUxLWI1MDctYzgxNGRmNjE2NTViOjQzOWU2MmU4LWYwMzctNDlhMi1iNDUzLTQxZDVlNDRkOWRjYg=="
OPENROUTER_TOKEN = "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"

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Создание временной директории
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def signal_handler(signum, frame):
    print("\nПолучен сигнал завершения. Очистка и выход...")
    # Очищаем временные файлы
    for file in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, file))
        except Exception as e:
            print(f"Ошибка при удалении файла {file}: {e}")
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def send_voice_with_retry(chat_id, voice_data, caption=None, max_retries=3):
    """Отправка голосового сообщения с повторными попытками"""
    for attempt in range(max_retries):
        try:
            print(f"Попытка отправки голосового сообщения {attempt + 1}/{max_retries}")
            bot.send_voice(chat_id, voice_data, caption=caption)
            print("Голосовое сообщение успешно отправлено")
            return True
        except Exception as e:
            print(f"Ошибка при отправке голосового сообщения (попытка {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"Ожидание 2 секунды перед следующей попыткой...")
                time.sleep(2)
            else:
                print("Достигнуто максимальное количество попыток")
                return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Привет! Я бот, который может отвечать на голосовые и текстовые сообщения. Просто отправь мне сообщение!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        print(f"Получено текстовое сообщение от {message.from_user.username}: {message.text}")
        
        # Отправляем текст в OpenRouter
        headers = {
            'Authorization': f'Bearer {OPENROUTER_TOKEN}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-repo',
            'X-Title': 'Telegram Bot'
        }
        
        data = {
            'model': 'deepseek/deepseek-chat-v3-0324:free',
            'messages': [{'role': 'user', 'content': message.text}],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        print("Отправляем запрос к OpenRouter API...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data
        )
        
        print(f"Статус ответа OpenRouter: {response.status_code}")
        print(f"Ответ OpenRouter: {response.text}")
        
        if response.status_code != 200:
            print(f"Ошибка OpenRouter: {response.text}")
            bot.reply_to(message, "Извините, произошла ошибка при генерации ответа.")
            return
        
        # Получаем ответ от OpenRouter
        reply = response.json()['choices'][0]['message']['content']
        print(f"Ответ OpenRouter: {reply}")
        
        # Отправляем ответ в SaluteSpeech для синтеза речи
        headers = {
            'Authorization': f'Bearer {SALUTE_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'audio/ogg',
            'User-Agent': 'Mozilla/5.0'
        }
        
        data = {
            'text': reply,
            'voice': 'Bys_24000',
            'format': 'oggopus',
            'sample_rate': 24000,
            'emotion': 'neutral',
            'speed': 1.0,
            'pitch': 1.0
        }
        
        print("Отправляем запрос к SaluteSpeech API...")
        print(f"Заголовки запроса: {headers}")
        print(f"Данные запроса: {data}")
        
        # Отключаем проверку SSL для Salute Speech API
        response = requests.post(
            'https://smartspeech.sber.ru/rest/v1/text:synthesize',
            headers=headers,
            json=data,
            verify=False  # Отключаем проверку SSL
        )
        
        print(f"Статус ответа SaluteSpeech: {response.status_code}")
        print(f"Заголовки ответа: {response.headers}")
        
        if response.status_code != 200:
            print(f"Ошибка синтеза речи: {response.text}")
            bot.reply_to(message, "Извините, произошла ошибка при синтезе речи.")
            return
        
        # Отправляем голосовое сообщение
        print("Отправляем голосовое сообщение...")
        if not send_voice_with_retry(message.chat.id, response.content, caption=reply):
            bot.reply_to(message, "Извините, произошла ошибка при отправке голосового сообщения.")
            return
        
    except Exception as e:
        print(f"Ошибка при обработке текстового сообщения: {str(e)}")
        bot.reply_to(message, "Извините, произошла ошибка при обработке сообщения.")

if __name__ == "__main__":
    try:
        print("Бот запущен...")
        # Удаляем webhook и ждем завершения
        bot.remove_webhook()
        time.sleep(1)
        
        # Запускаем бота с параметрами для избежания конфликтов
        bot.polling(none_stop=True, interval=1, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        print("Завершение работы бота...")
        # Очищаем временные файлы
        for file in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, file))
            except Exception as e:
                print(f"Ошибка при удалении файла {file}: {e}")
