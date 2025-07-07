import telebot
import requests
import urllib.parse
import os
import re
from bs4 import BeautifulSoup
import json
import time
from telebot import types

# Получаем токены из переменных окружения для безопасности (Render.com)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
VK_API_TOKEN = os.getenv('VK_API_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError('TELEGRAM_TOKEN не найден! Добавьте его в переменные окружения Render.com')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def clean_name(name):
    """Очищает имя от лишних символов"""
    return re.sub(r'[^\w\s]', '', name).strip().lower()

def is_exact_match(full_name, profile_name):
    """Проверяет точное совпадение имени"""
    full_clean = clean_name(full_name)
    profile_clean = clean_name(profile_name)
    
    # Разбиваем на слова
    full_words = set(full_clean.split())
    profile_words = set(profile_clean.split())
    
    # Проверяем, что все слова из полного имени есть в профиле
    return full_words.issubset(profile_words)

def generate_nicknames(name, surname):
    """Генерирует 5 популярных форматов никнеймов по имени и фамилии."""
    name = name.lower()
    surname = surname.lower()
    return [
        f"{name}{surname}",
        f"{name}_{surname}",
        f"{name}.{surname}",
        f"{name}-{surname}",
        f"{surname}.{name}"
    ]

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🔍 Поиск в соцсетях")
    btn2 = types.KeyboardButton("🎮 Поиск в игровых сервисах")
    btn3 = types.KeyboardButton("✉️ Поиск по email")
    btn4 = types.KeyboardButton("📞 Поиск по телефону")
    btn5 = types.KeyboardButton("🧾 Поиск по ИНН")
    btn6 = types.KeyboardButton("🧾 Поиск по СНИЛС")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    bot.send_message(message.chat.id, "Привет! Я OSINT-бот. Выбери, что ты хочешь искать:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Поиск в соцсетях")
def menu_find_social(message):
    bot.send_message(message.chat.id, "Напиши /find Имя Фамилия для поиска в соцсетях.")

@bot.message_handler(func=lambda message: message.text == "🎮 Поиск в игровых сервисах")
def menu_find_gamer(message):
    bot.send_message(message.chat.id, "Напиши /find_gamer Имя Фамилия для поиска в игровых сервисах.")

@bot.message_handler(func=lambda message: message.text == "✉️ Поиск по email")
def menu_find_email(message):
    bot.send_message(message.chat.id, "Напиши /find_email email для поиска по email.")

@bot.message_handler(func=lambda message: message.text == "📞 Поиск по телефону")
def menu_find_phone(message):
    bot.send_message(message.chat.id, "Напиши /find_phone телефон для поиска по телефону.")

@bot.message_handler(func=lambda message: message.text == "🧾 Поиск по ИНН")
def menu_find_inn(message):
    bot.send_message(message.chat.id, "Напиши /find_inn ИНН для поиска по ИНН.")

@bot.message_handler(func=lambda message: message.text == "🧾 Поиск по СНИЛС")
def menu_find_snils(message):
    bot.send_message(message.chat.id, "Напиши /find_snils СНИЛС для поиска по СНИЛС.")

def parse_vk_search(name, surname, count=10):
    """Парсинг поиска ВКонтакте"""
    full_name = f"{name} {surname}"
    encoded_name = urllib.parse.quote(full_name)
    url = f"https://vk.com/search?c%5Bq%5D={encoded_name}&c%5Bsection%5D=people"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # Ищем профили в результатах поиска
        profile_links = soup.find_all('a', href=re.compile(r'/id\d+'))
        
        for link in profile_links[:20]:  # Проверяем больше ссылок
            profile_url = 'https://vk.com' + link.get('href')
            profile_name = link.get_text(strip=True)
            
            if is_exact_match(full_name, profile_name):
                results.append((profile_name, profile_url))
                if len(results) >= count:
                    break
        
        return results
    except Exception as e:
        return [("Ошибка парсинга VK", str(e))]

def parse_ok_search(name, surname, count=10):
    """Парсинг поиска Одноклассников"""
    full_name = f"{name} {surname}"
    encoded_name = urllib.parse.quote(full_name)
    url = f"https://ok.ru/search?st.query={encoded_name}&st.mode=Users"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # Ищем профили в результатах поиска
        profile_links = soup.find_all('a', href=re.compile(r'/profile/\d+'))
        
        for link in profile_links[:20]:
            profile_url = 'https://ok.ru' + link.get('href')
            profile_name = link.get_text(strip=True)
            
            if is_exact_match(full_name, profile_name):
                results.append((profile_name, profile_url))
                if len(results) >= count:
                    break
        
        return results
    except Exception as e:
        return [("Ошибка парсинга OK", str(e))]

def parse_instagram_search(name, surname, count=10):
    """Парсинг поиска Instagram (через теги)"""
    full_name = f"{name}{surname}"
    url = f"https://www.instagram.com/explore/tags/{full_name.lower()}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # Ищем ссылки на профили
        profile_links = soup.find_all('a', href=re.compile(r'/[^/]+/$'))
        
        for link in profile_links[:20]:
            profile_url = 'https://www.instagram.com' + link.get('href')
            profile_name = link.get('href').strip('/')
            
            if is_exact_match(full_name, profile_name):
                results.append((profile_name, profile_url))
                if len(results) >= count:
                    break
        
        return results
    except Exception as e:
        return [("Ошибка парсинга Instagram", str(e))]

def parse_telegram_search(name, surname, count=10):
    """Парсинг поиска Telegram"""
    full_name = f"{name}{surname}"
    url = f"https://t.me/s/{full_name.lower()}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # Ищем ссылки на каналы/чаты
        channel_links = soup.find_all('a', href=re.compile(r'/s/[^/]+'))
        
        for link in channel_links[:20]:
            profile_url = 'https://t.me' + link.get('href')
            profile_name = link.get('href').split('/')[-1]
            
            if is_exact_match(full_name, profile_name):
                results.append((profile_name, profile_url))
                if len(results) >= count:
                    break
        
        return results
    except Exception as e:
        return [("Ошибка парсинга Telegram", str(e))]

def parse_search_results(email, engine="google", count=10):
    """Парсит поисковую выдачу Google или Яндекс по email и возвращает список (title, url)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    if engine == "google":
        url = f"https://www.google.com/search?q={urllib.parse.quote(email)}"
    else:
        url = f"https://yandex.ru/search/?text={urllib.parse.quote(email)}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        if engine == "google":
            for g in soup.find_all('div', class_='tF2Cxc')[:count]:
                a = g.find('a')
                title = g.find('h3')
                if a and title:
                    results.append((title.get_text(strip=True), a['href']))
        else:
            for li in soup.find_all('li', class_='serp-item')[:count]:
                a = li.find('a', href=True)
                title = a.get_text(strip=True) if a else None
                href = a['href'] if a else None
                if title and href:
                    results.append((title, href))
            # Альтернативно для Яндекса:
            if not results:
                for a in soup.find_all('a', attrs={'accesskey': True}, href=True)[:count]:
                    title = a.get_text(strip=True)
                    href = a['href']
                    if title and href:
                        results.append((title, href))
        return results
    except Exception as e:
        return [(f"Ошибка парсинга {engine}", str(e))]

@bot.message_handler(commands=['find'])
def find_person(message):
    bot.send_chat_action(message.chat.id, 'typing')  # Показываем, что бот печатает
    query = message.text.replace('/find', '').strip()
    if not query or len(query.split()) < 2:
        bot.send_message(message.chat.id, "Пожалуйста, укажи имя и фамилию после команды /find (например: /find Иван Иванов)")
        return

    name, surname = query.split(' ', 1)
    full_name = f"{name} {surname}"
    
    # Отправляем сообщение о начале поиска
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Парсим результаты из разных соцсетей (теперь count=10)
    vk_results = parse_vk_search(name, surname, count=10)
    ok_results = parse_ok_search(name, surname, count=10)
    insta_results = parse_instagram_search(name, surname, count=10)
    tg_results = parse_telegram_search(name, surname, count=10)
    
    # Формируем результат
    result = f"🔍 <b>Результаты поиска для: {full_name}</b>\n\n"
    
    # VK результаты
    if vk_results and not vk_results[0][0].startswith("Ошибка"):
        if len(vk_results) > 0:
            result += "📘 <b>ВКонтакте (топ-10):</b>\n"
            for profile_name, profile_url in vk_results:
                result += f"• <a href='{profile_url}'>{profile_name}</a>\n"
            result += "\n"
        else:
            result += "📘 <b>ВКонтакте:</b> Совпадений не найдено\n\n"
    else:
        result += "📘 <b>ВКонтакте:</b> <a href='https://vk.com/search?c%5Bq%5D=" + urllib.parse.quote(full_name) + "&c%5Bsection%5D=people'>Поиск</a>\n\n"
    
    # Одноклассники результаты
    if ok_results and not ok_results[0][0].startswith("Ошибка"):
        if len(ok_results) > 0:
            result += "👥 <b>Одноклассники (топ-10):</b>\n"
            for profile_name, profile_url in ok_results:
                result += f"• <a href='{profile_url}'>{profile_name}</a>\n"
            result += "\n"
        else:
            result += "👥 <b>Одноклассники:</b> Совпадений не найдено\n\n"
    else:
        result += "👥 <b>Одноклассники:</b> <a href='https://ok.ru/search?st.query=" + urllib.parse.quote(full_name) + "&st.mode=Users'>Поиск</a>\n\n"
    
    # Instagram результаты
    if insta_results and not insta_results[0][0].startswith("Ошибка"):
        if len(insta_results) > 0:
            result += "📷 <b>Instagram (топ-10):</b>\n"
            for profile_name, profile_url in insta_results:
                result += f"• <a href='{profile_url}'>{profile_name}</a>\n"
            result += "\n"
        else:
            result += "📷 <b>Instagram:</b> Совпадений не найдено\n\n"
    else:
        result += "📷 <b>Instagram:</b> <a href='https://www.instagram.com/explore/tags/" + full_name.replace(' ', '').lower() + "/'>Поиск</a>\n\n"
    
    # Telegram результаты
    if tg_results and not tg_results[0][0].startswith("Ошибка"):
        if len(tg_results) > 0:
            result += "📱 <b>Telegram (топ-10):</b>\n"
            for profile_name, profile_url in tg_results:
                result += f"• <a href='{profile_url}'>{profile_name}</a>\n"
            result += "\n"
        else:
            result += "📱 <b>Telegram:</b> Совпадений не найдено\n\n"
    else:
        result += "📱 <b>Telegram:</b> <a href='https://t.me/s/" + full_name.replace(' ', '').lower() + "'>Поиск</a>\n\n"
    
    # Дополнительные ссылки
    result += "🔗 <b>Дополнительные поиски:</b>\n"
    result += f"• <a href='https://www.google.com/search?q={urllib.parse.quote(full_name)}'>Google</a>\n"
    result += f"• <a href='https://yandex.ru/search/?text={urllib.parse.quote(full_name)}'>Яндекс</a>\n"
    result += f"• <a href='https://www.facebook.com/search/people/?q={urllib.parse.quote(full_name)}'>Facebook</a>\n"
    result += f"• <a href='https://www.youtube.com/results?search_query={urllib.parse.quote(full_name)}'>YouTube</a>\n"
    result += f"• <a href='https://rutube.ru/search?text={urllib.parse.quote(full_name)}'>RUTUBE</a>\n"
    
    result += "\n<i>💡 Бот показывает только точные совпадения по имени и фамилии. Для расширенного поиска используйте дополнительные ссылки.</i>"
    
    result += "\n<b>Государственные и судебные реестры:</b>\n" + get_gov_links(full_name)
    result += "\n<b>Новости и СМИ:</b>\n" + get_news_links(full_name)
    result += "\n<b>Карты и объявления:</b>\n" + get_map_links(full_name)
    
    bot.send_message(message.chat.id, result, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['find_email'])
def find_by_email(message):
    email = message.text.replace('/find_email', '').strip()
    if not email:
        bot.send_message(message.chat.id, "Пожалуйста, укажи email после команды /find_email")
        return
    google_results = parse_search_results(email, engine="google", count=10)
    yandex_results = parse_search_results(email, engine="yandex", count=10)
    result = f"🔍 <b>Результаты поиска для email: {email}</b>\n\n"
    result += "<b>Google:</b>\n"
    if google_results and not google_results[0][0].startswith("Ошибка"):
        for title, url in google_results:
            result += f"• <a href='{url}'>{title}</a>\n"
    else:
        result += "• Ошибка парсинга Google\n"
    result += "\n<b>Яндекс:</b>\n"
    if yandex_results and not yandex_results[0][0].startswith("Ошибка"):
        for title, url in yandex_results:
            result += f"• <a href='{url}'>{title}</a>\n"
    else:
        result += "• Ошибка парсинга Яндекс\n"
    result += "\n<i>Для расширенного поиска используйте дополнительные сервисы.</i>"
    bot.send_message(message.chat.id, result, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['find_phone'])
def find_by_phone(message):
    phone = message.text.replace('/find_phone', '').strip()
    if not phone:
        bot.send_message(message.chat.id, "Пожалуйста, укажи телефон после команды /find_phone")
        return
    google_url = f"https://www.google.com/search?q={urllib.parse.quote(phone)}"
    yandex_url = f"https://yandex.ru/search/?text={urllib.parse.quote(phone)}"
    result = (
        f"🔍 <b>Результаты поиска для телефона: {phone}</b>\n\n"
        f"• <a href='{google_url}'>Google</a>\n"
        f"• <a href='{yandex_url}'>Яндекс</a>\n"
        "\n<i>Для расширенного поиска используйте дополнительные сервисы.</i>"
    )
    bot.send_message(message.chat.id, result, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['find_inn'])
def find_by_inn(message):
    inn = message.text.replace('/find_inn', '').strip()
    if not inn:
        bot.send_message(message.chat.id, "Пожалуйста, укажи ИНН после команды /find_inn")
        return
    nalog_url = f"https://service.nalog.ru/inn.do"
    result = (
        f"🔍 <b>Проверка ИНН: {inn}</b>\n\n"
        f"• <a href='{nalog_url}'>Проверить на сайте ФНС</a>\n"
    )
    bot.send_message(message.chat.id, result, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['find_snils'])
def find_by_snils(message):
    snils = message.text.replace('/find_snils', '').strip()
    if not snils:
        bot.send_message(message.chat.id, "Пожалуйста, укажи СНИЛС после команды /find_snils")
        return
    result = (
        f"🔍 <b>Проверка СНИЛС: {snils}</b>\n\n"
        f"• <a href='https://www.gosuslugi.ru/'>Проверить на Госуслугах</a>\n"
    )
    bot.send_message(message.chat.id, result, parse_mode='HTML', disable_web_page_preview=True)

def get_gov_links(full_name):
    encoded = urllib.parse.quote(full_name)
    return (
        f"• <a href='https://fssp.gov.ru/iss/ip'>ФССП (исполнительные производства)</a>\n"
        f"• <a href='https://kad.arbitr.ru/'>Арбитражный суд</a>\n"
        f"• <a href='https://sudrf.ru/'>Судебные дела</a>\n"
        f"• <a href='https://bankrot.fedresurs.ru/'>Реестр банкротов</a>\n"
        f"• <a href='https://zakupki.gov.ru/'>Госзакупки</a>\n"
    )

def get_news_links(full_name):
    encoded = urllib.parse.quote(full_name)
    return (
        f"• <a href='https://news.google.com/search?q={encoded}'>Google News</a>\n"
        f"• <a href='https://news.yandex.ru/yandsearch?text={encoded}'>Яндекс.Новости</a>\n"
    )

def get_map_links(full_name):
    encoded = urllib.parse.quote(full_name)
    return (
        f"• <a href='https://2gis.ru/search/{encoded}'>2GIS</a>\n"
        f"• <a href='https://yandex.ru/maps/?text={encoded}'>Яндекс.Карты</a>\n"
        f"• <a href='https://www.google.com/maps/search/{encoded}'>Google Maps</a>\n"
        f"• <a href='https://www.avito.ru/rossiya?q={encoded}'>Avito</a>\n"
    )

def get_gamer_profiles(username):
    """Возвращает ссылки на профили пользователя в популярных игровых сервисах по никнейму."""
    profiles = []
    # Twitch
    profiles.append(("Twitch", f"https://www.twitch.tv/{username}"))
    # Steam (поиск по кастомному ID)
    profiles.append(("Steam (Custom ID)", f"https://steamcommunity.com/id/{username}"))
    # Steam (поиск по числовому SteamID64)
    profiles.append(("Steam (SteamID64)", f"https://steamcommunity.com/profiles/{username}"))
    # Epic Games (поиск по никнейму через сайт Fortnite)
    profiles.append(("Epic Games (Fortnite)", f"https://fortnitetracker.com/profile/all/{username}"))
    # Battle.net (поиск по никнейму)
    profiles.append(("Battle.net", f"https://battle.net/{username}"))
    # Discord (поиск по тегу, только ссылка на Discord, т.к. профили приватные)
    profiles.append(("Discord", f"https://discord.com/users/{username}"))
    # Xbox Live
    profiles.append(("Xbox Live", f"https://account.xbox.com/en-us/Profile?gamertag={username}"))
    # Origin (EA)
    profiles.append(("Origin (EA)", f"https://www.ea.com/profile/{username}"))
    # Uplay (Ubisoft Connect)
    profiles.append(("Uplay (Ubisoft Connect)", f"https://ubisoftconnect.com/en-US/profile/{username}"))
    return profiles

@bot.message_handler(commands=['find_gamer'])
def find_gamer(message):
    query = message.text.replace('/find_gamer', '').strip()
    if not query or len(query.split()) < 2:
        bot.send_message(message.chat.id, "Пожалуйста, укажи имя и фамилию после команды /find_gamer (например: /find_gamer Иван Иванов)")
        return
    name, surname = query.split(' ', 1)
    nicknames = generate_nicknames(name, surname)
    result = f"\U0001F3AE <b>Варианты профилей для: {name} {surname}</b>\n\n"
    for nickname in nicknames:
        result += f"<b>Никнейм:</b> {nickname}\n"
        profiles = get_gamer_profiles(nickname)
        for service, url in profiles:
            result += f"• <b>{service}:</b> <a href='{url}'>{url}</a>\n"
        result += "\n"
    result += "<i>Некоторые сервисы могут требовать авторизацию или не поддерживать прямой поиск по никнейму.</i>"
    bot.send_message(message.chat.id, result, parse_mode='HTML', disable_web_page_preview=True)

if __name__ == '__main__':
    print("OSINT-бот запущен!")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"Ошибка в polling: {e}")
            time.sleep(5)  # Подождать 5 секунд и попробовать снова