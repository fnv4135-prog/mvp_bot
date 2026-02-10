# 1. Проверь SQLite
import sqlite3
conn = sqlite3.connect('portfolio_bots.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Таблицы в БД:", cursor.fetchall())
conn.close()

# 2. Проверь Google Sheets переменную
import os
print("GOOGLE_SHEETS_CREDENTIALS_JSON есть?", "GOOGLE_SHEETS_CREDENTIALS_JSON" in os.environ)

# 3. Проверь health check
import requests
response = requests.get("https://mvp-4hpg.onrender.com/health")
print("Health check:", response.text)

# 4. Проверь GitHub Pages
response = requests.get("https://fnv4135-prog.github.io/mvp/")
print("Лендинг работает:", response.status_code == 200)