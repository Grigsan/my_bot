import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SALUTE_API_KEY = "ODg2NjgxNGUtNjA1Yi00NDUxLWI1MDctYzgxNGRmNjE2NTViOmMzZjZiYzA4LTgyNTMtNDcxMC1hYzU4LWYzODM3NDhlNjk0YQ=="  # <-- сюда вставьте ваш Bearer Token

def test_salute_token():
    url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"
    headers = {
        "Authorization": f"Bearer {SALUTE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "text": "Проверка синтеза речи",
        "voice": "Oksana",
        "format": "opus",
        "sampleRateHertz": 48000,
        "emotion": "neutral",
        "speed": 1.0,
        "pitch": 1.0,
        "lang": "ru-RU"
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    print("Статус:", response.status_code)
    if response.status_code == 200:
        print("Токен рабочий! Синтез речи успешен.")
        with open("test_voice.ogg", "wb") as f:
            f.write(response.content)
        print("Файл test_voice.ogg сохранён.")
    else:
        print("Ошибка:", response.text)

test_salute_token()