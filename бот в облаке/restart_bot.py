import os
import sys
import subprocess
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    filename='/home/grigson69/mytelegrambot/restart.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def restart_bot():
    try:
        # Путь к основному файлу бота
        bot_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'googlTTs.py')
        
        # Завершаем текущий процесс бота, если он запущен
        os.system('pkill -f googlTTs.py')
        
        # Запускаем бота заново
        subprocess.Popen([sys.executable, bot_script])
        
        logging.info("Бот успешно перезапущен")
        print("Бот успешно перезапущен")
    except Exception as e:
        logging.error(f"Ошибка при перезапуске бота: {str(e)}")
        print(f"Ошибка при перезапуске бота: {str(e)}")

if __name__ == '__main__':
    restart_bot() 