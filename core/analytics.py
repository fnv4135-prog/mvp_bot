import os
import json
import base64
import logging
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
DEFAULT_SPREADSHEET_ID = "1acJjGdELWRm9urc1q2dDy5OymQ2fN2K-q9njTHpcO-Q"
WORKSHEET_NAME = "Лог событий"


class GoogleSheetsAnalytics:
    def __init__(self):
        self.sheet = None
        self.spreadsheet_id = None
        self._init_connection()

    def _init_connection(self):
        """Инициализация подключения с приоритетом: base64 -> json-переменная -> файл"""
        creds_json = None

        # 1. Пробуем base64 (РЕКОМЕНДУЕТСЯ)
        creds_b64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if creds_b64:
            try:
                json_str = base64.b64decode(creds_b64).decode()
                creds_json = json_str
                logger.info("✅ Используем GOOGLE_CREDENTIALS_BASE64")
            except Exception as e:
                logger.error(f"❌ Ошибка декодирования base64: {e}")

        # 2. Если нет base64 — пробуем обычную переменную
        if not creds_json:
            for env_var in ["GOOGLE_CREDENTIALS", "GOOGLE_SHEETS_CREDENTIALS_JSON"]:
                creds_json = os.getenv(env_var)
                if creds_json:
                    logger.info(f"✅ Используем переменную окружения {env_var}")
                    break

        # 3. Если ничего нет — пробуем файл (только для локальной разработки)
        if not creds_json:
            creds_file = "gsheets_credentials.json"
            if os.path.exists(creds_file):
                try:
                    with open(creds_file, "r") as f:
                        creds_json = f.read()
                    logger.info("✅ Используем файл gsheets_credentials.json")
                except Exception as e:
                    logger.error(f"❌ Ошибка чтения файла: {e}")
            else:
                logger.warning("❌ Нет данных для Google Sheets. Аналитика отключена.")
                self.sheet = None
                return

        # --- Парсим JSON (БЕЗ ЗАМЕНЫ \\n НА \n — JSON сам разберёт экранирование) ---
        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            self.sheet = None
            return

        # --- Авторизация ---
        try:
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
        except Exception as e:
            logger.error(f"❌ Ошибка авторизации: {e}")
            self.sheet = None
            return

        # --- ID таблицы ---
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", DEFAULT_SPREADSHEET_ID)
        if not self.spreadsheet_id:
            logger.error("❌ Не указан GOOGLE_SHEET_ID")
            self.sheet = None
            return

        # --- Открываем таблицу и лист ---
        try:
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            try:
                self.sheet = spreadsheet.worksheet(WORKSHEET_NAME)
            except gspread.WorksheetNotFound:
                self.sheet = spreadsheet.add_worksheet(
                    title=WORKSHEET_NAME,
                    rows=1000,
                    cols=20
                )
                self._ensure_headers()
                logger.info(f"✅ Создан новый лист '{WORKSHEET_NAME}'")

            self._ensure_headers()
            logger.info("✅ Подключение к Google Sheets установлено")

        except Exception as e:
            logger.error(f"❌ Ошибка открытия таблицы: {e}")
            self.sheet = None

    def _ensure_headers(self):
        """Проверяет и создаёт заголовки."""
        if not self.sheet:
            return
        try:
            headers = self.sheet.row_values(1)
            expected = ["Timestamp", "User ID", "Username", "Action",
                        "Bot Mode", "Details", "Source", "Session ID"]
            if not headers or headers[0] != expected[0]:
                self.sheet.insert_row(expected, index=1)
                logger.info("✅ Заголовки таблицы обновлены")
        except Exception as e:
            logger.error(f"❌ Ошибка заголовков: {e}")

    def log_event(self, user_id: int, username: str = "", action: str = "",
                  bot_mode: str = "", details: str = "", source: str = "telegram_bot") -> bool:
        """Запись события в Google Sheets."""
        if not self.sheet:
            logger.info(f"[ANALYTICS] {user_id} | {action} | {bot_mode} | {details}")
            return False

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username_clean = username or ""
            session_id = f"{datetime.now().strftime('%Y%m%d')}_{user_id}"

            row = [
                timestamp,
                str(user_id),
                username_clean,
                action,
                bot_mode,
                details,
                source,
                session_id
            ]
            self.sheet.append_row(row, value_input_option="USER_ENTERED")
            logger.debug(f"✅ Записано в Google Sheets: {action} для {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка записи: {e}")
            return False

    def test_connection(self) -> bool:
        """Проверка соединения (быстрый запрос)."""
        if not self.sheet:
            return False
        try:
            self.sheet.acell("A1")
            return True
        except:
            return False


analytics = GoogleSheetsAnalytics()