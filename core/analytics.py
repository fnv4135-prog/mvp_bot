import os
import json
import base64
import logging
from datetime import datetime

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
        """Инициализация подключения с детальными отпечатками."""
        print("🔥🔥🔥 _init_connection ВЫЗВАН 🔥🔥🔥", flush=True)
        logger.info("🚦 НАЧАЛО _init_connection")
        creds_json = None

        # ----- 1. Пробуем base64 -----
        logger.info("🔍 Шаг 1: ищем GOOGLE_CREDENTIALS_BASE64")
        creds_b64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if creds_b64:
            try:
                json_str = base64.b64decode(creds_b64).decode()
                creds_json = json_str
                logger.info(f"✅ Шаг 1.1: base64 декодирован, длина JSON {len(creds_json)}")
            except Exception as e:
                logger.error(f"❌ Шаг 1.1: ошибка декодирования base64: {e}")
        else:
            logger.warning("⚠️ Шаг 1: GOOGLE_CREDENTIALS_BASE64 не найдена")

        # ----- 2. Альтернативные способы (если нет base64) -----
        if not creds_json:
            logger.info("🔍 Шаг 2: пробуем другие переменные")
            for env_var in ["GOOGLE_CREDENTIALS", "GOOGLE_SHEETS_CREDENTIALS_JSON"]:
                creds_json = os.getenv(env_var)
                if creds_json:
                    logger.info(f"✅ Шаг 2.1: найдена переменная {env_var}")
                    break

        # ----- 3. Файл (локально) -----
        if not creds_json:
            logger.info("🔍 Шаг 3: пробуем файл gsheets_credentials.json")
            creds_file = "gsheets_credentials.json"
            if os.path.exists(creds_file):
                try:
                    with open(creds_file, "r") as f:
                        creds_json = f.read()
                    logger.info("✅ Шаг 3.1: файл прочитан")
                except Exception as e:
                    logger.error(f"❌ Шаг 3.1: ошибка чтения файла: {e}")
            else:
                logger.warning("❌ Шаг 3: файл не найден, аналитика отключена")
                self.sheet = None
                return

        if not creds_json:
            logger.error("❌ Шаг: нет credentials, останов")
            self.sheet = None
            return

        # ----- 4. Парсинг JSON -----
        logger.info("🔍 Шаг 4: парсинг JSON")
        try:
            creds_dict = json.loads(creds_json)
            logger.info("✅ Шаг 4.1: JSON успешно распарсен")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Шаг 4.1: ошибка парсинга JSON: {e}")
            self.sheet = None
            return

        # ----- 5. Авторизация -----
        logger.info("🔍 Шаг 5: авторизация в Google")
        try:
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            logger.info("✅ Шаг 5.1: авторизация успешна, client получен")
        except Exception as e:
            logger.error(f"❌ Шаг 5.1: ошибка авторизации: {e}")
            self.sheet = None
            return

        # ----- 6. ID таблицы -----
        logger.info("🔍 Шаг 6: получение ID таблицы")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", DEFAULT_SPREADSHEET_ID)
        logger.info(f"✅ Шаг 6.1: ID таблицы = {self.spreadsheet_id}")
        if not self.spreadsheet_id:
            logger.error("❌ Шаг 6.1: ID таблицы пустой")
            self.sheet = None
            return

        # ----- 7. Открытие таблицы -----
        logger.info("🔍 Шаг 7: открытие таблицы по ID")
        try:
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            logger.info(f"✅ Шаг 7.1: таблица открыта, имя = {spreadsheet.title}")
        except Exception as e:
            logger.error(f"❌ Шаг 7.1: ошибка открытия таблицы: {e}")
            self.sheet = None
            return

        # ----- 8. Получение/создание листа -----
        logger.info(f"🔍 Шаг 8: получение листа {WORKSHEET_NAME}")
        try:
            self.sheet = spreadsheet.worksheet(WORKSHEET_NAME)
            logger.info("✅ Шаг 8.1: лист найден")
        except gspread.WorksheetNotFound:
            logger.info("🔍 Шаг 8.2: лист не найден, создаю новый")
            self.sheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=20)
            self._ensure_headers()
            logger.info("✅ Шаг 8.3: новый лист создан")

        # ----- 9. Проверка/создание заголовков -----
        self._ensure_headers()
        logger.info("✅ Шаг 9: заголовки проверены/созданы")

        # ----- 10. УСПЕХ -----
        logger.info("🎉🎉🎉 ПОДКЛЮЧЕНИЕ К GOOGLE SHEETS УСТАНОВЛЕНО 🎉🎉🎉")
        print("🎉 GOOGLE SHEETS ГОТОВА К РАБОТЕ 🎉", flush=True)

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

    def ensure_connection(self):
        """Если соединение потеряно, пробуем переподключиться."""
        if not self.sheet:
            logger.warning("⚠️ Соединение потеряно, пробую переподключиться...")
            self._init_connection()
        return self.sheet is not None

    def log_event(self, user_id: int, username: str = "", action: str = "",
                  bot_mode: str = "", details: str = "", source: str = "telegram_bot") -> bool:
        """Запись события в Google Sheets."""
        # 🔍 ДИАГНОСТИКА
        logger.info(f"🟡 log_event ВЫЗВАН: action={action}, user={user_id}, bot_mode={bot_mode}")
        logger.info(f"🟡 Состояние self.sheet: {self.sheet is not None}")

        # Если sheet нет, пытаемся переподключиться
        if not self.sheet:
            self.ensure_connection()
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

            # 🟢 Пробуем записать
            self.sheet.append_row(row, value_input_option="USER_ENTERED")
            logger.info(f"✅✅✅ ЗАПИСАНО В GOOGLE SHEETS: {row}")
            return True

        except Exception as e:
            logger.error(f"❌❌❌ ОШИБКА ЗАПИСИ В GOOGLE SHEETS: {e}")
            # Не обнуляем self.sheet — возможно, ошибка временная
            return False

    def test_connection(self) -> bool:
        """Проверка соединения (быстрый запрос)."""
        if not self.sheet:
            return False
        try:
            self.sheet.acell("A1")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка проверки соединения: {e}")
            self.sheet = None  # Сбрасываем, чтобы переподключиться позже
            return False


analytics = GoogleSheetsAnalytics()