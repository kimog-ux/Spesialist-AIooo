import requests

try:
    response = requests.get('https://api.telegram.org', timeout=10)
    if response.status_code == 200:
        print("✅ Соединение с Telegram API работает")
    else:
        print(f"❌ Ошибка HTTP: {response.status_code}")
except Exception as e:
    print(f"❌ Критическая ошибка соединения: {e}")