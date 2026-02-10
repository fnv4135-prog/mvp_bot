# core/analytics.py
import os
import json
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

logger = logging.getLogger(__name__)


class GoogleSheetsAnalytics:
    def __init__(self):
        self.sheet = None
        self.init_connection()

    def init_connection(self):
        """Инициализация подключения к Google Sheets"""
        try:
            # Сначала пробуем получить JSON из переменной окружения
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")

            if creds_json:
                # Парсим JSON из строки
                creds_info = json.loads(creds_json)
                scope = ['https://spreadsheets.google.com/feeds',
                         'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_info(creds_info, scopes=scope)
                logger.info("✅ Используем Google Sheets из переменной окружения")
            else:
                # Пробуем файл (если есть)
                creds_file = "gsheets_credentials.json"
                if not os.path.exists(creds_file):
                    logger.warning("❌ Нет данных для Google Sheets (ни файла, ни переменной)")
                    self.sheet = None
                    return

                scope = ['https://spreadsheets.google.com/feeds',
                         'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_file(creds_file, scopes=scope)
                logger.info("✅ Используем Google Sheets из файла")

            # Подключаемся к таблице
            client = gspread.authorize(creds)
            spreadsheet_id = "1acJjGdELWRm9urc1q2dDy5OymQ2fN2K-q9njTHpcO-Q"
            spreadsheet = client.open_by_key(spreadsheet_id)
            self.sheet = spreadsheet.sheet1

            # Проверяем заголовки
            headers = self.sheet.row_values(1)
            if not headers or headers[0] != "Timestamp":
                new_headers = ["Timestamp", "User ID", "Username", "Action",
                               "Bot Mode", "Details", "Source", "Session ID"]
                self.sheet.insert_row(new_headers, index=1)
                logger.info("Созданы заголовки таблицы")

            logger.info("✅ Подключение к Google Sheets установлено")

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Google Sheets: {e}")
            self.sheet = None

    def log_event(self, user_id: int, username: str, action: str,
                  bot_mode: str = "", details: str = "", source: str = "telegram_bot"):
        """Логирование события в Google Sheets"""

        if not self.sheet:
            # Если нет подключения, просто логируем в консоль
            logger.info(f"[ANALYTICS] {user_id} | {action} | {bot_mode} | {details}")
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username_clean = username or ""
            session_id = f"{datetime.now().strftime('%Y%m%d')}_{user_id}"

            row_data = [
                timestamp,
                user_id,
                username_clean,
                action,
                bot_mode,
                details,
                source,
                session_id
            ]

            self.sheet.append_row(row_data)
            logger.debug(f"✅ Записано в Google Sheets: {action} для {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка записи в Google Sheets: {e}")
            return False


# Глобальный экземпляр
analytics = GoogleSheetsAnalytics()