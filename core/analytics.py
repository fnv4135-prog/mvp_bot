import os
import json
import logging
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# Константы
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
DEFAULT_SPREADSHEET_ID = "1acJjGdELWRm9urc1q2dDy5OymQ2fN2K-q9njTHpcO-Q"  # твоя таблица
WORKSHEET_NAME = "Лог событий"  # можно изменить


class GoogleSheetsAnalytics:
    """Клиент для отправки событий в Google Sheets."""

    def __init__(self):
        self.sheet = None
        self.spreadsheet_id = None
        self._init_connection()

    def _init_connection(self):
        """Инициализация подключения к Google Sheets с приоритетом переменных окружения."""
        # --- 1. Получаем credentials ---
        creds_json = None

        # Проверяем разные имена переменных (для совместимости)
        for env_var in ["GOOGLE_CREDENTIALS", "GOOGLE_SHEETS_CREDENTIALS_JSON"]:
            creds_json = os.getenv(env_var)
            if creds_json:
                logger.info(f"✅ Используем переменную окружения {env_var}")
                break

        # Если нет переменной, пробуем файл
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

        # --- 2. Парсим JSON (восстанавливаем переносы строк) ---
        try:
            # Заменяем экранированные \n на реальные переносы
            if "\\n" in creds_json:
                creds_json = creds_json.replace("\\n", "\n")
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            self.sheet = None
            return

        # --- 3. Авторизация ---
        try:
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
        except Exception as e:
            logger.error(f"❌ Ошибка авторизации: {e}")
            self.sheet = None
            return

        # --- 4. ID таблицы ---
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", DEFAULT_SPREADSHEET_ID)
        if not self.spreadsheet_id:
            logger.error("❌ Не указан GOOGLE_SHEET_ID")
            self.sheet = None
            return

        # --- 5. Открываем таблицу и лист ---
        try:
            spreadsheet = client.open_by_key(self.spreadsheet_id)

            # Пытаемся получить существующий лист
            try:
                self.sheet = spreadsheet.worksheet(WORKSHEET_NAME)
            except gspread.WorksheetNotFound:
                # Создаём новый лист с заголовками
                self.sheet = spreadsheet.add_worksheet(
                    title=WORKSHEET_NAME,
                    rows=1000,
                    cols=20
                )
                self._ensure_headers()
                logger.info(f"✅ Создан новый лист '{WORKSHEET_NAME}'")

            # Проверяем заголовки (на случай, если лист существовал, но без них)
            self._ensure_headers()
            logger.info("✅ Подключение к Google Sheets установлено")

        except Exception as e:
            logger.error(f"❌ Ошибка открытия таблицы: {e}")
            self.sheet = None

    def _ensure_headers(self):
        """Проверяет и при необходимости создаёт заголовки в первой строке."""
        if not self.sheet:
            return

        try:
            headers = self.sheet.row_values(1)
            expected_headers = [
                "Timestamp", "User ID", "Username", "Action",
                "Bot Mode", "Details", "Source", "Session ID"
            ]

            # Если заголовков нет или они не совпадают — перезаписываем
            if not headers or headers[0] != expected_headers[0]:
                self.sheet.insert_row(expected_headers, index=1)
                logger.info("✅ Заголовки таблицы обновлены")
        except Exception as e:
            logger.error(f"❌ Ошибка проверки заголовков: {e}")

    def log_event(self, user_id: int, username: str = "", action: str = "",
                  bot_mode: str = "", details: str = "", source: str = "telegram_bot") -> bool:
        """
        Записывает событие в Google Sheets.

        Возвращает True при успехе, False при ошибке или отсутствии подключения.
        """
        if not self.sheet:
            # Резервное логирование в консоль
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

            # Асинхронность: gspread синхронный, но для небольшой нагрузки сойдёт.
            # Если бот разрастётся, оберни в asyncio.to_thread()
            self.sheet.append_row(row, value_input_option="USER_ENTERED")

            logger.debug(f"✅ Записано в Google Sheets: {action} для {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка записи в Google Sheets: {e}")
            # Не отключаем sheet полностью, чтобы следующие попытки могли пройти
            return False

    def test_connection(self) -> bool:
        """Проверка доступности таблицы (читать первую ячейку)."""
        if not self.sheet:
            return False
        try:
            self.sheet.acell("A1")  # быстрый запрос
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка проверки соединения: {e}")
            return False


# Глобальный экземпляр для импорта в других модулях
analytics = GoogleSheetsAnalytics()