    import os
    import telebot
    import requests
    import json
    import time
    import sys
    import tempfile
    from gtts import gTTS
    import re
    from flask import Flask
    from threading import Thread

    # --- Веб-сервер для Render ---
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "I'm alive"

    def run_flask():
      port = int(os.environ.get('PORT', 5000))
      app.run(host='0.0.0.0', port=port)

    # --- Основной код бота ---
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

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

            clean_response = re.sub(r'[\-*#"“”«»—–]+', '', ai_response)

            tts = gTTS(clean_response, lang='ru')
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=TEMP_DIR) as tmp_file:
                tts.write_to_fp(tmp_file)
                tmp_file_path = tmp_file.name

            with open(tmp_file_path, "rb") as audio:
                bot.send_voice(message.chat.id, audio)

            os.remove(tmp_file_path)

            bot.send_message(message.chat.id, clean_response)

        except Exception as e:
            print(f"Ошибка: {str(e)}")
            bot.reply_to(message, f"⚠️ Произошла ошибка: {str(e)}")


    def run_bot():
        print("Бот запущен...")
        bot.polling(none_stop=True)

    if __name__ == '__main__':
        # Запускаем Flask в одном потоке, а бота - в другом
        flask_thread = Thread(target=run_flask)
        flask_thread.start()

        run_bot()