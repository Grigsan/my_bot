import os
import telebot
import requests
import json
import time
import signal
import sys
import urllib3

# Отключаем предупреждения о небезопасных SSL-соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация
TELEGRAM_TOKEN = "8085023273:AAEEprv8N5caD9Hr75CvNUbvYsOMD3MQfUE"
OPENROUTER_KEY = "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"

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Создание временной директории
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def signal_handler(signum, frame):
    """Обработчик сигналов завершения"""
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

def generate_ai_response(prompt):
    """Генерация ответа через OpenRouter"""
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
    """Обработчик команды /start"""
    bot.reply_to(message, "Привет! Я бот, который может отвечать на ваши сообщения. Просто напишите что-нибудь!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик текстовых сообщений"""
    try:
        print(f"Получено текстовое сообщение от {message.from_user.username}: {message.text}")
        
        # Показываем статус "печатает"
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Генерация ответа ИИ
        ai_response = generate_ai_response(message.text)
        print(f"Ответ ИИ: {ai_response}")
        
        # Отправка ответа
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        bot.reply_to(message, f"⚠️ Произошла ошибка: {str(e)}")

if __name__ == '__main__':
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