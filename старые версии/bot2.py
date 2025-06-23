import os
from dotenv import load_dotenv
import telebot
import requests
import json
import time
import signal
import sys
import urllib3
import tempfile

# Отключаем предупреждения о небезопасных SSL-соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Получение токенов из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
SALUTE_TOKEN = os.getenv('SALUTE_TOKEN')
OPENROUTER_TOKEN = os.getenv('OPENROUTER_TOKEN')

# ... existing code ...

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        print(f"Получено голосовое сообщение от {message.from_user.username}")
        
        # Получаем информацию о файле
        file_info = bot.get_file(message.voice.file_id)
        print(f"Информация о файле: {file_info}")
        
        # Скачиваем файл
        downloaded_file = bot.download_file(file_info.file_path)
        print(f"Размер скачанного файла: {len(downloaded_file)} байт")
        
        # Сохраняем оригинальный файл для отладки
        debug_file = os.path.join(TEMP_DIR, f'debug_{int(time.time())}.oga')
        with open(debug_file, 'wb') as f:
            f.write(downloaded_file)
        print(f"Сохранен отладочный файл: {debug_file}")
        
        # Конвертируем аудио
        pcm_audio = convert_audio(downloaded_file)
        
        # Отправляем в SaluteSpeech
        headers = {
            'Authorization': f'Bearer {SALUTE_TOKEN}',
            'Content-Type': 'audio/x-pcm;bit=16;rate=16000;channels=1'
        }
        
        response = requests.post(
            'https://smartspeech.sber.ru/rest/v1/speech:recognize',
            headers=headers,
            data=pcm_audio
        )
        
        if response.status_code != 200:
            print(f"Ошибка SaluteSpeech: {response.text}")
            bot.reply_to(message, "Извините, произошла ошибка при распознавании речи.")
            return
        
        # Получаем текст из ответа
        text = response.json().get('result', [{}])[0].get('text', '')
        print(f"Распознанный текст: {text}")
        
        if not text:
            bot.reply_to(message, "Извините, не удалось распознать речь.")
            return
        
        # Отправляем текст в OpenRouter
        headers = {
            'Authorization': f'Bearer {OPENROUTER_TOKEN}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-repo',  # Замените на ваш репозиторий
            'X-Title': 'Telegram Bot'  # Название вашего приложения
        }
        
        data = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': text}]
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data
        )
        
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
            'Content-Type': 'application/json'
        }
        
        data = {
            'text': reply,
            'voice': 'Bys_24000',
            'format': 'oggopus',
            'sample_rate': 24000
        }
        
        response = requests.post(
            'https://smartspeech.sber.ru/rest/v1/text:synthesize',
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            print(f"Ошибка синтеза речи: {response.text}")
            bot.reply_to(message, "Извините, произошла ошибка при синтезе речи.")
            return
        
        # Отправляем голосовое сообщение
        if not send_voice_with_retry(message.chat.id, response.content, caption=reply):
            bot.reply_to(message, "Извините, произошла ошибка при отправке голосового сообщения.")
            return
        
    except Exception as e:
        print(f"Ошибка при обработке голосового сообщения: {str(e)}")
        bot.reply_to(message, "Извините, произошла ошибка при обработке сообщения.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        print(f"Получено текстовое сообщение от {message.from_user.username}: {message.text}")
        
        # Отправляем текст в OpenRouter
        headers = {
            'Authorization': f'Bearer {OPENROUTER_TOKEN}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-repo',  # Замените на ваш репозиторий
            'X-Title': 'Telegram Bot'  # Название вашего приложения
        }
        
        data = {
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': message.text}]
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data
        )
        
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
            'Content-Type': 'application/json'
        }
        
        data = {
            'text': reply,
            'voice': 'Bys_24000',
            'format': 'oggopus',
            'sample_rate': 24000
        }
        
        response = requests.post(
            'https://smartspeech.sber.ru/rest/v1/text:synthesize',
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            print(f"Ошибка синтеза речи: {response.text}")
            bot.reply_to(message, "Извините, произошла ошибка при синтезе речи.")
            return
        
        # Отправляем голосовое сообщение
        if not send_voice_with_retry(message.chat.id, response.content, caption=reply):
            bot.reply_to(message, "Извините, произошла ошибка при отправке голосового сообщения.")
            return
        
    except Exception as e:
        print(f"Ошибка при обработке текстового сообщения: {str(e)}")
        bot.reply_to(message, "Извините, произошла ошибка при обработке сообщения.")
